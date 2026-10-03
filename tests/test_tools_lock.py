"""Check that tools.lock holds every pin and that each pin has a valid form."""

import re
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "tools.lock"
REQUIRED = {
    "OKF_COMMIT",
    "QGC_PLAN_VERSION",
    "QGC_MISSION_VERSION",
    "QGC_GEOFENCE_VERSION",
    "QGC_RALLY_VERSION",
    "SORA_EDITION",
    "PX4_VERSION",
    "LLM_MODEL",
}


def read_lock() -> dict[str, str]:
    """Return the KEY=VALUE pairs in tools.lock. Ignore comments and blank lines."""
    pairs: dict[str, str] = {}
    for line in LOCK.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        pairs[key] = value
    return pairs


def test_all_pins_present() -> None:
    assert REQUIRED <= read_lock().keys()


def test_okf_commit_is_full_sha() -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", read_lock()["OKF_COMMIT"])


def test_qgc_versions_are_integers() -> None:
    lock = read_lock()
    for key in REQUIRED - {"OKF_COMMIT", "SORA_EDITION", "PX4_VERSION", "LLM_MODEL"}:
        assert lock[key].isdigit(), key


def test_sora_edition() -> None:
    assert read_lock()["SORA_EDITION"] == "2.5"


def test_px4_version_is_a_release_tag() -> None:
    assert re.fullmatch(r"v\d+\.\d+\.\d+", read_lock()["PX4_VERSION"])


def test_llm_model_is_a_claude_model_id() -> None:
    assert re.fullmatch(r"claude-[a-z0-9-]+", read_lock()["LLM_MODEL"])


def test_llm_model_is_the_owner_choice() -> None:
    """The owner chose Sonnet 5.5 from the DRN-09 eval (2026-10-02)."""
    assert read_lock()["LLM_MODEL"] == "claude-sonnet-5-5"
