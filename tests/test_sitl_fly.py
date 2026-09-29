"""Check the parts of sitl_fly that do not need PX4: parameters, environment, errors (DRN-10)."""

import ctypes
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from bundle_helpers import BUNDLE
from mission import load_mission
from sitl_fly import SIH_QUADX, failsafe_params, load_cxx_runtime, main, px4_env

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


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux only")
def test_cxx_runtime_symbol_is_global_on_linux() -> None:
    """The MAVSDK 4.0.1 aarch64 wheel needs this libstdc++ symbol but does not link libstdc++."""
    load_cxx_runtime()
    symbol = (
        "_ZNSt28__atomic_futex_unsigned_base19_M_futex_wait_until"
        "EPjjbNSt6chrono8durationIlSt5ratioILl1ELl1EEEENS2_IlS3_ILl1ELl1000000000EEEE"
    )
    assert hasattr(ctypes.CDLL(None), symbol)


def test_module_imports_without_mavsdk() -> None:
    """MAVSDK is an optional extra; it is imported only inside the flight function."""
    code = "import sys, sitl_fly; print('mavsdk' in sys.modules)"
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
