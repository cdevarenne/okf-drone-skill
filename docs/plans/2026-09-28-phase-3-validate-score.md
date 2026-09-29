# okf-drone-skill Phase 3 Plan: validate_plan and score_risk

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** `make plan MISSION=<path>` writes `mission.plan`, then `validation.json` (the v1
checks) and `risk.json` (the hazard matrix and the SORA 2.5 summary). Every result cites the one
verified concept that governs it, or is a gap.

**Spec:** `docs/specs/2026-09-28-okf-drone-skill-v1-design.md` §5.3, §5.4, §5.5, §6 steps 3
and 4, §9 Phase 3. **Backlog:** DRN-05 (`validate_plan`), DRN-06 (`score_risk`).

**Provenance:** Tasks 1 to 4 were run in a prototype on 2026-09-28 (Python 3.14.0rc2, uv 0.8.17,
ruff 0.16.9, pytest 9.1.1), on a copy of `main` at `ebc7d8f`. The file contents below are copied
from that run. The tasks were replayed in order on a fresh copy; the replay is identical to the
prototype, and the expected outputs come from it. The prototype found one bug before the plan
was written: the hazard matrix lost the second line of a wrapped mitigation bullet.

## Global constraints

- Commits on `main` as `cdevarenne`, dated in PST (`TZ=America/Los_Angeles`). Short subject in
  ASD-STE100. Body line `Closes #N`.
- Every commit ships tests, or says that it is docs only. The test fails first.
- Before every commit: `make verify`. Run `ruff format` only on the files of the task, never on
  a whole folder (it reformats committed files).
- No rule value in code. Every check reads its rule from `table:` of its governing concept.
- A concept counts only if a person verified it. An unverified concept is a missing concept.

## Decisions for the owner (before Task 0)

1. **Two new statuses and gap kinds** (spec §5.3). `not_applicable`: the concept does not apply
   (the open-category height limit on a specific mission; SORA on an open mission). It does not
   change the decision. A `gap` can now also cite a concept: the concept exists, but a declared
   input is missing (`terrain: varied`, an ARC fact, the adjacent area).
2. **Unverified = missing.** Spec §5.4 says an unverified table gives `not_assessed`. The code
   checks for a `verified` entry by `human:` at run time.
3. **ARC facts are declared, not derived.** The `risk/arc` rules name facts such as
   `above_500ft_agl`. The 500 ft value is in a key name, not a value, so the code does not
   compute it from the altitude. A specific mission declares all seven facts; a missing fact is
   a gap. `above_500ft_agl` is about the operational volume (flight geography plus contingency
   volume), which the operator knows and v1 does not model.
4. **The SORA block** (`sora.mitigations`, `sora.adjacent_area`) is declared by the operator.
   The levels of robustness are claims that the report shows; v1 does not check the Annex B
   criteria.
5. **Containment table choice.** The first table that fits the UA size (`max_dimension_m`),
   speed (`below_speed_ms`) and the declared `shelter`. A 1 m UA with `shelter: false` uses
   Table 10 (3 m, no shelter), because Table 8 assumes shelter. The column is the more
   stringent of the declared density limit and assembly size.
6. **Two names in code, with comments:** the band `assemblies-of-people` (for the small-UA
   exception) and the prefix `risk/m1` (the M1 floor applies to M1 mitigations only). Both
   name bundle content; neither is a value.
7. **Every specific mission is HOLD in v1**, because `sora.oso` has no concept (Phase 1,
   Decision 2). Seeded m05 relies on this.
8. **The decision** (GO / NO-GO / HOLD) is Phase 4 (`render_report`). Phase 3 writes the
   results that it reads.

## Task 0: Tracking issues (no commit)

- [ ] **Step 1:** Create one issue per task. The last issue is #21, so Task N becomes #N+21.

```
T1 (DRN-05): Spec: result statuses, risk.json and the SORA inputs
T2 (DRN-05): Mission schema: ARC facts and the SORA block
T3 (DRN-05): validate_plan
T4 (DRN-06): score_risk and the full plan target
T5 (DRN-06): README for Phase 3
```

Body: `Phase 3. See docs/plans/2026-09-28-phase-3-validate-score.md, Task N.`

- [ ] **Step 2:** List the issues. Expected: #22 to #26 open.

---

## Task 1: Spec: result statuses, risk.json and the SORA inputs (#22)

**Files:** modify `docs/specs/2026-09-28-okf-drone-skill-v1-design.md`. Docs only.

- [ ] **Step 1:** Apply this change (`git apply` accepts it):

```diff
--- a/docs/specs/2026-09-28-okf-drone-skill-v1-design.md
+++ b/docs/specs/2026-09-28-okf-drone-skill-v1-design.md
@@ -126,6 +126,25 @@
 failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
 ```
 
+A `specific` mission also declares the ARC facts (the `when` keys of `risk/arc`) and a `sora`
+block. A missing fact or block gives a gap for the SORA step that needs it.
+
+```yaml
+airspace:
+  class: G
+  declared_by: operator
+  atypical_airspace: false
+  above_fl600: false
+  airport_environment: false
+  above_500ft_agl: false     # the operational volume, not only the flight geography
+  mode_c_veil_or_tmz: false
+  controlled_airspace: false
+  over_urban_area: false
+sora:
+  mitigations: {m1a: low}    # risk/<id>: declared level of robustness (low | medium | high)
+  adjacent_area: {below_people_km2: 5000, assemblies: under-40k, shelter: true}
+```
+
 The schema is `.claude/skills/drone-mission-compliance/schemas/mission.schema.json` (Phase 2).
 Value sets that come from the bundle (mission types, population density bands, failsafe
 actions) are not in the schema; the pipeline checks them against the bundle.
@@ -137,14 +156,29 @@
 
 ### 5.3 Check result (`validation.json`)
 
-`{check_id, status: pass|fail|gap, concept_id|null, evidence, message}`.
-`gap` has `concept_id: null` and names the missing concept.
+`{mission_id, checks: [{check_id, status: pass|fail|gap|not_applicable, concept_id|null,
+evidence, message}]}`.
+
+- A concept counts only if it has a `verified` entry by a person. An unverified concept is
+  treated as missing.
+- `gap` with `concept_id: null`: no verified concept governs the check; the message names it.
+- `gap` with a `concept_id`: the concept exists, but a declared input that it needs is missing
+  (for example `terrain: varied`, or an ARC fact); the message names the input.
+- `not_applicable`: the concept does not apply to this mission (for example the open-category
+  height limit on a specific-category mission).
 
 ### 5.4 Risk result (`risk.json`)
 
-Hazard matrix rows `{hazard_id, likelihood, severity, score, mitigations[], residual}`.
-SORA summary `{igrc, mitigations_applied[], final_grc, initial_arc, residual_arc, sail}`.
-Each value cites its concept. A missing or unverified table gives `"not_assessed"` plus a gap.
+`{mission_id, hazards: [...], sora: {...}, checks: [...]}`.
+
+Hazard matrix rows `{hazard_id, likelihood, severity, score, mitigations[], residual}`, one per
+verified hazard. `score` is likelihood x severity.
+SORA summary: `igrc`, `final_grc`, `initial_arc`, `residual_arc`, `tmpr`, `sail`,
+`containment`, `oso`, each `{value, concept_id}`, plus `mitigations_applied[]`. Only a
+`specific` mission is scored; for an `open` mission the summary is
+`{status: not_applicable}`. `checks` has one result per SORA step, in the §5.3 form.
+A value that cannot be found is `"not_assessed"` and has a gap; the steps after it are
+`"not_assessed"` too.
 
 ### 5.5 Decision
 
@@ -152,6 +186,9 @@
 - **NO-GO:** at least one check fails.
 - **HOLD:** no fail, but at least one gap. A human must add knowledge or decide.
 
+The decision reads the checks in `validation.json` and in `risk.json`. `not_applicable` does
+not change it.
+
 ## 6. Pipeline
 
 `gen_plan | validate_plan | score_risk | render_report`, file-based, one purpose each.
@@ -167,7 +204,12 @@
    `regulations/easa-open` limit is from the closest point of the surface. With
    `terrain: flat`, the check compares the plan altitudes with the limit. With
    `terrain: varied`, v1 has no terrain data, so the check is a gap (HOLD).
-4. `score_risk`: hazard matrix from `hazards/`; SORA summary from `risk/` tables.
+4. `score_risk`: hazard matrix from `hazards/`; SORA summary from `risk/` tables, in step
+   order: iGRC (band row, left-most column that fits the UA; the small-UA rule), final GRC
+   (the declared mitigations in `sequence` order; the M1 floor), initial ARC (first matching
+   rule), residual ARC and TMPR (VLOS reduction), SAIL, containment (the first table that fits
+   the UA size, speed and declared shelter; the more stringent of the density and assembly
+   columns). The OSO step has no concept in v1, so a specific mission is always HOLD.
 5. `render_report`: fills the flight-plan template sections, the decision and the audit trail.
 
 ## 7. Seeded missions (`missions/SEEDED.yaml`)
```

- [ ] **Step 2: Verify.** `make verify`. Expected: `216 passed`.
- [ ] **Step 3: Commit.** `Add the result statuses, risk.json and the SORA inputs to the spec (docs only)`,
  `Closes #22`.

---

## Task 2: Mission schema: ARC facts and the SORA block (#23)

**Files:** create `tests/fixtures/missions/specific.yaml`; modify
`.claude/skills/drone-mission-compliance/schemas/mission.schema.json`.

- [ ] **Step 1: Write the failing test.** The new fixture is the failing test:
  `test_fixture_mission_is_valid` runs on every fixture.

`tests/fixtures/missions/specific.yaml`:

```yaml
# Test fixture. The coordinates are arbitrary test values.
id: specific
mission_type: mapping-survey
category: specific
operation: BVLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8030, -0.6020], [44.8030, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 60
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

Run `uv run pytest -q`. Expected: `1 failed, 216 passed`
(`test_fixture_mission_is_valid[specific]`: `airspace` and `sora` are not in the schema).

- [ ] **Step 2: Replace the schema.** The file is now written by `json.dumps(indent=2)`, so the
  whole file changes form. The new parts are `airspace` (seven optional boolean facts,
  `additionalProperties: false`) and `sora`.

`.claude/skills/drone-mission-compliance/schemas/mission.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "okf-drone-skill/mission-request",
  "title": "Mission request (missions/<id>.yaml)",
  "$comment": "Spec \u00a75.2. Value sets that come from the bundle (mission_type, population_density, failsafe actions) are not listed here; the pipeline checks them against the bundle. The airspace facts are the ARC conditions in risk/arc; they and the sora block are needed only for category specific.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "id",
    "mission_type",
    "category",
    "operation",
    "home",
    "terrain",
    "area",
    "geofence",
    "max_altitude_agl_m",
    "speed_ms",
    "pattern",
    "ua",
    "ground",
    "airspace",
    "failsafes"
  ],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]*$"
    },
    "mission_type": {
      "type": "string"
    },
    "category": {
      "enum": [
        "open",
        "specific"
      ]
    },
    "operation": {
      "enum": [
        "VLOS",
        "BVLOS"
      ]
    },
    "home": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "lat",
        "lon",
        "amsl_m"
      ],
      "properties": {
        "lat": {
          "type": "number",
          "minimum": -90,
          "maximum": 90
        },
        "lon": {
          "type": "number",
          "minimum": -180,
          "maximum": 180
        },
        "amsl_m": {
          "type": "number"
        }
      }
    },
    "terrain": {
      "enum": [
        "flat",
        "varied"
      ]
    },
    "area": {
      "$ref": "#/$defs/polygonObject"
    },
    "geofence": {
      "$ref": "#/$defs/polygonObject"
    },
    "max_altitude_agl_m": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "speed_ms": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "pattern": {
      "oneOf": [
        {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "spacing_m"
          ],
          "properties": {
            "spacing_m": {
              "type": "number",
              "exclusiveMinimum": 0
            },
            "datum": {
              "$ref": "#/$defs/latLon"
            }
          }
        },
        {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "route"
          ],
          "properties": {
            "route": {
              "type": "array",
              "minItems": 2,
              "items": {
                "$ref": "#/$defs/latLon"
              }
            }
          }
        }
      ]
    },
    "ua": {
      "type": "object",
      "required": [
        "mtom_kg",
        "char_dimension_m",
        "max_speed_ms"
      ],
      "properties": {
        "mtom_kg": {
          "type": "number",
          "exclusiveMinimum": 0
        },
        "char_dimension_m": {
          "type": "number",
          "exclusiveMinimum": 0
        },
        "max_speed_ms": {
          "type": "number",
          "exclusiveMinimum": 0
        }
      }
    },
    "ground": {
      "type": "object",
      "required": [
        "population_density"
      ],
      "properties": {
        "population_density": {
          "type": "string"
        }
      }
    },
    "airspace": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "class",
        "declared_by"
      ],
      "properties": {
        "class": {
          "type": "string"
        },
        "declared_by": {
          "type": "string"
        },
        "atypical_airspace": {
          "type": "boolean"
        },
        "above_fl600": {
          "type": "boolean"
        },
        "airport_environment": {
          "type": "boolean"
        },
        "above_500ft_agl": {
          "type": "boolean"
        },
        "mode_c_veil_or_tmz": {
          "type": "boolean"
        },
        "controlled_airspace": {
          "type": "boolean"
        },
        "over_urban_area": {
          "type": "boolean"
        }
      }
    },
    "failsafes": {
      "type": "object",
      "additionalProperties": {
        "type": "string"
      },
      "propertyNames": {
        "enum": [
          "lost_link",
          "low_battery",
          "critical_battery",
          "geofence_breach"
        ]
      }
    },
    "sora": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "mitigations": {
          "type": "object",
          "additionalProperties": {
            "enum": [
              "low",
              "medium",
              "high"
            ]
          }
        },
        "adjacent_area": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "below_people_km2",
            "assemblies",
            "shelter"
          ],
          "properties": {
            "below_people_km2": {
              "type": [
                "number",
                "null"
              ],
              "exclusiveMinimum": 0
            },
            "assemblies": {
              "type": "string"
            },
            "shelter": {
              "type": "boolean"
            }
          }
        }
      }
    }
  },
  "$defs": {
    "latLon": {
      "type": "array",
      "prefixItems": [
        {
          "type": "number",
          "minimum": -90,
          "maximum": 90
        },
        {
          "type": "number",
          "minimum": -180,
          "maximum": 180
        }
      ],
      "minItems": 2,
      "maxItems": 2
    },
    "polygonObject": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "polygon"
      ],
      "properties": {
        "polygon": {
          "type": "array",
          "minItems": 3,
          "items": {
            "$ref": "#/$defs/latLon"
          }
        }
      }
    }
  }
}
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `All checks passed!` and `217 passed`.
- [ ] **Step 4: Commit.** `Add the ARC facts and the SORA block to the mission schema`,
  `Closes #23`.

---

## Task 3: validate_plan (#24)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/results.py`,
`.claude/skills/drone-mission-compliance/scripts/validate_plan.py`, `tests/bundle_helpers.py`,
`tests/test_validate_plan.py`.

- [ ] **Step 1: Write the failing test.**

`tests/bundle_helpers.py`:

```python
"""Helpers for tests that need a changed copy of the real bundle."""

from dataclasses import replace
from pathlib import Path

from okf_lib import Bundle, load_bundle

BUNDLE = load_bundle(Path(__file__).resolve().parents[1] / "knowledge")


def without(*concept_ids: str) -> Bundle:
    """Return the bundle without the given concepts."""
    return Bundle({k: v for k, v in BUNDLE.concepts.items() if k not in concept_ids})


def unverified(*concept_ids: str) -> Bundle:
    """Return the bundle with the `verified` entries removed from the given concepts."""
    concepts = dict(BUNDLE.concepts)
    for cid in concept_ids:
        fm = {k: v for k, v in concepts[cid].frontmatter.items() if k != "verified"}
        concepts[cid] = replace(concepts[cid], frontmatter=fm)
    return Bundle(concepts)
```

`tests/test_validate_plan.py`:

```python
"""Check validate_plan: each check against its concept, the gaps, and the CLI."""

import json
from pathlib import Path

import pytest
from bundle_helpers import BUNDLE, unverified, without
from gen_plan import build_plan, read_pins
from mission import load_mission
from validate_plan import CHECKS, main, validate

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"
PINS = read_pins(ROOT / "tools.lock")


def run(name: str = "survey", bundle=BUNDLE, edit_plan=None, **changes) -> dict[str, dict]:
    """Return {check_id: result} for a fixture mission with changes."""
    mission = load_mission(MISSIONS / f"{name}.yaml")
    mission.update(changes)
    plan = build_plan(mission, BUNDLE, PINS)
    if edit_plan:
        edit_plan(plan)
    return {r.check_id: r.to_dict() for r in validate(mission, plan, bundle)}


@pytest.mark.parametrize("name", ["survey", "inspection", "search"])
def test_fixture_missions_pass_every_check(name: str) -> None:
    results = run(name)
    assert list(results) == list(CHECKS)
    assert {r["status"] for r in results.values()} == {"pass"}


def test_every_result_cites_its_governing_concept() -> None:
    for check_id, r in run().items():
        assert r["concept_id"] == BUNDLE.governing(check_id).id


def test_altitude_above_the_limit_fails() -> None:
    """Seeded m02."""
    r = run(max_altitude_agl_m=150)["alt.max_agl"]
    assert (r["status"], r["concept_id"]) == ("fail", "regulations/easa-open")
    assert "150" in r["evidence"] and "120" in r["evidence"]


def test_varied_terrain_is_a_gap_with_its_concept() -> None:
    r = run(terrain="varied")["alt.max_agl"]
    assert (r["status"], r["concept_id"]) == ("gap", "regulations/easa-open")


def test_open_category_checks_do_not_apply_to_specific() -> None:
    results = run("specific")
    assert results["alt.max_agl"]["status"] == "not_applicable"
    assert results["category.operation"]["status"] == "pass"


@pytest.mark.parametrize(
    "changes",
    [{"operation": "BVLOS"}, {"ua": {"mtom_kg": 25, "char_dimension_m": 1, "max_speed_ms": 20}}],
)
def test_open_category_conditions_fail(changes: dict) -> None:
    assert run(**changes)["category.operation"]["status"] == "fail"


def test_waypoint_outside_the_geofence_fails() -> None:
    """Seeded m03: the declared geofence does not contain the whole area."""
    fence = {
        "polygon": [[44.7980, -0.6020], [44.8005, -0.6020], [44.8005, -0.5980], [44.7980, -0.5980]]
    }
    r = run(geofence=fence)["plan.inside_geofence"]
    assert (r["status"], r["concept_id"]) == ("fail", "failsafes/geofence-breach")


def test_missing_lost_link_action_fails() -> None:
    """Seeded m04."""
    failsafes = {"low_battery": "RTL", "critical_battery": "LAND", "geofence_breach": "RTL"}
    r = run(failsafes=failsafes)["failsafe.lost_link"]
    assert (r["status"], r["concept_id"]) == ("fail", "failsafes/lost-link")
    assert "not declared" in r["evidence"]


def test_action_not_in_the_concept_fails() -> None:
    failsafes = {
        "lost_link": "HOVER",
        "low_battery": "RTL",
        "critical_battery": "RTL",
        "geofence_breach": "RTL",
    }
    results = run(failsafes=failsafes)
    assert results["failsafe.lost_link"]["status"] == "fail"
    assert results["failsafe.critical_battery"]["status"] == "fail"


def test_plan_structure_checks() -> None:
    def break_ends(plan):
        items = plan["mission"]["items"]
        items[0]["command"], items[-1]["command"] = 16, 16

    results = run(edit_plan=break_ends)
    assert results["plan.first_item_takeoff"]["status"] == "fail"
    assert results["plan.last_item_return"]["status"] == "fail"


def test_plan_may_end_with_land() -> None:
    def land(plan):
        plan["mission"]["items"][-1]["command"] = 21

    assert run(edit_plan=land)["plan.last_item_return"]["status"] == "pass"


def test_missing_or_unverified_concept_is_a_gap() -> None:
    for bundle in (without("regulations/easa-open"), unverified("regulations/easa-open")):
        results = run(bundle=bundle)
        for check_id in ("alt.max_agl", "category.operation"):
            assert results[check_id]["status"] == "gap"
            assert results[check_id]["concept_id"] is None


def test_cli_writes_validation_json(tmp_path: Path) -> None:
    mission = MISSIONS / "survey.yaml"
    plan = build_plan(load_mission(mission), BUNDLE, PINS)
    (tmp_path / "survey").mkdir()
    (tmp_path / "survey" / "mission.plan").write_text(json.dumps(plan))
    args = [
        "--mission",
        str(mission),
        "--knowledge",
        str(ROOT / "knowledge"),
        "--out",
        str(tmp_path),
    ]
    assert main(args) == 0
    doc = json.loads((tmp_path / "survey" / "validation.json").read_text())
    assert doc["mission_id"] == "survey" and len(doc["checks"]) == len(CHECKS)


def test_cli_returns_2_without_a_plan(tmp_path: Path) -> None:
    args = ["--mission", str(MISSIONS / "survey.yaml"), "--knowledge", str(ROOT / "knowledge")]
    assert main([*args, "--out", str(tmp_path)]) == 2
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_validate_plan.py`,
`ModuleNotFoundError: No module named 'validate_plan'`.

- [ ] **Step 2: Write the shared results module.**

`.claude/skills/drone-mission-compliance/scripts/results.py`:

```python
"""Check results for validation.json and risk.json (spec §5.3, §5.4), and the grounding rule."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from okf_lib import Bundle, Concept

PASS, FAIL, GAP, NOT_APPLICABLE = "pass", "fail", "gap", "not_applicable"


@dataclass(frozen=True)
class CheckResult:
    """One check or score. `concept_id` is None only for a gap with no concept."""

    check_id: str
    status: str
    concept_id: str | None
    evidence: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_verified(concept: Concept) -> bool:
    """Return True if a person verified the concept (a `verified` entry by `human:...`)."""
    entries = concept.frontmatter.get("verified") or []
    return any(str(e.get("by", "")).startswith("human:") for e in entries)


def governing(bundle: Bundle, check_id: str) -> Concept | None:
    """Return the verified concept that governs `check_id`, or None (a coverage gap)."""
    concept = bundle.governing(check_id)
    return concept if concept is not None and is_verified(concept) else None


def verified_concept(bundle: Bundle, concept_id: str) -> Concept | None:
    """Return the concept `concept_id` if it exists and is verified, else None."""
    concept = bundle.concepts.get(concept_id)
    return concept if concept is not None and is_verified(concept) else None


def no_concept(check_id: str) -> CheckResult:
    """Return the gap for a check that no verified concept governs."""
    return CheckResult(
        check_id, GAP, None, "", f"no verified concept in the bundle governs {check_id}"
    )


def result(
    concept: Concept, check_id: str, status: str, evidence: str, message: str
) -> CheckResult:
    """Return a result that cites `concept`."""
    return CheckResult(check_id, status, concept.id, evidence, message)
```

- [ ] **Step 3: Write validate_plan.**

`.claude/skills/drone-mission-compliance/scripts/validate_plan.py`:

```python
"""Validate a .plan and its mission request against the bundle (spec §6, step 3).

Each check reads its rule from the one verified concept that governs its check id. A check with
no verified concept is a gap. validate_plan writes out/<id>/validation.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from geometry import LocalFrame, centroid, contains
from mission import MissionError, load_mission
from okf_lib import Bundle, Concept, load_bundle
from results import (
    FAIL,
    GAP,
    NOT_APPLICABLE,
    PASS,
    CheckResult,
    governing,
    no_concept,
    result,
    verified_concept,
)

Mission = dict[str, Any]
Plan = dict[str, Any]


def position_items(plan: Plan) -> list[dict[str, Any]]:
    """Return the mission items that have a position (QGC writes `Altitude` for them)."""
    return [i for i in plan["mission"]["items"] if "Altitude" in i]


def check_alt_max_agl(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "alt.max_agl"
    if m["category"] != "open":
        return result(c, cid, NOT_APPLICABLE, f"category {m['category']}", "open category only")
    if m["terrain"] != "flat":
        return result(
            c,
            cid,
            GAP,
            f"terrain {m['terrain']}",
            "the plan altitudes are relative to home; v1 has no terrain data",
        )
    limit = c.table["max_height_above_surface_m"]
    highest = max(i["Altitude"] for i in position_items(plan))
    evidence = f"highest item {highest} m above home; terrain flat; limit {limit} m"
    if highest > limit:
        return result(c, cid, FAIL, evidence, f"the plan flies above {limit} m")
    return result(c, cid, PASS, evidence, "the plan stays within the height limit")


def check_category_operation(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "category.operation"
    if m["category"] != "open":
        return result(c, cid, PASS, f"category {m['category']}", "no open-category condition")
    allowed, below = c.table["operations"], c.table["below_takeoff_mass_kg"]
    evidence = f"operation {m['operation']}; MTOM {m['ua']['mtom_kg']} kg"
    problems = []
    if m["operation"] not in allowed:
        problems.append(f"the open category allows only {', '.join(allowed)}")
    if not m["ua"]["mtom_kg"] < below:
        problems.append(f"the open category needs an MTOM below {below} kg")
    if problems:
        return result(c, cid, FAIL, evidence, "; ".join(problems))
    return result(c, cid, PASS, evidence, "the operation meets the open-category conditions")


def check_first_item_takeoff(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "plan.first_item_takeoff"
    first = plan["mission"]["items"][0]["command"]
    evidence = f"first item command {first}"
    if first != c.table["mavlink_id"]:
        return result(c, cid, FAIL, evidence, f"the first item is not {c.table['name']}")
    return result(c, cid, PASS, evidence, "the plan starts with a takeoff")


def check_last_item_return(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "plan.last_item_return"
    allowed = {c.table["mavlink_id"]}
    land = verified_concept(bundle, "mavlink/nav-land")
    if land is not None:
        allowed.add(land.table["mavlink_id"])
    last = plan["mission"]["items"][-1]["command"]
    evidence = f"last item command {last}; allowed {sorted(allowed)}"
    if last not in allowed:
        return result(c, cid, FAIL, evidence, "the plan does not end with RTL or LAND")
    return result(c, cid, PASS, evidence, "the plan ends with RTL or LAND")


def check_inside_geofence(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "plan.inside_geofence"
    fences = [
        [tuple(p) for p in f["polygon"]] for f in plan["geoFence"]["polygons"] if f["inclusion"]
    ]
    if not fences:
        return result(c, cid, FAIL, "no inclusion polygon", "the plan has no geofence")
    outside = []
    for item in position_items(plan):
        p = (item["params"][4], item["params"][5])
        if not any(_inside(fence, p) for fence in fences):
            outside.append(item["doJumpId"])
    evidence = f"{len(position_items(plan))} items; outside: {outside or 'none'}"
    if outside:
        return result(c, cid, FAIL, evidence, f"items {outside} are outside the geofence")
    return result(c, cid, PASS, evidence, "every item is inside the geofence")


def _inside(fence: list[tuple[float, float]], p: tuple[float, float]) -> bool:
    frame = LocalFrame(centroid(fence))
    return contains([frame.to_xy(q) for q in fence], frame.to_xy(p))


def _failsafe(m: Mission, c: Concept, cid: str, key: str, allowed: list[str]) -> CheckResult:
    declared = m["failsafes"].get(key)
    evidence = f"failsafes.{key}: {declared if declared is not None else 'not declared'}"
    if declared is None:
        return result(c, cid, FAIL, evidence, f"the mission declares no {key} action")
    if declared not in allowed:
        return result(c, cid, FAIL, evidence, f"{declared} is not one of {', '.join(allowed)}")
    return result(c, cid, PASS, evidence, f"the {key} action is {declared}")


def check_lost_link(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    return _failsafe(m, c, "failsafe.lost_link", c.table["mission_key"], c.table["actions"])


def check_low_battery(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    key = c.table["mission_keys"]["low"]
    return _failsafe(m, c, "failsafe.low_battery", key, c.table["actions"])


def check_critical_battery(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    key = c.table["mission_keys"]["critical"]
    return _failsafe(m, c, "failsafe.critical_battery", key, c.table["critical_actions"])


def check_geofence_breach(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    key = c.table["mission_key"]
    return _failsafe(m, c, "failsafe.geofence_breach", key, c.table["actions"])


Check = Callable[[Mission, Plan, Concept, Bundle], CheckResult]
CHECKS: dict[str, Check] = {
    "alt.max_agl": check_alt_max_agl,
    "category.operation": check_category_operation,
    "plan.first_item_takeoff": check_first_item_takeoff,
    "plan.last_item_return": check_last_item_return,
    "plan.inside_geofence": check_inside_geofence,
    "failsafe.lost_link": check_lost_link,
    "failsafe.low_battery": check_low_battery,
    "failsafe.critical_battery": check_critical_battery,
    "failsafe.geofence_breach": check_geofence_breach,
}


def validate(mission: Mission, plan: Plan, bundle: Bundle) -> list[CheckResult]:
    """Return one result per check, in the order of CHECKS."""
    results = []
    for check_id, fn in CHECKS.items():
        concept = governing(bundle, check_id)
        if concept is None:
            results.append(no_concept(check_id))
        else:
            results.append(fn(mission, plan, concept, bundle))
    return results


def main(argv: list[str] | None = None) -> int:
    """Write out/<id>/validation.json. Return 0, or 2 for a bad request or a missing plan."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
        plan_path = args.out / mission["id"] / "mission.plan"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (MissionError, OSError, ValueError) as e:
        print(e, file=sys.stderr)
        return 2
    checks = validate(mission, plan, load_bundle(args.knowledge))
    doc = {"mission_id": mission["id"], "checks": [r.to_dict() for r in checks]}
    out = args.out / mission["id"] / "validation.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Verify.** `make verify`. Expected: `All checks passed!` and `234 passed`.
- [ ] **Step 5: Commit.** `Add validate_plan`, `Closes #24`.

---

## Task 4: score_risk and the full plan target (#25)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/score_risk.py`,
`tests/test_score_risk.py`; modify `Makefile`.

- [ ] **Step 1: Write the failing test.**

`tests/test_score_risk.py`:

```python
"""Check score_risk: the hazard matrix, each SORA step against its table, the gaps, and the CLI."""

import copy
import json
from pathlib import Path

from bundle_helpers import BUNDLE, unverified
from mission import load_mission
from score_risk import hazard_matrix, main, score

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"


def specific(**changes) -> dict:
    mission = copy.deepcopy(load_mission(MISSIONS / "specific.yaml"))
    for path, value in changes.items():
        *parents, key = path.split("__")
        node = mission
        for p in parents:
            node = node[p]
        node[key] = value
    return mission


def sora(mission: dict, bundle=BUNDLE) -> tuple[dict, dict]:
    doc = score(mission, bundle)
    return doc["sora"], {c["check_id"]: c for c in doc["checks"]}


def value(summary: dict, key: str):
    return summary[key]["value"]


def test_hazard_matrix_rows() -> None:
    rows, gaps = hazard_matrix(BUNDLE)
    assert gaps == []
    assert {r["hazard_id"] for r in rows} == {c.id for c in BUNDLE.of_type("Hazard")}
    for r in rows:
        assert r["score"] == r["likelihood"] * r["severity"]
        assert r["mitigations"] and not any("](" in m for m in r["mitigations"])


def test_hazard_matrix_skips_unverified_hazards() -> None:
    rows, _ = hazard_matrix(unverified("hazards/loss-of-c2"))
    assert "hazards/loss-of-c2" not in {r["hazard_id"] for r in rows}


def test_open_category_is_not_scored() -> None:
    summary, checks = sora(load_mission(MISSIONS / "survey.yaml"))
    assert summary == {"status": "not_applicable"}
    assert list(checks) == ["sora.applicable"]
    assert checks["sora.applicable"]["concept_id"] == "regulations/easa-specific-sora"


def test_specific_fixture_summary() -> None:
    summary, checks = sora(specific())
    assert [value(summary, k) for k in ("igrc", "final_grc", "initial_arc", "residual_arc")] == [
        4,
        3,
        "b",
        "b",
    ]
    assert [value(summary, k) for k in ("tmpr", "sail", "containment")] == ["low", "II", "low"]
    assert summary["mitigations_applied"] == [
        {"concept_id": "risk/m1a", "level": "low", "credit": -1}
    ]
    assert checks["sora.oso"] == {
        "check_id": "sora.oso",
        "status": "gap",
        "concept_id": None,
        "evidence": "",
        "message": "no verified concept in the bundle governs sora.oso",
    }
    assert {c["status"] for k, c in checks.items() if k != "sora.oso"} == {"pass"}


def test_small_ua_rule() -> None:
    summary, _ = sora(specific(ua__mtom_kg=0.2, ua__max_speed_ms=20))
    assert value(summary, "igrc") == 1


def test_unknown_band_is_a_gap() -> None:
    _, checks = sora(specific(ground__population_density="crowded"))
    assert (checks["sora.igrc"]["status"], checks["sora.igrc"]["concept_id"]) == (
        "gap",
        "risk/igrc",
    )
    assert checks["sora.final_grc"]["status"] == "gap"


def test_ua_outside_the_table_fails() -> None:
    _, checks = sora(specific(ua__char_dimension_m=50))
    assert checks["sora.igrc"]["status"] == "fail"


def test_m1_floor() -> None:
    summary, _ = sora(specific(sora__mitigations={"m1a": "medium", "m1b": "high"}))
    assert value(summary, "final_grc") == 1


def test_mitigation_level_without_credit_fails() -> None:
    _, checks = sora(specific(sora__mitigations={"m1b": "low"}))
    assert checks["sora.final_grc"]["status"] == "fail"


def test_unknown_mitigation_is_a_gap() -> None:
    _, checks = sora(specific(sora__mitigations={"m3": "low"}))
    assert (checks["sora.final_grc"]["status"], checks["sora.final_grc"]["concept_id"]) == (
        "gap",
        "risk/igrc",
    )


def test_vlos_reduces_the_arc() -> None:
    summary, _ = sora(specific(operation="VLOS", airspace__over_urban_area=True))
    assert value(summary, "initial_arc") == "c"
    assert value(summary, "residual_arc") == "b"
    assert value(summary, "tmpr") == "none (VLOS)"


def test_missing_airspace_fact_is_a_gap_downstream_too() -> None:
    mission = specific()
    del mission["airspace"]["atypical_airspace"]
    summary, checks = sora(mission)
    assert (checks["sora.initial_arc"]["status"], checks["sora.initial_arc"]["concept_id"]) == (
        "gap",
        "risk/arc",
    )
    for key in ("residual_arc", "sail", "containment"):
        assert value(summary, key) == "not_assessed"
        assert checks[f"sora.{key}"]["status"] == "gap"


def test_final_grc_above_the_table_fails() -> None:
    mission = specific(
        ua__char_dimension_m=5,
        ua__max_speed_ms=60,
        ground__population_density="high-density-metropolitan",
        sora__mitigations={},
    )
    summary, checks = sora(mission)
    assert value(summary, "final_grc") == 8
    assert checks["sora.sail"]["status"] == "fail"


def test_containment_needs_the_adjacent_area() -> None:
    mission = specific()
    del mission["sora"]["adjacent_area"]
    _, checks = sora(mission)
    assert (checks["sora.containment"]["status"], checks["sora.containment"]["concept_id"]) == (
        "gap",
        "risk/containment",
    )


def test_containment_out_of_scope_fails() -> None:
    adjacent = {"below_people_km2": None, "assemblies": "over-400k", "shelter": True}
    mission = specific(ua__char_dimension_m=2, ua__max_speed_ms=30, sora__adjacent_area=adjacent)
    _, checks = sora(mission)
    assert checks["sora.containment"]["status"] == "fail"


def test_cli_writes_risk_json(tmp_path: Path) -> None:
    args = ["--mission", str(MISSIONS / "specific.yaml"), "--knowledge", str(ROOT / "knowledge")]
    assert main([*args, "--out", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "specific" / "risk.json").read_text())
    assert doc == score(load_mission(MISSIONS / "specific.yaml"), BUNDLE)
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_score_risk.py`,
`ModuleNotFoundError: No module named 'score_risk'`.

- [ ] **Step 2: Write score_risk.**

`.claude/skills/drone-mission-compliance/scripts/score_risk.py`:

```python
"""Score the mission risk: the hazard matrix and the SORA 2.5 summary (spec §6, step 4).

Every value comes from a verified concept. A value that cannot be found is "not_assessed" and
has a gap. score_risk writes out/<id>/risk.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from mission import MissionError, load_mission
from okf_lib import Bundle, load_bundle
from results import (
    FAIL,
    GAP,
    NOT_APPLICABLE,
    PASS,
    CheckResult,
    governing,
    is_verified,
    no_concept,
    result,
)

NOT_ASSESSED = "not_assessed"
ASSEMBLIES_BAND = "assemblies-of-people"  # the band name in risk/igrc for `not_over_assemblies`
M1_PREFIX = "risk/m1"  # the M1 mitigations, to which the iGRC floor applies (S2 S.4.3.4)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")

Mission = dict[str, Any]


def hazard_matrix(bundle: Bundle) -> tuple[list[dict[str, Any]], list[CheckResult]]:
    """Return one row per verified Hazard concept, and a gap if there is none."""
    rows = []
    for c in bundle.of_type("Hazard"):
        if not is_verified(c):
            continue
        fm = c.frontmatter
        mitigations = _bullets(bundle.section(c, "Mitigation") or "")
        rows.append(
            {
                "hazard_id": c.id,
                "likelihood": fm["likelihood"],
                "severity": fm["severity"],
                "score": fm["likelihood"] * fm["severity"],
                "mitigations": mitigations,
                "residual": fm["residual"],
            }
        )
    gaps = [] if rows else [no_concept("hazards.matrix")]
    return rows, gaps


def _bullets(text: str) -> list[str]:
    """Return the '- ' list items of a section, with wrapped lines joined and links as text."""
    items: list[str] = []
    for line in text.splitlines():
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("  ") and items:
            items[-1] += " " + line.strip()
    return [_LINK.sub(r"\1", item) for item in items]


class _Sora:
    """The SORA 2.5 steps for one specific-category mission, in order."""

    def __init__(self, mission: Mission, bundle: Bundle) -> None:
        self.m, self.bundle = mission, bundle
        self.summary: dict[str, Any] = {}
        self.checks: list[CheckResult] = []

    def _add(self, key: str, value: Any, check: CheckResult) -> Any:
        self.summary[key] = {"value": value, "concept_id": check.concept_id}
        self.checks.append(check)
        return value if check.status == PASS else None

    def _skip(self, key: str, check_id: str, needs: str) -> None:
        self.summary[key] = {"value": NOT_ASSESSED, "concept_id": None}
        self.checks.append(CheckResult(check_id, GAP, None, "", f"not assessed: it needs {needs}"))

    def igrc(self) -> tuple[int, int | None] | None:
        cid = "sora.igrc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["igrc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        ua, band = self.m["ua"], self.m["ground"]["population_density"]
        row = next((r for r in c.table["rows"] if r["band"] == band), None)
        if row is None:
            bands = ", ".join(r["band"] for r in c.table["rows"])
            self._add(
                "igrc", NOT_ASSESSED, result(c, cid, GAP, f"band {band}", f"use one of: {bands}")
            )
            return None
        small = c.table["small_ua"]
        if (
            ua["mtom_kg"] <= small["max_takeoff_mass_kg"]
            and ua["max_speed_ms"] <= small["max_speed_ms"]
            and not (small["not_over_assemblies"] and band == ASSEMBLIES_BAND)
        ):
            ev = f"MTOM {ua['mtom_kg']} kg, speed {ua['max_speed_ms']} m/s"
            self._add("igrc", small["igrc"], result(c, cid, PASS, ev, "small UA rule"))
            return small["igrc"], None
        col = next(
            (
                i
                for i, k in enumerate(c.table["columns"])
                if ua["char_dimension_m"] <= k["max_dimension_m"]
                and ua["max_speed_ms"] <= k["max_speed_ms"]
            ),
            None,
        )
        ev = f"band {band}; dimension {ua['char_dimension_m']} m; speed {ua['max_speed_ms']} m/s"
        value = None if col is None else row["igrc"][col]
        if value is None:
            self._add("igrc", None, result(c, cid, FAIL, ev, "outside SORA: certified category"))
            return None
        self._add("igrc", value, result(c, cid, PASS, ev, f"iGRC {value} (column {col + 1})"))
        return value, col

    def final_grc(self, igrc: int, col: int | None) -> int | None:
        cid = "sora.final_grc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["final_grc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        declared = (self.m.get("sora") or {}).get("mitigations") or {}
        concepts = {f"risk/{k}": level for k, level in declared.items()}
        mitigations = sorted(
            (m for m in self.bundle.of_type("Mitigation") if is_verified(m)),
            key=lambda m: m.table["sequence"],
        )
        unknown = sorted(set(concepts) - {m.id for m in mitigations})
        if unknown:
            msg = f"no verified mitigation concept for {', '.join(unknown)}"
            self._add("final_grc", NOT_ASSESSED, result(c, cid, GAP, str(declared), msg))
            return None
        grc, applied = igrc, []
        floor_row = next(r for r in c.table["rows"] if r["band"] == c.table["final_grc_floor"])
        for m in mitigations:
            if m.id not in concepts:
                continue
            level = concepts[m.id]
            credit = m.table["credit"][level]
            if credit is None:
                msg = f"{m.id} has no credit at level {level}"
                self._add("final_grc", None, result(c, cid, FAIL, str(declared), msg))
                return None
            grc += credit
            applied.append({"concept_id": m.id, "level": level, "credit": credit})
            if m.id.startswith(M1_PREFIX) and col is not None:
                grc = max(grc, floor_row["igrc"][col])
        self.summary["mitigations_applied"] = applied
        ev = f"iGRC {igrc}; credits {[a['credit'] for a in applied]}"
        return self._add("final_grc", grc, result(c, cid, PASS, ev, f"final GRC {grc}"))

    def arc(self) -> str | None:
        cid = "sora.initial_arc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["initial_arc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        facts = self.m["airspace"]
        for rule in c.table["initial_arc"]:
            match = True
            for key, want in rule["when"].items():
                if key == "airspace_class_in":
                    match = match and facts["class"] in want
                    continue
                if key not in facts:
                    msg = f"declare airspace.{key} (true or false)"
                    self._add("initial_arc", NOT_ASSESSED, result(c, cid, GAP, "", msg))
                    return None
                match = match and facts[key] == want
            if match:
                ev = f"first matching rule: {rule['when'] or 'default'}"
                return self._add(
                    "initial_arc", rule["arc"], result(c, cid, PASS, ev, f"ARC-{rule['arc']}")
                )
        return None

    def residual_arc(self, initial: str) -> str | None:
        cid = "sora.residual_arc"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["residual_arc"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        order = list(c.table["tmpr"])
        res = c.table["residual_arc"]
        arc = initial
        if self.m["operation"] in res["vlos_applies_to"]:
            lowest = order.index(res["lowest_by_vlos"])
            reduced = order.index(initial) - res["vlos_reduction_classes"]
            arc = order[max(reduced, min(lowest, order.index(initial)))]
        tmpr = (
            "none (VLOS)" if self.m["operation"] in res["vlos_applies_to"] else c.table["tmpr"][arc]
        )
        self.summary["tmpr"] = {"value": tmpr, "concept_id": c.id}
        ev = f"initial ARC-{initial}; operation {self.m['operation']}"
        return self._add("residual_arc", arc, result(c, cid, PASS, ev, f"ARC-{arc}; TMPR {tmpr}"))

    def sail(self, grc: int, arc: str) -> str | None:
        cid = "sora.sail"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["sail"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return None
        ev = f"final GRC {grc}; residual ARC-{arc}"
        row = next((r for r in c.table["rows"] if grc <= r["final_grc_max"]), None)
        if row is None:
            msg = f"final GRC above the table: {c.table['above_table']}"
            self._add("sail", None, result(c, cid, FAIL, ev, msg))
            return None
        sail = row["sail"][c.table["arc_columns"].index(arc)]
        return self._add("sail", sail, result(c, cid, PASS, ev, f"SAIL {sail}"))

    def containment(self, sail: str) -> None:
        cid = "sora.containment"
        c = governing(self.bundle, cid)
        if c is None:
            self.summary["containment"] = {"value": NOT_ASSESSED, "concept_id": None}
            self.checks.append(no_concept(cid))
            return
        ua = self.m["ua"]
        if ua["mtom_kg"] < c.table["low_below_takeoff_mass_kg"]:
            ev = f"MTOM {ua['mtom_kg']} kg"
            self._add("containment", "low", result(c, cid, PASS, ev, "low containment"))
            return
        adjacent = (self.m.get("sora") or {}).get("adjacent_area")
        if adjacent is None:
            msg = "declare sora.adjacent_area (below_people_km2, assemblies, shelter)"
            self._add("containment", NOT_ASSESSED, result(c, cid, GAP, "", msg))
            return
        table = next(
            (
                t
                for t in c.table["tables"]
                if ua["char_dimension_m"] <= t["max_dimension_m"]
                and ua["max_speed_ms"] < t["below_speed_ms"]
                and t["shelter"] == adjacent["shelter"]
            ),
            None,
        )
        if table is None:
            msg = "no containment table for this UA size, speed and shelter"
            self._add("containment", NOT_ASSESSED, result(c, cid, GAP, str(adjacent), msg))
            return
        cols = table["columns"]
        kinds = list(dict.fromkeys(k["assemblies"] for k in cols))
        if adjacent["assemblies"] not in kinds:
            msg = f"assemblies must be one of: {', '.join(kinds)}"
            self._add("containment", NOT_ASSESSED, result(c, cid, GAP, str(adjacent), msg))
            return
        density, kind = adjacent["below_people_km2"], kinds.index(adjacent["assemblies"])
        fits = [
            i
            for i, k in enumerate(cols)
            if kinds.index(k["assemblies"]) <= kind
            and (
                k["below_people_km2"] is None
                or (density is not None and density <= k["below_people_km2"])
            )
        ]
        row = next(r for r in table["rows"] if sail in r["sail"])
        ev = f"table {table['id']}; SAIL {sail}; adjacent area {adjacent}"
        level = row["robustness"][max(fits)] if fits else "out-of-scope"
        if level == "out-of-scope":
            self._add("containment", None, result(c, cid, FAIL, ev, "outside SORA"))
            return
        self._add("containment", level, result(c, cid, PASS, ev, f"{level} containment"))


def sora_summary(mission: Mission, bundle: Bundle) -> tuple[dict[str, Any], list[CheckResult]]:
    """Return the SORA summary and its results. Only a specific-category mission is scored."""
    c = governing(bundle, "sora.applicable")
    if c is None:
        return {"status": NOT_ASSESSED}, [no_concept("sora.applicable")]
    if mission["category"] != "specific":
        check = result(c, "sora.applicable", NOT_APPLICABLE, f"category {mission['category']}", "")
        return {"status": NOT_APPLICABLE}, [check]
    s = _Sora(mission, bundle)
    s.checks.append(result(c, "sora.applicable", PASS, "category specific", "SORA 2.5 applies"))
    got = s.igrc()
    grc = s.final_grc(*got) if got else s._skip("final_grc", "sora.final_grc", "sora.igrc")
    initial = s.arc()
    arc = (
        s.residual_arc(initial)
        if initial
        else s._skip("residual_arc", "sora.residual_arc", "sora.initial_arc")
    )
    if grc is not None and arc is not None:
        sail = s.sail(grc, arc)
    else:
        sail = s._skip("sail", "sora.sail", "the final GRC and the residual ARC")
    if sail is not None:
        s.containment(sail)
    else:
        s._skip("containment", "sora.containment", "sora.sail")
    s.checks.append(no_concept("sora.oso"))
    s.summary["oso"] = {"value": NOT_ASSESSED, "concept_id": None}
    return s.summary, s.checks


def score(mission: Mission, bundle: Bundle) -> dict[str, Any]:
    """Return the risk.json document."""
    rows, hazard_gaps = hazard_matrix(bundle)
    summary, checks = sora_summary(mission, bundle)
    return {
        "mission_id": mission["id"],
        "hazards": rows,
        "sora": summary,
        "checks": [r.to_dict() for r in hazard_gaps + checks],
    }


def main(argv: list[str] | None = None) -> int:
    """Write out/<id>/risk.json. Return 0, or 2 for a bad request."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
    except MissionError as e:
        print(e, file=sys.stderr)
        return 2
    out = args.out / mission["id"] / "risk.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(score(mission, load_bundle(args.knowledge)), indent=2) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Extend the `plan` target.** In `Makefile`, the `plan` recipe becomes (each
  recipe line starts with a tab):

```makefile
plan:
	$(PY) $(SCRIPTS)/gen_plan.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out
	$(PY) $(SCRIPTS)/validate_plan.py --mission $(MISSION) --knowledge knowledge --out out
	$(PY) $(SCRIPTS)/score_risk.py --mission $(MISSION) --knowledge knowledge --out out
```

- [ ] **Step 4: Verify.** `make verify`. Expected: `All checks passed!` and `250 passed`. Then
  `make plan MISSION=tests/fixtures/missions/specific.yaml`. Expected: three lines,
  `wrote out/specific/mission.plan`, `.../validation.json`, `.../risk.json`. In `risk.json`:
  iGRC 4, final GRC 3, ARC-b, TMPR low, SAIL II, containment low, and a `sora.oso` gap.
- [ ] **Step 5: Commit.** `Add score_risk and run it in the plan target`, `Closes #25`.

---

## Task 5: README for Phase 3 (#26)

**Files:** modify `README.md`. Docs only.

- [ ] **Step 1:** In the status table, set Phase 3 to `Done` and Phase 4 to `Next`. In "Quick
  start", change the `make plan` comment to `# writes mission.plan, validation.json, risk.json`.
  In "How grounding works", add: "A concept counts only if a person verified it; an unverified
  concept is a gap."
- [ ] **Step 2: Commit.** `Update the README for Phase 3 (docs only)`, `Closes #26`.

After Task 5: write the Phase 4 plan (`render_report`, `signoff.yaml`, the seeded missions m01
to m05 and `missions/SEEDED.yaml`, the decision, and the golden test). Phase 4 ends with the
owner's review of the m01 to m05 output (spec §9).
