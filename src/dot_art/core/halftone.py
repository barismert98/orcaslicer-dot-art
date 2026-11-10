"""Halftone mode: from a tone field to blobs whose volume carries the tone."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

ToneField = Callable[[float, float], float]

SIZE_CLASSES = 6
DARK_BOOST_START = 0.5  # coverage where extra material begins
DOME_RATIO = 0.3  # a free blob's height over its width: an estimate for molten PLA on a PLA surface


@dataclass(frozen=True)
class Screen:
    """Defaults are estimates from a 0.4 mm nozzle's geometry and are not yet print tested."""

    pitch: float = 3.2  # the largest blob plus a 0.2 mm gap; a closer spacing merges the darkest blobs
    min_diameter: float = 0.6  # 0.06 mm3: smaller is too little filament to meter from a 0.4 mm nozzle
    max_diameter: float = 3.0  # big blobs are the point of this plugin
    drop_coverage: float = 0.06  # paler than this prints nothing, so highlights stay clean
    dark_boost: float = 1.25  # dark tones ramp up to the largest blob by this factor


@dataclass(frozen=True)
class Dot:
    x: float
    y: float
    diameter: float
    volume: float
    style: int = 0
    height: float = 0.3  # nozzle tip above the base while this blob forms


def _disc_area(diameter: float) -> float:
    return math.pi / 4 * diameter * diameter


def dark_multiplier(coverage: float, screen: Screen) -> float:
    """Extra material for dark tones, reaching `dark_boost` at full coverage."""
    if coverage <= DARK_BOOST_START:
        return 1.0
    return 1.0 + (screen.dark_boost - 1.0) * (coverage - DARK_BOOST_START) / (1 - DARK_BOOST_START)


def diameter_for(coverage: float, screen: Screen) -> float:
    """Blob diameter for a tone: its footprint grows evenly from the smallest blob to the largest.

    Separate blobs cannot reach full ink coverage, so tones spread over the blob sizes a
    nozzle can form rather than following true area coverage, which would clip the darks.
    """
    smallest, largest = _disc_area(screen.min_diameter), _disc_area(screen.max_diameter)
    progress = max(coverage - screen.drop_coverage, 0.0) / (1 - screen.drop_coverage)
    area = (smallest + (largest / screen.dark_boost - smallest) * progress) * dark_multiplier(coverage, screen)
    return math.sqrt(4 * min(max(area, smallest), largest) / math.pi)


def blob_height(diameter: float, min_height: float, dome_ratio: float = DOME_RATIO) -> float:
    """Where the nozzle tip holds: at the top of the finished dome, so it is not buried in it."""
    return max(min_height, diameter * dome_ratio)


def dot_volume(diameter: float, height: float) -> float:
    """Volume of a spherical-cap dome of this footprint and height."""
    radius = diameter / 2
    return math.pi * height / 6 * (3 * radius * radius + height * height)


def densest_pitch(max_diameter: float, min_height: float, dome_ratio: float = DOME_RATIO) -> float:
    """The closest spacing at which the darkest tone still fits under the nozzle.

    Blobs closer than their width merge, and their material spreads into a sheet. At this
    spacing the sheet is as thick as the nozzle's holding height. Any closer and the nozzle
    would be buried in filament it has already laid.
    """
    height = blob_height(max_diameter, min_height, dome_ratio)
    return math.sqrt(dot_volume(max_diameter, height) / height)


def lattice(width: float, height: float, pitch: float) -> list:
    """Dot centers inside the rectangle, on a square lattice turned 45 degrees like newspaper print."""
    step = pitch / math.sqrt(2)
    rows = int(height / step) + 1
    columns = int(width / (2 * step)) + 1
    points = []
    for row in range(rows):
        offset = step if row % 2 else 0.0
        for column in range(columns):
            x = offset + column * 2 * step
            y = row * step
            if x <= width and y <= height:
                points.append((x, y))
    return points


def build(
    field: ToneField, width: float, height: float, screen: Screen, min_height: float, style: int = 0, dome_ratio: float = DOME_RATIO
) -> list:
    """Dots for a rectangle with its lower-left corner at the origin; `field` gives coverage 0..1."""
    dots = []
    for x, y in lattice(width, height, screen.pitch):
        coverage = min(max(field(x, y), 0.0), 1.0)
        if coverage < screen.drop_coverage:
            continue
        diameter = diameter_for(coverage, screen)
        nozzle_height = blob_height(diameter, min_height, dome_ratio)
        dots.append(Dot(x, y, diameter, dot_volume(diameter, nozzle_height), style, nozzle_height))
    return dots


def size_class(diameter: float, screen: Screen) -> int:
    span = screen.max_diameter - screen.min_diameter
    if span <= 0:
        return 0
    return min(int((diameter - screen.min_diameter) / span * SIZE_CLASSES), SIZE_CLASSES - 1)


def order_small_to_large(dots: list, screen: Screen) -> list:
    """Smallest dots first and the over-extruded dark ones last.

    A nozzle that has just laid a large dot carries excess melt on its tip, which would
    smear onto the small, separate dots of the highlights. Each size class is one
    serpentine sweep, so the extra travel stays small.
    """
    groups: dict = {}
    for dot in dots:
        groups.setdefault(size_class(dot.diameter, screen), []).append(dot)
    ordered = []
    for size in sorted(groups):
        rows: dict = {}
        for dot in groups[size]:
            rows.setdefault(round(dot.y, 3), []).append(dot)
        for index, y in enumerate(sorted(rows)):
            ordered.extend(sorted(rows[y], key=lambda dot: dot.x, reverse=bool(index % 2)))
    return ordered
