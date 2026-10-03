"""Generate a QGroundControl .plan from a mission request and the bundle (spec §6, step 2).

gen_plan writes what the mission request asks for. It does not correct a request that breaks a
rule (for example an altitude above a limit): validate_plan finds that and cites the concept.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from geometry import LocalFrame, centroid, expanding_square, grid
from mission import MissionError, load_mission
from okf_lib import Bundle, load_bundle

# MAVLink enums for the .plan header (S9): MAV_AUTOPILOT_PX4 and MAV_TYPE_QUADROTOR.
FIRMWARE_PX4 = 12
VEHICLE_QUADROTOR = 2
ALTITUDE_MODE_RELATIVE = 1  # QGC: altitudes relative to the home position
FENCE_POLYGON_VERSION = 1  # S8 example; the subset schema accepts 1 and 2
DECIMALS = 7  # 1e-7 degree, the MAVLink integer scale


class GapError(LookupError):
    """The bundle has no concept for something that the plan needs (a coverage gap)."""


def read_pins(lock: Path) -> dict[str, str]:
    """Return the KEY=VALUE pairs in tools.lock."""
    pairs = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            pairs[key] = value
    return pairs


def _concept_table(bundle: Bundle, concept_id: str) -> dict[str, Any]:
    concept = bundle.concepts.get(concept_id)
    if concept is None:
        raise GapError(f"gap: no concept {concept_id} in the bundle")
    return dict(concept.table)


def _latlon(p: tuple[float, float]) -> list[float]:
    return [round(p[0], DECIMALS), round(p[1], DECIMALS)]


def pattern_points(mission: dict[str, Any], pattern: str) -> list[tuple[float, float]]:
    """Return the pattern waypoints as (lat, lon) for the pattern that the bundle names."""
    area = [tuple(p) for p in mission["area"]["polygon"]]
    spec = mission["pattern"]
    if pattern == "corridor":
        if "route" not in spec:
            raise MissionError("the corridor pattern needs pattern.route")
        return [tuple(p) for p in spec["route"]]
    if "spacing_m" not in spec:
        raise MissionError(f"the {pattern} pattern needs pattern.spacing_m")
    frame = LocalFrame(centroid(area))
    area_xy = [frame.to_xy(p) for p in area]
    if pattern == "grid":
        xy = grid(area_xy, spec["spacing_m"])
    elif pattern == "expanding-square":
        if "datum" not in spec:
            raise MissionError("the expanding-square pattern needs pattern.datum")
        xy = expanding_square(area_xy, frame.to_xy(tuple(spec["datum"])), spec["spacing_m"])
    else:
        raise GapError(f"gap: gen_plan has no generator for pattern {pattern!r}")
    if not xy:
        raise MissionError(f"the {pattern} gives no waypoint in the area; use a smaller spacing_m")
    return [frame.to_latlon(q) for q in xy]


def _position_item(cmd: dict[str, Any], seq: int, p: tuple[float, float], alt: float) -> dict:
    lat, lon = _latlon(p)
    return {
        "type": "SimpleItem",
        "command": cmd["mavlink_id"],
        "frame": cmd["frame"],
        "params": [0, 0, 0, None, lat, lon, alt],
        "autoContinue": True,
        "doJumpId": seq,
        "Altitude": alt,
        "AltitudeMode": ALTITUDE_MODE_RELATIVE,
        "AMSLAltAboveTerrain": None,
    }


def build_plan(mission: dict[str, Any], bundle: Bundle, pins: dict[str, str]) -> dict[str, Any]:
    """Return the .plan document for a mission request."""
    mission_type = _concept_table(bundle, f"mission-types/{mission['mission_type']}")
    takeoff = _concept_table(bundle, "mavlink/nav-takeoff")
    waypoint = _concept_table(bundle, "mavlink/nav-waypoint")
    rtl = _concept_table(bundle, "mavlink/nav-rtl")
    home = (mission["home"]["lat"], mission["home"]["lon"])
    alt = mission["max_altitude_agl_m"]

    items = [_position_item(takeoff, 1, home, alt)]
    for p in pattern_points(mission, mission_type["pattern"]):
        items.append(_position_item(waypoint, len(items) + 1, p, alt))
    items.append(
        {
            "type": "SimpleItem",
            "command": rtl["mavlink_id"],
            "frame": rtl["frame"],
            "params": [0, 0, 0, 0, 0, 0, 0],
            "autoContinue": True,
            "doJumpId": len(items) + 1,
        }
    )
    return {
        "fileType": "Plan",
        "version": int(pins["QGC_PLAN_VERSION"]),
        "groundStation": "okf-drone-skill",
        "mission": {
            "version": int(pins["QGC_MISSION_VERSION"]),
            "firmwareType": FIRMWARE_PX4,
            "globalPlanAltitudeMode": ALTITUDE_MODE_RELATIVE,
            "vehicleType": VEHICLE_QUADROTOR,
            "cruiseSpeed": mission["speed_ms"],
            "hoverSpeed": mission["speed_ms"],
            "plannedHomePosition": [*_latlon(home), mission["home"]["amsl_m"]],
            "items": items,
        },
        "geoFence": {
            "version": int(pins["QGC_GEOFENCE_VERSION"]),
            "circles": [],
            "polygons": [
                {
                    "inclusion": True,
                    "version": FENCE_POLYGON_VERSION,
                    "polygon": [_latlon(tuple(p)) for p in mission["geofence"]["polygon"]],
                }
            ],
        },
        "rallyPoints": {"version": int(pins["QGC_RALLY_VERSION"]), "points": []},
    }


def main(argv: list[str] | None = None) -> int:
    """Write out/<id>/mission.plan. Return 0, or 2 for a coverage gap or a bad request."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
        plan = build_plan(mission, load_bundle(args.knowledge), read_pins(args.lock))
    except (GapError, ValueError) as e:
        print(e, file=sys.stderr)
        return 2
    out = args.out / mission["id"] / "mission.plan"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
