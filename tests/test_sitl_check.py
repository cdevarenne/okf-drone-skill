"""Check sitl_check on tracks recorded in real PX4 v1.17.0 SITL flights (DRN-10)."""

import copy
import json
from pathlib import Path

import pytest
from bundle_helpers import BUNDLE, without
from mission import load_mission
from sitl_check import check_track

ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "tests" / "fixtures" / "sitl"
PARAMS = {"NAV_DLL_ACT": 2, "GF_ACTION": 3}  # RTL for lost link and geofence breach


def run(name: str, track_of: str | None = None, params=PARAMS, bundle=BUNDLE, **changes) -> dict:
    mission = load_mission(ROOT / "missions" / f"{name}.yaml")
    mission.update(changes)
    plan = json.loads((ROOT / "examples" / name / "mission.plan").read_text())
    track = json.loads((TRACKS / f"{track_of or name}.track.json").read_text())
    return {r.check_id: r.to_dict() for r in check_track(mission, plan, track, params, bundle)}


def test_m01_flight_passes_every_check() -> None:
    results = run("m01-survey-open")
    assert {r["status"] for r in results.values()} == {"pass"}
    assert results["alt.max_agl"]["concept_id"] == "regulations/easa-open"


def test_m02_flight_above_the_limit_fails() -> None:
    results = run("m02-altitude-over-limit")
    r = results["alt.max_agl"]
    assert (r["status"], r["concept_id"]) == ("fail", "regulations/easa-open")
    assert "limit 120 m" in r["evidence"]
    assert results["plan.last_item_return"]["status"] == "pass"


def test_m03_refused_mission_is_not_flown() -> None:
    """PX4 refused the m03 mission (geofence violation), so there is no flight evidence."""
    results = run("m03-outside-geofence")
    for check_id in ("alt.max_agl", "plan.inside_geofence"):
        assert (results[check_id]["status"], results[check_id]["concept_id"]) == (
            "gap",
            BUNDLE.governing(check_id).id,
        )
    assert results["plan.last_item_return"]["status"] == "fail"


def test_undeclared_failsafe_fails() -> None:
    """m04 declares no lost-link action, so no NAV_DLL_ACT value is set."""
    results = run("m04-no-lost-link", track_of="m01-survey-open", params={"GF_ACTION": 3})
    assert results["failsafe.lost_link"]["status"] == "fail"
    assert results["failsafe.geofence_breach"]["status"] == "pass"


def test_parameter_that_does_not_match_fails() -> None:
    results = run("m01-survey-open", params={"NAV_DLL_ACT": 3, "GF_ACTION": 3})
    assert results["failsafe.lost_link"]["status"] == "fail"


def test_specific_category_height_does_not_apply() -> None:
    assert run("m05-specific-bvlos", track_of="m01-survey-open")["alt.max_agl"]["status"] == (
        "not_applicable"
    )


def test_varied_terrain_is_a_gap() -> None:
    assert run("m01-survey-open", terrain="varied")["alt.max_agl"]["status"] == "gap"


def test_sample_outside_the_geofence_fails() -> None:
    moved = copy.deepcopy(json.loads((TRACKS / "m01-survey-open.track.json").read_text()))
    airborne = next(p for p in moved if p["in_air"])
    airborne["lat"] += 0.01  # about 1.1 km north, outside the fence
    mission = load_mission(ROOT / "missions" / "m01-survey-open.yaml")
    plan = json.loads((ROOT / "examples" / "m01-survey-open" / "mission.plan").read_text())
    results = {r.check_id: r for r in check_track(mission, plan, moved, PARAMS, BUNDLE)}
    assert results["plan.inside_geofence"].status == "fail"


@pytest.mark.parametrize("concept_id", ["regulations/easa-open", "failsafes/lost-link"])
def test_missing_concept_is_a_gap(concept_id: str) -> None:
    results = run("m01-survey-open", bundle=without(concept_id))
    gaps = [r for r in results.values() if r["status"] == "gap"]
    assert gaps and all(r["concept_id"] is None for r in gaps)
