"""Check the MAVLink conversions of mavlink_gcs without a vehicle (DRN-10)."""

import json
import math
from pathlib import Path

import pytest
from mavlink_gcs import (
    FENCE_VERTEX_INCLUSION,
    MISSION_STATE_COMPLETE,
    MISSION_TYPE_FENCE,
    MISSION_TYPE_MISSION,
    PX4_AUTO_MISSION,
    Gcs,
    fence_items,
    int_as_param_float,
    mission_items,
    param_float_as_int,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "examples" / "m01-survey-open" / "mission.plan").read_text())


def test_mission_items_follow_the_plan() -> None:
    items = mission_items(PLAN)
    source = PLAN["mission"]["items"]
    assert [i["seq"] for i in items] == list(range(len(source)))
    assert [i["command"] for i in items] == [s["command"] for s in source]
    assert [i["frame"] for i in items] == [s["frame"] for s in source]
    assert {i["mission_type"] for i in items} == {MISSION_TYPE_MISSION}
    first = items[0]
    assert first["x"] == round(source[0]["params"][4] * 1e7)
    assert first["y"] == round(source[0]["params"][5] * 1e7)
    assert first["z"] == source[0]["params"][6]
    assert math.isnan(first["params"][3])  # yaw null in the plan: NaN keeps the yaw mode


def test_return_item_has_no_position() -> None:
    last = mission_items(PLAN)[-1]
    assert (last["x"], last["y"], last["z"]) == (0, 0, 0.0)


def test_fence_items_are_inclusion_vertices() -> None:
    polygon = PLAN["geoFence"]["polygons"][0]["polygon"]
    items = fence_items(PLAN)
    assert len(items) == len(polygon)
    assert {i["command"] for i in items} == {FENCE_VERTEX_INCLUSION}
    assert {i["mission_type"] for i in items} == {MISSION_TYPE_FENCE}
    assert {i["params"][0] for i in items} == {float(len(polygon))}
    assert [(i["x"], i["y"]) for i in items] == [
        (round(lat * 1e7), round(lon * 1e7)) for lat, lon in polygon
    ]


@pytest.mark.parametrize("value", [0, 1, 2, 3, 5, -1, 1000000])
def test_int32_param_round_trip(value: int) -> None:
    assert param_float_as_int(int_as_param_float(value)) == value


def _gcs_with(**state) -> Gcs:
    gcs = Gcs.__new__(Gcs)  # no connection: the state logic only
    gcs.state = {"mission_seq": 0, "mission_total": 0, "mission_state": 0, "custom_mode": 0}
    gcs.state.update(state)
    return gcs


def test_progress_is_total_when_the_mission_is_complete() -> None:
    gcs = _gcs_with(mission_seq=23, mission_total=24, mission_state=MISSION_STATE_COMPLETE)
    assert gcs.progress() == (24, 24)
    assert _gcs_with(mission_seq=7, mission_total=24, mission_state=3).progress() == (7, 24)


def test_mission_mode_is_px4_auto_mission() -> None:
    assert _gcs_with(custom_mode=PX4_AUTO_MISSION).in_mission_mode()
    assert not _gcs_with(custom_mode=(4 << 16) | (5 << 24)).in_mission_mode()  # AUTO.RTL
