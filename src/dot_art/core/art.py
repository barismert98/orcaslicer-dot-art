"""From job settings and a picture to the ordered dots of the art layer.

Halftone is one mode behind the family's shape: settings in, a path out. Its path is a
list of dots with a volume each (DECISIONS.md records this known difference).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, fields, replace
from typing import Callable

from . import estimate, gcode, halftone, tone_prep
from . import shape as frame
from .image import GrayImage, tone

MODE_HALFTONE = "halftone"
SUPPORTED_NOZZLE = 0.4  # the dot sizes and flows in this version were chosen for this nozzle
NOZZLE_TOLERANCE = 0.001
MIN_ART_SIZE = 10.0
MIN_PITCH, MAX_PITCH = 0.6, 12.0  # the lower bound is for small blobs; bigger ones are limited by `_smallest_pitch`
PITCH_STEP, PITCH_DIGITS = 0.1, 1  # the Spacing field's step, so the limit shown is a value the field can hold
MIN_BLOB_DIAMETER = 0.4  # the nozzle's bore: nothing smaller can form
MAX_BLOB_DIAMETER = 8.0  # 67 mm3 from one spot; big blobs are the point, and a print has yet to show the real ceiling
MIN_DOT_HEIGHT, MAX_DOT_HEIGHT = 0.15, 0.6  # under about half the bore's width the flow is choked
MIN_DOME_RATIO, MAX_DOME_RATIO = 0.1, 0.6
MIN_FLOW, MAX_FLOW = 0.2, 10.0  # mm3/s
MAX_DWELL = 0.5  # s
MIN_MARGIN = 1.5  # a blob's radius may reach this far past the art area; larger blobs need a wider margin
MAX_RETRACT = 2.0  # the X1C's direct drive needs no more
MIN_LIFT, MAX_LIFT = 0.1, 1.0  # the nozzle must clear the blobs it has already laid
ESTIMATE_Z = 1.0  # any height: the time estimate only needs moves relative to the art layer
MIN_CONTRAST, MAX_CONTRAST = 0.5, 3.0  # 3 already clips two thirds of the tones; 0.5 squeezes them into the middle half
MIN_GAMMA, MAX_GAMMA = 0.3, 3.0  # these move mid-gray to 0.81 and 0.13
MAX_DROP_COVERAGE = 0.5
MIN_DARK_BOOST, MAX_DARK_BOOST = 1.0, 1.6
ABSENT_FROM_OLD_JOBS = {"auto_tone": False, "shape": frame.RECTANGLE}  # a job saved before these existed must print as it did


class ArtError(Exception):
    """Settings or a slice that the art cannot be built from; the message is for the user."""


@dataclass(frozen=True)
class Params:
    mode: str = MODE_HALFTONE
    width: float = 100.0  # big blobs need a large picture to resolve anything
    height: float = 100.0
    margin: float = 3.0
    base_layers: int = 5
    base_filament: int = 1
    art_filament: int = 2
    pitch: float = 3.2
    min_diameter: float = 0.6
    max_diameter: float = 3.0
    drop_coverage: float = 0.06
    dark_boost: float = 1.25
    dot_height: float = 0.3
    dome_ratio: float = halftone.DOME_RATIO
    retract: float = 0.8
    lift: float = 0.3
    flow: float = 4.0
    dwell: float = 0.1
    invert: bool = False
    contrast: float = 1.0
    gamma: float = 1.0
    auto_tone: bool = True
    shape: str = frame.RECTANGLE
    layer_height: float = 0.2
    nozzle: float = SUPPORTED_NOZZLE

    def __post_init__(self) -> None:
        object.__setattr__(self, "height", frame.art_size(self.shape, self.width, self.height)[1])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Params":
        known = {field.name: field for field in fields(cls)}
        values = dict(ABSENT_FROM_OLD_JOBS)
        for key, value in data.items():
            if key not in known:
                continue
            if value is None or value != value:  # an emptied number box arrives as null or NaN
                raise ArtError(f"{key.replace('_', ' ').capitalize()} is empty.")
            kind = type(getattr(cls(), key))
            values[key] = kind(value)
        return cls(**values)

    @property
    def art_outline(self) -> frame.Outline:
        return frame.art_outline(self.shape, self.width, self.height)

    @property
    def base_outline(self) -> frame.Outline:
        return frame.base_outline(self.shape, self.width, self.height, self.margin)

    @property
    def base_width(self) -> float:
        return self.base_outline.width

    @property
    def base_height(self) -> float:
        return self.base_outline.height

    @property
    def screen(self) -> halftone.Screen:
        return halftone.Screen(self.pitch, self.min_diameter, self.max_diameter, self.drop_coverage, self.dark_boost)

    @property
    def style(self) -> gcode.Style:
        return gcode.Style(retract=self.retract, lift=self.lift, flow=self.flow, dwell=self.dwell)


@dataclass(frozen=True)
class Art:
    params: Params
    dots: list
    styles: list


def machine_from_config(get: Callable[[str], object], tool: int = 0) -> gcode.Machine:
    """Read a Machine from a resolved config getter; missing keys keep their defaults."""
    base = gcode.Machine()

    def number(key: str, default: float) -> float:
        raw = get(key)
        if raw in (None, ""):
            return default
        parts = str(raw).split(",")
        try:
            return float(parts[min(tool, len(parts) - 1)])
        except ValueError:
            return default

    bed = base.bed
    area = get("printable_area")
    if area:
        xs, ys = zip(*(tuple(float(c) for c in p.split("x")) for p in str(area).split(",")))
        bed = (min(xs), min(ys), max(xs), max(ys))
    return gcode.Machine(
        travel_speed=number("travel_speed", base.travel_speed),
        travel_acceleration=number("travel_acceleration", base.travel_acceleration),
        retract_speed=number("retraction_speed", base.retract_speed),
        deretract_speed=number("deretraction_speed", 0.0) or number("retraction_speed", base.deretract_speed),
        exit_retract=number("retraction_length", base.exit_retract),
        filament_diameter=number("filament_diameter", base.filament_diameter),
        flow_ratio=number("filament_flow_ratio", base.flow_ratio),
        max_volumetric=number("filament_max_volumetric_speed", base.max_volumetric),
        nozzle=number("nozzle_diameter", base.nozzle),
        bed=bed,
    )


def opening_params(get: Callable[[str], object], saved: dict | None) -> dict:
    """The settings a freshly opened tab shows.

    Stringing is left to each user's own tuning, so Retraction starts from their preset. A
    saved value is theirs and stays. `saved` is the params of the saved job, if there is one.
    """
    params = Params()
    retract = (saved or {}).get("retract")
    if retract is None:
        preset = machine_from_config(get, params.art_filament - 1).exit_retract
        retract = min(max(preset, 0.0), MAX_RETRACT)
    return replace(params, retract=float(retract)).to_dict()


def _smallest_pitch(params: Params) -> float:
    densest = halftone.densest_pitch(params.max_diameter, params.dot_height, params.dome_ratio)
    return max(MIN_PITCH, round(math.ceil(densest / PITCH_STEP) * PITCH_STEP, PITCH_DIGITS))  # 14 * 0.1 is just above 1.4


def _validate_blobs(params: Params) -> None:
    if not MIN_BLOB_DIAMETER <= params.min_diameter <= params.max_diameter <= MAX_BLOB_DIAMETER:
        raise ArtError(f"Blob sizes must run from at least {MIN_BLOB_DIAMETER:g} mm up to at most {MAX_BLOB_DIAMETER:g} mm, smallest first.")
    if not MIN_DOT_HEIGHT <= params.dot_height <= MAX_DOT_HEIGHT:
        raise ArtError(f"Nozzle height must be between {MIN_DOT_HEIGHT:g} and {MAX_DOT_HEIGHT:g} mm.")
    if not MIN_DOME_RATIO <= params.dome_ratio <= MAX_DOME_RATIO:
        raise ArtError(f"Dome height must be between {MIN_DOME_RATIO * 100:g}% and {MAX_DOME_RATIO * 100:g}% of the blob's width.")
    smallest_pitch = _smallest_pitch(params)
    if not smallest_pitch <= params.pitch <= MAX_PITCH:
        raise ArtError(f"Dot spacing must be at least {smallest_pitch:.1f} mm for {params.max_diameter:g} mm blobs, or the nozzle ends up inside the filament, and at most {MAX_PITCH:g} mm.")
    if not MIN_FLOW <= params.flow <= MAX_FLOW:
        raise ArtError(f"Blob flow must be between {MIN_FLOW:g} and {MAX_FLOW:g} mm3/s.")
    if not 0 <= params.dwell <= MAX_DWELL:
        raise ArtError(f"The hold after a blob must be at most {MAX_DWELL * 1000:g} ms.")


def _validate_tone(params: Params) -> None:
    if not MIN_CONTRAST <= params.contrast <= MAX_CONTRAST:
        raise ArtError(f"Contrast must be between {MIN_CONTRAST:g} and {MAX_CONTRAST:g}.")
    if not MIN_GAMMA <= params.gamma <= MAX_GAMMA:
        raise ArtError(f"Gamma must be between {MIN_GAMMA:g} and {MAX_GAMMA:g}.")
    if not 0 <= params.drop_coverage <= MAX_DROP_COVERAGE:
        raise ArtError(f"Skip tones below must be between 0 and {MAX_DROP_COVERAGE * 100:g}%.")
    if not MIN_DARK_BOOST <= params.dark_boost <= MAX_DARK_BOOST:
        raise ArtError(f"Dark tone extra must be between 0 and {(MAX_DARK_BOOST - MIN_DARK_BOOST) * 100:.0f}%.")


def validate(params: Params, machine: gcode.Machine) -> None:
    if params.mode != MODE_HALFTONE:
        raise ArtError(f"Unknown mode: {params.mode}")
    if params.shape not in frame.SHAPES:
        raise ArtError(f"Unknown frame shape: {params.shape}")
    if min(params.width, params.height) < MIN_ART_SIZE:
        raise ArtError(f"The art must be at least {MIN_ART_SIZE:g} mm wide and tall.")
    smallest_margin = max(MIN_MARGIN, params.max_diameter / 2)
    if params.margin < smallest_margin:
        raise ArtError(f"The margin must be at least {smallest_margin:g} mm, or the largest blobs hang off the base.")
    _validate_blobs(params)
    _validate_tone(params)
    if not 0 <= params.retract <= MAX_RETRACT:
        raise ArtError(f"Retraction must be between 0 and {MAX_RETRACT:g} mm.")
    if not MIN_LIFT <= params.lift <= MAX_LIFT:
        raise ArtError(f"Lift must be between {MIN_LIFT:g} and {MAX_LIFT:g} mm.")
    if params.base_layers < 1:
        raise ArtError("The base needs at least one layer.")
    if params.base_filament == params.art_filament:
        raise ArtError("Choose two different filaments, one for the base and one for the dots.")
    bed_width, bed_depth = machine.bed[2] - machine.bed[0], machine.bed[3] - machine.bed[1]
    if params.base_width > bed_width or params.base_height > bed_depth:
        raise ArtError(f"The base is {params.base_width:g} x {params.base_height:g} mm, larger than the {bed_width:g} x {bed_depth:g} mm bed.")
    if abs(machine.nozzle - SUPPORTED_NOZZLE) > NOZZLE_TOLERANCE:
        raise ArtError(f"Dot Art is tuned for a {SUPPORTED_NOZZLE:g} mm nozzle; this printer preset uses {machine.nozzle:g} mm.")


def _coverage_field(params: Params, image: GrayImage) -> halftone.ToneField:
    def coverage(x: float, y: float) -> float:
        brightness = tone(image.sample(x / params.width, 1.0 - y / params.height), params.contrast, params.gamma)
        return brightness if params.invert else 1.0 - brightness

    return coverage


def _lattice_center(params: Params) -> tuple:
    """Where the art area's middle falls: the lattice rarely ends exactly on the far edges."""
    points = halftone.lattice(params.width, params.height, params.pitch)
    return max(x for x, _ in points) / 2, max(y for _, y in points) / 2


def build(params: Params, image: GrayImage | None, machine: gcode.Machine) -> Art:
    """The dots in print order, centered on the origin."""
    validate(params, machine)
    if image is None:
        raise ArtError("Pick a picture first.")
    screen = params.screen
    picture = tone_prep.prepare(image) if params.auto_tone else image
    flat = halftone.build(_coverage_field(params, picture), params.width, params.height, screen, params.dot_height, dome_ratio=params.dome_ratio)
    if not flat:
        raise ArtError("This picture has nothing dark enough to print. Try Invert, or more contrast.")
    middle_x, middle_y = _lattice_center(params)
    centered = [replace(d, x=d.x - middle_x, y=d.y - middle_y) for d in flat]
    outline = params.art_outline  # after centering: the margin already keeps a blob centered in the art on the base
    kept = [d for d in centered if outline.contains(d.x, d.y)]
    if not kept:
        raise ArtError("This picture has nothing dark enough inside the frame. Try another shape or more contrast.")
    return Art(params, halftone.order_small_to_large(kept, screen), [params.style])


def stats(art: Art, machine: gcode.Machine) -> dict:
    """Real numbers from the moves the print would make."""
    block = gcode.emit(art.dots, art.styles, machine, 0.0, 0.0, ESTIMATE_Z, True)
    totals = estimate.estimate(block, machine.travel_acceleration)
    return {
        "dots": len(art.dots),
        "time_s": totals.seconds,
        "retractions": totals.retractions,
        "travel_mm": totals.travel_mm,
        "filament_mm": totals.filament_mm,
    }
