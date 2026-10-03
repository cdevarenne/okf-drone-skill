"""Check gen_plan against the fixture missions, the bundle and the .plan subset schema."""

import copy
import json
from itertools import pairwise
from pathlib import Path

import pytest
from bundle_helpers import unverified
from gen_plan import GapError, build_plan, main, read_pins
from geometry import LocalFrame, centroid, contains
from jsonschema import Draft202012Validator
from mission import MissionError, load_mission
from okf_lib import Bundle, load_bundle

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"
SCHEMA = json.loads((ROOT / "tests" / "fixtures" / "qgc" / "plan.schema.json").read_text())
BUNDLE = load_bundle(ROOT / "knowledge")
PINS = read_pins(ROOT / "tools.lock")
NAMES = ["survey", "inspection", "search"]


def plan_for(name: str, **changes) -> dict:
    mission = load_mission(MISSIONS / f"{name}.yaml")
    mission.update(changes)
    return build_plan(mission, BUNDLE, PINS)


def waypoints(plan: dict) -> list[tuple[float, float]]:
    return [(i["params"][4], i["params"][5]) for i in plan["mission"]["items"][1:-1]]


@pytest.mark.parametrize("name", NAMES)
def test_plan_validates_against_the_subset_schema(name: str) -> None:
    assert list(Draft202012Validator(SCHEMA).iter_errors(plan_for(name))) == []


@pytest.mark.parametrize("name", NAMES)
def test_plan_structure_comes_from_the_bundle(name: str) -> None:
    items = plan_for(name)["mission"]["items"]
    assert items[0]["command"] == BUNDLE.concepts["mavlink/nav-takeoff"].table["mavlink_id"]
    assert items[-1]["command"] == BUNDLE.concepts["mavlink/nav-rtl"].table["mavlink_id"]
    assert items[-1]["frame"] == BUNDLE.concepts["mavlink/nav-rtl"].table["frame"]
    waypoint = BUNDLE.concepts["mavlink/nav-waypoint"].table["mavlink_id"]
    assert all(i["command"] == waypoint for i in items[1:-1])
    assert [i["doJumpId"] for i in items] == list(range(1, len(items) + 1))


@pytest.mark.parametrize("name", NAMES)
def test_waypoints_are_inside_the_area_at_the_requested_altitude(name: str) -> None:
    mission = load_mission(MISSIONS / f"{name}.yaml")
    plan = plan_for(name)
    area = [tuple(p) for p in mission["area"]["polygon"]]
    frame = LocalFrame(centroid(area))
    area_xy = [frame.to_xy(p) for p in area]
    assert waypoints(plan)
    assert all(contains(area_xy, frame.to_xy(p)) for p in waypoints(plan))
    alts = [i["Altitude"] for i in plan["mission"]["items"][:-1]]
    assert alts == [mission["max_altitude_agl_m"]] * len(alts)
    fence = plan["geoFence"]["polygons"][0]
    assert fence["inclusion"] and fence["polygon"] == mission["geofence"]["polygon"]


@pytest.mark.parametrize("name", NAMES)
def test_plan_is_deterministic(name: str) -> None:
    assert json.dumps(plan_for(name)) == json.dumps(plan_for(name))


def test_grid_rows_are_spacing_apart() -> None:
    mission = load_mission(MISSIONS / "survey.yaml")
    frame = LocalFrame(centroid([tuple(p) for p in mission["area"]["polygon"]]))
    ys = [frame.to_xy(p)[1] for p in waypoints(plan_for("survey"))]
    rows = [ys[i] for i in range(0, len(ys), 2)]
    spacing = mission["pattern"]["spacing_m"]
    assert len(rows) > 2
    assert all(abs(b - a - spacing) < 0.05 for a, b in pairwise(rows))  # 1e-7 degree rounding


def test_corridor_flies_the_route() -> None:
    mission = load_mission(MISSIONS / "inspection.yaml")
    assert [list(p) for p in waypoints(plan_for("inspection"))] == mission["pattern"]["route"]


def test_search_starts_at_the_datum() -> None:
    mission = load_mission(MISSIONS / "search.yaml")
    assert list(waypoints(plan_for("search"))[0]) == mission["pattern"]["datum"]


def test_altitude_is_not_corrected() -> None:
    """gen_plan writes the requested altitude. validate_plan judges it (seeded m02)."""
    items = plan_for("survey", max_altitude_agl_m=150)["mission"]["items"]
    assert {i["Altitude"] for i in items[:-1]} == {150}


def test_unknown_mission_type_is_a_gap() -> None:
    with pytest.raises(GapError, match="mission-types/crop-spraying"):
        plan_for("survey", mission_type="crop-spraying")


def test_missing_command_concept_is_a_gap() -> None:
    concepts = {k: v for k, v in BUNDLE.concepts.items() if k != "mavlink/nav-rtl"}
    mission = load_mission(MISSIONS / "survey.yaml")
    with pytest.raises(GapError, match="mavlink/nav-rtl"):
        build_plan(mission, Bundle(concepts=concepts), PINS)


def test_unverified_concept_is_a_gap() -> None:
    mission = load_mission(MISSIONS / "survey.yaml")
    with pytest.raises(GapError, match="no verified concept mavlink/nav-takeoff"):
        build_plan(mission, unverified("mavlink/nav-takeoff"), PINS)


def test_pattern_input_must_match_the_mission_type() -> None:
    route = load_mission(MISSIONS / "inspection.yaml")["pattern"]
    with pytest.raises(MissionError, match="spacing_m"):
        plan_for("survey", pattern=copy.deepcopy(route))


def test_grid_with_no_waypoint_is_a_bad_request() -> None:
    """Review 2026-10-02: an area 5.5 m wide with spacing 40 m gave takeoff and RTL only, and GO."""
    narrow = [[44.7985, -0.6015], [44.79855, -0.6015], [44.79855, -0.5985], [44.7985, -0.5985]]
    with pytest.raises(MissionError, match="no waypoint"):
        plan_for("survey", area={"polygon": narrow})


def test_cli_writes_the_plan(tmp_path: Path) -> None:
    args = ["--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock")]
    code = main([*args, "--mission", str(MISSIONS / "search.yaml"), "--out", str(tmp_path)])
    assert code == 0
    written = json.loads((tmp_path / "search" / "mission.plan").read_text())
    assert written == plan_for("search")


def test_cli_returns_2_on_a_bad_request(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: bad\n", encoding="utf-8")
    args = ["--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock")]
    assert main([*args, "--mission", str(bad), "--out", str(tmp_path)]) == 2
    assert not (tmp_path / "bad").exists()
