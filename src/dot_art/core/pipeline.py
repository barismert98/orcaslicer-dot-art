"""From a saved job and a sliced file to the edited file."""
from __future__ import annotations

from dataclasses import dataclass

from . import art as art_module
from . import gcode, progress, splice
from .image import GrayImage

JOB_VERSION = 2  # 2: stationary blobs; a version 1 job holds the settings of drawn circles
LAYER_HEIGHT_TOLERANCE = 0.005
ART_LAYERS = 1


@dataclass(frozen=True)
class Outcome:
    text: str
    changed: bool
    message: str


def job_to_dict(params: art_module.Params, image: GrayImage) -> dict:
    return {
        "version": JOB_VERSION,
        "mode": params.mode,
        "params": params.to_dict(),
        "image": {"width": image.width, "height": image.height, "data": image.to_base64()},
    }


def job_from_dict(data: dict) -> tuple:
    raw = data["image"]
    return art_module.Params.from_dict(data["params"]), GrayImage.from_base64(raw["width"], raw["height"], raw["data"])


def _is_readable(job: dict) -> bool:
    return job.get("version") == JOB_VERSION and job.get("mode") == art_module.MODE_HALFTONE


def _check_slice(params: art_module.Params, top: splice.TopLayer) -> None:
    if abs(params.layer_height - top.height) > LAYER_HEIGHT_TOLERANCE:
        raise art_module.ArtError(
            f"The job was saved for a {params.layer_height:g} mm layer height but this slice uses {top.height:g} mm. "
            "Delete the base from the plate, press the save button again, and slice."
        )
    if top.tool + 1 != params.art_filament:
        raise art_module.ArtError(
            f"The art layer uses filament {top.tool + 1}, but the job asks for filament {params.art_filament}. "
            "Delete the base from the plate, press the save button again, and slice."
        )


def process(text: str, job: dict | None, get_config) -> Outcome:
    """Raises ArtError or ValueError when the base matches but the dots cannot be built."""
    if job is None:
        return Outcome(text, False, "No saved job; G-code left as it is.")
    if splice.is_done(text):
        return Outcome(text, False, "Already processed.")
    if not _is_readable(job):
        return Outcome(text, False, "The saved job is from another version, so the top layer stays solid. Press the save button in the Dot Art tab and slice again.")
    params, image = job_from_dict(job)
    lines = text.split("\n")
    try:
        top = splice.locate(lines, ART_LAYERS)
        splice.check_base(top, *params.base_outline.extents())
    except splice.NotPlaceholder as reason:
        return Outcome(text, False, f"Not the Dot Art base: {reason}. G-code left as it is.")
    _check_slice(params, top)
    machine = art_module.machine_from_config(get_config, top.tool)
    art = art_module.build(params, image, machine)
    base_top = top.z - top.height
    block = gcode.emit(art.dots, art.styles, machine, top.center[0], top.center[1], base_top, top.relative_e, top.debt_start, top.e_end)
    summary = art_module.stats(art, machine)
    message = (
        f"Replaced the top layer with {summary['dots']:,} blobs on the base at Z{base_top:g}, about {summary['time_s'] / 60:.0f} min. "
        "OrcaSlicer's own time and filament totals still count the plain layer."
    )
    return Outcome("\n".join(progress.spliced(lines, top, block, machine.travel_acceleration)), True, message)
