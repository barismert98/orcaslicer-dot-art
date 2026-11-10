"""Frame shapes: the outline of the art and of the base, as convex polygons around the origin.

Width and height always mean the art's bounding box, before the margin. Every shape is convex
and mirrors across both axes, so a blob test is a list of half-planes and a sliced base's
bounding-box center is the shape's center. A family plugin keeps its own copy of this module.
"""
from __future__ import annotations

import math

SQUARE, CIRCLE, RECTANGLE, OVAL, ROUNDED_RECTANGLE, HEXAGON = "square", "circle", "rectangle", "oval", "rounded_rectangle", "hexagon"
SHAPES = (SQUARE, CIRCLE, RECTANGLE, OVAL, ROUNDED_RECTANGLE, HEXAGON)  # the list and order the family plugins share
FIXED_HEIGHT_SHARE = {SQUARE: 1.0, CIRCLE: 1.0, HEXAGON: math.sqrt(3) / 2}  # these have one size: height over width
HEXAGON_SIDES = 6
CURVE_SEGMENTS = 48  # a multiple of 8 puts vertices on both axes and the diagonals; the CLI refused 120
CORNER_SEGMENTS = 10
CORNER_SHARE = 0.15  # the rounded corner's radius, as a share of the shorter side
EDGE_TOLERANCE = 1e-9  # mm; a point exactly on an edge counts as inside


class Outline:
    """A convex counter-clockwise polygon."""

    def __init__(self, points: list) -> None:
        self.points = tuple(points)
        self._edges = tuple(_inward_edge(a, b) for a, b in zip(self.points, self.points[1:] + self.points[:1]))

    @property
    def width(self) -> float:
        xs = [x for x, _ in self.points]
        return max(xs) - min(xs)

    @property
    def height(self) -> float:
        ys = [y for _, y in self.points]
        return max(ys) - min(ys)

    def contains(self, x: float, y: float, clearance: float = 0.0) -> bool:
        """Whether the point is at least `clearance` inside every edge."""
        return all(nx * x + ny * y - offset >= clearance - EDGE_TOLERANCE for nx, ny, offset in self._edges)

    def extents(self) -> tuple:
        """Width, height and the width measured at 45 degrees, which tell a circle from a square."""
        sums = [x + y for x, y in self.points]
        return self.width, self.height, (max(sums) - min(sums)) / math.sqrt(2)


def _inward_edge(a: tuple, b: tuple) -> tuple:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    return nx, ny, nx * a[0] + ny * a[1]


def _rectangle(half_x: float, half_y: float) -> list:
    return [(-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)]


def _ellipse(half_x: float, half_y: float) -> list:
    steps = [2 * math.pi * i / CURVE_SEGMENTS for i in range(CURVE_SEGMENTS)]
    return [(half_x * math.cos(angle), half_y * math.sin(angle)) for angle in steps]


def _rounded(half_x: float, half_y: float) -> list:
    radius = CORNER_SHARE * 2 * min(half_x, half_y)
    centers = ((half_x - radius, -half_y + radius), (half_x - radius, half_y - radius), (-half_x + radius, half_y - radius), (-half_x + radius, -half_y + radius))
    points = []
    for quarter, (cx, cy) in enumerate(centers):
        start = (quarter - 1) * math.pi / 2
        for step in range(CORNER_SEGMENTS + 1):
            angle = start + step / CORNER_SEGMENTS * math.pi / 2
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def _hexagon(half_x: float, _half_y: float) -> list:
    """Regular and flat on top, so the width runs across two corners."""
    steps = [2 * math.pi * i / HEXAGON_SIDES for i in range(HEXAGON_SIDES)]
    return [(half_x * math.cos(angle), half_x * math.sin(angle)) for angle in steps]


_BUILDERS = {SQUARE: _rectangle, RECTANGLE: _rectangle, CIRCLE: _ellipse, OVAL: _ellipse, ROUNDED_RECTANGLE: _rounded, HEXAGON: _hexagon}


def art_size(name: str, width: float, height: float) -> tuple:
    """The art's real size: a shape with one size ignores a height left over from another shape."""
    return (width, width * FIXED_HEIGHT_SHARE[name]) if name in FIXED_HEIGHT_SHARE else (width, height)


def art_outline(name: str, width: float, height: float) -> Outline:
    real_width, real_height = art_size(name, width, height)
    return Outline(_BUILDERS[name](real_width / 2, real_height / 2))


def _shifted_outward(points: tuple, margin: float) -> list:
    """Moves each corner so that every edge lies `margin` further out."""
    count = len(points)
    moved = []
    for i, (x, y) in enumerate(points):
        before, after = _inward_edge(points[i - 1], points[i]), _inward_edge(points[i], points[(i + 1) % count])
        miter = 1 + before[0] * after[0] + before[1] * after[1]
        moved.append((x - margin * (before[0] + after[0]) / miter, y - margin * (before[1] + after[1]) / miter))
    return moved


def base_outline(name: str, width: float, height: float, margin: float) -> Outline:
    return Outline(_shifted_outward(art_outline(name, width, height).points, margin))
