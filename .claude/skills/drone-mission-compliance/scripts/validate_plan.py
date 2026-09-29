"""Validate a .plan and its mission request against the bundle (spec §6, step 3).

Each check reads its rule from the one verified concept that governs its check id. A check with
no verified concept is a gap. validate_plan writes out/<id>/validation.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from geometry import LocalFrame, centroid, contains
from mission import MissionError, load_mission
from okf_lib import Bundle, Concept, load_bundle
from results import (
    FAIL,
    GAP,
    NOT_APPLICABLE,
    PASS,
    CheckResult,
    governing,
    no_concept,
    result,
    verified_concept,
)

Mission = dict[str, Any]
Plan = dict[str, Any]


def position_items(plan: Plan) -> list[dict[str, Any]]:
    """Return the mission items that have a position (QGC writes `Altitude` for them)."""
    return [i for i in plan["mission"]["items"] if "Altitude" in i]


def check_alt_max_agl(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "alt.max_agl"
    if m["category"] != "open":
        return result(c, cid, NOT_APPLICABLE, f"category {m['category']}", "open category only")
    if m["terrain"] != "flat":
        return result(
            c,
            cid,
            GAP,
            f"terrain {m['terrain']}",
            "the plan altitudes are relative to home; v1 has no terrain data",
        )
    limit = c.table["max_height_above_surface_m"]
    highest = max(i["Altitude"] for i in position_items(plan))
    evidence = f"highest item {highest} m above home; terrain flat; limit {limit} m"
    if highest > limit:
        return result(c, cid, FAIL, evidence, f"the plan flies above {limit} m")
    return result(c, cid, PASS, evidence, "the plan stays within the height limit")


def check_category_operation(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "category.operation"
    if m["category"] != "open":
        return result(c, cid, PASS, f"category {m['category']}", "no open-category condition")
    allowed, below = c.table["operations"], c.table["below_takeoff_mass_kg"]
    evidence = f"operation {m['operation']}; MTOM {m['ua']['mtom_kg']} kg"
    problems = []
    if m["operation"] not in allowed:
        problems.append(f"the open category allows only {', '.join(allowed)}")
    if not m["ua"]["mtom_kg"] < below:
        problems.append(f"the open category needs an MTOM below {below} kg")
    if problems:
        return result(c, cid, FAIL, evidence, "; ".join(problems))
    return result(c, cid, PASS, evidence, "the operation meets the open-category conditions")


def check_first_item_takeoff(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "plan.first_item_takeoff"
    first = plan["mission"]["items"][0]["command"]
    evidence = f"first item command {first}"
    if first != c.table["mavlink_id"]:
        return result(c, cid, FAIL, evidence, f"the first item is not {c.table['name']}")
    return result(c, cid, PASS, evidence, "the plan starts with a takeoff")


def check_last_item_return(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "plan.last_item_return"
    allowed = {c.table["mavlink_id"]}
    land = verified_concept(bundle, "mavlink/nav-land")
    if land is not None:
        allowed.add(land.table["mavlink_id"])
    last = plan["mission"]["items"][-1]["command"]
    evidence = f"last item command {last}; allowed {sorted(allowed)}"
    if last not in allowed:
        return result(c, cid, FAIL, evidence, "the plan does not end with RTL or LAND")
    return result(c, cid, PASS, evidence, "the plan ends with RTL or LAND")


def check_inside_geofence(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    cid = "plan.inside_geofence"
    fences = [
        [tuple(p) for p in f["polygon"]] for f in plan["geoFence"]["polygons"] if f["inclusion"]
    ]
    if not fences:
        return result(c, cid, FAIL, "no inclusion polygon", "the plan has no geofence")
    outside = []
    for item in position_items(plan):
        p = (item["params"][4], item["params"][5])
        if not any(_inside(fence, p) for fence in fences):
            outside.append(item["doJumpId"])
    evidence = f"{len(position_items(plan))} items; outside: {outside or 'none'}"
    if outside:
        return result(c, cid, FAIL, evidence, f"items {outside} are outside the geofence")
    return result(c, cid, PASS, evidence, "every item is inside the geofence")


def _inside(fence: list[tuple[float, float]], p: tuple[float, float]) -> bool:
    frame = LocalFrame(centroid(fence))
    return contains([frame.to_xy(q) for q in fence], frame.to_xy(p))


def _failsafe(m: Mission, c: Concept, cid: str, key: str, allowed: list[str]) -> CheckResult:
    declared = m["failsafes"].get(key)
    evidence = f"failsafes.{key}: {declared if declared is not None else 'not declared'}"
    if declared is None:
        return result(c, cid, FAIL, evidence, f"the mission declares no {key} action")
    if declared not in allowed:
        return result(c, cid, FAIL, evidence, f"{declared} is not one of {', '.join(allowed)}")
    return result(c, cid, PASS, evidence, f"the {key} action is {declared}")


def check_lost_link(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    return _failsafe(m, c, "failsafe.lost_link", c.table["mission_key"], c.table["actions"])


def check_low_battery(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    key = c.table["mission_keys"]["low"]
    return _failsafe(m, c, "failsafe.low_battery", key, c.table["actions"])


def check_critical_battery(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    key = c.table["mission_keys"]["critical"]
    return _failsafe(m, c, "failsafe.critical_battery", key, c.table["critical_actions"])


def check_geofence_breach(m: Mission, plan: Plan, c: Concept, bundle: Bundle) -> CheckResult:
    key = c.table["mission_key"]
    return _failsafe(m, c, "failsafe.geofence_breach", key, c.table["actions"])


Check = Callable[[Mission, Plan, Concept, Bundle], CheckResult]
CHECKS: dict[str, Check] = {
    "alt.max_agl": check_alt_max_agl,
    "category.operation": check_category_operation,
    "plan.first_item_takeoff": check_first_item_takeoff,
    "plan.last_item_return": check_last_item_return,
    "plan.inside_geofence": check_inside_geofence,
    "failsafe.lost_link": check_lost_link,
    "failsafe.low_battery": check_low_battery,
    "failsafe.critical_battery": check_critical_battery,
    "failsafe.geofence_breach": check_geofence_breach,
}


def validate(mission: Mission, plan: Plan, bundle: Bundle) -> list[CheckResult]:
    """Return one result per check, in the order of CHECKS."""
    results = []
    for check_id, fn in CHECKS.items():
        concept = governing(bundle, check_id)
        if concept is None:
            results.append(no_concept(check_id))
        else:
            results.append(fn(mission, plan, concept, bundle))
    return results


def main(argv: list[str] | None = None) -> int:
    """Write out/<id>/validation.json. Return 0, or 2 for a bad request or a missing plan."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        mission = load_mission(args.mission)
        plan_path = args.out / mission["id"] / "mission.plan"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (MissionError, OSError, ValueError) as e:
        print(e, file=sys.stderr)
        return 2
    checks = validate(mission, plan, load_bundle(args.knowledge))
    doc = {"mission_id": mission["id"], "checks": [r.to_dict() for r in checks]}
    out = args.out / mission["id"] / "validation.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
