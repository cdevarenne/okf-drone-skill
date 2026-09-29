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
