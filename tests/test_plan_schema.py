"""Check the vendored .plan subset schema against a valid plan and against broken copies."""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from test_tools_lock import read_lock

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "qgc"
SCHEMA = json.loads((FIXTURES / "plan.schema.json").read_text())
VALID = json.loads((FIXTURES / "minimal.plan").read_text())


def errors(plan: dict[str, Any]) -> list[str]:
    """Return the schema error messages for a plan."""
    return [e.message for e in Draft202012Validator(SCHEMA).iter_errors(plan)]


def test_schema_is_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)


def test_minimal_plan_is_valid() -> None:
    assert errors(VALID) == []


def test_schema_versions_match_tools_lock() -> None:
    lock = read_lock()
    props = SCHEMA["properties"]
    assert props["version"]["const"] == int(lock["QGC_PLAN_VERSION"])
    assert props["mission"]["properties"]["version"]["const"] == int(lock["QGC_MISSION_VERSION"])
    assert props["geoFence"]["properties"]["version"]["const"] == int(lock["QGC_GEOFENCE_VERSION"])
    assert props["rallyPoints"]["properties"]["version"]["const"] == int(lock["QGC_RALLY_VERSION"])


def _drop_file_type(p: dict[str, Any]) -> None:
    del p["fileType"]


def _mission_v1(p: dict[str, Any]) -> None:
    p["mission"]["version"] = 1


def _six_params(p: dict[str, Any]) -> None:
    p["mission"]["items"][0]["params"] = [0, 0, 0, 0, 0, 0]


def _complex_item(p: dict[str, Any]) -> None:
    p["mission"]["items"][0]["type"] = "ComplexItem"


def _two_point_fence(p: dict[str, Any]) -> None:
    p["geoFence"]["polygons"][0]["polygon"] = [[44.79, -0.60], [44.80, -0.60]]


def _bad_latitude(p: dict[str, Any]) -> None:
    p["mission"]["plannedHomePosition"][0] = 91.0


def _circle_fence(p: dict[str, Any]) -> None:
    p["geoFence"]["circles"] = [{"circle": {"center": [44.8, -0.6], "radius": 100}}]


@pytest.mark.parametrize(
    "breaks",
    [_drop_file_type, _mission_v1, _six_params, _complex_item, _two_point_fence, _bad_latitude, _circle_fence],
)
def test_broken_plan_is_rejected(breaks: Callable[[dict[str, Any]], None]) -> None:
    plan = copy.deepcopy(VALID)
    breaks(plan)
    assert errors(plan) != []
