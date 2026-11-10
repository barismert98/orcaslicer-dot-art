"""Packs the real dots for the page, which draws them on a canvas."""
from __future__ import annotations

import base64
import struct

from .art import Art

UNITS_PER_MM = 100  # 0.01 mm is finer than one preview pixel


def encode(art: Art) -> dict:
    """Base64 of little-endian 16-bit x, y, diameter per dot, in print order.

    x and y run from the left and lower edge of the base. Sending the dots rather than a
    rendered image keeps the UI thread free: pure Python takes seconds to draw 20,000 dots.
    """
    params = art.params
    half_x, half_y = params.base_width / 2, params.base_height / 2
    values = []
    for dot in art.dots:
        values += [
            round((dot.x + half_x) * UNITS_PER_MM),
            round((dot.y + half_y) * UNITS_PER_MM),
            round(dot.diameter * UNITS_PER_MM),
        ]
    return {
        "count": len(art.dots),
        "units": UNITS_PER_MM,
        "width": params.base_width,
        "height": params.base_height,
        "outline": [[x + half_x, y + half_y] for x, y in params.base_outline.points],
        "data": base64.b64encode(struct.pack(f"<{len(values)}H", *values)).decode("ascii"),
    }
