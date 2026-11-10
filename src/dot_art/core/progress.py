"""Keeps the printer's percent and remaining time true once the art replaces the plain top layer.

The slicer wrote its `M73` lines for the plain layer. The art usually takes far longer, so
every line is recomputed on one timeline that includes it, and the art block gets its own.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import estimate, splice

_PROGRESS = re.compile(r"^M73 P(\d+) R(\d+)\s*$")
_TOTAL_TIME = re.compile(r"total estimated time: ((?:\d+[dhms] ?)+)")
_TIME_PART = re.compile(r"(\d+)([dhms])")
_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
HEADER_LINES = 20  # the time sits in the header block at the top of the file
FULL_PERCENT = 100
SECONDS_PER_MINUTE = 60
ROUNDING_GUARD = 1e-6  # so the sum of rounded shares can still reach exactly 100%


def total_seconds(lines: list) -> int | None:
    """The whole print's time from the slicer's header, or None when the file has none."""
    for line in lines[:HEADER_LINES]:
        match = _TOTAL_TIME.search(line)
        if match:
            return sum(int(amount) * _UNIT_SECONDS[unit] for amount, unit in _TIME_PART.findall(match.group(1)))
    return None


def _percents(lines: list) -> list:
    return [int(match.group(1)) for match in map(_PROGRESS.match, lines) if match]


@dataclass(frozen=True)
class _Timeline:
    """Maps the plain print's percentages to the time of the print that includes the art."""

    plain_total: float
    total: float

    def plain_elapsed(self, percent: int) -> float:
        return percent / FULL_PERCENT * self.plain_total

    def line(self, elapsed: float) -> str:
        percent = min(int(elapsed / self.total * FULL_PERCENT + ROUNDING_GUARD), FULL_PERCENT)
        minutes = int(max(self.total - elapsed, 0.0) / SECONDS_PER_MINUTE + ROUNDING_GUARD)
        return f"M73 P{percent} R{minutes}"

    def rewritten(self, lines: list, shift: float) -> list:
        """The slicer's lines, moved `shift` seconds later."""
        result = []
        for line in lines:
            match = _PROGRESS.match(line)
            result.append(self.line(self.plain_elapsed(int(match.group(1))) + shift) if match else line)
        return result


def _is_travel(line: str) -> bool:
    return line.startswith("G1 X") and " E" not in line


def _timed_block(block: list, line_starts: tuple, timeline: _Timeline, start: float) -> list:
    """One line per change of percent or minute, between blobs so a blob is never interrupted."""
    result, last = [], None
    for line, seconds in zip(block, line_starts):
        if _is_travel(line):
            current = timeline.line(start + seconds)
            if current != last:
                result.append(current)
                last = current
        result.append(line)
    return result


def spliced(lines: list, top: splice.TopLayer, block: list, acceleration: float) -> list:
    """`lines` with the top layer replaced by `block`, and the progress lines made true."""
    before, after = lines[: top.region_start], lines[top.region_end :]
    plain_total = total_seconds(lines)
    if not plain_total or not (_percents(before) or _percents(after)):
        return splice.replace(lines, top, block)
    totals = estimate.estimate(block, acceleration)
    start_percent = max(_percents(before), default=0)
    end_percent = min(_percents(after), default=FULL_PERCENT)
    plain_layer = (end_percent - start_percent) / FULL_PERCENT * plain_total
    shift = totals.seconds - plain_layer
    timeline = _Timeline(plain_total, plain_total + shift)
    start = timeline.plain_elapsed(start_percent)
    return timeline.rewritten(before, 0.0) + _timed_block(block, totals.line_starts, timeline, start) + timeline.rewritten(after, shift)
