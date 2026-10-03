"""A small MAVLink ground station for PX4 SITL, on pymavlink (DRN-10).

It does only what sitl_fly needs: heartbeats, parameters, mission and geofence upload,
arm, mission start, and telemetry. It is single-threaded: every wait loop sends the GCS
heartbeat and reads the messages. The plan conversion functions do not need a connection.
"""

from __future__ import annotations

import math
import struct
import time
from typing import Any

# MAVLink values (S9, MAVLink common message set).
MISSION_TYPE_MISSION, MISSION_TYPE_FENCE = 0, 1
FENCE_VERTEX_INCLUSION = 5001  # MAV_CMD_NAV_FENCE_POLYGON_VERTEX_INCLUSION
FRAME_GLOBAL = 0  # MAV_FRAME_GLOBAL
PARAM_TYPE_INT32 = 6  # MAV_PARAM_TYPE_INT32
CMD_ARM_DISARM = 400  # MAV_CMD_COMPONENT_ARM_DISARM
CMD_MISSION_START = 300  # MAV_CMD_MISSION_START
CMD_SET_MESSAGE_INTERVAL = 511  # MAV_CMD_SET_MESSAGE_INTERVAL
RESULT_ACCEPTED = 0  # MAV_RESULT_ACCEPTED
MISSION_ACCEPTED = 0  # MAV_MISSION_ACCEPTED
ARMED_FLAG = 128  # MAV_MODE_FLAG_SAFETY_ARMED
IN_AIR_STATES = {2, 3, 4}  # MAV_LANDED_STATE_IN_AIR, _TAKEOFF, _LANDING
MISSION_STATE_COMPLETE = 5  # MISSION_STATE_COMPLETE
GCS_TYPE, AUTOPILOT_INVALID = 6, 8  # MAV_TYPE_GCS, MAV_AUTOPILOT_INVALID
# PX4 sends these at up to 50 Hz of simulator time; at speed 10 that is about 3,600 messages
# per second. A slow computer then reads the mission requests too late, and PX4 stops the upload
# ("Operation timeout"). quiet() stops these streams; the tool does not read them.
QUIET_MESSAGES = {
    "GPS_RAW_INT": 24, "ATTITUDE": 30, "ATTITUDE_QUATERNION": 31, "LOCAL_POSITION_NED": 32,
    "SERVO_OUTPUT_RAW": 36, "VFR_HUD": 74, "ATTITUDE_TARGET": 83,
    "POSITION_TARGET_LOCAL_NED": 85,
}  # fmt: skip
READ_MESSAGES = {
    "HEARTBEAT", "GLOBAL_POSITION_INT", "EXTENDED_SYS_STATE", "MISSION_CURRENT", "STATUSTEXT"
}  # fmt: skip
STATUSTEXT_KEEP = 10  # the last PX4 texts, for example the reason for an arm refusal
POSITION_MSG_ID = 33  # GLOBAL_POSITION_INT
POSITION_INTERVAL_US = 100_000  # 10 Hz of simulator time; the track samples at 0.2 s wall time
UPLOAD_RESEND_S = 2.0  # send MISSION_COUNT again after this many seconds with no request
# PX4 custom mode: main mode in bits 16-23, sub mode in bits 24-31 (PX4 commander).
PX4_AUTO_MISSION = (4 << 16) | (4 << 24)


class GcsError(RuntimeError):
    """The vehicle did not answer, or it refused a request."""


def _scaled(deg: float) -> int:
    return round(deg * 1e7)


def mission_items(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the MISSION_ITEM_INT fields for the plan's mission items, in order."""
    items = []
    for seq, item in enumerate(plan["mission"]["items"]):
        p = [math.nan if v is None else float(v) for v in item["params"]]
        positioned = "Altitude" in item
        items.append(
            {
                "seq": seq,
                "frame": item["frame"],
                "command": item["command"],
                "autocontinue": int(item["autoContinue"]),
                "params": p[:4],
                "x": _scaled(p[4]) if positioned else 0,
                "y": _scaled(p[5]) if positioned else 0,
                "z": p[6] if positioned else 0.0,
                "mission_type": MISSION_TYPE_MISSION,
            }
        )
    return items


def fence_items(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the MISSION_ITEM_INT fields for the plan's inclusion polygons."""
    items: list[dict[str, Any]] = []
    for fence in plan["geoFence"]["polygons"]:
        if not fence["inclusion"]:
            continue
        for lat, lon in fence["polygon"]:
            items.append(
                {
                    "seq": len(items),
                    "frame": FRAME_GLOBAL,
                    "command": FENCE_VERTEX_INCLUSION,
                    "autocontinue": 0,
                    "params": [float(len(fence["polygon"])), 0.0, 0.0, 0.0],
                    "x": _scaled(lat),
                    "y": _scaled(lon),
                    "z": 0.0,
                    "mission_type": MISSION_TYPE_FENCE,
                }
            )
    return items


def int_as_param_float(value: int) -> float:
    """Return the float that carries an INT32 parameter byte by byte (PX4 encoding)."""
    return struct.unpack("<f", struct.pack("<i", value))[0]


def param_float_as_int(value: float) -> int:
    """Return the INT32 parameter value carried byte by byte in a float."""
    return struct.unpack("<i", struct.pack("<f", value))[0]


class Gcs:
    """A MAVLink ground station on one UDP link to one PX4 vehicle (system 1, component 1)."""

    def __init__(self, url: str) -> None:
        from pymavlink import mavutil

        self.conn = mavutil.mavlink_connection(url, source_system=255, source_component=190)
        self.target = (1, 1)
        self.state: dict[str, Any] = {
            "lat": None, "lon": None, "rel_alt_m": None, "armed": False, "landed_state": 0,
            "custom_mode": 0, "mission_seq": 0, "mission_total": 0, "mission_state": 0,
            "statustext": [],
        }  # fmt: skip
        self._last_heartbeat = 0.0

    def _tick(self) -> None:
        now = time.time()
        if now - self._last_heartbeat >= 1.0:
            self.conn.mav.heartbeat_send(GCS_TYPE, AUTOPILOT_INVALID, 0, 0, 0)
            self._last_heartbeat = now

    def _update(self, msg: Any) -> None:
        kind = msg.get_type()
        s = self.state
        if kind == "HEARTBEAT" and msg.get_srcSystem() == 1 and msg.get_srcComponent() == 1:
            s["armed"] = bool(msg.base_mode & ARMED_FLAG)
            s["custom_mode"] = msg.custom_mode
        elif kind == "GLOBAL_POSITION_INT":
            s["lat"], s["lon"] = msg.lat / 1e7, msg.lon / 1e7
            s["rel_alt_m"] = msg.relative_alt / 1000
        elif kind == "EXTENDED_SYS_STATE":
            s["landed_state"] = msg.landed_state
        elif kind == "MISSION_CURRENT":
            s["mission_seq"], s["mission_total"] = msg.seq, getattr(msg, "total", 0)
            s["mission_state"] = getattr(msg, "mission_state", 0)
        elif kind == "STATUSTEXT":
            s["statustext"] = [*s["statustext"], msg.text][-STATUSTEXT_KEEP:]

    def recv(self, types: set[str] | None = None, timeout: float = 1.0) -> Any:
        """Return the next message of one of `types` (any if None), or None after `timeout`."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._tick()
            msg = self.conn.recv_match(blocking=True, timeout=0.1)
            if msg is None or msg.get_type() == "BAD_DATA":
                continue
            self._update(msg)
            if types is None or msg.get_type() in types:
                return msg
        return None

    def pump(self, seconds: float) -> None:
        """Read messages for `seconds`, keeping the state current."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            self.recv(None, deadline - time.time())

    def wait_position(self, timeout: float) -> None:
        """Wait for a heartbeat and a global position from the vehicle."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.recv(None, 0.5)
            if self.state["lat"] is not None and self.state["lat"] != 0:
                return
        raise GcsError("no global position from the vehicle")

    def quiet(self) -> None:
        """Stop the high-rate streams that the tool does not read, and slow the position."""
        for msg_id in QUIET_MESSAGES.values():
            self.command(CMD_SET_MESSAGE_INTERVAL, msg_id, -1)
        self.command(CMD_SET_MESSAGE_INTERVAL, POSITION_MSG_ID, POSITION_INTERVAL_US)

    def set_param_int(self, name: str, value: int) -> int | None:
        """Set an INT32 parameter and return the value that the vehicle reports back."""
        for _ in range(5):
            self.conn.mav.param_set_send(
                *self.target, name.encode(), int_as_param_float(value), PARAM_TYPE_INT32
            )
            deadline = time.time() + 2
            while time.time() < deadline:
                msg = self.recv({"PARAM_VALUE"}, deadline - time.time())
                if msg is not None and msg.param_id == name:
                    return param_float_as_int(msg.param_value)
        return None

    def upload(self, items: list[dict[str, Any]], mission_type: int) -> None:
        """Upload mission or fence items with the MAVLink mission protocol.

        If the vehicle sends no request for UPLOAD_RESEND_S, send MISSION_COUNT again: PX4 then
        starts the transfer again.
        """
        deadline, last = time.time() + 30, 0.0
        while time.time() < deadline:
            if time.time() - last >= UPLOAD_RESEND_S:
                self.conn.mav.mission_count_send(*self.target, len(items), mission_type)
                last = time.time()
            msg = self.recv({"MISSION_REQUEST_INT", "MISSION_REQUEST", "MISSION_ACK"}, 0.5)
            if msg is None or getattr(msg, "mission_type", mission_type) != mission_type:
                continue
            last = time.time()
            if msg.get_type() == "MISSION_ACK":
                if msg.type != MISSION_ACCEPTED:
                    raise GcsError(
                        f"upload refused (mission type {mission_type}, result {msg.type})"
                    )
                return
            if msg.seq >= len(items):
                raise GcsError(
                    f"vehicle asked for seq {msg.seq} of {len(items)} (mission type {mission_type})"
                )
            it = items[msg.seq]
            self.conn.mav.mission_item_int_send(
                *self.target, it["seq"], it["frame"], it["command"], 0, it["autocontinue"],
                *it["params"], it["x"], it["y"], it["z"], mission_type,
            )  # fmt: skip
        raise GcsError(f"upload timed out (mission type {mission_type})")

    def command(self, command: int, *params: float) -> int | None:
        """Send COMMAND_LONG and return the result of its COMMAND_ACK, or None."""
        p = list(params) + [0.0] * (7 - len(params))
        self.conn.mav.command_long_send(*self.target, command, 0, *p)
        deadline = time.time() + 2
        while time.time() < deadline:
            msg = self.recv({"COMMAND_ACK"}, deadline - time.time())
            if msg is not None and msg.command == command:
                return msg.result
        return None

    def in_air(self) -> bool:
        return self.state["landed_state"] in IN_AIR_STATES

    def in_mission_mode(self) -> bool:
        return self.state["custom_mode"] == PX4_AUTO_MISSION

    def progress(self) -> tuple[int, int]:
        """Return (done, total). `done` equals `total` when the mission is complete."""
        s = self.state
        done = (
            s["mission_total"] if s["mission_state"] == MISSION_STATE_COMPLETE else s["mission_seq"]
        )
        return done, s["mission_total"]

    def close(self) -> None:
        self.conn.close()
