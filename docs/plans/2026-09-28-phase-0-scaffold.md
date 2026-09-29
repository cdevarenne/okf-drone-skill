# okf-drone-skill Phase 0 Plan: scaffold, pins, sources

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** a repo that builds and tests, with every external version pinned, a vendored `.plan`
subset schema, and a source register for the SORA 2.5 read (spec §3, §9 Phase 0).

**Spec:** `docs/specs/2026-09-28-okf-drone-skill-v1-design.md`. **Backlog:** DRN-02.

**Provenance:** every file below was run in a prototype on 2026-09-28 (Python 3.14.7, uv 0.12.13).
The expected outputs come from that run. The OKF pin was checked the same day:
`git ls-remote https://github.com/GoogleCloudPlatform/open-knowledge-format HEAD` returned
`ad30107c31c06aec8a7d5636e0d1058118604e6f`, the same commit as okf-grc-skill.

## Global constraints

- Python `>=3.14`, uv. Runtime dependency: PyYAML. Dev: pytest, jsonschema, ruff.
- Commits on `main` as the repo-local identity (`cdevarenne`, noreply email). No `Co-Authored-By`
  trailer. Short subject in ASD-STE100. Body line `Closes #N`.
- Every commit ships tests, or says that it is docs-only.
- CI is manual-only. Do not add or run a workflow.
- Task 4 is a human gate. The executing agent stops there.

## Task 0: Tracking issues (no commit)

- [ ] **Step 1:** Create one issue per task. The repo has no issues yet, so Task N becomes issue #N.

```bash
gh issue create --title "T1 (DRN-02): Scaffold and pinned versions" --body "Phase 0. See docs/plans/2026-09-28-phase-0-scaffold.md, Task 1."
gh issue create --title "T2 (DRN-02): Vendored .plan subset schema" --body "Phase 0. See docs/plans/2026-09-28-phase-0-scaffold.md, Task 2."
gh issue create --title "T3 (DRN-02): Source register" --body "Phase 0. See docs/plans/2026-09-28-phase-0-scaffold.md, Task 3."
gh issue create --title "T4 (DRN-02): Owner reads SORA 2.5 and PX4 sources" --body "Human gate. See docs/plans/2026-09-28-phase-0-scaffold.md, Task 4."
```

- [ ] **Step 2:** `gh issue list`. Expected: 4 open issues, #1 to #4.

---

## Task 1: Scaffold and pinned versions (#1)

**Files:** create `pyproject.toml`, `tools.lock`, `Makefile`, `tests/test_tools_lock.py`, and an empty
`.gitkeep` in `knowledge/`, `missions/`, `.claude/skills/drone-mission-compliance/scripts/`,
`docs/data/`, `docs/screenshots/`.

- [ ] **Step 1: Write the project file and sync.**

`pyproject.toml`:

```toml
[project]
name = "okf-drone-skill"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["pyyaml>=6.0.2"]

[dependency-groups]
dev = ["pytest>=8.4", "jsonschema>=4.25", "ruff>=0.13"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = [".claude/skills/drone-mission-compliance/scripts"]

[tool.ruff]
line-length = 100
```

Run `uv sync`. Expected: `uv.lock` is created.

- [ ] **Step 2: Write the failing test.**

`tests/test_tools_lock.py`:

```python
"""Check that tools.lock holds every pin and that each pin has a valid form."""

import re
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "tools.lock"
REQUIRED = {
    "OKF_COMMIT",
    "QGC_PLAN_VERSION",
    "QGC_MISSION_VERSION",
    "QGC_GEOFENCE_VERSION",
    "QGC_RALLY_VERSION",
    "SORA_EDITION",
}


def read_lock() -> dict[str, str]:
    """Return the KEY=VALUE pairs in tools.lock. Ignore comments and blank lines."""
    pairs: dict[str, str] = {}
    for line in LOCK.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        pairs[key] = value
    return pairs


def test_all_pins_present() -> None:
    assert REQUIRED <= read_lock().keys()


def test_okf_commit_is_full_sha() -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", read_lock()["OKF_COMMIT"])


def test_qgc_versions_are_integers() -> None:
    lock = read_lock()
    for key in REQUIRED - {"OKF_COMMIT", "SORA_EDITION"}:
        assert lock[key].isdigit(), key


def test_sora_edition() -> None:
    assert read_lock()["SORA_EDITION"] == "2.5"
```

Run `uv run pytest -q`. Expected: `4 failed`, each with `FileNotFoundError` for `tools.lock`.

- [ ] **Step 3: Write the pins.**

`tools.lock`:

```sh
# Pinned external versions. Read by the Makefile and tests/test_tools_lock.py.
# OKF v0.2 spec and reference visualizer (GoogleCloudPlatform/open-knowledge-format). No tags exist; pin by commit.
OKF_COMMIT=ad30107c31c06aec8a7d5636e0d1058118604e6f
# QGroundControl .plan format: https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html
QGC_PLAN_VERSION=1
QGC_MISSION_VERSION=2
QGC_GEOFENCE_VERSION=2
QGC_RALLY_VERSION=2
# JARUS SORA edition, as adopted by EASA ED Decision 2025/018/R.
SORA_EDITION=2.5
```

- [ ] **Step 4: Write the Makefile.** Recipe lines start with a tab.

`Makefile`:

```makefile
include tools.lock

PY := uv run python
OKF := reference-agent @ git+https://github.com/GoogleCloudPlatform/open-knowledge-format@$(OKF_COMMIT)

.PHONY: bootstrap test lint verify render clean

bootstrap:
	uv sync

test:
	uv run pytest -q

lint:
	uv run ruff check .

verify: lint test

render:
	mkdir -p out
	uvx --python 3.14 --from "$(OKF)" reference-agent visualize --bundle knowledge --out out/knowledge-viz.html

clean:
	rm -rf out .pytest_cache .ruff_cache
```

`make render` needs a bundle. Do not run it until Phase 1.

- [ ] **Step 5: Create the empty directories.**

```bash
mkdir -p knowledge missions .claude/skills/drone-mission-compliance/scripts docs/data docs/screenshots
touch knowledge/.gitkeep missions/.gitkeep .claude/skills/drone-mission-compliance/scripts/.gitkeep docs/data/.gitkeep docs/screenshots/.gitkeep
```

- [ ] **Step 6: Verify.** Run `make verify`. Expected: `All checks passed!` and `4 passed`.

- [ ] **Step 7: Commit.**

```bash
git add pyproject.toml uv.lock tools.lock Makefile tests knowledge missions .claude docs/data docs/screenshots
git commit -m "Add the scaffold and the pinned versions" -m "Closes #1"
```

---

## Task 2: Vendored .plan subset schema (#2)

**Files:** create `tests/test_plan_schema.py`, `tests/fixtures/qgc/plan.schema.json`,
`tests/fixtures/qgc/minimal.plan`.

The schema is written for this repo from the QGC documentation (source S8). It accepts only
`SimpleItem` mission items and polygon geofences, as the spec §1 scope says. The polygon
`version` accepts 1 and 2, because the QGC page states 2 but its example uses 1.

- [ ] **Step 1: Write the failing test.**

`tests/test_plan_schema.py`:

```python
"""Check the vendored .plan subset schema against a valid plan and against broken copies."""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from test_tools_lock import read_lock

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "qgc"
SCHEMA = json.loads((FIXTURES / "plan.schema.json").read_text())
VALID = json.loads((FIXTURES / "minimal.plan").read_text())


def errors(plan: dict[str, Any]) -> list[str]:
    """Return the schema error messages for a plan."""
    return [e.message for e in Draft202012Validator(SCHEMA).iter_errors(plan)]


def test_schema_is_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)


def test_minimal_plan_is_valid() -> None:
    assert errors(VALID) == []


def test_schema_versions_match_tools_lock() -> None:
    lock = read_lock()
    props = SCHEMA["properties"]
    assert props["version"]["const"] == int(lock["QGC_PLAN_VERSION"])
    assert props["mission"]["properties"]["version"]["const"] == int(lock["QGC_MISSION_VERSION"])
    assert props["geoFence"]["properties"]["version"]["const"] == int(lock["QGC_GEOFENCE_VERSION"])
    assert props["rallyPoints"]["properties"]["version"]["const"] == int(lock["QGC_RALLY_VERSION"])


def _drop_file_type(p: dict[str, Any]) -> None:
    del p["fileType"]


def _mission_v1(p: dict[str, Any]) -> None:
    p["mission"]["version"] = 1


def _six_params(p: dict[str, Any]) -> None:
    p["mission"]["items"][0]["params"] = [0, 0, 0, 0, 0, 0]


def _complex_item(p: dict[str, Any]) -> None:
    p["mission"]["items"][0]["type"] = "ComplexItem"


def _two_point_fence(p: dict[str, Any]) -> None:
    p["geoFence"]["polygons"][0]["polygon"] = [[44.79, -0.60], [44.80, -0.60]]


def _bad_latitude(p: dict[str, Any]) -> None:
    p["mission"]["plannedHomePosition"][0] = 91.0


def _circle_fence(p: dict[str, Any]) -> None:
    p["geoFence"]["circles"] = [{"circle": {"center": [44.8, -0.6], "radius": 100}}]


@pytest.mark.parametrize(
    "breaks",
    [_drop_file_type, _mission_v1, _six_params, _complex_item, _two_point_fence, _bad_latitude, _circle_fence],
)
def test_broken_plan_is_rejected(breaks: Callable[[dict[str, Any]], None]) -> None:
    plan = copy.deepcopy(VALID)
    breaks(plan)
    assert errors(plan) != []
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_plan_schema.py` with
`FileNotFoundError` for `plan.schema.json`.

- [ ] **Step 2: Write the schema.**

`tests/fixtures/qgc/plan.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "okf-drone-skill/qgc-plan-subset",
  "title": "QGroundControl .plan file (subset)",
  "$comment": "Subset written for this repo from https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html. Only SimpleItem mission items. Circle geofences and ComplexItem are not in v1.",
  "type": "object",
  "required": ["fileType", "version", "groundStation", "mission", "geoFence", "rallyPoints"],
  "properties": {
    "fileType": {"const": "Plan"},
    "version": {"const": 1},
    "groundStation": {"type": "string"},
    "mission": {
      "type": "object",
      "required": ["version", "firmwareType", "vehicleType", "cruiseSpeed", "hoverSpeed", "plannedHomePosition", "items"],
      "properties": {
        "version": {"const": 2},
        "firmwareType": {"type": "integer"},
        "globalPlanAltitudeMode": {"type": "integer"},
        "vehicleType": {"type": "integer"},
        "cruiseSpeed": {"type": "number"},
        "hoverSpeed": {"type": "number"},
        "plannedHomePosition": {"$ref": "#/$defs/latLonAlt"},
        "items": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/simpleItem"}}
      }
    },
    "geoFence": {
      "type": "object",
      "required": ["version", "circles", "polygons"],
      "properties": {
        "version": {"const": 2},
        "circles": {"type": "array", "maxItems": 0},
        "polygons": {"type": "array", "items": {"$ref": "#/$defs/fencePolygon"}}
      }
    },
    "rallyPoints": {
      "type": "object",
      "required": ["version", "points"],
      "properties": {
        "version": {"const": 2},
        "points": {"type": "array", "items": {"$ref": "#/$defs/latLonAlt"}}
      }
    }
  },
  "$defs": {
    "latLonAlt": {
      "type": "array",
      "prefixItems": [
        {"type": "number", "minimum": -90, "maximum": 90},
        {"type": "number", "minimum": -180, "maximum": 180},
        {"type": "number"}
      ],
      "minItems": 3,
      "maxItems": 3
    },
    "latLon": {
      "type": "array",
      "prefixItems": [
        {"type": "number", "minimum": -90, "maximum": 90},
        {"type": "number", "minimum": -180, "maximum": 180}
      ],
      "minItems": 2,
      "maxItems": 2
    },
    "simpleItem": {
      "type": "object",
      "required": ["type", "command", "frame", "params", "autoContinue", "doJumpId"],
      "properties": {
        "type": {"const": "SimpleItem"},
        "command": {"type": "integer"},
        "frame": {"type": "integer"},
        "params": {"type": "array", "minItems": 7, "maxItems": 7, "items": {"type": ["number", "null"]}},
        "autoContinue": {"type": "boolean"},
        "doJumpId": {"type": "integer", "minimum": 1},
        "Altitude": {"type": "number"},
        "AltitudeMode": {"type": "integer"},
        "AMSLAltAboveTerrain": {"type": ["number", "null"]}
      }
    },
    "fencePolygon": {
      "type": "object",
      "required": ["inclusion", "polygon", "version"],
      "properties": {
        "inclusion": {"type": "boolean"},
        "polygon": {"type": "array", "minItems": 3, "items": {"$ref": "#/$defs/latLon"}},
        "version": {"enum": [1, 2]}
      }
    }
  }
}
```

- [ ] **Step 3: Write the valid fixture.** Takeoff (22), one waypoint (16), RTL (20), and an
inclusion fence around them. The coordinates are arbitrary test values.

`tests/fixtures/qgc/minimal.plan`:

```json
{
  "fileType": "Plan",
  "version": 1,
  "groundStation": "okf-drone-skill",
  "mission": {
    "version": 2,
    "firmwareType": 12,
    "globalPlanAltitudeMode": 1,
    "vehicleType": 2,
    "cruiseSpeed": 15,
    "hoverSpeed": 5,
    "plannedHomePosition": [44.8000, -0.6000, 50.0],
    "items": [
      {"type": "SimpleItem", "command": 22, "frame": 3, "params": [0, 0, 0, null, 44.8000, -0.6000, 30],
       "autoContinue": true, "doJumpId": 1, "Altitude": 30, "AltitudeMode": 1, "AMSLAltAboveTerrain": null},
      {"type": "SimpleItem", "command": 16, "frame": 3, "params": [0, 0, 0, null, 44.8010, -0.6000, 30],
       "autoContinue": true, "doJumpId": 2, "Altitude": 30, "AltitudeMode": 1, "AMSLAltAboveTerrain": null},
      {"type": "SimpleItem", "command": 20, "frame": 2, "params": [0, 0, 0, 0, 0, 0, 0],
       "autoContinue": true, "doJumpId": 3}
    ]
  },
  "geoFence": {
    "version": 2,
    "circles": [],
    "polygons": [
      {"inclusion": true, "version": 1,
       "polygon": [[44.7990, -0.6010], [44.8020, -0.6010], [44.8020, -0.5990], [44.7990, -0.5990]]}
    ]
  },
  "rallyPoints": {"version": 2, "points": []}
}
```

- [ ] **Step 4: Verify.** Run `make verify`. Expected: `All checks passed!` and `14 passed`.

- [ ] **Step 5: Commit.**

```bash
git add tests
git commit -m "Add the .plan subset schema and its tests" -m "Closes #2"
```

---

## Task 3: Source register (#3)

**Files:** create `docs/sources.md`.

`docs/sources.md`:

```markdown
# Sources

Every regulatory value in `knowledge/` comes from a document in this table.
The owner reads each document and sets `Status` to `read` with the date.
A concept can cite only a document with status `read`.

| Id | Document | Edition / date | URL | Needed for | Status |
|---|---|---|---|---|---|
| S1 | Commission Implementing Regulation (EU) 2019/947 | consolidated text | https://eur-lex.europa.eu/eli/reg_impl/2019/947/oj | `regulations/easa-open`, `regulations/easa-specific-sora` | unread |
| S2 | EASA ED Decision 2025/018/R, Annex (AMC & GM to Reg. 2019/947, Issue 1, Amendment 4; SORA 2.5) | 15 Sep 2025; corrigendum 12 Dec 2025 | https://easa.europa.eu/en/document-library/agency-decisions/ed-decision-2025018r | applicability and transition dates | unread |
| S3 | EASA Easy Access Rules for UAS | revision of June 2026 | https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-unmanned-aircraft-systems-regulations-eu | consolidated AMC text | unread |
| S4 | JARUS SORA 2.5 Main Body (JAR_doc_25) | 2.5 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf | `risk/igrc`, `risk/arc`, `risk/sail`, `risk/containment`, M1(A)/M1(B)/M1(C), M2, M3 status, OSO list | unread |
| S5 | JARUS SORA 2.5 Annex E (JAR_doc_28) | 2.5 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Annex-E-Release.JAR_doc_28pdf.pdf | OSO robustness | unread |
| S6 | JARUS SORA 2.5 Annex F (JAR_doc_29) | 2.5 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Annex-F-Release.JAR_doc_29pdf.pdf | critical-area model for non-typical UA (not needed for the v1 iGRC table) | unread |
| S7 | PX4 parameter reference | main | https://docs.px4.io/main/en/advanced_config/parameter_reference.html | `failsafes/*` parameter names | unread |
| S8 | QGroundControl plan file format | master | https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html | `platform/qgc-plan-format`, `tests/fixtures/qgc/plan.schema.json` | read 2026-09-28 by agent; owner to confirm |

## Local copies

Downloaded by the owner on 2026-09-28 (local time). Kept outside the repo; not redistributed.

| File | Source | Download page | Bytes | SHA-256 |
|---|---|---|---|---|
| `annex_to_ed_decision_2025-018-r_1.pdf` | S2 | https://www.easa.europa.eu/en/downloads/142514/en | 3448513 | `4733d5501b55297ed2b27cd8dceeb1eee3268af05f9421318bc54b452f83999e` |
| `corrigendum_to_ed_decision_2025-018-r.pdf` | S2 | https://www.easa.europa.eu/en/downloads/142969/en | 167350 | `b810d348896c3cecf34365e41a9275533f8e13649659f2d2872f48ed35119ff3` |
| `SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf` | S4 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf | 1344663 | `2471913e55c38999dc5ba0894ac696c3e4722ddb0956b1c62f15e6fbd9a1be1c` |

The Decision itself (2 pages, not stored locally): https://www.easa.europa.eu/en/downloads/142510/en.
Per that text (read by agent 2026-09-28, owner to confirm), the Decision enters into force on its
publication in the EASA Official Publication.

EASA SORA overview page (links to the SORA 2.5 package):
https://www.easa.europa.eu/en/domains/drones-air-mobility/operating-drone/specific-category-civil-drones/specific-operations-risk-assessment-sora#group-easa-downloads

## Findings to confirm when reading S4

These come from a secondary source (https://eudroneport.com/blog/sora-2-5-european-uas-operations/).

1. M1 is split into M1(A) sheltering, M1(B) operational restrictions, M1(C) ground observation.
2. Intrinsic GRC uses population density and a critical-area calculation (Annex F).
3. Containment has low, medium and high levels.

Checked 2026-09-28 in S4 (agent, text extraction and page images). The owner confirms.

- M3: S4 change log (edition 2.5) says "Removal of ERP as a mitigation". S4 Table 5 lists only
  M1(A), M1(B), M1(C) and M2. S2 OSO #08 names the ERP as Criterion #4.
- SAIL: S4 §4.7, Table 7 (p. 47): final GRC x residual ARC -> SAIL I to VI; final GRC > 7 is
  Category C (certified).
- Containment: S4 §4.8, Tables 8 to 13 (pp. 49-51), by UA size, SAIL, adjacent-area population
  and outdoor assemblies. Table 8 rows read "IV - VI" and "V-VI"; confirm on the page.
- OSOs: S4 §4.9.3, Table 14 (p. 54): 17 OSOs (#01-#09, #13, #16-#20, #23, #24).
- S2 and S4 differ: OSO #04 is L/M/H for SAIL IV/V/VI in S4 and M/H/H in S2 (p. 44). The
  dependency columns also differ. The bundle uses S2 values and cites S4 as origin.

Population density bands: found 2026-09-28 in S2 (AMC Issue 1, Amendment 3, Table 1 and
Table 2, pages 23-25) and S4 (Table 2 and Table 3, pages 34-36). The iGRC values are the same in
both. Bands: controlled ground area, < 5, < 50, < 500, < 5 000, < 50 000, > 50 000 people/km2.
The owner confirms.

Resolved 2026-09-28: the corrigendum to ED Decision 2025/018/R (12 December 2025, 1 page) only
renames the annex. "AMC and GM to Reg. (EU) 2019/947 — Issue 1, Amendment 3" becomes
"Issue 1, Amendment 4". It changes no text or table. Decision date: 15 September 2025.
Cite S2 as "AMC & GM to Reg. (EU) 2019/947, Issue 1, Amendment 4 (ED Decision 2025/018/R, as
corrected 12 December 2025)". The downloaded annex does not state an applicability date.

## Known discrepancy in S8

The geofence polygon table says "Documented version is 2", but the polygon example uses
`"version": 1`. The subset schema accepts both.
```

- [ ] **Step 1:** Write the file above.
- [ ] **Step 2: Verify.** `make verify` still gives `14 passed`.
- [ ] **Step 3: Commit.** Docs only; no test.

```bash
git add docs/sources.md
git commit -m "Add the source register (docs only)" -m "Closes #3"
```

---

## Task 4: Human gate: owner reads the sources (#4)

**The executing agent stops here and hands off to the owner.**

- [ ] **Step 1:** The owner reads S1 to S7 and sets each `Status` to `read YYYY-MM-DD`.
- [ ] **Step 2:** Done 2026-09-28: the corrigendum renames the annex only.
- [ ] **Step 3:** The owner confirms or corrects the three findings and fills the four unknowns in
  `docs/sources.md`.
- [ ] **Step 4:** The owner confirms S8.
- [ ] **Step 5:** Commit (docs only) with `Closes #4`.

After Task 4: write the Phase 1 plan (the bundle, DRN-03) from the confirmed values.
