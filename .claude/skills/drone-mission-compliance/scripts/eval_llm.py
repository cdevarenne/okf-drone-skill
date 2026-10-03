"""Eval of the LLM steps on the seeded missions (DRN-09 spec §7). Writes docs/data/drn-09-eval.json.

Replay by default: the answers come from tests/fixtures/llm/, so the output is the same each run.
The owner records the answers once with LLM_MODE=record. The cost comes from the recorded usage.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import intake
import narrate
import yaml
from gen_plan import read_pins
from llm import LLM, LLMError, Request, cost_usd
from mission import load_mission
from okf_lib import load_bundle
from pipeline import run_mission

Json = dict[str, Any]
LABEL_OF_GUARDRAIL_TEXTS = "m01"  # x01 and x02 are m01 with a change (spec §7)


def label_for(text: Path, missions: Path) -> Path:
    """Return the seeded mission request that labels a text: mNN.txt -> missions/mNN-*.yaml."""
    prefix = text.stem if text.stem.startswith("m") else LABEL_OF_GUARDRAIL_TEXTS
    return next(missions.glob(f"{prefix.split('-')[0]}-*.yaml"))


def _leaves(doc: Json, prefix: str = "") -> dict[str, Any]:
    leaves = {}
    for key, value in doc.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            leaves |= _leaves(value, f"{path}.")
        else:
            leaves[path] = value
    return leaves


def score_intake(accepted: list[Json], label: Json) -> Json:
    """Return correct, wrong (paths), missing (label paths left empty) and the filled failsafes."""
    expected = {p: v for p, v in _leaves(label).items() if p != "id"}
    got = {f["path"]: f["value"] for f in accepted}
    wrong = sorted(p for p, v in got.items() if expected.get(p) != v)
    return {
        "correct": sum(1 for p, v in got.items() if p in expected and expected[p] == v),
        "wrong": wrong,
        "missing": sorted(set(expected) - set(got)),
        "failsafes_filled": sorted(p for p in got if p.startswith("failsafes.")),
    }


def _cost(llm: LLM, request: Request) -> float:
    recorded = json.loads((llm.fixtures / f"{request.key(llm.model)}.json").read_text())
    return cost_usd(llm.model, recorded["usage"])


def eval_model(llm: LLM, args: argparse.Namespace) -> Json:
    """Return the intake and narrate results and the recorded cost for one model."""
    root, bundle, cost = intake.specs(), load_bundle(args.knowledge), 0.0
    sets = intake.value_sets(bundle)
    intake_results = {}
    for text_file in sorted(args.texts.glob("*.txt")):
        text = text_file.read_text(encoding="utf-8")
        req = intake.request(text, sets)
        try:
            answer = llm.complete(req)
        except LLMError as e:
            raise LLMError(f"{text_file.name}: {e}") from e
        cost += _cost(llm, req)
        accepted = [f for f in answer["fields"] if intake.check_field(f, text, root, sets) is None]
        score = score_intake(accepted, load_mission(label_for(text_file, args.missions)))
        intake_results[text_file.stem] = score | {"dropped": len(answer["fields"]) - len(accepted)}
    narrate_results = {}
    with tempfile.TemporaryDirectory() as tmp:
        for entry in yaml.safe_load(args.seeded.read_text(encoding="utf-8")):
            mission_path = args.missions / f"{entry['mission']}.yaml"
            with contextlib.redirect_stdout(io.StringIO()):  # the pipeline's own "wrote" lines
                run_mission(mission_path, args.knowledge, args.lock, Path(tmp))
            folder = Path(tmp) / entry["mission"]
            doc = narrate.inputs(
                load_mission(mission_path),
                json.loads((folder / "validation.json").read_text(encoding="utf-8")),
                json.loads((folder / "risk.json").read_text(encoding="utf-8")),
                bundle,
            )
            if not narrate.to_explain(doc):
                narrate_results[entry["mission"]] = {"skipped": "no fail and no gap"}
                continue
            req = narrate.request(doc)
            try:
                answer = llm.complete(req)
            except LLMError as e:
                raise LLMError(f"{entry['mission']}: {e}") from e
            cost += _cost(llm, req)
            reasons = narrate.validate(answer, doc, bundle)
            narrate_results[entry["mission"]] = {"accepted": not reasons, "reasons": reasons}
    return {"intake": intake_results, "narrate": narrate_results, "cost_usd": round(cost, 6)}


def main(argv: list[str] | None = None) -> int:
    """Write the eval data. Return 0, or 2 if an answer is missing or a call fails."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--texts", type=Path, default=Path("missions/text"))
    parser.add_argument("--seeded", type=Path, default=Path("missions/SEEDED.yaml"))
    parser.add_argument("--missions", type=Path, default=Path("missions"))
    parser.add_argument("--knowledge", type=Path, default=Path("knowledge"))
    parser.add_argument("--lock", type=Path, default=Path("tools.lock"))
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures/llm"))
    parser.add_argument("--data", type=Path, default=Path("docs/data/drn-09-eval.json"))
    args = parser.parse_args(argv)
    if not any(args.texts.glob("*.txt")):
        print(f"{args.texts}: no .txt mission texts (DRN-09 plan, Task 6)", file=sys.stderr)
        return 2
    models = os.environ.get("LLM_EVAL_MODELS", "").split() or [read_pins(args.lock)["LLM_MODEL"]]
    results = {}
    with tempfile.TemporaryDirectory() as out:
        for model in models:
            llm = LLM.from_env(args.lock, Path(out))
            llm.model, llm.fixtures = model, args.fixtures
            try:
                results[model] = eval_model(llm, args)
            except LLMError as e:
                print(e, file=sys.stderr)
                return 2
    doc = {"source": "missions/text, missions/SEEDED.yaml (DRN-09 spec §7)", "models": results}
    args.data.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.data}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
