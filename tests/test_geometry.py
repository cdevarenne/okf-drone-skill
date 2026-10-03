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
    segment_inside,
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


@pytest.mark.parametrize(
    ("p", "q", "inside"),
    [
        ((10.0, 10.0), (40.0, 90.0), True),  # inside the vertical arm
        ((25.0, 90.0), (90.0, 25.0), False),  # cuts the notch
        ((10.0, 50.0), (90.0, 50.0), True),  # along the edge y = 50 of the notch
        ((10.0, 10.0), (50.0, 50.0), True),  # ends at the reflex vertex
        ((40.0, 60.0), (60.0, 40.0), True),  # through the reflex vertex, inside on both sides
        ((10.0, 10.0), (110.0, 10.0), False),  # one end outside
    ],
)
def test_segment_inside(p, q, inside) -> None:
    assert segment_inside(L_SHAPE, p, q) is inside
