"""Fly a generated mission.plan in PX4 SITL and check the flown track (DRN-10).

Start PX4 (SIH quadrotor, headless) at the mission home, set the declared failsafe actions,
upload the geofence and the mission, fly it, record the track, and write out/<id>/sitl.json
and out/<id>/sitl_track.json. The PX4 flight log (.ulg) stays in out/<id>/sitl/.

This step is optional and not part of `make plan`: it needs a PX4 SITL build (`make px4`) and
the `sitl` extra (pymavlink). It calls no LLM.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from gen_plan import read_pins
from mission import MissionError, load_mission
from okf_lib import Bundle, load_bundle
from results import governing
from sitl_check import check_track

SIH_QUADX = "10040"  # PX4 airframe 10040_sihsim_quadx (headless SIH simulator)
GCS_URL = "udpin:0.0.0.0:14550"  # PX4 SITL "Normal" MAVLink link; arming needs a GCS here
SAMPLE_S = 0.2  # wall-clock time between track samples
START_TRIES_S = 20  # wall-clock seconds to get PX4 into Mission mode


class SitlError(RuntimeError):
    """PX4 SITL did not start, did not accept the mission, or did not arm."""


def failsafe_params(mission: dict[str, Any], bundle: Bundle) -> dict[str, int]:
    """Return the PX4 parameters for the declared failsafe actions, from `px4_action`.

    An action that is not declared, or that the concept does not map, gives no parameter; the
    check of that failsafe then fails.
    """
    params = {}
    for check_id in ("failsafe.lost_link", "failsafe.geofence_breach"):
        concept = governing(bundle, check_id)
        if concept is None or "px4_action" not in concept.table:
            continue
        mapping = concept.table["px4_action"]
        value = mapping["values"].get(mission["failsafes"].get(concept.table["mission_key"]))
        if value is not None:
            params[mapping["param"]] = value
    return params


def px4_env(mission: dict[str, Any], speed: float) -> dict[str, str]:
    """Return the environment that starts PX4 SIH at the mission home."""
    home = mission["home"]
    return {
        **os.environ,
        "PX4_SYS_AUTOSTART": SIH_QUADX,
        "PX4_HOME_LAT": str(home["lat"]),
        "PX4_HOME_LON": str(home["lon"]),
        "PX4_HOME_ALT": str(home["amsl_m"]),
        "PX4_SIM_SPEED_FACTOR": str(speed),
        "HEADLESS": "1",
    }


def fly(plan: dict[str, Any], params: dict[str, int], timeout_s: float) -> tuple[list, dict]:
    """Connect to PX4, set the params, upload and fly the plan. Return the track and params."""
    from mavlink_gcs import (
        CMD_ARM_DISARM,
        CMD_MISSION_START,
        MISSION_TYPE_FENCE,
        MISSION_TYPE_MISSION,
        RESULT_ACCEPTED,
        Gcs,
        GcsError,
        fence_items,
        mission_items,
    )

    gcs = Gcs(GCS_URL)
    try:
        gcs.wait_position(60)
        gcs.quiet()  # a slow computer must read the mission requests in time
        read_back = {name: gcs.set_param_int(name, value) for name, value in params.items()}
        gcs.upload(fence_items(plan), MISSION_TYPE_FENCE)
        gcs.upload(mission_items(plan), MISSION_TYPE_MISSION)
        for _ in range(30):  # PX4 denies arming until it registers the GCS
            if gcs.command(CMD_ARM_DISARM, 1) == RESULT_ACCEPTED:
                break
            gcs.pump(1)
        else:
            raise SitlError("PX4 did not arm")
        for _ in range(START_TRIES_S):  # PX4 checks a new mission before it allows Mission mode
            gcs.command(CMD_MISSION_START, 0, 0)
            gcs.pump(1)
            if gcs.in_mission_mode() or gcs.in_air() or not gcs.state["armed"]:
                break
        track, start, flew = [], time.time(), False
        while time.time() - start < timeout_s:
            gcs.pump(SAMPLE_S)
            s = gcs.state
            done, total = gcs.progress()
            point = {
                "t_s": round(time.time() - start, 2),
                "lat": s["lat"],
                "lon": s["lon"],
                "rel_alt_m": round(s["rel_alt_m"], 2),
                "armed": s["armed"],
                "in_air": gcs.in_air(),
                "mission_seq": done,
                "mission_total": total,
            }
            track.append(point)
            flew = flew or point["in_air"]
            if not point["armed"] and (flew or point["t_s"] > START_TRIES_S):
                break  # landed after the flight, or PX4 disarmed without a flight
        return track, read_back
    except GcsError as e:
        raise SitlError(str(e)) from e
    finally:
        gcs.close()


def run(
    mission_path: Path,
    knowledge: Path,
    lock: Path,
    out: Path,
    px4_build: Path,
    speed: float,
    timeout_s: float,
) -> dict[str, Any]:
    """Start PX4, fly the mission, stop PX4, and return the sitl.json document."""
    mission = load_mission(mission_path)
    folder = out / mission["id"]
    plan_text = (folder / "mission.plan").read_text(encoding="utf-8")
    bundle = load_bundle(knowledge)
    work = (folder / "sitl").resolve()  # PX4 changes to this folder; paths must be absolute
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    px4 = subprocess.Popen(
        [
            str(px4_build.resolve() / "bin" / "px4"),
            "-d",
            str(px4_build.resolve() / "etc"),
            "-w",
            str(work),
        ],
        env=px4_env(mission, speed),
        stdout=(work / "px4.log").open("w"),
        stderr=subprocess.STDOUT,
    )
    try:
        track, params = fly(json.loads(plan_text), failsafe_params(mission, bundle), timeout_s)
    finally:
        px4.terminate()
        px4.wait(timeout=30)
    checks = check_track(mission, json.loads(plan_text), track, params, bundle)
    air = [p for p in track if p["in_air"]]
    log = (work / "px4.log").read_text(encoding="utf-8", errors="replace").splitlines()
    warnings = list(dict.fromkeys(line.strip() for line in log if line.startswith("WARN")))
    return {
        "mission_id": mission["id"],
        "px4_version": read_pins(lock)["PX4_VERSION"],
        "simulator": f"SIH quadrotor (airframe {SIH_QUADX}), speed factor {speed}",
        "summary": {
            "track_points": len(track),
            "sim_flight_time_s": round((air[-1]["t_s"] - air[0]["t_s"]) * speed) if air else 0,
            "max_rel_alt_m": max((p["rel_alt_m"] for p in air), default=None),
            "params_read_back": params,
            "px4_warnings": warnings,
        },
        "checks": [c.to_dict() for c in checks],
    }, track


def main(argv: list[str] | None = None) -> int:
    """Write sitl.json and sitl_track.json. Return 0, or 2 if the flight could not run."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--px4-build", type=Path, required=True)
    parser.add_argument("--speed", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=600.0, help="wall-clock seconds")
    args = parser.parse_args(argv)
    try:
        doc, track = run(
            args.mission,
            args.knowledge,
            args.lock,
            args.out,
            args.px4_build,
            args.speed,
            args.timeout,
        )
    except (MissionError, SitlError, OSError) as e:
        print(e, file=sys.stderr)
        return 2
    folder = args.out / doc["mission_id"]
    (folder / "sitl_track.json").write_text(json.dumps(track) + "\n", encoding="utf-8")
    (folder / "sitl.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    for c in doc["checks"]:
        print(f"{c['status']:5} {c['check_id']}: {c['evidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
