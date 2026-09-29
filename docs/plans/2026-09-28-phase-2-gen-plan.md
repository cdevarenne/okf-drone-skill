# okf-drone-skill Phase 2 Plan: gen_plan

Execute with Claude Code, task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** `make plan MISSION=<path>` reads a mission request and the bundle, and writes
`out/<id>/mission.plan`, a QGroundControl plan that validates against the vendored subset schema.
The pattern (grid, corridor, expanding square) comes from the mission-type concept. The mission
commands and frames come from the MAVLink concepts.

**Spec:** `docs/specs/2026-09-28-okf-drone-skill-v1-design.md` §5.2, §6 step 2, §9 Phase 2.
**Backlog:** DRN-04.

**Provenance:** Tasks 1 to 4 were run in a prototype on 2026-09-28 (Python 3.14.0rc2, uv 0.8.17,
ruff 0.16.9, pytest 9.1.1), on a copy of `main` at `a8be5fd`. The file contents below are copied
from that run, and the tasks were replayed in order to get the expected outputs. The prototype
found one bug before the plan was written: a missing mission file gave a traceback. `load_mission`
now raises `MissionError`, and a test covers it.

## Global constraints

- Commits on `main` as `cdevarenne`, dated in PST (`TZ=America/Los_Angeles`). Short subject in
  ASD-STE100. Body line `Closes #N`.
- Every commit ships tests, or says that it is docs only. The test fails first.
- Before every commit: `make verify` (ruff and pytest).
- No regulatory value in code. `gen_plan` reads the pattern name, the command ids and the frames
  from the bundle. A missing concept is a gap (`GapError`), never a default.
- `gen_plan` writes what the request asks for and never corrects it. `validate_plan` (Phase 3)
  judges the plan.
- `gen_plan` calls no LLM.

## Decisions for the owner (before Task 0)

1. **Height rule** (agreed 2026-09-28). The plan altitudes are relative to home. The
   `regulations/easa-open` limit is from the closest point of the surface. The mission request
   declares `terrain: flat | varied`. With `flat`, `alt.max_agl` compares the plan altitude with
   the limit. With `varied`, the check is a gap (HOLD). Task 1 writes this in the spec; Phase 3
   implements the check.
2. **New mission-request fields** (spec §5.2, Task 1): `home` (takeoff point and
   `plannedHomePosition`), `terrain`, `geofence` (the inclusion polygon, declared apart from the
   `area`), `speed_ms`, `pattern` (`spacing_m`, plus `datum` for the expanding square, or
   `route` for the corridor). The airspace facts for the ARC decision tree wait for Phase 3.
3. **m03 is seeded through the geofence.** `gen_plan` keeps the pattern inside the `area`. m03
   declares a `geofence` that does not contain the whole area, so a waypoint is outside the
   geofence and `plan.inside_geofence` fails (cites `failsafes/geofence-breach`).
4. **`jsonschema` becomes a runtime dependency.** `mission.py` validates the request against a
   JSON Schema at run time. It moves from the dev group to `dependencies`.
5. **Constants in code** (not regulatory values; each has a comment with its source):
   `firmwareType` 12 (`MAV_AUTOPILOT_PX4`) and `vehicleType` 2 (`MAV_TYPE_QUADROTOR`) from S9;
   `AltitudeMode` 1 (relative to home); geofence polygon `version` 1 (the S8 example); lat/lon
   rounded to 7 decimals (the MAVLink 1e-7 degree scale); the mean earth radius for the local
   projection. v1 plans only multicopters.
6. **Geometry.** A local equirectangular projection (good for areas of a few km). The `area` must
   be convex. Grid lines run west to east, `spacing_m` apart, and end half a spacing inside the
   area. The expanding square starts at `datum` (legs north, east, south, west: 1, 1, 2, 2, ...
   x spacing) and stops before the first point that is not strictly inside the area. The
   corridor flies the `route` as given.
7. **No human gate** in Phase 2 (spec §9). Optional: the owner loads one generated plan in
   QGroundControl (Task 5, Step 3).

## Task 0: Tracking issues (no commit)

- [ ] **Step 1:** Create one issue per task. The last issue is #16, so Task N becomes #N+16.

```
T1 (DRN-04): Spec: mission request fields and the height rule
T2 (DRN-04): Mission request schema and loader
T3 (DRN-04): Geometry and flight patterns
T4 (DRN-04): gen_plan and make plan
T5 (DRN-04): README for Phase 2
```

Body: `Phase 2. See docs/plans/2026-09-28-phase-2-gen-plan.md, Task N.`

- [ ] **Step 2:** List the issues. Expected: #17 to #21 open.

---

## Task 1: Spec: mission request fields and the height rule (#17)

**Files:** modify `docs/specs/2026-09-28-okf-drone-skill-v1-design.md`. Docs only.

- [ ] **Step 1:** In §5.2, replace the YAML block with:

```yaml
id: m01-survey-open       # the file name without .yaml
mission_type: mapping-survey  # a concept in mission-types/
category: open            # open | specific
operation: VLOS           # VLOS | BVLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}  # takeoff point; plannedHomePosition
terrain: flat             # flat | varied
area: {polygon: [[lat, lon], ...]}      # convex; the pattern stays inside it
geofence: {polygon: [[lat, lon], ...]}  # the inclusion polygon in the .plan
max_altitude_agl_m: 100   # the altitude of every item, relative to home
speed_ms: 8               # cruise and hover speed in the .plan
pattern: {spacing_m: 40}  # grid; expanding square adds datum: [lat, lon];
                          # corridor is {route: [[lat, lon], ...]}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}  # value set comes from risk/igrc.md
airspace: {class: G, declared_by: operator}
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

- [ ] **Step 2:** In §5.2, before "Airspace, NOTAM and weather are **declared inputs**", add:

```markdown
The schema is `.claude/skills/drone-mission-compliance/schemas/mission.schema.json` (Phase 2).
Value sets that come from the bundle (mission types, population density bands, failsafe
actions) are not in the schema; the pipeline checks them against the bundle.
```

and after that sentence add:

```markdown
Terrain is a declared input too: v1 has no terrain data (see §6, `alt.max_agl`).
```

- [ ] **Step 3:** In §6, replace steps 2 and 3 with:

```markdown
2. `gen_plan`: pattern by mission type (grid, corridor, expanding square; the pattern name
   comes from the mission-type concept). Writes takeoff at `home`, the pattern waypoints, RTL,
   and the declared geofence polygon. It writes what the request asks for and never corrects
   it; `validate_plan` judges the result. A mission type or command with no concept is a gap.
3. `validate_plan`: v1 checks: altitude ceiling, all waypoints inside geofence, first item is
   takeoff, last item is RTL or land, declared failsafes present, category matches operation.
   Height rule (`alt.max_agl`): the plan altitudes are relative to home, and the
   `regulations/easa-open` limit is from the closest point of the surface. With
   `terrain: flat`, the check compares the plan altitudes with the limit. With
   `terrain: varied`, v1 has no terrain data, so the check is a gap (HOLD).
```

- [ ] **Step 4:** In §7, replace the m03 and m05 rows with:

```markdown
| m03 | one waypoint outside the geofence (the declared geofence does not contain the area) | NO-GO, cites `failsafes/geofence-breach` |
| m05 | specific category, BVLOS; the OSO table (`sora.oso`) is not in the bundle | HOLD (gap), not GO |
```

- [ ] **Step 5: Verify.** `make verify`. Expected: `167 passed`.
- [ ] **Step 6: Commit.** `Add the mission request fields and the height rule to the spec (docs only)`,
  `Closes #17`.

---

## Task 2: Mission request schema and loader (#18)

**Files:** create `.claude/skills/drone-mission-compliance/schemas/mission.schema.json`,
`.claude/skills/drone-mission-compliance/scripts/mission.py`, `tests/test_mission.py`,
`tests/fixtures/missions/{survey,inspection,search}.yaml`; modify `pyproject.toml`, `uv.lock`.

- [ ] **Step 1: Move `jsonschema` to the runtime dependencies.** In `pyproject.toml`:

```toml
dependencies = ["jsonschema>=4.25", "pyyaml>=6.0.2"]

[dependency-groups]
dev = ["pytest>=8.4", "ruff>=0.13"]
```

Run `uv lock` and `uv sync`. Do not edit `uv.lock` by hand. Expected diff in `uv.lock`:
`jsonschema` moves from the `dev` group to `requires-dist`; no version changes.

- [ ] **Step 2: Write the fixture missions.** The coordinates are arbitrary test values.

`tests/fixtures/missions/survey.yaml`:

```yaml
# Test fixture. The coordinates are arbitrary test values.
id: survey
mission_type: mapping-survey
category: open
operation: VLOS
home: {lat: 44.7990, lon: -0.6000, amsl_m: 50}
terrain: flat
area: {polygon: [[44.7985, -0.6015], [44.8025, -0.6015], [44.8025, -0.5985], [44.7985, -0.5985]]}
geofence: {polygon: [[44.7980, -0.6020], [44.8030, -0.6020], [44.8030, -0.5980], [44.7980, -0.5980]]}
max_altitude_agl_m: 60
speed_ms: 8
pattern: {spacing_m: 40}
ua: {mtom_kg: 0.9, char_dimension_m: 0.35, max_speed_ms: 15}
ground: {population_density: sparsely-populated}
airspace: {class: G, declared_by: operator}
failsafes: {lost_link: RTL, low_battery: RTL, critical_battery: LAND, geofence_breach: RTL}
```

`tests/fixtures/missions/inspection.yaml` and `search.yaml` are the same, except:

| File | `id` | `mission_type` | `pattern` |
|---|---|---|---|
| `inspection.yaml` | `inspection` | `infrastructure-inspection` | `{route: [[44.7995, -0.6008], [44.8005, -0.6002], [44.8015, -0.5996]]}` |
| `search.yaml` | `search` | `search-pattern` | `{spacing_m: 30, datum: [44.8005, -0.6000]}` |

- [ ] **Step 3: Write the failing test.**

`tests/test_mission.py`:

```python
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
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_mission.py`,
`ModuleNotFoundError: No module named 'mission'`.

- [ ] **Step 4: Write the schema.**

`.claude/skills/drone-mission-compliance/schemas/mission.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "okf-drone-skill/mission-request",
  "title": "Mission request (missions/<id>.yaml)",
  "$comment": "Spec §5.2. Value sets that come from the bundle (mission_type, population_density, failsafe actions) are not listed here; the pipeline checks them against the bundle.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "mission_type", "category", "operation", "home", "terrain", "area", "geofence",
               "max_altitude_agl_m", "speed_ms", "pattern", "ua", "ground", "airspace", "failsafes"],
  "properties": {
    "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
    "mission_type": {"type": "string"},
    "category": {"enum": ["open", "specific"]},
    "operation": {"enum": ["VLOS", "BVLOS"]},
    "home": {
      "type": "object",
      "additionalProperties": false,
      "required": ["lat", "lon", "amsl_m"],
      "properties": {
        "lat": {"type": "number", "minimum": -90, "maximum": 90},
        "lon": {"type": "number", "minimum": -180, "maximum": 180},
        "amsl_m": {"type": "number"}
      }
    },
    "terrain": {"enum": ["flat", "varied"]},
    "area": {"$ref": "#/$defs/polygonObject"},
    "geofence": {"$ref": "#/$defs/polygonObject"},
    "max_altitude_agl_m": {"type": "number", "exclusiveMinimum": 0},
    "speed_ms": {"type": "number", "exclusiveMinimum": 0},
    "pattern": {
      "oneOf": [
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["spacing_m"],
          "properties": {
            "spacing_m": {"type": "number", "exclusiveMinimum": 0},
            "datum": {"$ref": "#/$defs/latLon"}
          }
        },
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["route"],
          "properties": {"route": {"type": "array", "minItems": 2, "items": {"$ref": "#/$defs/latLon"}}}
        }
      ]
    },
    "ua": {
      "type": "object",
      "required": ["mtom_kg", "char_dimension_m", "max_speed_ms"],
      "properties": {
        "mtom_kg": {"type": "number", "exclusiveMinimum": 0},
        "char_dimension_m": {"type": "number", "exclusiveMinimum": 0},
        "max_speed_ms": {"type": "number", "exclusiveMinimum": 0}
      }
    },
    "ground": {
      "type": "object",
      "required": ["population_density"],
      "properties": {"population_density": {"type": "string"}}
    },
    "airspace": {
      "type": "object",
      "required": ["class", "declared_by"],
      "properties": {"class": {"type": "string"}, "declared_by": {"type": "string"}}
    },
    "failsafes": {
      "type": "object",
      "additionalProperties": {"type": "string"},
      "propertyNames": {"enum": ["lost_link", "low_battery", "critical_battery", "geofence_breach"]}
    }
  },
  "$defs": {
    "latLon": {
      "type": "array",
      "prefixItems": [
        {"type": "number", "minimum": -90, "maximum": 90},
        {"type": "number", "minimum": -180, "maximum": 180}
      ],
      "minItems": 2,
      "maxItems": 2
    },
    "polygonObject": {
      "type": "object",
      "additionalProperties": false,
      "required": ["polygon"],
      "properties": {"polygon": {"type": "array", "minItems": 3, "items": {"$ref": "#/$defs/latLon"}}}
    }
  }
}
```

- [ ] **Step 5: Write the loader.**

`.claude/skills/drone-mission-compliance/scripts/mission.py`:

```python
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
```

- [ ] **Step 6: Verify.** `make verify`. Expected: `All checks passed!` and `182 passed`.
- [ ] **Step 7: Commit.** `Add the mission request schema and loader`, `Closes #18`.

---

## Task 3: Geometry and flight patterns (#19)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/geometry.py`,
`tests/test_geometry.py`.

- [ ] **Step 1: Write the failing test.**

`tests/test_geometry.py`:

```python
"""Check the local projection, the polygon tests and the three flight patterns."""

import math

import pytest
from geometry import (
    EARTH_RADIUS_M,
    GeometryError,
    LocalFrame,
    contains,
    expanding_square,
    grid,
    is_convex,
    on_boundary,
)

SQUARE = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
L_SHAPE = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (50.0, 50.0), (50.0, 100.0), (0.0, 100.0)]


def test_projection_round_trip() -> None:
    frame = LocalFrame((44.8, -0.6))
    for p in [(44.8, -0.6), (44.81, -0.59), (44.79, -0.61)]:
        lat, lon = frame.to_latlon(frame.to_xy(p))
        assert math.isclose(lat, p[0], abs_tol=1e-12) and math.isclose(lon, p[1], abs_tol=1e-12)


def test_projection_scale() -> None:
    frame = LocalFrame((44.8, -0.6))
    x, y = frame.to_xy((45.8, -0.6))
    assert x == 0 and math.isclose(y, math.radians(1) * EARTH_RADIUS_M)
    x, _ = frame.to_xy((44.8, 0.4))
    assert math.isclose(x, math.radians(1) * EARTH_RADIUS_M * math.cos(math.radians(44.8)))


def test_contains_and_boundary() -> None:
    assert contains(SQUARE, (50, 50)) and not on_boundary(SQUARE, (50, 50))
    assert contains(SQUARE, (100, 50)) and on_boundary(SQUARE, (100, 50))
    assert contains(SQUARE, (0, 0)) and on_boundary(SQUARE, (0, 0))
    assert not contains(SQUARE, (100.01, 50))
    assert not contains(L_SHAPE, (75, 75)) and contains(L_SHAPE, (25, 75))


def test_is_convex() -> None:
    assert is_convex(SQUARE) and is_convex(SQUARE[::-1])
    assert not is_convex(L_SHAPE)
    assert not is_convex([(0, 0), (50, 0), (100, 0), (100, 100), (0, 100)])
    assert not is_convex(SQUARE[:2])


def test_grid_rows_and_half_swath() -> None:
    assert grid(SQUARE, 20) == [
        (10, 10), (90, 10),
        (90, 30), (10, 30),
        (10, 50), (90, 50),
        (90, 70), (10, 70),
        (10, 90), (90, 90),
    ]  # fmt: skip


def test_grid_short_chord_uses_midpoint() -> None:
    triangle = [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]
    points = grid(triangle, 40)
    assert points[-1] == (50.0, 60.0)
    assert all(contains(triangle, p) and not on_boundary(triangle, p) for p in points)


@pytest.mark.parametrize(
    ("area", "spacing"), [(L_SHAPE, 20), (SQUARE, 0), (SQUARE, -5)], ids=["concave", "zero", "neg"]
)
def test_grid_rejects_bad_input(area, spacing) -> None:
    with pytest.raises(GeometryError):
        grid(area, spacing)


def test_expanding_square_legs() -> None:
    points = expanding_square(SQUARE, (50.0, 50.0), 10)
    assert points[:5] == [(50, 50), (50, 60), (60, 60), (60, 40), (40, 40)]
    assert points[-1] == (10, 10)
    assert len(points) == 17
    assert all(not on_boundary(SQUARE, p) for p in points)


@pytest.mark.parametrize(
    ("datum", "spacing"), [((0.0, 50.0), 10), ((150.0, 50.0), 10), ((50.0, 50.0), 0)]
)
def test_expanding_square_rejects_bad_input(datum, spacing) -> None:
    with pytest.raises(GeometryError):
        expanding_square(SQUARE, datum, spacing)
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_geometry.py`,
`ModuleNotFoundError: No module named 'geometry'`.

- [ ] **Step 2: Write the module.**

`.claude/skills/drone-mission-compliance/scripts/geometry.py`:

```python
"""Plane geometry for small mission areas, and the three flight patterns.

A position is (lat, lon) in degrees (WGS84). A local plane in metres (x east, y north), centred
on an origin, approximates the earth for areas of a few kilometres (equirectangular projection).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

EARTH_RADIUS_M = 6371008.8  # IUGG mean earth radius
LatLon = tuple[float, float]
XY = tuple[float, float]


class GeometryError(ValueError):
    """A polygon or a pattern input is not valid."""


class LocalFrame:
    """Convert between (lat, lon) and a local plane in metres around an origin."""

    def __init__(self, origin: LatLon) -> None:
        self.lat0, self.lon0 = origin
        self._kx = math.radians(1) * EARTH_RADIUS_M * math.cos(math.radians(self.lat0))
        self._ky = math.radians(1) * EARTH_RADIUS_M

    def to_xy(self, p: LatLon) -> XY:
        """Return (x east, y north) in metres."""
        return ((p[1] - self.lon0) * self._kx, (p[0] - self.lat0) * self._ky)

    def to_latlon(self, q: XY) -> LatLon:
        """Return (lat, lon) in degrees."""
        return (self.lat0 + q[1] / self._ky, self.lon0 + q[0] / self._kx)


def centroid(points: Sequence[LatLon]) -> LatLon:
    """Return the mean of the vertices. Good enough as a projection origin."""
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def _cross(o: XY, a: XY, b: XY) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def is_convex(poly: Sequence[XY]) -> bool:
    """Return True if the polygon (3 or more vertices, any winding) is strictly convex."""
    n = len(poly)
    turns = [_cross(poly[i], poly[(i + 1) % n], poly[(i + 2) % n]) for i in range(n)]
    return n >= 3 and (all(t > 0 for t in turns) or all(t < 0 for t in turns))


def on_boundary(poly: Sequence[XY], q: XY) -> bool:
    """Return True if q is on an edge of the polygon."""
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        in_box = min(a[0], b[0]) <= q[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= q[1] <= max(
            a[1], b[1]
        )
        if in_box and _cross(a, b, q) == 0:
            return True
    return False


def contains(poly: Sequence[XY], q: XY) -> bool:
    """Return True if q is inside the polygon or on its boundary (ray casting)."""
    if on_boundary(poly, q):
        return True
    inside = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > q[1]) != (y2 > q[1]):
            x = x1 + (q[1] - y1) * (x2 - x1) / (y2 - y1)
            if q[0] < x:
                inside = not inside
    return inside


def _chord(poly: Sequence[XY], y: float) -> tuple[float, float] | None:
    """Return (x_west, x_east) where the horizontal line at y crosses a convex polygon."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return (min(xs), max(xs)) if len(xs) >= 2 else None


def grid(area: Sequence[XY], spacing: float) -> list[XY]:
    """Return a boustrophedon grid over a convex area.

    Lines run west-east, `spacing` apart. The first line is spacing/2 north of the south edge.
    Each line ends spacing/2 inside the area (the half swath), or at the chord midpoint if the
    chord is shorter than `spacing`. Odd lines run east to west.
    """
    if spacing <= 0:
        raise GeometryError("spacing must be positive")
    if not is_convex(area):
        raise GeometryError("the area polygon must be convex")
    ys = [p[1] for p in area]
    points: list[XY] = []
    y = min(ys) + spacing / 2
    row = 0
    while y < max(ys):
        chord = _chord(area, y)
        if chord:
            west, east = chord
            if east - west > spacing:
                west, east = west + spacing / 2, east - spacing / 2
            else:
                west = east = (west + east) / 2
            line = [(west, y), (east, y)] if row % 2 == 0 else [(east, y), (west, y)]
            points.extend(line if west != east else line[:1])
            row += 1
        y += spacing
    return points


def expanding_square(area: Sequence[XY], datum: XY, spacing: float) -> list[XY]:
    """Return an expanding-square search from `datum`, inside the area.

    Legs go north, east, south, west, with lengths 1, 1, 2, 2, 3, 3, ... x spacing. The pattern
    stops before the first point that is not strictly inside the area (a point on the boundary
    stops it too, so that rounding cannot move a waypoint outside).
    """
    if spacing <= 0:
        raise GeometryError("spacing must be positive")
    if not contains(area, datum) or on_boundary(area, datum):
        raise GeometryError("the datum is not strictly inside the area")
    headings = [(0.0, 1.0), (1.0, 0.0), (0.0, -1.0), (-1.0, 0.0)]
    points = [datum]
    leg = 0
    while True:
        dx, dy = headings[leg % 4]
        length = spacing * (leg // 2 + 1)
        x, y = points[-1]
        nxt = (x + dx * length, y + dy * length)
        if not contains(area, nxt) or on_boundary(area, nxt):
            return points
        points.append(nxt)
        leg += 1
```

- [ ] **Step 3: Verify.** `make verify`. Expected: `All checks passed!` and `195 passed`.
- [ ] **Step 4: Commit.** `Add the geometry and the flight patterns`, `Closes #19`.

---

## Task 4: gen_plan and make plan (#20)

**Files:** create `.claude/skills/drone-mission-compliance/scripts/gen_plan.py`,
`tests/test_gen_plan.py`; modify `Makefile`.

- [ ] **Step 1: Write the failing test.**

`tests/test_gen_plan.py`:

```python
"""Check gen_plan against the fixture missions, the bundle and the .plan subset schema."""

import copy
import json
from itertools import pairwise
from pathlib import Path

import pytest
from gen_plan import GapError, build_plan, main, read_pins
from geometry import LocalFrame, centroid, contains
from jsonschema import Draft202012Validator
from mission import MissionError, load_mission
from okf_lib import Bundle, load_bundle

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"
SCHEMA = json.loads((ROOT / "tests" / "fixtures" / "qgc" / "plan.schema.json").read_text())
BUNDLE = load_bundle(ROOT / "knowledge")
PINS = read_pins(ROOT / "tools.lock")
NAMES = ["survey", "inspection", "search"]


def plan_for(name: str, **changes) -> dict:
    mission = load_mission(MISSIONS / f"{name}.yaml")
    mission.update(changes)
    return build_plan(mission, BUNDLE, PINS)


def waypoints(plan: dict) -> list[tuple[float, float]]:
    return [(i["params"][4], i["params"][5]) for i in plan["mission"]["items"][1:-1]]


@pytest.mark.parametrize("name", NAMES)
def test_plan_validates_against_the_subset_schema(name: str) -> None:
    assert list(Draft202012Validator(SCHEMA).iter_errors(plan_for(name))) == []


@pytest.mark.parametrize("name", NAMES)
def test_plan_structure_comes_from_the_bundle(name: str) -> None:
    items = plan_for(name)["mission"]["items"]
    assert items[0]["command"] == BUNDLE.concepts["mavlink/nav-takeoff"].table["mavlink_id"]
    assert items[-1]["command"] == BUNDLE.concepts["mavlink/nav-rtl"].table["mavlink_id"]
    assert items[-1]["frame"] == BUNDLE.concepts["mavlink/nav-rtl"].table["frame"]
    waypoint = BUNDLE.concepts["mavlink/nav-waypoint"].table["mavlink_id"]
    assert all(i["command"] == waypoint for i in items[1:-1])
    assert [i["doJumpId"] for i in items] == list(range(1, len(items) + 1))


@pytest.mark.parametrize("name", NAMES)
def test_waypoints_are_inside_the_area_at_the_requested_altitude(name: str) -> None:
    mission = load_mission(MISSIONS / f"{name}.yaml")
    plan = plan_for(name)
    area = [tuple(p) for p in mission["area"]["polygon"]]
    frame = LocalFrame(centroid(area))
    area_xy = [frame.to_xy(p) for p in area]
    assert waypoints(plan)
    assert all(contains(area_xy, frame.to_xy(p)) for p in waypoints(plan))
    alts = [i["Altitude"] for i in plan["mission"]["items"][:-1]]
    assert alts == [mission["max_altitude_agl_m"]] * len(alts)
    fence = plan["geoFence"]["polygons"][0]
    assert fence["inclusion"] and fence["polygon"] == mission["geofence"]["polygon"]


@pytest.mark.parametrize("name", NAMES)
def test_plan_is_deterministic(name: str) -> None:
    assert json.dumps(plan_for(name)) == json.dumps(plan_for(name))


def test_grid_rows_are_spacing_apart() -> None:
    mission = load_mission(MISSIONS / "survey.yaml")
    frame = LocalFrame(centroid([tuple(p) for p in mission["area"]["polygon"]]))
    ys = [frame.to_xy(p)[1] for p in waypoints(plan_for("survey"))]
    rows = [ys[i] for i in range(0, len(ys), 2)]
    spacing = mission["pattern"]["spacing_m"]
    assert len(rows) > 2
    assert all(abs(b - a - spacing) < 0.05 for a, b in pairwise(rows))  # 1e-7 degree rounding


def test_corridor_flies_the_route() -> None:
    mission = load_mission(MISSIONS / "inspection.yaml")
    assert [list(p) for p in waypoints(plan_for("inspection"))] == mission["pattern"]["route"]


def test_search_starts_at_the_datum() -> None:
    mission = load_mission(MISSIONS / "search.yaml")
    assert list(waypoints(plan_for("search"))[0]) == mission["pattern"]["datum"]


def test_altitude_is_not_corrected() -> None:
    """gen_plan writes the requested altitude. validate_plan judges it (seeded m02)."""
    items = plan_for("survey", max_altitude_agl_m=150)["mission"]["items"]
    assert {i["Altitude"] for i in items[:-1]} == {150}


def test_unknown_mission_type_is_a_gap() -> None:
    with pytest.raises(GapError, match="mission-types/crop-spraying"):
        plan_for("survey", mission_type="crop-spraying")


def test_missing_command_concept_is_a_gap() -> None:
    concepts = {k: v for k, v in BUNDLE.concepts.items() if k != "mavlink/nav-rtl"}
    mission = load_mission(MISSIONS / "survey.yaml")
    with pytest.raises(GapError, match="mavlink/nav-rtl"):
        build_plan(mission, Bundle(concepts=concepts), PINS)


def test_pattern_input_must_match_the_mission_type() -> None:
    route = load_mission(MISSIONS / "inspection.yaml")["pattern"]
    with pytest.raises(MissionError, match="spacing_m"):
        plan_for("survey", pattern=copy.deepcopy(route))


def test_cli_writes_the_plan(tmp_path: Path) -> None:
    args = ["--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock")]
    code = main([*args, "--mission", str(MISSIONS / "search.yaml"), "--out", str(tmp_path)])
    assert code == 0
    written = json.loads((tmp_path / "search" / "mission.plan").read_text())
    assert written == plan_for("search")


def test_cli_returns_2_on_a_bad_request(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: bad\n", encoding="utf-8")
    args = ["--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock")]
    assert main([*args, "--mission", str(bad), "--out", str(tmp_path)]) == 2
    assert not (tmp_path / "bad").exists()
```

Run `uv run pytest -q`. Expected: `ERROR collecting tests/test_gen_plan.py`,
`ModuleNotFoundError: No module named 'gen_plan'`.

- [ ] **Step 2: Write gen_plan.**

`.claude/skills/drone-mission-compliance/scripts/gen_plan.py`:

```python
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
```

- [ ] **Step 3: Add the `plan` target.** In `Makefile`, add after `include tools.lock`:

```makefile
SCRIPTS := .claude/skills/drone-mission-compliance/scripts
```

add `plan` to `.PHONY`, and add before `test:` (the recipe line starts with a tab):

```makefile
plan:
	$(PY) $(SCRIPTS)/gen_plan.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out
```

- [ ] **Step 4: Verify.** `make verify`. Expected: `All checks passed!` and `216 passed`.
  Then `make plan MISSION=tests/fixtures/missions/survey.yaml`. Expected:
  `wrote out/survey/mission.plan` (24 items: takeoff, 22 grid waypoints, RTL). And
  `make plan MISSION=tests/fixtures/missions/nope.yaml`. Expected: one line
  `...: cannot read the file: No such file or directory` and `make` error 2.
- [ ] **Step 5: Commit.** `Add gen_plan and the plan target`, `Closes #20`.

---

## Task 5: README for Phase 2 (#21)

**Files:** modify `README.md`. Docs only.

- [ ] **Step 1:** In the README status table, set Phase 2 to `Done`. In "Quick start", add
  `make plan MISSION=tests/fixtures/missions/survey.yaml  # writes out/survey/mission.plan`.
  In "Layout", add `schemas/` under the skill folder and `tests/fixtures/missions/`.
- [ ] **Step 2: Commit.** `Update the README for Phase 2 (docs only)`, `Closes #21`.
- [ ] **Step 3 (owner, optional):** Open `out/survey/mission.plan` in QGroundControl. Check that
  it loads, and that the fence and the grid are where you expect. Report any load error; the
  subset schema and the constants in Decision 5 are the first suspects.

After Task 5: write the Phase 3 plan (`validate_plan` DRN-05, `score_risk` DRN-06), with the
airspace facts for the ARC decision tree and the SORA mitigation declarations in the mission
request.
