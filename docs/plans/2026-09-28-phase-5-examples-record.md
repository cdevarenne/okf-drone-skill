# okf-drone-skill Phase 5 Plan: examples, screenshots and the record

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** a reader can see what the skill does without running it. `examples/` holds the
generated output of m01 to m05, the README shows the knowledge graph and a plan in
QGroundControl, and "How this was built" gives the whole record: method, bugs found, sources,
units, human gates, limits and what's next. The spec records the v1 state.

**Spec:** `docs/specs/2026-09-28-okf-drone-skill-v1-design.md` §1, §9 Phase 5, §10.
**Backlog:** DRN-08.

**Provenance:** Tasks 1, 3 and 4 were run in a prototype on 2026-09-28 (Python 3.14.0rc2, uv
0.8.17, ruff 0.16.9, pytest 9.1.1), on a copy of `main` at `c273466`, and replayed on a fresh
copy. The replay gives the same `examples/` and leaves `docs/data/seeded.json` unchanged. The
two diffs below apply to `main` at `c273466`.

## Global constraints

- Commits on `main` as `cdevarenne`, dated in PST (`TZ=America/Los_Angeles`). Short subject in
  ASD-STE100. Body line `Closes #N`.
- Every commit ships tests, or says that it is docs only. The test fails first.
- `examples/` and `docs/data/seeded.json` are generated (`make examples`); never edit them by
  hand. The README cites them and does not copy their numbers.
- The screenshots are the owner's: the visualizer loads scripts from a CDN, and QGroundControl
  runs on the owner's machine.

## Decisions for the owner (before Task 0)

1. **`examples/` is committed.** `make examples` runs the seeded missions with `--out examples`,
   so it never touches `out/` (where the owner's signed files are). The five files per mission
   are committed, with empty approval fields. A test fails if they are not current.
2. **Two screenshots:** `docs/screenshots/knowledge-graph.png` (from `make render`) and
   `docs/screenshots/qgc-m01-survey-open.png` (the m01 plan in QGroundControl).
3. **The README record** (Task 4 diff): method, bugs found by prototyping, sources, units,
   human gates, "Generated, never typed", "Limits (v1)" and "What's next". It also fixes the
   doubled list marker of the "Human gates" bullet (`- - **Human gates.**`).
4. **The spec records the v1 state** (Task 3 diff): the status line, an evidence table for each
   §1 "done when" criterion, the confirmed SORA findings in §3, the phase state in §9, and the
   later owner decisions in §10 (height rule, units, failsafe fields, sign-off values).
5. **No human gate** (spec §9). The owner's screenshot task is a contribution, not a review.

## Task 0: Tracking issues (no commit)

- [ ] **Step 1:** Create one issue per task. The last issue is #32, so Task N becomes #N+32.

```
T1 (DRN-08): Generated examples of the seeded missions
T2 (DRN-08): Screenshots: knowledge graph and QGroundControl (owner)
T3 (DRN-08): Spec: the v1 state and the later decisions
T4 (DRN-08): README: examples, screenshots and the record
```

Body: `Phase 5. See docs/plans/2026-09-28-phase-5-examples-record.md, Task N.`

- [ ] **Step 2:** List the issues. Expected: #33 to #36 open.

---

## Task 1: Generated examples of the seeded missions (#33)

**Files:** create `tests/test_examples.py`, `examples/` (generated); modify `Makefile`.

- [ ] **Step 1: Write the failing test.**

`tests/test_examples.py`:

```python
"""Check that examples/ holds the current generated output of the seeded missions.

`make examples` writes examples/; nobody edits it by hand.
"""

from pathlib import Path

import pytest
import yaml
from seeded import run_all

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
MISSIONS = [e["mission"] for e in yaml.safe_load((ROOT / "missions" / "SEEDED.yaml").read_text())]
FILES = ["mission.plan", "validation.json", "risk.json", "report.md", "signoff.yaml"]


@pytest.fixture(scope="module")
def fresh(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("examples")
    run_all(ROOT / "missions" / "SEEDED.yaml", ROOT / "knowledge", ROOT / "tools.lock", out)
    return out


def test_examples_hold_every_seeded_mission() -> None:
    assert sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir()) == sorted(MISSIONS)


@pytest.mark.parametrize("mission", MISSIONS)
def test_example_files_are_current(fresh: Path, mission: str) -> None:
    assert sorted(p.name for p in (EXAMPLES / mission).iterdir()) == sorted(FILES)
    for name in FILES:
        assert (EXAMPLES / mission / name).read_text() == (fresh / mission / name).read_text(), name
```

Run `uv run pytest -q`. Expected: `6 failed, 281 passed` (`examples/` does not exist).

- [ ] **Step 2: Add the `examples` target.** In `Makefile`, add `examples` to `.PHONY`, and add
  after the `seeded` recipe (recipe lines start with a tab):

```makefile
examples:
	rm -rf examples
	$(PY) $(SCRIPTS)/seeded.py --seeded missions/SEEDED.yaml --knowledge knowledge --lock tools.lock --out examples --data docs/data/seeded.json
```

- [ ] **Step 3: Generate.** Run `make examples`. Expected: the five decision lines of
  `make seeded`, `examples/<id>/` with five files for each seeded mission, and no change to
  `docs/data/seeded.json` (`git status` shows only `examples/`, `Makefile` and the test).
- [ ] **Step 4: Verify.** `make verify`. Expected: `All checks passed!` and `287 passed`.
- [ ] **Step 5: Commit.** `Add the generated examples of the seeded missions`, `Closes #33`.

---

## Task 2: Screenshots: knowledge graph and QGroundControl (#34)

**The owner does this task.** The agent waits.

- [ ] **Step 1:** Run `make render`. Open `out/knowledge-viz.html` in a browser, arrange the
  graph, and save a PNG as `docs/screenshots/knowledge-graph.png`.
- [ ] **Step 2:** Open `examples/m01-survey-open/mission.plan` in QGroundControl (Plan view).
  Save a PNG that shows the grid, the geofence and the home position as
  `docs/screenshots/qgc-m01-survey-open.png`.
- [ ] **Step 3:** Delete `docs/screenshots/.gitkeep`. Commit (docs only) with `Closes #34`.

---

## Task 3: Spec: the v1 state and the later decisions (#35)

**Files:** modify `docs/specs/2026-09-28-okf-drone-skill-v1-design.md`. Docs only.

- [ ] **Step 1:** Apply this change (`git apply` accepts it):

```diff
--- a/docs/specs/2026-09-28-okf-drone-skill-v1-design.md
+++ b/docs/specs/2026-09-28-okf-drone-skill-v1-design.md
@@ -1,7 +1,8 @@
 # okf-drone-skill v1 — Design Spec
 
 - **Date:** 2026-09-28
-- **Status:** draft; owner decisions recorded (§10)
+- **Status:** v1 implemented; the owner reviewed the seeded missions (2026-09-28). Owner
+  decisions are in §10.
 - **Tracking:** `DevMoi/backlog.csv` DRN-01..DRN-08
 - **Template:** `cdevarenne/okf-grc-skill` (layout, bundle conventions, `okf_lib`, grounding rule, method)
 - **Sources:** `drone_flightplan_usecase.md`, `drone_sora_hazards_bundle.md`, `Comprehensive Drone Flight Plan Template.md`. Optional: `DroneControlSW.02.md`.
@@ -25,6 +26,17 @@
 5. The bundle conformance test passes, and each concept carries `verified`.
 6. `make render` writes the OKF visualizer HTML for `knowledge/`.
 
+**Evidence (2026-09-28):**
+
+| # | Evidence |
+|---|---|
+| 1 | `tests/test_render_report.py`; `make plan MISSION=missions/m01-survey-open.yaml` |
+| 2 | `tests/test_seeded.py`; [`docs/data/seeded.json`](../data/seeded.json) (generated) |
+| 3 | `tests/test_validate_plan.py`, `tests/test_score_risk.py`, `tests/test_check_ids.py` |
+| 4 | `tests/test_gen_plan.py`; `tests/test_seeded.py` (every seeded plan) |
+| 5 | `tests/test_bundle_conformance.py` (`test_every_concept_is_human_verified`) |
+| 6 | `make render` on the owner's machine (Python 3.14.7) |
+
 **Out of scope for v1:** simulation (PX4 SITL is DRN-10), live NOTAM / TFR / weather feeds,
 LLM steps (DRN-09), fleet operations, FAA Part 107, national (DGAC) additions, a flight
 controller, computer vision, ROS.
@@ -58,8 +70,8 @@
 - Containment has low, medium and high levels and is assessed earlier.
 
 Source for these three points: [EU Drone Port, SORA 2.5 summary](https://eudroneport.com/blog/sora-2-5-european-uas-operations/)
-(secondary). DRN-02 confirms them in the JARUS main body. Not yet confirmed: the status of M3 (ERP),
-the OSO count, and the SAIL table values.
+(secondary). DRN-02 confirmed them in S2 and S4 (see `docs/sources.md`): M3 (ERP) is removed
+in 2.5, there are 17 OSOs, and the SAIL table is as in `risk/sail`.
 
 ## 4. Repository layout
 
@@ -260,6 +272,9 @@
 | 4 | report + loop (DRN-07) | owner reviews m01–m05 output |
 | 5 | screenshots, README "How this was built" | — |
 
+State (2026-09-28): phases 0 to 4 are done, and their human gates passed. The plans are in
+`docs/plans/`.
+
 ## 10. Decisions (owner, 2026-09-28)
 
 1. Repo name: `okf-drone-skill`.
@@ -269,3 +284,11 @@
 4. Population density and all other SORA values: SORA 2.5 as adopted by EASA in 2025
    (ED Decision 2025/018/R). Not SORA 2.0. The owner reads the iGRC table in DRN-02 before
    the bundle uses it.
+5. Height rule: the plan altitudes are relative to home. With `terrain: flat` the check
+   compares them with the 120 m limit; with `terrain: varied` it is a gap (Phase 2).
+6. Units: metric everywhere. Where the source uses aviation units (500 ft AGL, FL600), the
+   bundle keeps them and gives the metric value next to them (Phase 3).
+7. `px4_action` and `px4_level` in the failsafe concepts; lost link covers the data link and
+   the RC link; S2 values where S2 and S4 differ (Phase 1).
+8. The sign-off `decision` is GO or NO-GO. HOLD is a proposal of the tool, not a sign-off
+   value (Phase 4).
```

- [ ] **Step 2: Verify.** `make verify`. Expected: `287 passed`.
- [ ] **Step 3: Commit.** `Record the v1 state and the later decisions in the spec (docs only)`,
  `Closes #35`.

---

## Task 4: README: examples, screenshots and the record (#36)

**Needs:** Task 2 (the README shows the two screenshots).

**Files:** modify `README.md`. Docs only.

- [ ] **Step 1:** Apply this change (`git apply` accepts it):

```diff
--- a/README.md
+++ b/README.md
@@ -20,7 +20,7 @@
 | 2 | `gen_plan`: mission request to QGroundControl `.plan` | Done |
 | 3 | `validate_plan`, `score_risk` | Done |
 | 4 | `render_report`, `signoff.yaml`, the seeded missions m01 to m05 | Done, reviewed by the owner |
-| 5 | Screenshots, "How this was built" | Planned |
+| 5 | Screenshots, examples, "How this was built" | Done |
 
 The spec is [`docs/specs/2026-09-28-okf-drone-skill-v1-design.md`](docs/specs/2026-09-28-okf-drone-skill-v1-design.md).
 
@@ -67,6 +67,19 @@
 concepts to [`docs/data/seeded.json`](docs/data/seeded.json). The golden test fails if that file
 is not current.
 
+## Examples
+
+[`examples/`](examples/) has the five output files of each seeded mission, as `make examples`
+writes them: `mission.plan`, `validation.json`, `risk.json`, `report.md` and `signoff.yaml`
+(with empty approval fields). Start with
+[`examples/m02-altitude-over-limit/report.md`](examples/m02-altitude-over-limit/report.md).
+A test fails if `examples/` is not the current output.
+
+![m01 in QGroundControl](docs/screenshots/qgc-m01-survey-open.png)
+
+*The m01 plan (`examples/m01-survey-open/mission.plan`) in QGroundControl: takeoff at home,
+the grid inside the area, return to launch, and the inclusion geofence.*
+
 ## Knowledge bundle
 
 | Folder | Content | Sources |
@@ -82,6 +95,12 @@
 Where the EASA text (S2) and the JARUS text (S4) differ, the bundle uses the EASA text. The
 differences are listed in [`docs/sources.md`](docs/sources.md).
 
+![OKF knowledge graph](docs/screenshots/knowledge-graph.png)
+
+*The bundle rendered by the OKF reference visualizer (`make render`). Each node is one concept
+file and each edge is a markdown link. It is a browsing aid; the pipeline reads the same files
+directly.*
+
 ## Quick start
 
 Needs Python 3.14 and [uv](https://docs.astral.sh/uv/).
@@ -92,25 +111,59 @@
 make render      # OKF visualizer HTML of knowledge/ in out/knowledge-viz.html
 make plan MISSION=missions/m01-survey-open.yaml  # writes the five files in out/m01-survey-open/
 make seeded      # runs m01 to m05; writes docs/data/seeded.json
+make examples    # writes examples/ and docs/data/seeded.json
 ```
 
 ## How this was built
 
-Built with an AI coding agent (Claude Code) under a written process. The record is in the repo.
+Built with an AI coding agent (Claude Code) under a written process. The record is in the repo:
+the spec, one plan per phase, and one tracking issue and one commit per task.
 
 - **Spec, then plan, then tasks.** The spec is in [`docs/specs/`](docs/specs/). Each phase has
   a plan in [`docs/plans/`](docs/plans/) with the complete code and the expected test output.
-  Each task has a tracking issue and one commit. The test fails first.
-- **Plans are prototyped first.** The Phase 1 loader, tests and SORA tables were run in a
-  scratch copy before they went into the plan. Executing the plan still found one plan error (a
-  folder index cut one line short); it was fixed in the plan and in the bundle.
+  The owner approved each plan before its first task. Each task has a tracking issue and one
+  commit. The test fails first.
+- **Plans are prototyped first.** The code of each plan was run in a scratch copy, then the
+  tasks were replayed in order on a fresh copy of `main`. The expected outputs in the plans
+  come from that replay.
+- **Bugs found before they reached `main`.** Prototyping found: a traceback for a missing
+  mission file (Phase 2); a lost second line in wrapped hazard mitigations (Phase 3); a GO
+  decision when no check ran, now HOLD (Phase 4). Executing the plans found one plan error: a
+  folder index cut one line short (Phase 1), fixed in the plan and in the bundle.
 - **Sources before values.** No regulatory value was written from memory. Each one was read in
   a source document that the owner had read and marked `read`. The local copies are checked by
   SHA-256. Reading the source corrected one assumption (the 120 m limit is Article 4(1)(e) of
-  Reg. (EU) 2019/947, not 4(1)(d)).
-- - **Human gates.** The owner read the sources (Phase 0), verified every concept (Phase 1), and
-  reviewed the reports of the seeded missions m01 to m05 (Phase 4) before the next phase. The
-  tool only proposes a decision; in the Phase 4 review, the owner filled `signoff.yaml` by hand.
+  Reg. (EU) 2019/947, not 4(1)(d)). When a source site blocked automated download, the owner
+  supplied the document.
+- **Units.** All inputs and outputs are metric. Where the source uses aviation units (500 ft
+  AGL, FL600), the bundle keeps them and gives the metric value next to them.
+- **Human gates.** The owner read the sources (Phase 0), verified every concept (Phase 1), and
+  reviewed the reports of the seeded missions m01 to m05 (Phase 4) before the next phase. A
+  concept that changed after its review was verified again (`risk/arc`, units). The owner
+  loaded a generated plan in QGroundControl (Phase 2). The tool only proposes a decision; in
+  the Phase 4 review, the owner filled `signoff.yaml` by hand.
+- **Generated, never typed.** `docs/data/seeded.json` and `examples/` are written by `make`;
+  tests fail if they are not current.
+
+## Limits (v1)
+
+- Airspace, NOTAM, TFR, weather and terrain are declared inputs. There is no live data.
+- The height check runs only on flat terrain; with varied terrain it is a gap.
+- The SORA OSO table is not in the bundle, so every specific-category mission is HOLD.
+- The SORA mitigation levels and the adjacent-area limits are the operator's claims; the Annex
+  B and Annex E criteria are not checked. The contingency volume and the ground risk buffer are
+  not modelled.
+- Multicopters only; convex areas; three patterns (grid, corridor, expanding square);
+  `SimpleItem` mission items only.
+- EU rules only: no FAA Part 107, no national additions (for example DGAC).
+- No simulation and no LLM step.
+
+## What's next
+
+- DRN-09: optional LLM steps that the owner runs, outside `make plan`.
+- DRN-10: fly the generated plans in PX4 SITL.
+- The OSO table (S2 Table 14) and its checks, so that a specific-category mission can be GO.
+- Terrain data, so that the height check can run on varied terrain.
 
 ## Pins
 
@@ -129,6 +182,8 @@
 docs/specs/, docs/plans/      spec and phase plans
 docs/sources.md               source register
 docs/data/                    generated results (make seeded)
+examples/                     generated output of m01 to m05 (make examples)
+docs/screenshots/             README images
 ```
 
 ## License
```

- [ ] **Step 2: Verify.** `make verify`. Expected: `287 passed`. Check that the two images
  show on the GitHub page of the repo.
- [ ] **Step 3: Commit.** `Add the examples, the screenshots and the record to the README (docs only)`,
  `Closes #36`.

After Task 4, v1 is complete (DRN-01 to DRN-08). The next items are in the README, "What's
next".
