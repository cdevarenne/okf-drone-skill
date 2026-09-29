"""Check a track flown in PX4 SITL against the plan and the bundle (DRN-10).

The checks reuse the v1 check ids: the flight is new evidence for the same rules, from the same
verified concepts. A track point is a dict with t_s, lat, lon, rel_alt_m, armed, in_air,
mission_seq and mission_total.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from geometry import LocalFrame, centroid, contains
from okf_lib import Bundle
from results import FAIL, GAP, NOT_APPLICABLE, PASS, CheckResult, governing, no_concept, result

Track = Sequence[dict[str, Any]]


def _airborne(track: Track) -> list[dict[str, Any]]:
    return [p for p in track if p["in_air"]]


def _flown_alt(m: dict, track: Track, bundle: Bundle) -> CheckResult:
    cid = "alt.max_agl"
    c = governing(bundle, cid)
    if c is None:
        return no_concept(cid)
    if m["category"] != "open":
        return result(c, cid, NOT_APPLICABLE, f"category {m['category']}", "open category only")
    if m["terrain"] != "flat":
        return result(c, cid, GAP, f"terrain {m['terrain']}", "v1 has no terrain data")
    air = _airborne(track)
    if not air:
        return result(c, cid, GAP, "no airborne track point", "not flown: no flight evidence")
    limit = c.table["max_height_above_surface_m"]
    highest = max(p["rel_alt_m"] for p in air)
    ev = f"flown maximum {highest:.1f} m above home; limit {limit} m"
    if highest > limit:
        return result(c, cid, FAIL, ev, f"the vehicle flew above {limit} m")
    return result(c, cid, PASS, ev, "the flight stayed within the height limit")


def _flown_fence(plan: dict, track: Track, bundle: Bundle) -> CheckResult:
    cid = "plan.inside_geofence"
    c = governing(bundle, cid)
    if c is None:
        return no_concept(cid)
    fences = [
        [tuple(p) for p in f["polygon"]] for f in plan["geoFence"]["polygons"] if f["inclusion"]
    ]
    air = _airborne(track)
    if not fences:
        return result(c, cid, FAIL, "no inclusion polygon", "the plan has no geofence")
    if not air:
        return result(c, cid, GAP, "no airborne track point", "not flown: no flight evidence")
    frames = [LocalFrame(centroid(f)) for f in fences]
    polys = [[fr.to_xy(q) for q in f] for fr, f in zip(frames, fences, strict=True)]
    outside = [
        p["t_s"]
        for p in air
        if not any(
            contains(poly, fr.to_xy((p["lat"], p["lon"])))
            for fr, poly in zip(frames, polys, strict=True)
        )
    ]
    ev = f"{len(air)} airborne points; outside: {len(outside)}"
    if outside:
        return result(c, cid, FAIL, ev, f"the vehicle left the geofence at t = {outside[0]:.1f} s")
    return result(c, cid, PASS, ev, "the whole flight stayed inside the geofence")


def _flown_return(track: Track, bundle: Bundle) -> CheckResult:
    cid = "plan.last_item_return"
    c = governing(bundle, cid)
    if c is None:
        return no_concept(cid)
    total = max((p["mission_total"] for p in track), default=0)
    done = max((p["mission_seq"] for p in track), default=0)  # equals the total when the mission is complete
    last = track[-1] if track else None
    landed = last is not None and not last["in_air"] and not last["armed"]
    ev = f"mission progress {done} of {total}; landed and disarmed: {landed}"
    if total == 0 or done < total or not landed:
        return result(c, cid, FAIL, ev, "the mission did not finish with the vehicle on the ground")
    return result(c, cid, PASS, ev, "the mission finished and the vehicle landed")


def _failsafe_params(m: dict, params: dict[str, float], bundle: Bundle) -> list[CheckResult]:
    out = []
    for cid in ("failsafe.lost_link", "failsafe.geofence_breach"):
        c = governing(bundle, cid)
        if c is None:
            out.append(no_concept(cid))
            continue
        mapping = c.table["px4_action"]
        param, declared = mapping["param"], m["failsafes"].get(c.table["mission_key"])
        want = mapping["values"].get(declared)
        got = params.get(param)
        ev = f"{param}: set {want}, read back {got}"
        if want is None or got is None or int(got) != want:
            out.append(result(c, cid, FAIL, ev, f"{param} does not match the declared {declared}"))
        else:
            out.append(result(c, cid, PASS, ev, f"PX4 {param} = {want} ({declared})"))
    return out


def check_track(
    mission: dict, plan: dict, track: Track, params: dict[str, float], bundle: Bundle
) -> list[CheckResult]:
    """Return the SITL results, in the order of the v1 checks."""
    return [
        _flown_alt(mission, track, bundle),
        _flown_fence(plan, track, bundle),
        _flown_return(track, bundle),
        *_failsafe_params(mission, params, bundle),
    ]
