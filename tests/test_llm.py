"""Check the LLM interface offline: replay, record, the cache, the ledger and the budget guard."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from llm import LLM, BudgetExceeded, LLMError, Request, cost_usd, worst_case_usd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "drone-mission-compliance" / "scripts"
SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}
REQUEST = Request(task="narrate", system="rules", user="data", schema=SCHEMA, max_tokens=100)
USAGE = {"input_tokens": 1000, "output_tokens": 200}


class FakeClient:
    """Stands in for anthropic.Anthropic: records each request, returns one canned message."""

    def __init__(self, text: str = '{"summary": "HOLD"}', stop_reason: str = "end_turn") -> None:
        self.calls: list[dict] = []
        self.message = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(**USAGE),
        )
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **params) -> SimpleNamespace:
        self.calls.append(params)
        return self.message


def make(tmp_path: Path, mode: str, client=None, **kw) -> LLM:
    return LLM(
        mode=mode,
        model=kw.pop("model", "claude-opus-5-5"),
        fixtures=tmp_path / "fixtures",
        cache=tmp_path / "cache",
        ledger=tmp_path / "usage.jsonl",
        client=client,
        **kw,
    )


def ledger(llm: LLM) -> list[dict]:
    return [json.loads(line) for line in llm.ledger.read_text().splitlines()]


def test_replay_returns_the_recorded_output_and_bills_nothing(tmp_path: Path) -> None:
    llm = make(tmp_path, "replay")
    key = REQUEST.key(llm.model)
    recorded = {"task": "narrate", "model": llm.model, "output": {"summary": "GO"}, "usage": USAGE}
    llm.fixtures.mkdir()
    (llm.fixtures / f"{key}.json").write_text(json.dumps(recorded))
    assert llm.complete(REQUEST) == {"summary": "GO"}
    assert [(e["billed"], e["cost_usd"]) for e in ledger(llm)] == [(False, 0.0)]


def test_replay_without_a_fixture_names_the_task(tmp_path: Path) -> None:
    with pytest.raises(LLMError, match="narrate"):
        make(tmp_path, "replay").complete(REQUEST)


def test_api_call_then_cache_hit(tmp_path: Path) -> None:
    client = FakeClient()
    llm = make(tmp_path, "anthropic", client)
    assert llm.complete(REQUEST) == {"summary": "HOLD"}
    assert llm.complete(REQUEST) == {"summary": "HOLD"}
    assert len(client.calls) == 1
    assert [e["billed"] for e in ledger(llm)] == [True, False]
    assert ledger(llm)[0]["cost_usd"] == cost_usd(llm.model, USAGE)


def test_request_sends_the_schema_and_low_effort_on_opus(tmp_path: Path) -> None:
    client = FakeClient()
    make(tmp_path, "anthropic", client).complete(REQUEST)
    config = client.calls[0]["output_config"]
    assert config == {"format": {"type": "json_schema", "schema": SCHEMA}, "effort": "low"}
    assert "thinking" not in client.calls[0]


def test_haiku_gets_no_effort(tmp_path: Path) -> None:
    client = FakeClient()
    make(tmp_path, "anthropic", client, model="claude-haiku-4-5").complete(REQUEST)
    assert "effort" not in client.calls[0]["output_config"]


def test_record_writes_the_fixture(tmp_path: Path) -> None:
    llm = make(tmp_path, "record", FakeClient())
    llm.complete(REQUEST)
    fixture = json.loads((llm.fixtures / f"{REQUEST.key(llm.model)}.json").read_text())
    assert fixture["output"] == {"summary": "HOLD"}
    assert fixture["usage"] == USAGE | {
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def test_budget_guard_stops_the_call(tmp_path: Path) -> None:
    client = FakeClient()
    llm = make(
        tmp_path, "anthropic", client, budget_usd=worst_case_usd("claude-opus-5-5", REQUEST) / 2
    )
    with pytest.raises(BudgetExceeded):
        llm.complete(REQUEST)
    assert client.calls == []


@pytest.mark.parametrize(
    "client",
    [
        FakeClient(stop_reason="refusal"),
        FakeClient(stop_reason="max_tokens"),
        FakeClient(text="no"),
    ],
    ids=["refusal", "max_tokens", "not-json"],
)
def test_bad_answers_are_errors(tmp_path: Path, client: FakeClient) -> None:
    llm = make(tmp_path, "anthropic", client)
    with pytest.raises(LLMError, match="narrate"):
        llm.complete(REQUEST)
    assert not llm.cache.exists()


def test_cost_usd_uses_the_price_table() -> None:
    # Opus 5.5: 4 USD in, 20 USD out per million tokens.
    assert cost_usd("claude-opus-5-5", USAGE) == pytest.approx(0.008)


def test_model_without_a_price_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(LLMError, match="price"):
        make(tmp_path, "replay", model="claude-unknown")


def test_unknown_mode_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(LLMError, match="LLM_MODE"):
        make(tmp_path, "live")


def test_from_env_reads_the_pinned_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_MODE", raising=False)
    llm = LLM.from_env(ROOT / "tools.lock", tmp_path)
    assert (llm.mode, llm.model, llm.budget_usd) == ("replay", "claude-opus-5-5", 0.5)
    monkeypatch.setenv("LLM_MODEL", "claude-haiku-4-5")
    assert LLM.from_env(ROOT / "tools.lock", tmp_path).model == "claude-haiku-4-5"


def test_module_imports_without_anthropic() -> None:
    """anthropic is an optional extra; it is imported only for a paid call."""
    code = "import sys, llm; print('anthropic' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=SCRIPTS, capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "False"


def test_sdk_failure_is_an_llm_error(tmp_path: Path) -> None:
    """A failed paid call (no credentials, network, API error) stops the step with one message."""

    class Failing(FakeClient):
        def _create(self, **params):
            raise TypeError("Could not resolve authentication method.")

    client = Failing()
    client.messages = SimpleNamespace(create=client._create)
    llm = make(tmp_path, "anthropic", client)
    with pytest.raises(LLMError, match="narrate: the API call failed: .*authentication"):
        llm.complete(REQUEST)
    assert not llm.cache.exists() and not llm.ledger.exists()


def test_record_reuses_a_recorded_answer(tmp_path: Path) -> None:
    """A second record run pays only for the answers that are not recorded yet."""
    first = make(tmp_path, "record", FakeClient())
    first.complete(REQUEST)
    client = FakeClient()
    again = make(tmp_path, "record", client)
    again.cache = tmp_path / "other-cache"  # a new run: an empty cache, the same recorded answers
    assert again.complete(REQUEST) == {"summary": "HOLD"}
    assert client.calls == []
    assert [e["billed"] for e in ledger(again)][-1] is False
