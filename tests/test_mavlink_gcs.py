"""Check the MAVLink conversions of mavlink_gcs without a vehicle (DRN-10)."""

import json
import math
import time
from pathlib import Path

import mavlink_gcs
import pytest
from mavlink_gcs import (
    CMD_SET_MESSAGE_INTERVAL,
    FENCE_VERTEX_INCLUSION,
    MISSION_STATE_COMPLETE,
    MISSION_TYPE_FENCE,
    MISSION_TYPE_MISSION,
    POSITION_INTERVAL_US,
    POSITION_MSG_ID,
    PX4_AUTO_MISSION,
    QUIET_MESSAGES,
    READ_MESSAGES,
    RESULT_ACCEPTED,
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


def test_quiet_messages_are_not_read() -> None:
    assert not set(QUIET_MESSAGES) & READ_MESSAGES


def test_message_ids_match_pymavlink() -> None:
    mavlink = pytest.importorskip("pymavlink.dialects.v20.common")
    for name, msg_id in {**QUIET_MESSAGES, "GLOBAL_POSITION_INT": POSITION_MSG_ID}.items():
        assert getattr(mavlink, f"MAVLINK_MSG_ID_{name}") == msg_id


def test_quiet_stops_the_unread_streams_and_slows_the_position() -> None:
    gcs, sent = _gcs_with(), []
    gcs.command = lambda cmd, *params: sent.append((cmd, *params)) or RESULT_ACCEPTED
    gcs.quiet()
    assert sent == [(CMD_SET_MESSAGE_INTERVAL, i, -1) for i in QUIET_MESSAGES.values()] + [
        (CMD_SET_MESSAGE_INTERVAL, POSITION_MSG_ID, POSITION_INTERVAL_US)
    ]


class _Msg:
    def __init__(self, kind: str, **fields) -> None:
        self.kind, self.mission_type = kind, MISSION_TYPE_MISSION
        self.__dict__.update(fields)

    def get_type(self) -> str:
        return self.kind


def test_upload_sends_the_count_again_when_the_vehicle_does_not_answer(monkeypatch) -> None:
    """PX4 drops a transfer after its timeout; a new MISSION_COUNT starts it again."""
    monkeypatch.setattr(mavlink_gcs, "UPLOAD_RESEND_S", 0.05)
    items = mission_items(PLAN)[:2]
    counts, sent = [], []
    replies = [_Msg("MISSION_REQUEST_INT", seq=0), _Msg("MISSION_REQUEST_INT", seq=1)]
    replies.append(_Msg("MISSION_ACK", type=0))

    class Mav:
        def mission_count_send(self, *args) -> None:
            counts.append(args)

        def mission_item_int_send(self, *args) -> None:
            sent.append(args[2])

    def recv(types, timeout):
        if len(counts) < 2:  # the first MISSION_COUNT is lost
            time.sleep(0.01)
            return None
        return replies.pop(0)

    gcs = _gcs_with()
    gcs.target, gcs.conn, gcs.recv = (1, 1), type("Conn", (), {"mav": Mav()})(), recv
    gcs.upload(items, MISSION_TYPE_MISSION)
    assert len(counts) == 2 and sent == [0, 1]
