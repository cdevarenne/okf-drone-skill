# okf-drone-skill DRN-11 Plan: Adversarial review fixes

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** fix the review findings that the spec accepts: the skill manifest, a grid with no
waypoint, geofence legs, verified concepts, the `category.operation` status, small robustness
fixes, and the ARC flags against the altitude.

**Spec:** `docs/specs/2026-10-02-drn-11-review-fixes.md`. **Backlog:** DRN-11.
**Issues:** Task N is #N+41 (#42 to #49), created on 2026-10-02.

**Provenance:** the three reproductions in spec §2.1 were run on `main` at `d687185` on
2026-10-02 with `make plan` and missions in a scratch folder (not committed). The tests in
Tasks 3, 4 and 8 encode them.

## Global constraints

- Commits on `main` as `cdevarenne`, dated in PST (`TZ=America/Los_Angeles`). Short subject in
  ASD-STE100. Body line `Closes #N`. No Co-Authored-By trailer.
- Every commit ships tests, or says that it is docs only. The test fails first.
- Before each commit: `make lint` and `uv run pytest -q`. `ruff format` only on the files of
  the task.
- A task that changes generated output runs `make examples` in the same commit, so
  `tests/test_examples.py` and `docs/data/seeded.json` stay current.
- No rule value in code. A new value goes in a concept `table`.
- **Order:** Task 1, 2, 3, 5, 4, 6, 7, 8 (spec decision 5). Task 5 comes before Task 4.

## Task 0: Tracking issues (done)

#42 to #49 exist. The backlog row is DRN-11.

## Task 1: Spec and plan (#42)

- [ ] **Step 1:** Commit the spec and this plan. Docs only.
- [ ] **Step 2:** Adversarial review of the plan (scope `plan`). Fix each finding that we
  cannot refute, in this plan, before Task 2.

```bash
git add docs/specs/2026-10-02-drn-11-review-fixes.md docs/plans/2026-10-02-drn-11-review-fixes.md
TZ=America/Los_Angeles git commit -m "Add the DRN-11 spec and plan: review fixes (docs only)" -m "Closes #42"
```

## Task 2: SKILL.md (#43)

**Files:** create `.claude/skills/drone-mission-compliance/SKILL.md`, `tests/test_skill.py`.

- [ ] **Step 1: Failing test** `tests/test_skill.py`:

```python
"""Check the skill manifest: its frontmatter, and that each make target it names exists."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "drone-mission-compliance"
TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8") if (SKILL_DIR / "SKILL.md").exists() else ""


def test_frontmatter_names_the_skill() -> None:
    _, front, _ = TEXT.split("---", 2)
    meta = yaml.safe_load(front)
    assert meta["name"] == SKILL_DIR.name
    assert meta["description"].strip()


def test_each_make_target_exists() -> None:
    targets = set(re.findall(r"^([a-z][a-z0-9-]*):", (ROOT / "Makefile").read_text(), re.M))
    named = set(re.findall(r"`make ([a-z][a-z0-9-]*)", TEXT))
    assert named and named <= targets
```

Run: `uv run pytest tests/test_skill.py -q`. Expected: fail (no file).

- [ ] **Step 2:** Write `SKILL.md` with the content of spec §3.1, in ASD-STE100: frontmatter
  (`name: drone-mission-compliance`, `description` with when to use it), "Grounding rule",
  "Workflow" (`make plan`, read the outputs, report the decision, fails and gaps; `make sitl`
  only on the owner's request), "Sign-off" (never fill approval fields; GO or NO-GO only),
  "Scope" (EU civil operations; no live data; the owner runs the paid steps).
- [ ] **Step 3:** Test passes. `make lint`, `uv run pytest -q`.
- [ ] **Step 4:** Commit `Add the skill manifest SKILL.md` / `Closes #43`.

## Task 3: Reject a grid with no waypoint (#44)

**Files:** `scripts/gen_plan.py`, `tests/test_gen_plan.py`.

- [ ] **Step 1: Failing test** in `tests/test_gen_plan.py`:

```python
def test_grid_with_no_waypoint_is_a_bad_request() -> None:
    """Review 2026-10-02: an area narrower than spacing/2 gave takeoff and RTL only, and GO."""
    mission = load_mission(MISSIONS / "survey.yaml")
    lat0, lon0 = mission["area"]["polygon"][0]
    mission["area"]["polygon"] = [
        [lat0, lon0], [lat0 + 0.00005, lon0], [lat0 + 0.00005, lon0 + 0.003], [lat0, lon0 + 0.003]
    ]
    with pytest.raises(MissionError, match="no waypoint"):
        build_plan(mission, BUNDLE, PINS)
```

Expected: fail (no error is raised).

- [ ] **Step 2:** In `pattern_points`, after the pattern is built:

```python
    if not xy:
        raise MissionError(f"the {pattern} gives no waypoint in the area; use a smaller spacing_m")
```

(`MissionError` is a `ValueError`; `main` already returns 2 for it.)

- [ ] **Step 3:** Test passes; all tests pass. Commit `Stop gen_plan when the grid has no waypoint` / `Closes #44`.

## Task 5: Verified after the last change; gen_plan uses verified concepts (#46)

Run before Task 4.

**Files:** `scripts/results.py`, `scripts/gen_plan.py`, `tests/test_results.py` (new),
`tests/test_gen_plan.py`, `tests/test_bundle_conformance.py`.

- [ ] **Step 1: Failing tests.** `tests/test_results.py`:

```python
"""Check the verified rule: a person verified the concept after its last change."""

from dataclasses import replace

from bundle_helpers import BUNDLE
from results import is_verified


def _with(generated_at: str, verified_at: str):
    c = BUNDLE.concepts["mavlink/nav-rtl"]
    fm = dict(c.frontmatter)
    fm["generated"] = {"by": "claude-code", "at": generated_at}
    fm["verified"] = [{"by": "human:owner", "at": verified_at}]
    return replace(c, frontmatter=fm)


def test_verified_after_the_change_counts() -> None:
    assert is_verified(_with("2026-10-02T10:00:00-07:00", "2026-10-02T11:00:00-07:00"))


def test_verified_before_the_change_does_not_count() -> None:
    assert not is_verified(_with("2026-10-02T10:00:00-07:00", "2026-09-28T21:00:00-07:00"))


def test_offsets_are_compared_as_times() -> None:
    assert is_verified(_with("2026-10-02T17:00:00+00:00", "2026-10-02T10:00:00-07:00"))
```

In `tests/test_gen_plan.py`:

```python
def test_unverified_concept_is_a_gap() -> None:
    mission = load_mission(MISSIONS / "survey.yaml")
    with pytest.raises(GapError, match="no verified concept mavlink/nav-takeoff"):
        build_plan(mission, unverified("mavlink/nav-takeoff"), PINS)
```

(import `unverified` from `bundle_helpers`.) In `tests/test_bundle_conformance.py`, change
`test_every_concept_is_human_verified` to `assert is_verified(concept), concept.path`.

Expected: the "before the change" test and the gen_plan test fail.

- [ ] **Step 2:** `results.is_verified`:

```python
def is_verified(concept: Concept) -> bool:
    """Return True if a person verified the concept at or after its last change (`generated.at`)."""
    changed = _time(concept.frontmatter["generated"]["at"])
    entries = concept.frontmatter.get("verified") or []
    return any(
        str(e.get("by", "")).startswith("human:") and _time(e["at"]) >= changed for e in entries
    )


def _time(value: object) -> datetime:
    return datetime.fromisoformat(str(value))
```

`gen_plan._concept_table` uses `verified_concept(bundle, concept_id)`; the message is
`gap: no verified concept {concept_id} in the bundle`.

- [ ] **Step 3:** All tests pass. If a concept in `knowledge/` now fails the conformance test,
  stop and report it to the owner (it was changed after its verification). Commit
  `Count a concept as verified only after its last change` / `Closes #46`.

## Task 4: Check each leg against the geofence (#45)

**Human gate:** the concept text changes. The owner verifies it before the commit.

**Files:** `scripts/geometry.py`, `scripts/validate_plan.py`, `knowledge/failsafes/geofence-breach.md`,
`tests/test_geometry.py`, `tests/test_validate_plan.py`, `examples/`, `docs/data/seeded.json`.

- [ ] **Step 1: Failing tests.** `tests/test_geometry.py` (uses `L_SHAPE`):

```python
@pytest.mark.parametrize(
    ("p", "q", "inside"),
    [
        ((10.0, 10.0), (40.0, 90.0), True),   # inside the vertical arm
        ((25.0, 90.0), (90.0, 25.0), False),  # cuts the notch
        ((10.0, 50.0), (90.0, 50.0), True),   # along the edge y = 50 of the notch
        ((10.0, 10.0), (50.0, 50.0), True),   # ends at the reflex vertex
        ((40.0, 60.0), (60.0, 40.0), True),   # through the reflex vertex, inside on both sides
        ((10.0, 10.0), (110.0, 10.0), False), # end outside
    ],
)
def test_segment_inside(p, q, inside) -> None:
    assert segment_inside(L_SHAPE, p, q) is inside
```

Check each expected value on the drawing of `L_SHAPE` before Step 2. In
`tests/test_validate_plan.py`:

```python
L_FENCE = [[44.798, -0.602], [44.803, -0.602], [44.803, -0.601],
           [44.799, -0.601], [44.799, -0.598], [44.798, -0.598]]


def test_leg_outside_a_concave_geofence_fails() -> None:
    """Review 2026-10-02: both points inside the L, the straight leg crosses the notch."""
    r = run(
        "inspection",
        home={"lat": 44.7985, "lon": -0.6015, "amsl_m": 50},
        geofence={"polygon": L_FENCE},
        pattern={"route": [[44.8025, -0.6015], [44.7985, -0.5985]]},
    )["plan.inside_geofence"]
    assert r["status"] == "fail" and "legs outside: 2-3" in r["evidence"]


def test_return_leg_to_home_is_checked() -> None:
    """The RTL leg from the last waypoint back to Home crosses the notch."""
    r = run(
        "inspection",
        home={"lat": 44.8025, "lon": -0.6015, "amsl_m": 50},
        geofence={"polygon": L_FENCE},
        pattern={"route": [[44.8020, -0.6015], [44.7985, -0.6015], [44.7985, -0.5985]]},
    )["plan.inside_geofence"]
    assert r["status"] == "fail" and "legs outside: 4-home" in r["evidence"]
```

(The area of the inspection fixture does not limit a corridor route. Check the `doJumpId`
numbers against the built plan in Step 1, and correct the expected leg names if they differ.)

- [ ] **Step 2:** `geometry.segment_inside(poly, p, q)` (spec §3.3): ends inside (`contains`);
  no proper crossing with an edge (`_cross` signs strictly opposite on both segments); the
  midpoint of each part between the polygon vertices on the segment is inside.
- [ ] **Step 3:** `check_inside_geofence`: build the path (position items, then Home from
  `plannedHomePosition` if the last item has no position); test the items as now, and each leg
  with `segment_inside` in the frame of the fence. Evidence:
  `f"{n} items, {k} legs; items outside: {', '.join(items) or 'none'}; legs outside: {', '.join(legs) or 'none'}"`
  (items and legs as strings).
  A leg is named `"<doJumpId>-<doJumpId>"` or `"<doJumpId>-home"`.
- [ ] **Step 4:** Concept `failsafes/geofence-breach`: new rule text (spec §3.3), and
  `generated.at` = now. The conformance test now fails for this concept (Task 5). **Stop.**
  The owner reads the concept and adds a `verified` entry.
- [ ] **Step 5:** All tests pass. `make examples`. Check with `git diff examples/` that only
  the `plan.inside_geofence` evidence changed. Commit
  `Check each flight leg against the geofence` / `Closes #45`.

## Task 6: category.operation is not applicable outside the open category (#47)

**Files:** `scripts/validate_plan.py`, `tests/test_validate_plan.py`, `examples/`,
`docs/data/seeded.json`.

- [ ] **Step 1: Failing test:**

```python
def test_category_operation_is_not_applicable_to_a_specific_mission() -> None:
    r = run(category="specific", operation="BVLOS")["category.operation"]
    assert (r["status"], r["concept_id"]) == ("not_applicable", "regulations/easa-open")
```

- [ ] **Step 2:** In `check_category_operation`, return `NOT_APPLICABLE` with the message
  "open category only".
- [ ] **Step 3:** All tests pass. `make examples`; only m05 changes. Commit
  `Give not_applicable for category.operation outside the open category` / `Closes #47`.
- [ ] **Step 4 (human gate):** the owner reads `examples/m05-specific-bvlos/report.md` and
  `validation.json`. Close #47 after the review.

## Task 7: Small robustness fixes (#48)

**Files:** `scripts/render_report.py`, `scripts/sitl_fly.py`, `scripts/mavlink_gcs.py`,
`tests/test_render_report.py`, `tests/test_mavlink_gcs.py`, `tests/test_sitl_fly.py`.

- [ ] **Step 1: Failing tests:**

```python
# test_render_report.py
def test_malformed_signoff_returns_2_and_writes_nothing(tmp_path: Path) -> None:
    folder = pipeline(tmp_path, "survey")
    (folder / "signoff.yaml").write_text("approvals: [\n")
    report = (folder / "report.md").read_text()
    assert main(args(tmp_path, "survey")) == 2
    assert (folder / "report.md").read_text() == report


# test_mavlink_gcs.py
def test_statustext_is_kept() -> None:
    gcs = _gcs_with()
    for i in range(12):
        gcs._update(_Msg("STATUSTEXT", text=f"Preflight Fail: {i}"))
    assert gcs.state["statustext"] == [f"Preflight Fail: {i}" for i in range(2, 12)]


def test_upload_refuses_a_request_outside_the_items() -> None:
    gcs = _gcs_with()
    gcs.target = (1, 1)
    gcs.conn = type("Conn", (), {"mav": type("Mav", (), {"mission_count_send": lambda *a: None})()})()
    gcs.recv = lambda types, timeout: _Msg("MISSION_REQUEST_INT", seq=5)
    with pytest.raises(GcsError, match="seq 5"):
        gcs.upload(mission_items(PLAN)[:2], MISSION_TYPE_MISSION)
```

For `px4.log`: a test in `tests/test_sitl_fly.py` that replaces `subprocess.Popen` and `fly`
with fakes and checks that the file object given as `stdout` is closed after `run` returns.
Read the current tests in that file first and reuse their fakes.

- [ ] **Step 2:** `started()` catches `yaml.YAMLError` and raises `SignoffError(f"{path}: not
  valid YAML; a person must correct it")`. `Gcs`: `state["statustext"] = []`; `_update` appends
  `msg.text` for `STATUSTEXT` and keeps the last 10; `STATUSTEXT` in `READ_MESSAGES`.
  `upload`: `if msg.seq >= len(items): raise GcsError(f"vehicle asked for seq {msg.seq} of
  {len(items)} (mission type {mission_type})")`. `sitl_fly.fly`: `SitlError(f"PX4 did not
  arm: {'; '.join(gcs.state['statustext']) or 'no message'}")`. `run`: `with
  (work / "px4.log").open("w") as log:` around `Popen` and the `try/finally`.
- [ ] **Step 3:** All tests pass. Commit `Keep the PX4 messages and close the PX4 log` /
  `Closes #48`.
- [ ] **Step 4 (human gate):** the owner runs `make sitl MISSION=missions/m01-survey-open.yaml`
  in the VM once. The result must be the same as in the DRN-10 table.

## Task 8: ARC flags agree with the altitude (#49)

**Human gate:** the concept `risk/arc` changes. The owner verifies it before the commit.

**Files:** `knowledge/risk/arc.md`, `scripts/score_risk.py`, `tests/test_score_risk.py`.

- [ ] **Step 1: Failing tests** in `tests/test_score_risk.py`:

```python
def test_above_500ft_declared_false_fails() -> None:
    """Review 2026-10-02: 180 m with above_500ft_agl false gave ARC-b and SAIL II."""
    summary, checks = sora(specific(max_altitude_agl_m=180, airspace__above_500ft_agl=False))
    assert checks["sora.initial_arc"]["status"] == "fail"
    assert "152.4" in checks["sora.initial_arc"]["message"]
    assert summary["sail"]["value"] == "not_assessed"


def test_below_500ft_declared_true_is_valid() -> None:
    summary, checks = sora(specific(max_altitude_agl_m=100, airspace__above_500ft_agl=True))
    assert checks["sora.initial_arc"]["status"] == "pass"
    assert summary["initial_arc"]["value"] == "c"
```

Check the expected ARC with the `initial_arc` table of `risk/arc` and the airspace of the
`specific` fixture before Step 2.

- [ ] **Step 2:** `risk/arc`: `table.above_500ft_agl_m: 152.4`; the "Units" text says the code
  compares `max_altitude_agl_m` with it, in one direction only (spec §3.7); `generated.at` =
  now. In `score_risk` `arc()`, before the tree:

```python
        limit = c.table["above_500ft_agl_m"]
        if self.m["max_altitude_agl_m"] > limit and facts.get("above_500ft_agl") is False:
            msg = (
                f"the mission flies above 500 ft AGL ({limit} m) but declares "
                "above_500ft_agl: false"
            )
            ev = f"max_altitude_agl_m {self.m['max_altitude_agl_m']}"
            self._add("initial_arc", NOT_ASSESSED, result(c, cid, FAIL, ev, msg))
            return None
```

Check that the later SORA steps give `not_assessed` when `arc()` returns None, as for a gap.
- [ ] **Step 3:** **Stop.** The owner reads `risk/arc` and adds a `verified` entry.
- [ ] **Step 4:** All tests pass. `make examples`: no change expected (m05 flies at 100 m).
  Commit `Fail the ARC when the 500 ft flag contradicts the altitude` / `Closes #49`.

## After Task 8

- [ ] Adversarial review of the code (scope `code`). Fix or refute each finding.
- [ ] README: "Limits (v1)" and "What's next" for the changed rules; spec status "implemented".
- [ ] Backlog: DRN-11 `done`.
