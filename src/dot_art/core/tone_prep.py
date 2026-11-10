"""Automatic tone preparation: spreads a picture over its real light-to-dark range before it becomes blobs.

Values were chosen on the factory's benchmark picture. Blobs cannot show fine detail, so a dull
photo turns into an even gray texture unless its tones are spread and its edges deepened first.
"""
from __future__ import annotations

import math
from collections import Counter
from functools import lru_cache
from itertools import accumulate, chain

from .image import GrayImage

CLIP_SHARE = 0.01  # this share of pixels at each end may clip, so a few stray pixels do not set the range
LEVELS = 256
WHITE = 255
SHARPEN_SIZE = 0.015  # blur spread as a share of the long side: wider ones posterize the picture
SHARPEN_AMOUNT = 0.8
BLUR_PASSES = 2  # two box blurs are close enough to a Gaussian, and far faster in pure Python


def _clip_points(data: bytes) -> tuple:
    counts = Counter(data)
    allowed = CLIP_SHARE * len(data)
    running = list(accumulate(counts[level] for level in range(LEVELS)))
    low = next(level for level, total in enumerate(running) if total > allowed)
    high = next(level for level in range(WHITE, -1, -1) if running[-1] - (running[level - 1] if level else 0) > allowed)
    return low, high


def stretched(image: GrayImage) -> GrayImage:
    """Maps the picture's darkest and lightest real tones to black and white."""
    low, high = _clip_points(image.data)
    if high <= low:
        return image
    table = bytes(min(max(round((level - low) * WHITE / (high - low)), 0), WHITE) for level in range(LEVELS))
    return GrayImage(image.width, image.height, image.data.translate(table))


def _box(values, radius: int) -> list:
    """The running mean of a row; the window shrinks at the ends so edges do not darken."""
    totals = list(accumulate(values, initial=0))
    size = len(values)
    return [
        (totals[min(i + radius + 1, size)] - totals[max(i - radius, 0)]) / (min(i + radius + 1, size) - max(i - radius, 0))
        for i in range(size)
    ]


def _blurred(image: GrayImage, sigma: float) -> list:
    box_width = math.sqrt(6 * sigma * sigma + 1)  # the width whose two passes have this spread
    radius = max(round((box_width - 1) / 2), 1)
    rows = [image.data[y * image.width : (y + 1) * image.width] for y in range(image.height)]
    for _ in range(BLUR_PASSES):
        rows = [_box(row, radius) for row in rows]
        columns = [_box(column, radius) for column in zip(*rows)]
        rows = zip(*columns)
    return list(chain.from_iterable(rows))


def sharpened(image: GrayImage) -> GrayImage:
    """Deepens local edges, so a thin bright rim survives being sampled by big blobs."""
    blurred = _blurred(image, SHARPEN_SIZE * max(image.width, image.height))
    result = bytes(
        min(max(round(pixel + SHARPEN_AMOUNT * (pixel - soft)), 0), WHITE)
        for pixel, soft in zip(image.data, blurred)
    )
    return GrayImage(image.width, image.height, result)


@lru_cache(maxsize=1)
def prepare(image: GrayImage) -> GrayImage:
    """The picture ready for screening. Cached, as every change of a setting builds the blobs again."""
    return sharpened(stretched(image))
