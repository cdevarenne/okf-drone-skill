# okf-drone-skill Phase 4 Plan: report, sign-off and the seeded missions

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** `make plan MISSION=<path>` writes all five outputs of spec §1: `mission.plan`,
`validation.json`, `risk.json`, `report.md` and `signoff.yaml`. `make seeded` runs m01 to m05
and writes `docs/data/seeded.json`. The golden test checks that each seeded mission gets its
expected decision and cites the expected concepts. The phase ends with the owner's review of
the m01 to m05 reports.

**Spec:** `docs/specs/2026-09-28-okf-drone-skill-v1-design.md` §1, §5.5, §5.6 (new), §7, §8,
§9 Phase 4. **Backlog:** DRN-07.

**Provenance:** Tasks 1 to 4 were run in a prototype on 2026-09-28 (Python 3.14.0rc2, uv 0.8.17,
ruff 0.16.9, pytest 9.1.1), on a copy of `main` at `97763e5`. The file contents below are copied
from that run. The tasks were replayed in order on a fresh copy; the replay is identical to the
prototype (including the generated `docs/data/seeded.json`), and the expected outputs come from
it. The prototype changed one rule before the plan was written: with no checks at all, the
decision was GO; it is now HOLD.

## Global constraints

- Commits on `main` as `cdevarenne`, dated in PST (`TZ=America/Los_Angeles`). Short subject in
  ASD-STE100. Body line `Closes #N`.
- Every commit ships tests, or says that it is docs only. The test fails first.
- Before every commit: `make verify`. Run `ruff format` only on the files of the task.
- The tool proposes a decision. It never fills an approval field and never overwrites a
  sign-off that a person started.
- Published results are generated (`make seeded` writes `docs/data/seeded.json`), never typed.
  The README links to the file; it does not copy its content.

## Decisions for the owner (before Task 0)

1. **No checks means HOLD**, not GO (spec §5.5). An empty result set means nothing was checked.
2. **Report sections** follow the flight-plan template (S10): overview, operational details,
   airspace and compliance, risk, flight profile and failsafes, decision, audit trail,
   approvals. Sections of the template that v1 does not have (personnel and equipment,
   weather, emergency procedures, checklists, post-flight) are left out, not filled with
   placeholders. The report says that airspace, NOTAM, TFR and weather are declared inputs.
3. **No time stamp in the report**, so the same inputs give the same file and the golden test is
   stable. The audit trail gives the concepts, their `verified` entries, their sources and the
   pins.
4. **`signoff.yaml`**: three roles from S10 §11 (RPIC, mission supervisor/commander, safety
   officer (optional)), each with empty `name`, `decision`, `date`; plus the SHA-256 of
   `mission.plan` and `report.md`, so a signature is tied to the exact files.
5. **Sign-off protection.** If a person filled any approval field, `render_report` stops with
   exit code 2 and changes nothing (not the report either).
6. **Seeded missions** use one mission type per condition where possible: m01 survey (GO),
   m02 inspection at 150 m (NO-GO), m03 search with a geofence that stops at the datum latitude
   (NO-GO), m04 survey without a lost-link action (NO-GO), m05 specific BVLOS survey (HOLD).
   Each NO-GO fails exactly one check. The coordinates are arbitrary test values.
7. **`pipeline.py`** holds `run_mission` (the four steps, as `make plan` runs them), for the
   tests and for `seeded.py`. The Makefile still shows each step.

## Task 0: Tracking issues (no commit)

- [ ] **Step 1:** Create one issue per task. The last issue is #26, so Task N becomes #N+26.

```
T1 (DRN-07): Spec: report, sign-off and the seeded results
T2 (DRN-07): The decision rule
T3 (DRN-07): render_report, signoff.yaml and the pipeline runner
T4 (DRN-07): Seeded missions m01 to m05 and the golden test
T5 (DRN-07): README for Phase 4
T6 (DRN-07): Owner reviews the m01 to m05 output (human gate)
```

Body: `Phase 4. See docs/plans/2026-09-28-phase-4-report-seeded.md, Task N.`

- [ ] **Step 2:** List the issues. Expected: #27 to #32 open.

---

## Task 1: Spec: report, sign-off and the seeded results (#27)

**Files:** modify `docs/specs/2026-09-28-okf-drone-skill-v1-design.md`. Docs only.

- [ ] **Step 1:** Apply this change (`git apply` accepts it):

```diff
--- a/docs/specs/2026-09-28-okf-drone-skill-v1-design.md
+++ b/docs/specs/2026-09-28-okf-drone-skill-v1-design.md
@@ -187,7 +187,21 @@
 - **HOLD:** no fail, but at least one gap. A human must add knowledge or decide.
 
 The decision reads the checks in `validation.json` and in `risk.json`. `not_applicable` does
-not change it.
+not change it. No checks at all is HOLD: nothing was checked, so the tool cannot propose GO.
+
+### 5.6 Report and sign-off (`report.md`, `signoff.yaml`)
+
+- `report.md` has the sections of the flight-plan template: 1 mission overview, 2 operational
+  details, 3 airspace and regulatory compliance (the checks), 4 risk assessment (hazard matrix,
+  SORA summary), 5 flight profile and waypoint plan (items, declared failsafes), 6 decision,
+  7 audit trail (every cited concept with its `verified` entry and source; the pins), and
+  8 approvals. It has no time stamp: the same inputs give the same file.
+- The report shows aviation units with their metric values (500 ft AGL = 152.4 m).
+- `signoff.yaml`: `mission_id`, `proposed_decision`, `plan_sha256`, `report_sha256`, and
+  `approvals` with one entry per role (RPIC, mission supervisor, safety officer (optional)),
+  each with empty `name`, `decision` and `date`.
+- `render_report` never overwrites a `signoff.yaml` in which a person filled a field. It
+  stops with exit code 2, and the report stays as the person saw it.
 
 ## 6. Pipeline
 
@@ -214,6 +228,11 @@
 
 ## 7. Seeded missions (`missions/SEEDED.yaml`)
 
+`missions/SEEDED.yaml` lists each seeded mission with `expected` (the decision), `cites` (the
+concepts that its failed checks must cite) and `gaps` (the check ids that must be gaps).
+`make seeded` runs all of them and writes `docs/data/seeded.json`; the README cites that file.
+The golden test runs them again and checks that `docs/data/seeded.json` is current.
+
 | Mission | Seeded condition | Expected |
 |---|---|---|
 | m01 | open category, VLOS, within all limits | GO |
@@ -226,7 +245,8 @@
 
 - Conformance test: every concept parses, has `verified`, and each check id is unique.
 - Unit tests per script; the first test fails before the code exists.
-- Golden test: m01–m05 decisions and cited concept ids.
+- Golden test: m01–m05 decisions and cited concept ids; each seeded `mission.plan` validates
+  against the vendored subset schema; `docs/data/seeded.json` is current.
 - `make verify`: ruff, pytest, schema validation of every `mission.plan`.
 
 ## 9. Phases
```

- [ ] **Step 2: Verify.** `make verify`. Expected: `250 passed`.
- [ ] **Step 3: Commit.** `Add the report, the sign-off and the seeded results to the spec (docs only)`,
  `Closes #27`.

---

## Task 2: The decision rule (#28)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/decision.py`,
`tests/test_decision.py`.

- [ ] **Step 1: Write the failing test.**

`tests/test_decision.py`:

```python
"""Check the decision rule (spec §5.5)."""

import pytest
from decision import GO, HOLD, NO_GO, decide


def check(check_id: str, status: str) -> dict:
    return {
        "check_id": check_id,
        "status": status,
        "concept_id": None,
        "evidence": "",
        "message": "",
    }


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["pass", "pass"], GO),
        (["pass", "not_applicable"], GO),
        ([], HOLD),
        (["pass", "gap"], HOLD),
        (["gap", "not_applicable"], HOLD),
        (["pass", "fail"], NO_GO),
        (["gap", "fail"], NO_GO),
    ],
)
def test_decision_rule(statuses: list[str], expected: str) -> None:
    assert decide(check(f"c.{i}", s) for i, s in enumerate(statuses)).value == expected


def test_decision_keeps_the_causes() -> None:
    d = decide([check("a.x", "fail"), check("b.y", "gap"), check("c.z", "pass")])
    assert [c["check_id"] for c in d.fails] == ["a.x"]
    assert [c["check_id"] for c in d.gaps] == ["b.y"]
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_decision.py`,
`ModuleNotFoundError: No module named 'decision'`.

- [ ] **Step 2: Write the module.**

`.claude/skills/drone-mission-compliance/scripts/decision.py`:

```python
"""The go / no-go decision that the tool proposes (spec §5.5). A person makes the decision."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from results import FAIL, GAP

GO, NO_GO, HOLD = "GO", "NO-GO", "HOLD"


@dataclass(frozen=True)
class Decision:
    """The proposed decision and the results that caused it."""

    value: str
    fails: tuple[dict[str, Any], ...]
    gaps: tuple[dict[str, Any], ...]


def decide(checks: Iterable[dict[str, Any]]) -> Decision:
    """Return NO-GO if a check fails, else HOLD if a check is a gap, else GO.

    `pass` and `not_applicable` do not change the decision. No checks at all is HOLD: nothing
    was checked, so the tool cannot propose GO.
    """
    checks = list(checks)
    fails = tuple(c for c in checks if c["status"] == FAIL)
    gaps = tuple(c for c in checks if c["status"] == GAP)
    value = NO_GO if fails else HOLD if gaps or not checks else GO
    return Decision(value, fails, gaps)
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `All checks passed!` and `258 passed`.
- [ ] **Step 4: Commit.** `Add the decision rule`, `Closes #28`.

---

## Task 3: render_report, signoff.yaml and the pipeline runner (#29)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/pipeline.py`,
`.claude/skills/drone-mission-compliance/scripts/render_report.py`,
`tests/test_render_report.py`; modify `Makefile`.

- [ ] **Step 1: Write the failing test.**

`tests/test_render_report.py`:

```python
"""Check render_report: the report sections, the sign-off file, and its protection."""

import hashlib
from pathlib import Path

import pytest
import yaml
from pipeline import run_mission
from render_report import APPROVER_ROLES, main

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"
KNOWLEDGE, LOCK = ROOT / "knowledge", ROOT / "tools.lock"
SECTIONS = [
    "## 1. Mission overview",
    "## 2. Operational details",
    "## 3. Airspace and regulatory compliance",
    "## 4. Risk assessment",
    "## 5. Flight profile and waypoint plan",
    "## 6. Decision",
    "## 7. Audit trail",
    "## 8. Approvals",
]


def pipeline(tmp_path: Path, name: str) -> Path:
    assert run_mission(MISSIONS / f"{name}.yaml", KNOWLEDGE, LOCK, tmp_path) == 0
    return tmp_path / name


def args(tmp_path: Path, name: str) -> list[str]:
    return [
        "--mission", str(MISSIONS / f"{name}.yaml"), "--knowledge", str(KNOWLEDGE),
        "--lock", str(LOCK), "--out", str(tmp_path),
    ]  # fmt: skip


def test_report_has_the_template_sections_in_order(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "specific") / "report.md").read_text()
    positions = [report.index(s) for s in SECTIONS]
    assert positions == sorted(positions)
    assert report.startswith("# Mission report: specific\n\n**Proposed decision: HOLD**")


def test_report_names_every_cited_concept_in_the_audit_trail(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "specific") / "report.md").read_text()
    audit = report[report.index("## 7. Audit trail") :]
    for cid in ("risk/igrc", "risk/m1a", "hazards/loss-of-c2", "regulations/easa-open"):
        assert f"| {cid} |" in audit
    assert "human:cdevarenne" in audit


def test_report_shows_both_units_for_the_arc_limits(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "specific") / "report.md").read_text()
    assert "500 ft AGL (152.4 m)" in report


def test_open_mission_is_not_sora_scored(tmp_path: Path) -> None:
    report = (pipeline(tmp_path, "survey") / "report.md").read_text()
    assert "SORA 2.5: not applicable (category open)." in report
    assert "**Proposed decision: GO**" in report


def test_signoff_has_empty_approvals_and_the_file_hashes(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "specific")
    doc = yaml.safe_load((folder / "signoff.yaml").read_text())
    assert doc["proposed_decision"] == "HOLD"
    assert [a["role"] for a in doc["approvals"]] == list(APPROVER_ROLES)
    assert all(a[f] == "" for a in doc["approvals"] for f in ("name", "decision", "date"))
    for key, name in (("plan_sha256", "mission.plan"), ("report_sha256", "report.md")):
        assert doc[key] == hashlib.sha256((folder / name).read_bytes()).hexdigest()


def test_output_is_deterministic(tmp_path: Path) -> None:
    first = pipeline(tmp_path / "a", "search")
    second = pipeline(tmp_path / "b", "search")
    for name in ("report.md", "signoff.yaml"):
        assert (first / name).read_text() == (second / name).read_text()


def test_started_signoff_is_never_overwritten(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "survey")
    signoff = folder / "signoff.yaml"
    signed = signoff.read_text().replace('name: ""', 'name: "A. Pilot"', 1)
    signoff.write_text(signed)
    report = (folder / "report.md").read_text()
    assert main(args(tmp_path, "survey")) == 2
    assert signoff.read_text() == signed
    assert (folder / "report.md").read_text() == report


def test_unsigned_signoff_is_rewritten(tmp_path: Path) -> None:
    pipeline(tmp_path, "survey")
    assert main(args(tmp_path, "survey")) == 0


def test_missing_results_return_2(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "survey")
    (folder / "risk.json").unlink()
    (folder / "signoff.yaml").unlink()
    assert main(args(tmp_path, "survey")) == 2


@pytest.mark.parametrize("name", ["survey", "specific"])
def test_report_does_not_approve(tmp_path: Path, name: str) -> None:
    report = (pipeline(tmp_path, name) / "report.md").read_text()
    assert "a person decides and signs" in report
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_render_report.py`,
`ModuleNotFoundError: No module named 'pipeline'`.

- [ ] **Step 2: Write the pipeline runner.**

`.claude/skills/drone-mission-compliance/scripts/pipeline.py`:

```python
"""Run the four pipeline steps for one mission, as `make plan` does (spec §6)."""

from __future__ import annotations

from pathlib import Path

import gen_plan
import render_report
import score_risk
import validate_plan


def run_mission(mission: Path, knowledge: Path, lock: Path, out: Path) -> int:
    """Run gen_plan, validate_plan, score_risk and render_report. Return the first non-zero code."""
    common = ["--mission", str(mission), "--knowledge", str(knowledge), "--out", str(out)]
    for step, args in (
        (gen_plan.main, [*common, "--lock", str(lock)]),
        (validate_plan.main, common),
        (score_risk.main, common),
        (render_report.main, [*common, "--lock", str(lock)]),
    ):
        code = step(args)
        if code:
            return code
    return 0
```

- [ ] **Step 3: Write render_report.**

`.claude/skills/drone-mission-compliance/scripts/render_report.py`:

```python
"""Write the mission report and the sign-off file for a person (spec §6, step 5).

The report follows the sections of the flight-plan template (S10). It proposes a decision; it
does not approve the mission. signoff.yaml has empty approval fields that only a person fills.
render_report never overwrites a sign-off file that a person started to fill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from decision import Decision, decide
from gen_plan import read_pins
from mission import MissionError, load_mission
from okf_lib import Bundle, Concept, load_bundle

APPROVER_ROLES = (  # S10 §11 Approvals
    "Remote Pilot in Command (RPIC)",
    "Mission Supervisor/Commander",
    "Safety Officer (optional)",
)
APPROVAL_FIELDS = ("name", "decision", "date")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


class SignoffError(RuntimeError):
    """A person started to fill signoff.yaml; the tool must not overwrite it."""


def _table(header: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _source_line(bundle: Bundle, concept: Concept) -> str:
    text = bundle.section(concept, "Source") or ""
    first = next((line[2:] for line in text.splitlines() if line.startswith("- ")), "")
    return _LINK.sub(r"\1", first)


def _verified(concept: Concept) -> str:
    entries = concept.frontmatter.get("verified") or []
    return ", ".join(f"{e.get('by')} {e.get('at')}" for e in entries) or "not verified"


def _command_names(bundle: Bundle) -> dict[int, str]:
    return {c.table["mavlink_id"]: c.table["name"] for c in bundle.of_type("MAVLink Command")}


def cited_concepts(validation: dict, risk: dict) -> list[str]:
    """Return every concept id that the results cite, sorted."""
    ids = {c["concept_id"] for c in validation["checks"] + risk["checks"] if c["concept_id"]}
    ids |= {r["hazard_id"] for r in risk["hazards"]}
    sora = risk["sora"]
    ids |= {v["concept_id"] for v in sora.values() if isinstance(v, dict) and v["concept_id"]}
    ids |= {m["concept_id"] for m in sora.get("mitigations_applied", [])}
    return sorted(ids)


def render(
    mission: dict,
    plan: dict,
    validation: dict,
    risk: dict,
    bundle: Bundle,
    pins: dict[str, str],
    decision: Decision,
) -> str:
    """Return report.md. The text has no time stamp, so the same inputs give the same file."""
    m = mission
    out: list[str] = []
    add = out.append
    add(f"# Mission report: {m['id']}")
    add("")
    add(
        f"**Proposed decision: {decision.value}** ({_count(len(decision.fails), 'failed check')}, "
        f"{_count(len(decision.gaps), 'gap')}). The tool proposes; a person decides and signs "
        "`signoff.yaml`."
    )
    add("")
    add("## 1. Mission overview")
    add("")
    mt = bundle.concepts.get(f"mission-types/{m['mission_type']}")
    add(
        _table(
            ["Mission ID", "Mission type", "Category", "Operation"],
            [[m["id"], mt.title if mt else m["mission_type"], m["category"], m["operation"]]],
        )
    )
    add("")
    add("## 2. Operational details")
    add("")
    h = m["home"]
    add(
        _table(
            ["Item", "Value"],
            [
                ["Takeoff and landing (home)", f"{h['lat']}, {h['lon']}, {h['amsl_m']} m AMSL"],
                ["Maximum altitude", f"{m['max_altitude_agl_m']} m, relative to home"],
                ["Terrain (declared)", m["terrain"]],
                ["Speed", f"{m['speed_ms']} m/s"],
                ["Area vertices", len(m["area"]["polygon"])],
                ["Geofence vertices", len(m["geofence"]["polygon"])],
                [
                    "UA",
                    (
                        f"MTOM {m['ua']['mtom_kg']} kg, {m['ua']['char_dimension_m']} m, "
                        f"{m['ua']['max_speed_ms']} m/s"
                    ),
                ],
                ["Population density (declared)", m["ground"]["population_density"]],
            ],
        )
    )
    add("")
    add("## 3. Airspace and regulatory compliance")
    add("")
    add(
        "Airspace, NOTAM, TFR and weather are **declared inputs** in v1. The tool does not check "
        f"them against a live source. Airspace class {m['airspace']['class']}, declared by "
        f"{m['airspace']['declared_by']}."
    )
    add("")
    add(
        _table(
            ["Check", "Status", "Concept", "Evidence", "Message"],
            [
                [c["check_id"], c["status"], c["concept_id"] or "none", c["evidence"], c["message"]]
                for c in validation["checks"]
            ],
        )
    )
    add("")
    add("## 4. Risk assessment")
    add("")
    add("Hazard matrix (likelihood and severity 1 to 5; score = likelihood x severity):")
    add("")
    add(
        _table(
            ["Hazard", "L", "S", "Score", "Mitigation", "Residual"],
            [
                [
                    r["hazard_id"],
                    r["likelihood"],
                    r["severity"],
                    r["score"],
                    "; ".join(r["mitigations"]),
                    r["residual"],
                ]
                for r in risk["hazards"]
            ],
        )
    )
    add("")
    sora = risk["sora"]
    if sora.get("status") == "not_applicable":
        add("SORA 2.5: not applicable (category open).")
    else:
        add("SORA 2.5 summary:")
        add("")
        rows = [
            [k, v["value"], v["concept_id"] or "none"]
            for k, v in sora.items()
            if isinstance(v, dict)
        ]
        add(_table(["Step", "Value", "Concept"], rows))
        add("")
        applied = sora.get("mitigations_applied", [])
        add(
            "Declared mitigations (operator claims; v1 does not check the Annex B criteria): "
            + (
                ", ".join(f"{a['concept_id']} {a['level']} ({a['credit']})" for a in applied)
                or "none"
            )
            + "."
        )
        add("")
        add(
            "The ARC facts use aviation units, as in the source: 500 ft AGL (152.4 m) and FL600 "
            "(a pressure altitude). See `risk/arc`, Units."
        )
        add("")
        add(
            _table(
                ["Check", "Status", "Concept", "Evidence", "Message"],
                [
                    [
                        c["check_id"],
                        c["status"],
                        c["concept_id"] or "none",
                        c["evidence"],
                        c["message"],
                    ]
                    for c in risk["checks"]
                ],
            )
        )
    add("")
    add("## 5. Flight profile and waypoint plan")
    add("")
    add("File `mission.plan` (QGroundControl plan, WGS84). Altitudes in metres relative to home.")
    add("")
    names = _command_names(bundle)
    add(
        _table(
            ["Seq", "Command", "Frame", "Latitude", "Longitude", "Altitude (m)"],
            [
                [
                    i["doJumpId"],
                    names.get(i["command"], i["command"]),
                    i["frame"],
                    i["params"][4] if "Altitude" in i else "",
                    i["params"][5] if "Altitude" in i else "",
                    i.get("Altitude", ""),
                ]
                for i in plan["mission"]["items"]
            ],
        )
    )
    add("")
    add("Failsafe settings (declared; they are vehicle parameters, not part of the plan):")
    add("")
    rows = []
    for c in bundle.of_type("Failsafe"):
        keys = c.table.get("mission_keys") or (
            {"": c.table["mission_key"]} if "mission_key" in c.table else {}
        )
        for key in keys.values():
            rows.append(
                [
                    key,
                    m["failsafes"].get(key, "not declared"),
                    c.id,
                    ", ".join(c.table["px4_params"]),
                ]
            )
    add(_table(["Failsafe", "Declared action", "Concept", "PX4 parameters"], rows))
    add("")
    add("## 6. Decision")
    add("")
    add("Rule (spec §5.5): NO-GO if a check fails; else HOLD if a check is a gap; else GO.")
    add("")
    for label, items in (("Failed", decision.fails), ("Gaps", decision.gaps)):
        text = "; ".join(
            f"`{c['check_id']}` ({c['concept_id'] or 'no concept'}): {c['message']}" for c in items
        )
        add(f"- {label}: {text or 'none'}")
    add("")
    add("## 7. Audit trail")
    add("")
    concepts = [
        bundle.concepts[cid] for cid in cited_concepts(validation, risk) if cid in bundle.concepts
    ]
    add(
        _table(
            ["Concept", "Title", "Verified", "Source"],
            [[c.id, c.title, _verified(c), _source_line(bundle, c)] for c in concepts],
        )
    )
    add("")
    add(
        f"Pins: OKF `{pins['OKF_COMMIT']}`, QGC plan {pins['QGC_PLAN_VERSION']} / mission "
        f"{pins['QGC_MISSION_VERSION']}, SORA {pins['SORA_EDITION']}."
    )
    add("")
    add("## 8. Approvals")
    add("")
    add("A person fills `signoff.yaml`. The tool leaves every approval field empty.")
    return "\n".join(out) + "\n"


def signoff(mission_id: str, decision: str, plan_sha: str, report_sha: str) -> str:
    """Return signoff.yaml with empty approval fields."""
    lines = [
        "# Written by okf-drone-skill. The tool never fills the approval fields.",
        "# A person fills name, decision (GO or NO-GO) and date for each role.",
        f"mission_id: {mission_id}",
        f"proposed_decision: {decision}",
        f"plan_sha256: {plan_sha}",
        f"report_sha256: {report_sha}",
        "approvals:",
    ]
    for role in APPROVER_ROLES:
        lines.append(f'  - role: "{role}"')
        lines += [f'    {field}: ""' for field in APPROVAL_FIELDS]
    return "\n".join(lines) + "\n"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _count(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def started(path: Path) -> bool:
    """Return True if signoff.yaml exists and a person filled any approval field."""
    if not path.exists():
        return False
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return any(
        str(a.get(f) or "").strip() for a in doc.get("approvals") or [] for f in APPROVAL_FIELDS
    )


def write(mission: dict, out_dir: Path, bundle: Bundle, pins: dict[str, str]) -> Decision:
    """Write report.md and signoff.yaml in out_dir. Return the proposed decision."""
    if started(out_dir / "signoff.yaml"):
        raise SignoffError(f"{out_dir / 'signoff.yaml'}: a person started the sign-off")
    plan_text = (out_dir / "mission.plan").read_text(encoding="utf-8")
    validation = json.loads((out_dir / "validation.json").read_text(encoding="utf-8"))
    risk = json.loads((out_dir / "risk.json").read_text(encoding="utf-8"))
    d = decide(validation["checks"] + risk["checks"])
    report = render(mission, json.loads(plan_text), validation, risk, bundle, pins, d)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    text = signoff(mission["id"], d.value, _sha256(plan_text), _sha256(report))
    (out_dir / "signoff.yaml").write_text(text, encoding="utf-8")
    return d


def main(argv: list[str] | None = None) -> int:
    """Write report.md and signoff.yaml. Return 0, or 2 for a bad input or a started sign-off."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
        d = write(
            mission, args.out / mission["id"], load_bundle(args.knowledge), read_pins(args.lock)
        )
    except (MissionError, SignoffError, OSError, ValueError) as e:
        print(e, file=sys.stderr)
        return 2
    print(f"wrote {args.out / mission['id'] / 'report.md'} (proposed {d.value})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Add the report step to `plan`.** In `Makefile`, add after the `score_risk.py`
  line of the `plan` recipe (the line starts with a tab):

```makefile
	$(PY) $(SCRIPTS)/render_report.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out
```

- [ ] **Step 5: Verify.** `make verify`. Expected: `All checks passed!` and `269 passed`. Then
  `make plan MISSION=tests/fixtures/missions/specific.yaml`. Expected: the last line is
  `wrote out/specific/report.md (proposed HOLD)`, and `out/specific/` has the five files.
- [ ] **Step 6: Commit.** `Add render_report, the sign-off file and the pipeline runner`,
  `Closes #29`.

---

## Task 4: Seeded missions m01 to m05 and the golden test (#30)

**Files:** create `missions/SEEDED.yaml`, `missions/m01-survey-open.yaml`,
`missions/m02-altitude-over-limit.yaml`, `missions/m03-outside-geofence.yaml`,
`missions/m04-no-lost-link.yaml`, `missions/m05-specific-bvlos.yaml`,
`.claude/skills/drone-mission-compliance/scripts/seeded.py`, `tests/test_seeded.py`,
`docs/data/seeded.json` (generated); modify `Makefile`; delete `missions/.gitkeep`,
`docs/data/.gitkeep`.

- [ ] **Step 1: Write the failing test.**

`tests/test_seeded.py`:

```python
"""Golden test: every seeded mission gets its expected decision and cites its concepts (spec §7).

It also checks that docs/data/seeded.json is the current generated result.
"""

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from seeded import run_all

ROOT = Path(__file__).resolve().parents[1]
SEEDED = ROOT / "missions" / "SEEDED.yaml"
ENTRIES = yaml.safe_load(SEEDED.read_text())
SCHEMA = json.loads((ROOT / "tests" / "fixtures" / "qgc" / "plan.schema.json").read_text())


@pytest.fixture(scope="module")
def run(tmp_path_factory) -> tuple[dict, Path]:
    out = tmp_path_factory.mktemp("out")
    return run_all(SEEDED, ROOT / "knowledge", ROOT / "tools.lock", out), out


def test_every_mission_file_is_seeded() -> None:
    files = {p.stem for p in (ROOT / "missions").glob("*.yaml")} - {"SEEDED"}
    assert files == {e["mission"] for e in ENTRIES}


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["mission"])
def test_seeded_decision_and_citations(run, entry: dict) -> None:
    doc, _ = run
    result = next(m for m in doc["missions"] if m["mission"] == entry["mission"])
    assert result["decision"] == entry["expected"]
    assert set(entry.get("cites", [])) <= {f["concept_id"] for f in result["fails"]}
    assert set(entry.get("gaps", [])) <= {g["check_id"] for g in result["gaps"]}


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["mission"])
def test_seeded_plan_validates_against_the_subset_schema(run, entry: dict) -> None:
    _, out = run
    plan = json.loads((out / entry["mission"] / "mission.plan").read_text())
    assert list(Draft202012Validator(SCHEMA).iter_errors(plan)) == []


def test_published_results_are_current(run) -> None:
    """docs/data/seeded.json is generated by `make seeded`; it must match a fresh run."""
    doc, _ = run
    assert json.loads((ROOT / "docs" / "data" / "seeded.json").read_text()) == doc
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_seeded.py`,
`ModuleNotFoundError: No module named 'seeded'`.

- [ ] **Step 2: Write the seeded missions.**

`missions/SEEDED.yaml`:

```yaml
# Seeded missions (spec §7). tests/test_seeded.py runs each one; `make seeded` writes
# docs/data/seeded.json. `cites`: concepts that the failed checks must cite. `gaps`: check ids
# that must be gaps.
- mission: m01-survey-open
  expected: GO
- mission: m02-altitude-over-limit
  expected: NO-GO
  cites: [regulations/easa-open]
- mission: m03-outside-geofence
  expected: NO-GO
  cites: [failsafes/geofence-breach]
- mission: m04-no-lost-link
  expected: NO-GO
  cites: [failsafes/lost-link]
- mission: m05-specific-bvlos
  expected: HOLD
  gaps: [sora.oso]
```

`missions/m01-survey-open.yaml`:

```yaml
# Seeded mission (spec §7). The coordinates are arbitrary test values.
id: m01-survey-open
mission_type: mapping-survey
category: open
operation: VLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8030, -0.6020], [44.8030, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 100
speed_ms: 8
pattern: {spacing_m: 40}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}
airspace: {class: G, declared_by: operator}
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

`missions/m02-altitude-over-limit.yaml`:

```yaml
# Seeded mission (spec §7). The coordinates are arbitrary test values.
id: m02-altitude-over-limit
mission_type: infrastructure-inspection
category: open
operation: VLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8030, -0.6020], [44.8030, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 150
speed_ms: 8
pattern: {route: [[44.7995, -0.6008], [44.8005, -0.6002], [44.8015, -0.5996]]}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}
airspace: {class: G, declared_by: operator}
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

`missions/m03-outside-geofence.yaml`:

```yaml
# Seeded mission (spec §7). The coordinates are arbitrary test values.
id: m03-outside-geofence
mission_type: search-pattern
category: open
operation: VLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8005, -0.6020], [44.8005, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 60
speed_ms: 8
pattern: {spacing_m: 30, datum: [44.8005, -0.6000]}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}
airspace: {class: G, declared_by: operator}
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

`missions/m04-no-lost-link.yaml`:

```yaml
# Seeded mission (spec §7). The coordinates are arbitrary test values.
id: m04-no-lost-link
mission_type: mapping-survey
category: open
operation: VLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8030, -0.6020], [44.8030, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 100
speed_ms: 8
pattern: {spacing_m: 40}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}
airspace: {class: G, declared_by: operator}
failsafes: {low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

`missions/m05-specific-bvlos.yaml`:

```yaml
# Seeded mission (spec §7). The coordinates are arbitrary test values.
id: m05-specific-bvlos
mission_type: mapping-survey
category: specific
operation: BVLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8030, -0.6020], [44.8030, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 100
speed_ms: 8
pattern: {spacing_m: 40}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}
airspace:
  class: G
  declared_by: operator
  atypical_airspace: false
  above_fl600: false
  airport_environment: false
  above_500ft_agl: false
  mode_c_veil_or_tmz: false
  controlled_airspace: false
  over_urban_area: false
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
sora:
  mitigations: {m1a: low}
  adjacent_area: {below_people_km2: 5000, assemblies: under-40k, shelter: true}
```

Delete `missions/.gitkeep` and `docs/data/.gitkeep`.

- [ ] **Step 3: Write the seeded runner.**

`.claude/skills/drone-mission-compliance/scripts/seeded.py`:

```python
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
```

- [ ] **Step 4: Add the `seeded` target.** In `Makefile`, add `seeded` to `.PHONY`, and add after
  the `plan` recipe:

```makefile
seeded:
	$(PY) $(SCRIPTS)/seeded.py --seeded missions/SEEDED.yaml --knowledge knowledge --lock tools.lock --out out --data docs/data/seeded.json
```

- [ ] **Step 5: Generate the results.** Run `make seeded`. Expected output (after the `wrote`
  lines):

```
m01-survey-open: GO (expected GO)
m02-altitude-over-limit: NO-GO (expected NO-GO)
m03-outside-geofence: NO-GO (expected NO-GO)
m04-no-lost-link: NO-GO (expected NO-GO)
m05-specific-bvlos: HOLD (expected HOLD)
```

It writes `docs/data/seeded.json`. Do not edit that file by hand. Expected content in short:
m02 fails `alt.max_agl` (`regulations/easa-open`), m03 fails `plan.inside_geofence`
(`failsafes/geofence-breach`), m04 fails `failsafe.lost_link` (`failsafes/lost-link`), m05 has
one gap, `sora.oso` (no concept), and m01 has no fail and no gap.

- [ ] **Step 6: Verify.** `make verify`. Expected: `All checks passed!` and `281 passed`.
- [ ] **Step 7: Commit.** `Add the seeded missions, the golden test and the seeded results`,
  `Closes #30`.

---

## Task 5: README for Phase 4 (#31)

**Files:** modify `README.md`. Docs only.

- [ ] **Step 1:** In the status table, set Phase 4 to `Done, owner review pending`. In "Quick
  start", add `make seeded   # runs m01 to m05; writes docs/data/seeded.json`. Add a section
  "Seeded missions" after "How grounding works": one sentence per seeded condition (from spec
  §7), and a link to [`docs/data/seeded.json`](docs/data/seeded.json) for the results. Do not
  copy the results into the README. In "Layout", update the `missions/` line to
  `mission requests m01 to m05 and SEEDED.yaml`, and add `docs/data/` (generated results).
- [ ] **Step 2: Commit.** `Update the README for Phase 4 (docs only)`, `Closes #31`.

---

## Task 6: Human gate: owner reviews the m01 to m05 output (#32)

**The executing agent stops here and hands off to the owner.**

- [ ] **Step 1:** The owner runs `make seeded` and reads `out/m01-*/report.md` to
  `out/m05-*/report.md`. For each: is the proposed decision right, is the reason right, and
  does each check cite the right concept?
- [ ] **Step 2 (optional):** The owner fills one `signoff.yaml` in `out/` (not committed), runs
  `make plan` for that mission again, and sees exit code 2 with the files unchanged.
- [ ] **Step 3:** The owner records the result: in the README status table, set Phase 4 to
  `Done, reviewed by the owner`, and in "How this was built", add the Phase 4 review to the
  human gates. Commit (docs only) with `Closes #32`.

After Task 6: Phase 5 (screenshots, the README "How this was built" with the whole record).
