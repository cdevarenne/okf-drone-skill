"""Check the parts of sitl_fly that do not need PX4: parameters, environment, errors (DRN-10)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import sitl_fly
from bundle_helpers import BUNDLE
from mission import load_mission
from sitl_fly import SIH_QUADX, failsafe_params, main, px4_env, stop_px4

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "drone-mission-compliance" / "scripts"


def mission(name: str) -> dict:
    return load_mission(ROOT / "missions" / f"{name}.yaml")


def test_failsafe_params_come_from_px4_action() -> None:
    lost = BUNDLE.concepts["failsafes/lost-link"].table["px4_action"]
    fence = BUNDLE.concepts["failsafes/geofence-breach"].table["px4_action"]
    assert failsafe_params(mission("m01-survey-open"), BUNDLE) == {
        lost["param"]: lost["values"]["RTL"],
        fence["param"]: fence["values"]["RTL"],
    }


def test_undeclared_action_sets_no_param() -> None:
    assert "NAV_DLL_ACT" not in failsafe_params(mission("m04-no-lost-link"), BUNDLE)


def test_px4_env_starts_sih_at_the_mission_home() -> None:
    m = mission("m01-survey-open")
    env = px4_env(m, 10)
    assert env["PX4_SYS_AUTOSTART"] == SIH_QUADX
    assert (env["PX4_HOME_LAT"], env["PX4_HOME_LON"], env["PX4_HOME_ALT"]) == (
        str(m["home"]["lat"]),
        str(m["home"]["lon"]),
        str(m["home"]["amsl_m"]),
    )
    assert env["PX4_SIM_SPEED_FACTOR"] == "10" and env["HEADLESS"] == "1"


def test_module_imports_without_pymavlink() -> None:
    """pymavlink is an optional extra; it is imported only when the flight starts."""
    code = "import sys, sitl_fly, mavlink_gcs; print('pymavlink' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=SCRIPTS, capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "False"


def test_missing_px4_build_returns_2(tmp_path: Path) -> None:
    (tmp_path / "m01-survey-open").mkdir()
    shutil.copy(
        ROOT / "examples" / "m01-survey-open" / "mission.plan", tmp_path / "m01-survey-open"
    )
    args = [
        "--mission", str(ROOT / "missions" / "m01-survey-open.yaml"),
        "--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock"),
        "--out", str(tmp_path), "--px4-build", str(tmp_path / "no-px4"),
    ]  # fmt: skip
    assert main(args) == 2
    assert not (tmp_path / "m01-survey-open" / "sitl.json").exists()
    assert json.loads((tmp_path / "m01-survey-open" / "mission.plan").read_text())


def _m01_args(out: Path) -> list[str]:
    return [
        "--mission", str(ROOT / "missions" / "m01-survey-open.yaml"),
        "--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock"),
        "--out", str(out), "--px4-build", str(out / "no-px4"),
    ]  # fmt: skip


def test_running_px4_stops_the_flight(tmp_path: Path, monkeypatch, capsys) -> None:
    """A PX4 from an earlier run holds instance 0; a second PX4 cannot start."""
    (tmp_path / "m01-survey-open").mkdir()
    monkeypatch.setattr(sitl_fly, "running_px4", lambda: [11233])
    assert main(_m01_args(tmp_path)) == 2
    err = capsys.readouterr().err
    assert "11233" in err and "pkill -x px4" in err
    assert not (tmp_path / "m01-survey-open" / "sitl").exists()


def test_stop_px4_kills_a_process_that_ignores_sigterm() -> None:
    code = "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); print(1, flush=True); time.sleep(60)"
    proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE)
    proc.stdout.readline()  # the handler is set
    stop_px4(proc, 0.5)
    assert proc.returncode is not None
