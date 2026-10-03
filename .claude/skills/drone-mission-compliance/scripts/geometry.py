"""Plane geometry for small mission areas, and the three flight patterns.

A position is (lat, lon) in degrees (WGS84). A local plane in metres (x east, y north), centred
on an origin, approximates the earth for areas of a few kilometres (equirectangular projection).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import pairwise

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


def segment_inside(poly: Sequence[XY], p: XY, q: XY) -> bool:
    """Return True if the segment p-q is inside the polygon or on its boundary.

    Both ends are inside, no edge crosses the segment at a point inside both, and the
    midpoint of each part between the polygon vertices on the segment is inside.
    """
    if not (contains(poly, p) and contains(poly, q)):
        return False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if _cross(p, q, a) * _cross(p, q, b) < 0 and _cross(a, b, p) * _cross(a, b, q) < 0:
            return False
    d = (q[0] - p[0], q[1] - p[1])
    length2 = d[0] ** 2 + d[1] ** 2
    cuts = [0.0, 1.0]
    for v in poly:
        if length2 and on_boundary([p, q], v):
            cuts.append(((v[0] - p[0]) * d[0] + (v[1] - p[1]) * d[1]) / length2)
    cuts.sort()
    return all(
        contains(poly, (p[0] + d[0] * (s + t) / 2, p[1] + d[1] * (s + t) / 2))
        for s, t in pairwise(cuts)
    )


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
