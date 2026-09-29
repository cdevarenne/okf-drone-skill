"""Load a mission request (missions/<id>.yaml) and check it against the mission schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "mission.schema.json"


class MissionError(ValueError):
    """A mission request does not agree with the mission schema (spec §5.2)."""


def load_mission(path: Path) -> dict[str, Any]:
    """Return the mission request in `path`. Raise MissionError if it is not valid.

    The `id` must be the file name without `.yaml`.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise MissionError(f"{path}: cannot read the file: {e.strerror}") from e
    try:
        mission = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise MissionError(f"{path}: unparseable YAML: {e}") from e
    validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    errors = sorted(validator.iter_errors(mission), key=lambda e: list(e.absolute_path))
    if errors:
        lines = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in errors]
        raise MissionError(f"{path}: " + "; ".join(lines))
    if mission["id"] != path.stem:
        raise MissionError(f"{path}: id {mission['id']!r} is not the file name {path.stem!r}")
    return mission
