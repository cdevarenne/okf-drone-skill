"""Run every seeded mission through the pipeline and write docs/data/seeded.json (spec §7).

The published results are generated here, never typed. The exit code is 1 if a mission does
not get its expected decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from decision import decide
from pipeline import run_mission


def summarize(entry: dict[str, Any], out: Path) -> dict[str, Any]:
    """Return the result of one seeded mission from its output files."""
    folder = out / entry["mission"]
    checks = []
    for name in ("validation.json", "risk.json"):
        checks += json.loads((folder / name).read_text(encoding="utf-8"))["checks"]
    d = decide(checks)
    cited = sorted({c["concept_id"] for c in checks if c["concept_id"]})
    return {
        "mission": entry["mission"],
        "expected": entry["expected"],
        "decision": d.value,
        "fails": [{"check_id": c["check_id"], "concept_id": c["concept_id"]} for c in d.fails],
        "gaps": [{"check_id": c["check_id"], "concept_id": c["concept_id"]} for c in d.gaps],
        "concepts_cited": cited,
    }


def run_all(seeded: Path, knowledge: Path, lock: Path, out: Path) -> dict[str, Any]:
    """Run every seeded mission and return the document for docs/data/seeded.json."""
    entries = yaml.safe_load(seeded.read_text(encoding="utf-8"))
    results = []
    for entry in entries:
        mission = seeded.parent / f"{entry['mission']}.yaml"
        if run_mission(mission, knowledge, lock, out):
            raise RuntimeError(f"{mission}: the pipeline stopped")
        results.append(summarize(entry, out))
    return {"source": "missions/SEEDED.yaml", "missions": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeded", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args(argv)
    doc = run_all(args.seeded, args.knowledge, args.lock, args.out)
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    wrong = [m["mission"] for m in doc["missions"] if m["decision"] != m["expected"]]
    for m in doc["missions"]:
        print(f"{m['mission']}: {m['decision']} (expected {m['expected']})")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
