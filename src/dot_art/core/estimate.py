"""Motion-time estimate for dot G-code.

Every move starts and ends at rest. That is the honest case for dots: each one is
separated by an extruder-only move, so the planner has no speed to carry over.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

_WORD = re.compile(r"([XYZEF])([-+]?[0-9]*\.?[0-9]+)")
Z_ACCELERATION = 500.0
Z_MAX_SPEED = 20.0
E_ACCELERATION = 5000.0
_DWELL = re.compile(r"M400 P([0-9]+)")
MILLISECONDS = 1000.0


@dataclass(frozen=True)
class Totals:
    seconds: float
    travel_mm: float
    retractions: int
    filament_mm: float  # what the blobs use: an unretraction only returns filament that was pulled back
    line_starts: tuple = ()  # seconds into the block at which each line begins


def trapezoid_time(distance: float, speed: float, acceleration: float) -> float:
    """Time for a move from rest to rest under a speed limit and a constant acceleration."""
    if distance <= 0:
        return 0.0
    ramp_distance = speed * speed / acceleration
    if distance < ramp_distance:
        return 2 * math.sqrt(distance / acceleration)
    return distance / speed + speed / acceleration


def estimate(lines: list, xy_acceleration: float) -> Totals:
    x = y = z = None
    feed = 0.0
    seconds = travel = filament = 0.0
    retractions = 0
    line_starts = []
    for line in lines:
        line_starts.append(seconds)
        pause = _DWELL.match(line)
        if pause:
            seconds += float(pause.group(1)) / MILLISECONDS
        if not line.startswith("G1"):
            continue
        words = {letter: float(value) for letter, value in _WORD.findall(line.split(";", 1)[0])}
        feed = words.get("F", feed)
        speed = feed / 60
        new_x, new_y, new_z = words.get("X", x), words.get("Y", y), words.get("Z", z)
        distance = 0.0 if x is None or new_x is None else math.hypot(new_x - x, new_y - y)
        dz = 0.0 if z is None or new_z is None else abs(new_z - z)
        extrude = words.get("E", 0.0)
        if distance > 0:
            seconds += trapezoid_time(distance, speed, xy_acceleration)
            if extrude == 0:
                travel += distance
        elif dz > 0:
            seconds += trapezoid_time(dz, min(speed, Z_MAX_SPEED), Z_ACCELERATION)
        elif extrude:
            seconds += trapezoid_time(abs(extrude), speed, E_ACCELERATION)
        if extrude > 0 and distance > 0:
            filament += extrude
        elif extrude < 0:
            retractions += 1
        x, y, z = new_x, new_y, new_z
    return Totals(seconds, travel, retractions, filament, tuple(line_starts))
