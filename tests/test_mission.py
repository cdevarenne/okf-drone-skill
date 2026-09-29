"""Check the mission schema and the loader against the fixture missions and broken copies."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator
from mission import SCHEMA_PATH, MissionError, load_mission

MISSIONS = Path(__file__).resolve().parent / "fixtures" / "missions"
FIXTURES = sorted(MISSIONS.glob("*.yaml"))


def test_schema_is_valid() -> None:
    Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text()))


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_fixture_mission_is_valid(path: Path) -> None:
    assert load_mission(path)["id"] == path.stem


def _write(tmp_path: Path, mission: dict[str, Any], name: str = "survey") -> Path:
    path = tmp_path / f"{name}.yaml"
    path.write_text(yaml.safe_dump(mission), encoding="utf-8")
    return path


def _survey() -> dict[str, Any]:
    return yaml.safe_load((MISSIONS / "survey.yaml").read_text())


def _no_home(m: dict[str, Any]) -> None:
    del m["home"]


def _bad_terrain(m: dict[str, Any]) -> None:
    m["terrain"] = "hilly"


def _unknown_key(m: dict[str, Any]) -> None:
    m["altitude"] = 50


def _spacing_and_route(m: dict[str, Any]) -> None:
    m["pattern"]["route"] = [[44.8, -0.6], [44.81, -0.6]]


def _unknown_failsafe(m: dict[str, Any]) -> None:
    m["failsafes"]["gps_loss"] = "LAND"


def _two_point_area(m: dict[str, Any]) -> None:
    m["area"]["polygon"] = m["area"]["polygon"][:2]


def _zero_altitude(m: dict[str, Any]) -> None:
    m["max_altitude_agl_m"] = 0


@pytest.mark.parametrize(
    "breaks",
    [
        _no_home,
        _bad_terrain,
        _unknown_key,
        _spacing_and_route,
        _unknown_failsafe,
        _two_point_area,
        _zero_altitude,
    ],
)
def test_broken_mission_is_rejected(
    tmp_path: Path, breaks: Callable[[dict[str, Any]], None]
) -> None:
    mission = _survey()
    breaks(mission)
    with pytest.raises(MissionError):
        load_mission(_write(tmp_path, mission))


def test_missing_failsafe_is_valid(tmp_path: Path) -> None:
    """A mission without a lost-link action loads; validate_plan reports it (seeded m04)."""
    mission = _survey()
    del mission["failsafes"]["lost_link"]
    assert "lost_link" not in load_mission(_write(tmp_path, mission))["failsafes"]


def test_id_must_match_file_name(tmp_path: Path) -> None:
    with pytest.raises(MissionError, match="is not the file name"):
        load_mission(_write(tmp_path, _survey(), name="other"))


def test_unparseable_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "survey.yaml"
    path.write_text("id: [unclosed\n", encoding="utf-8")
    with pytest.raises(MissionError, match="unparseable YAML"):
        load_mission(path)


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(MissionError, match="cannot read the file"):
        load_mission(tmp_path / "nope.yaml")
