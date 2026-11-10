"""Turns ordered dots into G-code: the nozzle holds still over each dot and extrudes a blob."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .halftone import Dot

START_MARK = "; DOT_ART_START"
END_MARK = "; DOT_ART_END"
Z_FEED = 1200  # mm/min, the X1C's Z axis is limited to 20 mm/s
ENTRY_HOP = 0.4
MILLISECONDS = 1000
MICRO_MOVE = 0.02  # mm, 5% of the bore. OrcaSlicer's G-code processor counts an E move with no XY as an unretraction, never as extrusion
COORDINATE_DIGITS = 3
BLOB_FEATURE = "Top surface"  # the line type the blobs show under in the preview


@dataclass(frozen=True)
class Style:
    """Defaults are estimates and are not yet print tested."""

    retract: float = 0.8  # a big blob leaves more pressure in the melt zone than a small one
    lift: float = 0.3  # above the tallest blob laid so far
    flow: float = 4.0  # mm3/s, about a second for a 3 mm blob and still well under the X1C's limit
    dwell: float = 0.1  # s, lets the melt pressure finish feeding the blob before the retraction


@dataclass(frozen=True)
class Machine:
    travel_speed: float = 500.0
    travel_acceleration: float = 10000.0
    retract_speed: float = 30.0
    deretract_speed: float = 30.0
    exit_retract: float = 0.8
    filament_diameter: float = 1.75
    flow_ratio: float = 0.98
    max_volumetric: float = 15.0
    nozzle: float = 0.4
    bed: tuple = (0.0, 0.0, 256.0, 256.0)  # min x, min y, max x, max y

    @property
    def filament_area(self) -> float:
        return math.pi * (self.filament_diameter / 2) ** 2


def _num(value: float, digits: int = 3) -> str:
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


class _Writer:
    def __init__(self, cx: float, cy: float, machine: Machine) -> None:
        self.cx, self.cy = cx, cy
        self.machine = machine
        self.lines: list = []
        self.retracted = 0.0

    def set_retraction(self, amount: float) -> None:
        delta = self.retracted - amount
        if abs(delta) < 1e-6:
            return
        feed = self.machine.deretract_speed if delta > 0 else self.machine.retract_speed
        self.lines.append(f"G1 E{_num(delta, 5)} F{_num(feed * 60, 0)}")
        self.retracted = amount

    def set_height(self, height: float) -> None:
        self.lines.append(f"G1 Z{_num(height)} F{Z_FEED}")

    def travel(self, x: float, y: float) -> None:
        feed = self.machine.travel_speed * 60
        self.lines.append(f"G1 X{_num(self.cx + x)} Y{_num(self.cy + y)} F{_num(feed, 0)}")

    def deposit(self, dot: Dot, style: Style) -> None:
        """The blob forms during a micro-move too short to matter, at the blob's flow.

        The move's feed is its X speed, so it is set from how long the blob should take.
        """
        amount = dot.volume / self.machine.filament_area * self.machine.flow_ratio
        seconds = dot.volume / min(style.flow, self.machine.max_volumetric)
        feed = MICRO_MOVE / seconds * 60
        end_x = round(self.cx + dot.x, COORDINATE_DIGITS) + MICRO_MOVE
        self.lines.append(f"; LAYER_HEIGHT: {_num(dot.height)}")
        self.lines.append(f"; LINE_WIDTH: {_num(dot.diameter)}")
        self.lines.append(f"G1 X{_num(end_x)} Y{_num(self.cy + dot.y)} E{_num(amount, 5)} F{_num(feed, 2)}")

    def dwell(self, seconds: float) -> None:
        if seconds > 0:
            self.lines.append(f"M400 P{round(seconds * MILLISECONDS)}")  # the form Bambu's own G-code uses


def emit(
    dots: list,
    styles: list,
    machine: Machine,
    cx: float,
    cy: float,
    z: float,
    relative_e: bool,
    debt_before: float = 0.0,
    e_after: float | None = None,
) -> list:
    """Lines for the art block. `z` is the top of the base."""
    writer = _Writer(cx, cy, machine)
    lines = writer.lines
    lines.append(START_MARK)
    lines.append(f"; FEATURE: {BLOB_FEATURE}")
    if not relative_e:
        lines.append("M83")
    lines.append(f"M204 S{_num(machine.travel_acceleration, 0)}")
    writer.retracted = debt_before
    writer.set_retraction(max(debt_before, machine.exit_retract))
    writer.set_height(z + ENTRY_HOP)

    tallest = 0.0  # travel must clear every blob already laid, not only the last one
    for dot in dots:
        style = styles[dot.style]
        tallest = max(tallest, dot.height)
        writer.travel(dot.x, dot.y)
        writer.set_height(z + dot.height)
        writer.set_retraction(0.0)
        writer.deposit(dot, style)
        writer.dwell(style.dwell)
        writer.set_retraction(style.retract)  # before lifting, so the lift breaks a thin neck
        writer.set_height(z + tallest + style.lift)

    writer.set_retraction(machine.exit_retract)
    writer.set_height(z + tallest + ENTRY_HOP)
    if not relative_e:
        lines.append("M82")
        if e_after is not None:
            lines.append(f"G92 E{_num(e_after, 5)}")
    lines.append(END_MARK)
    return lines
