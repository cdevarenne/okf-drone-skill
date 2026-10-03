"""One small, cost-bounded interface to Claude: replay | record | anthropic (set by LLM_MODE).

A reduced copy of okf-grc-skill `llm.py` (DRN-09 spec §6). `replay` is the default and never
calls the API. A paid mode needs LLM_MODE=anthropic or record, set by the owner.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_plan import read_pins

Json = dict[str, Any]
MODES = ("replay", "record", "anthropic")
# USD per million tokens (input, output), from the pricing table of 2026-09-25.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
# Extra output_config per model. Opus 5.5 always thinks; low effort keeps the cost down.
# Haiku 4.5 rejects `effort`.
MODEL_CONFIG: dict[str, Json] = {
    "claude-opus-5-5": {"effort": "low"},
    "claude-sonnet-5-5": {"effort": "low"},
}
CACHE_WRITE, CACHE_READ = 1.25, 0.10  # multipliers on the input price
CHARS_PER_TOKEN = 3  # conservative: overestimates input tokens for the budget guard
REQUEST_TIMEOUT_S = 120.0  # per call; the SDK default is 10 minutes
DEFAULT_BUDGET_USD = "0.50"
USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


class LLMError(RuntimeError):
    """A call failed, was refused, was truncated, or has no recorded answer."""


class BudgetExceeded(LLMError):
    """The next call could make this run spend more than LLM_BUDGET_USD."""


@dataclass(frozen=True)
class Request:
    """One structured-output call. `system` is stable across runs (cached); `user` is per run."""

    task: str
    system: str
    user: str
    schema: Json
    max_tokens: int

    def key(self, model: str) -> str:
        """Return sha256(model + prompt): the name of the cache file and of the fixture."""
        payload = json.dumps([model, self.system, self.user, self.schema], sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cost_usd(model: str, usage: Json) -> float:
    """Return the cost in USD of one call from its `usage` block."""
    price_in, price_out = PRICES[model]
    total = (
        usage.get("input_tokens", 0) * price_in
        + usage.get("cache_creation_input_tokens", 0) * price_in * CACHE_WRITE
        + usage.get("cache_read_input_tokens", 0) * price_in * CACHE_READ
        + usage.get("output_tokens", 0) * price_out
    ) / 1_000_000
    return round(total, 6)


def worst_case_usd(model: str, request: Request) -> float:
    """Return the upper bound of one call: all input written to the cache, all max_tokens out."""
    chars = len(request.system) + len(request.user) + len(json.dumps(request.schema))
    usage = {"cache_creation_input_tokens": chars // CHARS_PER_TOKEN}
    return cost_usd(model, usage | {"output_tokens": request.max_tokens})


@dataclass
class LLM:
    """Structured JSON calls with a response cache, a usage ledger and a per-run budget guard."""

    mode: str = "replay"
    model: str = "claude-sonnet-5-5"  # tools.lock LLM_MODEL; from_env reads it
    fixtures: Path = Path("tests/fixtures/llm")
    cache: Path = Path("out/llm-cache")
    ledger: Path = Path("out/llm-usage.jsonl")
    budget_usd: float = float(DEFAULT_BUDGET_USD)
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    client: Any = None  # an anthropic.Anthropic; built only for a paid call

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise LLMError(f"LLM_MODE must be one of {MODES}, not {self.mode!r}")
        if self.model not in PRICES:
            raise LLMError(f"no price for model {self.model!r}; add it to PRICES")

    @classmethod
    def from_env(cls, lock: Path, out: Path) -> LLM:
        """Build from LLM_MODE, LLM_MODEL and LLM_BUDGET_USD; the default model is in tools.lock."""
        return cls(
            mode=os.environ.get("LLM_MODE", "replay"),
            model=os.environ.get("LLM_MODEL") or read_pins(lock)["LLM_MODEL"],
            cache=out / "llm-cache",
            ledger=out / "llm-usage.jsonl",
            budget_usd=float(os.environ.get("LLM_BUDGET_USD", DEFAULT_BUDGET_USD)),
        )

    def spent_usd(self) -> float:
        """Return the billed spend of this run, from the ledger."""
        if not self.ledger.is_file():
            return 0.0
        entries = map(json.loads, self.ledger.read_text(encoding="utf-8").splitlines())
        return sum(e["cost_usd"] for e in entries if e["run_id"] == self.run_id)

    def complete(self, request: Request) -> Json:
        """Return the JSON answer for `request`. Recorded answers and cache hits cost nothing.

        Replay uses only recorded answers. Record uses a recorded answer if there is one, so a
        second record run pays only for the answers that are not recorded yet.
        """
        key = request.key(self.model)
        fixture = self.fixtures / f"{key}.json"
        if self.mode == "replay" or (self.mode == "record" and fixture.is_file()):
            return self._recorded(request, key, fixture, "no recorded answer")
        hit = self.cache / f"{key}.json"
        if hit.is_file():
            return self._recorded(request, key, hit, "no cache entry")
        self._guard(request)
        output, usage = self._call_api(request)
        recorded = {"task": request.task, "model": self.model, "output": output, "usage": usage}
        self._save(hit, recorded)
        if self.mode == "record":
            self._save(self.fixtures / f"{key}.json", recorded)
        self._log(request, key, usage, billed=True)
        return output

    def _recorded(self, request: Request, key: str, path: Path, missing: str) -> Json:
        if not path.is_file():
            raise LLMError(
                f"{request.task}: {missing} ({key[:12]}); record it with LLM_MODE=record"
            )
        recorded = json.loads(path.read_text(encoding="utf-8"))
        self._log(request, key, recorded["usage"], billed=False)
        return recorded["output"]

    def _guard(self, request: Request) -> None:
        spent, estimate = self.spent_usd(), worst_case_usd(self.model, request)
        if spent + estimate > self.budget_usd:
            raise BudgetExceeded(
                f"{request.task}: spent ${spent:.4f} + up to ${estimate:.4f} would pass "
                f"LLM_BUDGET_USD=${self.budget_usd:.2f}; no call made"
            )

    def _client(self) -> Any:
        if self.client is None:
            import anthropic  # optional extra: uv sync --extra llm

            self.client = anthropic.Anthropic()
        return self.client

    def _call_api(self, request: Request) -> tuple[Json, Json]:
        try:
            message = self._client().messages.create(
                model=self.model,
                max_tokens=request.max_tokens,
                system=[
                    {"type": "text", "text": request.system, "cache_control": {"type": "ephemeral"}}
                ],
                messages=[{"role": "user", "content": request.user}],
                output_config={
                    "format": {"type": "json_schema", "schema": request.schema},
                    **MODEL_CONFIG.get(self.model, {}),
                },
                timeout=REQUEST_TIMEOUT_S,
            )
        # The SDK boundary: no credentials (TypeError), network and API errors, after the SDK's
        # own retries. Each one stops the step with one message, as a missing answer does.
        except Exception as e:
            raise LLMError(f"{request.task}: the API call failed: {e}") from e
        if message.stop_reason != "end_turn":
            raise LLMError(f"{request.task}: stop_reason {message.stop_reason!r}; answer rejected")
        try:
            output = json.loads(next(b.text for b in message.content if b.type == "text"))
        except (StopIteration, json.JSONDecodeError) as e:
            raise LLMError(f"{request.task}: the answer is not one JSON text block") from e
        if not isinstance(output, dict):
            raise LLMError(f"{request.task}: the answer is not one JSON object")
        return output, {k: getattr(message.usage, k, 0) or 0 for k in USAGE_KEYS}

    def _save(self, path: Path, doc: Json) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _log(self, request: Request, key: str, usage: Json, billed: bool) -> None:
        entry = {
            "ts": datetime.now(UTC).isoformat(timespec="seconds"),
            "run_id": self.run_id,
            "task": request.task,
            "mode": self.mode,
            "model": self.model,
            "prompt_key": key,
            **{k: usage.get(k, 0) for k in USAGE_KEYS},
            "billed": billed,
            "cost_usd": cost_usd(self.model, usage) if billed else 0.0,
        }
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
