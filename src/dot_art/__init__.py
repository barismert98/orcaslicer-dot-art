"""Dot Art for OrcaSlicer 2.5."""
import json
import os
import re

import orca

from . import plate
from .core import art as art_module
from .core import pipeline, placeholder, preview
from .core.image import GrayImage
from .ui import PAGE_HTML

JOB_FILE = "job.json"
STATUS_FILE = "last_run.json"
BASE_NAME = "dot_art_base"
SLICING_STEP_NAME = "Dot Art G-code"
DEFAULT_LAYER_HEIGHT = 0.2
TARGET_PRINTER = "Bambu Lab X1 Carbon"


def storage_path(name):
    return os.path.join(orca.host.plugin.storage(), name)


def read_json(name):
    try:
        with open(storage_path(name), encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None


def write_json(name, data):
    with open(storage_path(name), "w", encoding="utf-8") as handle:
        json.dump(data, handle)


def preset_value(key):
    try:
        return orca.host.preset_bundle().full_config_value(key)
    except (RuntimeError, KeyError):
        return None


def current_layer_height():
    try:
        return float(preset_value("layer_height"))
    except (TypeError, ValueError):
        return DEFAULT_LAYER_HEIGHT


def stack_heights(base_layers, layer_height):
    """Thickness of the base, the art layer and the whole print, given the slicer's first layer."""
    try:
        first = float(preset_value("initial_layer_print_height"))
    except (TypeError, ValueError):
        first = layer_height
    base = first + (base_layers - 1) * layer_height
    return {"base": base, "art": layer_height, "total": base + layer_height}


def printer_state():
    return {
        "nozzle": art_module.machine_from_config(preset_value).nozzle,
        "layer_height": current_layer_height(),
        "model": str(preset_value("printer_model") or ""),
        "target": TARGET_PRINTER,
        "supported_nozzle": art_module.SUPPORTED_NOZZLE,
    }


def slicing_step_selected():
    return SLICING_STEP_NAME in str(preset_value("slicing_pipeline_plugin") or "")


def prime_tower_on():
    """True or False from the presets; None when the setting cannot be read."""
    value = preset_value("enable_prime_tower")
    return None if value is None else str(value) not in ("0", "false")


def filament_slots():
    """The project's filaments, in slot order; slot numbers start at 1."""
    try:
        names = list(orca.host.preset_bundle().current_filament_preset_names())
    except (RuntimeError, AttributeError):
        names = []
    colors = re.findall(r"#[0-9A-Fa-f]{6}", str(preset_value("filament_colour") or ""))
    count = max(len(names), len(colors), 1)
    return [
        {
            "slot": index + 1,
            "name": names[index] if index < len(names) else f"Filament {index + 1}",
            "color": colors[index] if index < len(colors) else "#808080",
        }
        for index in range(count)
    ]


def running_version():
    return str(orca.host.app_info()["version"])


def base_on_plate():
    try:
        objects = orca.host.model().objects()
    except RuntimeError:
        return False
    return any(BASE_NAME in (obj.input_file or obj.name or "") for obj in objects)


def live_state():
    """What the checklist shows: read from the presets each time, never remembered."""
    return {"printer": printer_state(), "selected": slicing_step_selected(), "filaments": filament_slots(), "tower": prime_tower_on()}


def image_from_message(raw):
    return GrayImage.from_base64(raw["width"], raw["height"], raw["data"]) if raw else None


class DotArtPage(orca.pages.PagesPluginCapabilityBase):
    def get_name(self):
        return "Dot Art"

    def get_ui(self):
        return PAGE_HTML

    def get_icon(self):
        """OrcaSlicer strips the extension, adds .svg and uses an existing path as it is."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.svg").replace("\\", "/")

    def on_message(self, data):
        handlers = {"init": self._init, "preview": self._preview, "save": self._save, "state": self._state}
        handler = handlers.get(data.get("cmd"))
        if handler is None:
            return
        try:
            handler(data)
        except (art_module.ArtError, ValueError, OSError) as error:
            self.post_message({"type": "error", "message": str(error)})

    def _init(self, _data):
        saved = (read_json(JOB_FILE) or {}).get("params")
        self.post_message({"type": "init", "params": art_module.opening_params(preset_value, saved), **live_state(), "status": read_json(STATUS_FILE)})

    def _state(self, _data):
        self.post_message({"type": "state", **live_state(), "status": read_json(STATUS_FILE)})

    def _build(self, data):
        """Layer height and nozzle always come from the presets, which slice the base."""
        machine = art_module.machine_from_config(preset_value)
        layer_height = current_layer_height()
        params = art_module.Params.from_dict({**data["params"], "layer_height": layer_height, "nozzle": machine.nozzle})
        slots = len(filament_slots())
        if max(params.base_filament, params.art_filament) > slots:
            raise art_module.ArtError(f"This project has {slots} filament(s). Add a second one in the filament list first.")
        image = image_from_message(data.get("image"))
        return params, image, machine, art_module.build(params, image, machine)

    def _preview(self, data):
        params, _image, machine, art = self._build(data)
        self.post_message({
            "type": "preview",
            "dots": preview.encode(art),
            "stats": art_module.stats(art, machine),
            "stack": stack_heights(params.base_layers, params.layer_height),
            **live_state(),
        })

    def _save(self, data):
        params, image, machine, _art = self._build(data)
        stack = stack_heights(params.base_layers, params.layer_height)
        base = {
            "width": params.base_width,
            "height": params.base_height,
            "total": stack["total"],
            "filaments": [params.base_filament, params.art_filament],
            "shape": params.shape,
        }
        previous = read_json(JOB_FILE) or {}
        write_json(JOB_FILE, {**pipeline.job_to_dict(params, image), "base": base})
        content = placeholder.two_filament_3mf(
            params.base_outline.points,
            stack["base"],
            stack["total"],
            params.base_filament,
            params.art_filament,
            ((machine.bed[0] + machine.bed[2]) / 2, (machine.bed[1] + machine.bed[3]) / 2),
            running_version(),
        )
        path = storage_path(BASE_NAME + ".3mf")
        with open(path, "wb") as handle:
            handle.write(content)
        if base_on_plate():
            state = "present" if previous.get("base") == base else "stale"
        else:
            state = "added" if plate.add_to_plate(path) else "manual"
        self.post_message({"type": "saved", "path": path, "plate": state})


class DotArtSlicing(orca.slicing.SlicingPipelineCapabilityBase):
    def get_name(self):
        return SLICING_STEP_NAME

    def execute(self, ctx):
        if ctx.step != orca.slicing.Step.psGCodePostProcess:
            return orca.ExecutionResult.success("")
        try:
            with open(ctx.gcode_path, encoding="utf-8", newline="") as handle:
                text = handle.read()
            outcome = pipeline.process(text, read_json(JOB_FILE), ctx.config_value)
            if outcome.changed:
                with open(ctx.gcode_path, "w", encoding="utf-8", newline="") as handle:
                    handle.write(outcome.text)
        except (art_module.ArtError, ValueError, OSError) as error:
            write_json(STATUS_FILE, {"ok": False, "message": str(error)})
            return orca.ExecutionResult.failure(orca.PluginResult.RecoverableError, f"Dot Art: {error}")
        write_json(STATUS_FILE, {"ok": True, "changed": outcome.changed, "message": outcome.message})
        return orca.ExecutionResult.success(outcome.message)


@orca.plugin
class DotArtPlugin(orca.base):
    def register_capabilities(self):
        orca.register_capability(DotArtPage)
        orca.register_capability(DotArtSlicing)
