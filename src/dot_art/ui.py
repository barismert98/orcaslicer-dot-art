"""The page shown in the Dot Art tab."""
from .oneline_ui import CSS

_PAGE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
/*ONELINE_CSS*/
.app { height: 100vh; display: grid; gap: var(--ol-pad); padding: var(--ol-pad);
  grid-template-columns: 340px minmax(0, 1fr) 300px; grid-template-rows: minmax(0, 1fr) auto;
  grid-template-areas: "controls stage status" "controls stage actions"; }
.controls { grid-area: controls; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; min-height: 0; }
.stagewrap { grid-area: stage; display: flex; flex-direction: column; gap: 12px; min-height: 0; min-width: 0; }
.status { grid-area: status; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; min-height: 0; }
.actions { grid-area: actions; display: grid; gap: var(--ol-gap); }
.stage { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: var(--ol-pad); flex: 1; min-height: 0; }
.source { overflow-y: auto; }
#crop { width: 100%; display: block; border-radius: var(--ol-radius); background: var(--ol-surface-2); cursor: move; touch-action: none; }
.result { padding: 12px; display: flex; flex-direction: column; min-height: 0; min-width: 0; }
.result .ol-preview { flex: 1; padding: 12px; overflow: hidden; }
#c { display: block; }
#file { position: absolute; width: 1px; height: 1px; opacity: 0; }
#fileName { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#path { word-break: break-all; }
@media (max-width: 1240px) {
  .app { grid-template-columns: 320px minmax(0, 1fr); grid-template-rows: minmax(0, 1fr) auto auto;
    grid-template-areas: "controls stage" "controls status" "controls actions"; }
  .status { flex-direction: row; max-height: 190px; }
  .status > * { flex: 1; min-width: 0; overflow-y: auto; }
  .stage { grid-template-columns: 200px minmax(0, 1fr); }
}
@media (max-width: 760px) {
  .app { display: block; height: auto; min-height: 100%; }
  .controls, .status, .stagewrap { overflow: visible; margin-bottom: 12px; }
  .stage { grid-template-columns: minmax(0, 1fr); }
  .status { flex-direction: column; max-height: none; }
  .result .ol-preview { min-height: 320px; }
  .actions { position: sticky; bottom: 0; background: var(--orca-bg); padding: 8px 0; }
}
</style>
</head>
<body>
<form class="app" id="f" onsubmit="return false">
  <div class="controls">
    <h1>Dot Art</h1>
    <div class="ol-card">
      <h2>Filaments</h2>
      <label class="ol-field">Base <span class="ol-input ol-select"><i id="baseSwatch"></i><select id="base_filament"></select></span></label>
      <label class="ol-field">Dots <span class="ol-input ol-select"><i id="artSwatch"></i><select id="art_filament"></select></span></label>
    </div>
    <div class="ol-card">
      <h2>Size</h2>
      <fieldset class="ol-shapes">
        <legend>Frame shape</legend>
        <label><input type="radio" name="shape" value="square"><i class="square" aria-hidden="true"></i><span>Square</span></label>
        <label><input type="radio" name="shape" value="circle"><i class="circle" aria-hidden="true"></i><span>Circle</span></label>
        <label><input type="radio" name="shape" value="rectangle"><i class="rectangle" aria-hidden="true"></i><span>Rectangle</span></label>
        <label><input type="radio" name="shape" value="oval"><i class="oval" aria-hidden="true"></i><span>Oval</span></label>
        <label><input type="radio" name="shape" value="rounded_rectangle" aria-label="Rounded rectangle"><i class="rounded_rectangle" aria-hidden="true"></i><span>Rounded</span></label>
        <label><input type="radio" name="shape" value="hexagon"><i class="hexagon" aria-hidden="true"><svg viewBox="0 0 14 14"><polygon points="1,7 4,1.8 10,1.8 13,7 10,12.2 4,12.2"/></svg></i><span>Hexagon</span></label>
      </fieldset>
      <label class="ol-field"><span id="widthLabel">Art width</span> <span class="ol-input unit"><input id="width" type="number" step="1" min="10"><small>mm</small></span></label>
      <label class="ol-field" id="heightRow">Art height <span class="ol-input unit"><input id="height" type="number" step="1" min="10"><small>mm</small></span></label>
      <label class="ol-field">Base margin <span class="ol-input unit"><input id="margin" type="number" step="0.5" min="1.5"><small>mm</small></span></label>
      <label class="ol-field">Base layers <span class="ol-input"><input id="base_layers" type="number" step="1" min="1"></span></label>
      <div class="ol-stack" id="stackBar" hidden><i id="stackBase"></i><i id="stackArt"></i></div>
      <div class="ol-muted" id="stack"></div>
    </div>
    <div class="ol-card">
      <h2>Blobs</h2>
      <div class="ol-slider-row"><label for="pitch">Spacing</label><input class="ol-slider" id="pitch_slider" type="range" aria-label="Spacing" min="0.6" max="12" step="0.1"><span class="ol-input unit"><input id="pitch" type="number" min="0.6" max="12" step="0.1"><small>mm</small></span></div>
      <div class="ol-muted" id="spacingNote" role="status" hidden></div>
      <div class="ol-slider-row"><label for="min_diameter">Smallest blob</label><input class="ol-slider" id="min_diameter_slider" type="range" aria-label="Smallest blob" min="0.4" max="8" step="0.05"><span class="ol-input unit"><input id="min_diameter" type="number" min="0.4" max="8" step="0.05"><small>mm</small></span></div>
      <div class="ol-slider-row"><label for="max_diameter">Largest blob</label><input class="ol-slider" id="max_diameter_slider" type="range" aria-label="Largest blob" min="0.4" max="8" step="0.1"><span class="ol-input unit"><input id="max_diameter" type="number" min="0.4" max="8" step="0.1"><small>mm</small></span></div>
      <div class="ol-slider-row"><label for="drop_percent">Skip tones below</label><input class="ol-slider" id="drop_percent_slider" type="range" aria-label="Skip tones below" min="0" max="50" step="1"><span class="ol-input unit"><input id="drop_percent" type="number" min="0" max="50" step="1"><small>%</small></span></div>
      <div class="ol-slider-row"><label for="boost_percent">Dark tone extra</label><input class="ol-slider" id="boost_percent_slider" type="range" aria-label="Dark tone extra" min="0" max="60" step="5"><span class="ol-input unit"><input id="boost_percent" type="number" min="0" max="60" step="5"><small>%</small></span></div>
    </div>
    <details class="ol-card">
      <summary>Nozzle: height, flow, retraction, lift</summary>
      <label class="ol-field">Lowest height over base <span class="ol-input unit"><input id="dot_height" type="number" step="0.05" min="0.15" max="0.6"><small>mm</small></span></label>
      <label class="ol-field">Dome height <span class="ol-input unit"><input id="dome_percent" type="number" step="5" min="10" max="60"><small>% of width</small></span></label>
      <label class="ol-field">Blob flow <span class="ol-input unit"><input id="flow" type="number" step="0.5" min="0.2" max="10"><small>mm³/s</small></span></label>
      <label class="ol-field">Hold after blob <span class="ol-input unit"><input id="dwell_ms" type="number" step="10" min="0" max="500"><small>ms</small></span></label>
      <label class="ol-field">Retraction <span class="ol-input unit"><input id="retract" type="number" step="0.1" min="0" max="2"><small>mm</small></span></label>
      <label class="ol-field">Z lift <span class="ol-input unit"><input id="lift" type="number" step="0.05" min="0.1" max="1"><small>mm</small></span></label>
      <div class="ol-muted" style="margin-top:8px">Thin strings between dots usually mean the filament's retraction or temperature needs adjusting.</div>
    </details>
    <details class="ol-card">
      <summary>Tone: auto, invert, contrast, gamma</summary>
      <label class="ol-field">Auto tone <input id="auto_tone" type="checkbox"></label>
      <label class="ol-field">Invert <input id="invert" type="checkbox"></label>
      <div class="ol-slider-row"><label for="contrast">Contrast</label><input class="ol-slider" id="contrast_slider" type="range" aria-label="Contrast" min="0.5" max="3" step="0.1"><span class="ol-input"><input id="contrast" type="number" min="0.5" max="3" step="0.1"></span></div>
      <div class="ol-slider-row"><label for="gamma">Gamma</label><input class="ol-slider" id="gamma_slider" type="range" aria-label="Gamma" min="0.3" max="3" step="0.05"><span class="ol-input"><input id="gamma" type="number" min="0.3" max="3" step="0.05"></span></div>
    </details>
  </div>

  <div class="stagewrap">
    <div class="stage">
      <div class="ol-card source">
        <h2>Picture</h2>
        <canvas id="crop" width="540" height="540" title="Drag to move, scroll to zoom"></canvas>
        <div class="ol-muted" style="margin:8px 0 12px">Drag to move, scroll to zoom</div>
        <div class="ol-muted" id="fileName" style="margin-bottom:8px">No picture yet</div>
        <label class="ol-field">Zoom <span class="ol-input unit"><input id="zoom" type="number" step="0.1" min="1" max="8" value="1"><small>x</small></span></label>
        <label class="ol-field">Left / right <span class="ol-input unit"><input id="panx" type="number" step="5" min="-100" max="100" value="0"><small>%</small></span></label>
        <label class="ol-field">Up / down <span class="ol-input unit"><input id="pany" type="number" step="5" min="-100" max="100" value="0"><small>%</small></span></label>
        <label class="ol-button quiet" style="margin-top:12px;cursor:pointer" id="fileLabel">Choose a picture<input id="file" type="file" accept="image/*"></label>
      </div>
      <div class="ol-card result">
        <h2>The planned blobs, in your filament colors</h2>
        <div class="ol-preview" id="previewBox"><canvas id="c" width="10" height="10"></canvas></div>
      </div>
    </div>
    <div class="ol-metrics">
      <div class="ol-metric"><span class="ol-muted">Dots</span><b id="mDots">-</b></div>
      <div class="ol-metric"><span class="ol-muted">Dot layer time</span><b id="mTime">-</b></div>
      <div class="ol-metric"><span class="ol-muted">Retractions</span><b id="mRetract">-</b></div>
      <div class="ol-metric"><span class="ol-muted">Dot filament</span><b id="mFilament">-</b></div>
    </div>
  </div>

  <div class="status">
    <div class="ol-card">
      <h2>Before you slice</h2>
      <div id="checks"></div>
    </div>
    <div class="ol-card">
      <h2>Last slice</h2>
      <div class="ol-muted" id="lastSlice"></div>
    </div>
  </div>

  <div class="actions">
    <div class="ol-muted" id="msg"></div>
    <div class="ol-muted" id="path"></div>
    <button type="button" class="ol-button" id="save">Save job and add base to plate</button>
    <button type="button" class="ol-button quiet" id="refresh">Check last slice</button>
  </div>
</form>
<script>
var directFields = ["base_filament","art_filament","width","height","margin","base_layers","pitch","min_diameter","max_diameter","dot_height","flow","retract","lift","invert","auto_tone","contrast","gamma"];
var CROP_LONG_SIDE = 540, IMAGE_LONG_SIDE = 600, MANY_DOTS = 20000;
var NO_RESULT_TEXT = "No result yet. Bambu Lab printers: slice the base. Other printers: export the G-code. Then check here.";
var image = null, timer = null, ready = false, source = null, encodeTimer = null;
var filaments = [], filamentKey = "", printer = null, selected = null, tower = null, lastDots = null, dotCount = 0;
var send = function (m) { window.orca.postMessage(m); };
var el = function (i) { return document.getElementById(i); };

function msg(t, err) { var m = el("msg"); m.textContent = t || ""; m.className = err ? "ol-error" : "ol-muted"; }

function params() {
  var p = {};
  directFields.forEach(function (f) {
    var e = el(f);
    p[f] = e.type === "checkbox" ? e.checked : parseFloat(e.value);
  });
  p.drop_coverage = parseFloat(el("drop_percent").value) / 100;
  p.dark_boost = 1 + parseFloat(el("boost_percent").value) / 100;
  p.dwell = parseFloat(el("dwell_ms").value) / 1000;
  p.dome_ratio = parseFloat(el("dome_percent").value) / 100;
  p.shape = currentShape();
  return p;
}

function setParams(p) {
  directFields.forEach(function (f) {
    var e = el(f);
    if (e.type === "checkbox") e.checked = !!p[f]; else e.value = p[f];
  });
  el("drop_percent").value = Math.round(p.drop_coverage * 100);
  el("boost_percent").value = Math.round((p.dark_boost - 1) * 100);
  el("dwell_ms").value = Math.round(p.dwell * 1000);
  el("dome_percent").value = Math.round(p.dome_ratio * 100);
  wantedPitch = p.pitch;
  updateLimits();
  document.querySelector('input[name="shape"][value="' + p.shape + '"]').checked = true;
  sizes = { pair: { width: p.width, height: p.height }, single: null };
  heightTyped = false;
  showShapeFields();
}

var ONE_SIZE_HEIGHT_SHARE = { square: 1, circle: 1, hexagon: Math.sqrt(3) / 2 }, ROUNDED_CORNER_SHARE = 0.15;
var ONE_SIZE_LABEL = { square: "Art side", circle: "Art diameter", hexagon: "Across corners" };
var sizes = { pair: null, single: null }, heightTyped = false;

function currentShape() { return document.querySelector('input[name="shape"]:checked').value; }
function isOneSize() { return currentShape() in ONE_SIZE_HEIGHT_SHARE; }
function oneSizeHeight(width) { return width * ONE_SIZE_HEIGHT_SHARE[currentShape()]; }

function showShapeFields() {
  el("heightRow").hidden = isOneSize();
  el("widthLabel").textContent = ONE_SIZE_LABEL[currentShape()] || "Art width";
}

// Rectangle-family sizes and the single size are remembered apart, so 120 x 80 survives a trip to Circle.
function rememberSize() {
  var width = parseFloat(el("width").value), height = parseFloat(el("height").value);
  if (isNaN(width)) return;
  if (isOneSize()) { sizes.single = width; el("height").value = oneSizeHeight(width); }
  else if (!isNaN(height)) sizes.pair = { width: width, height: height };
}

function shapeChanged() {
  if (isOneSize()) {
    if (sizes.single === null) sizes.single = Math.min(sizes.pair.width, sizes.pair.height);
    el("width").value = sizes.single; el("height").value = oneSizeHeight(sizes.single);
  } else {
    el("width").value = sizes.pair.width; el("height").value = sizes.pair.height;
  }
  showShapeFields();
  moved();
  request();
}

function traceShape(g, wide, high) {
  var shape = currentShape();
  g.beginPath();
  if (shape === "circle" || shape === "oval") {
    g.ellipse(wide / 2, high / 2, wide / 2, high / 2, 0, 0, 2 * Math.PI);
  } else if (shape === "rounded_rectangle") {
    var r = ROUNDED_CORNER_SHARE * Math.min(wide, high);
    g.moveTo(r, 0); g.arcTo(wide, 0, wide, high, r); g.arcTo(wide, high, 0, high, r); g.arcTo(0, high, 0, 0, r); g.arcTo(0, 0, wide, 0, r);
    g.closePath();
  } else if (shape === "hexagon") {
    g.moveTo(0, high / 2); g.lineTo(wide / 4, 0); g.lineTo(3 * wide / 4, 0); g.lineTo(wide, high / 2); g.lineTo(3 * wide / 4, high); g.lineTo(wide / 4, high);
    g.closePath();
  } else {
    g.rect(0, 0, wide, high);
  }
}

// Only on the visible crop: the picture sent for screening stays whole, and Python drops the blobs outside.
function dimOutsideShape(g, wide, high) {
  if (currentShape() === "rectangle" || currentShape() === "square") return;
  traceShape(g, wide, high);
  g.rect(0, 0, wide, high);
  g.fillStyle = "rgba(0, 0, 0, 0.55)";
  g.fill("evenodd");
  traceShape(g, wide, high);
  g.strokeStyle = "rgba(255, 255, 255, 0.8)";
  g.lineWidth = 2;
  g.stroke();
}

var SLIDERS = { pitch: "mm", min_diameter: "mm", max_diameter: "mm", drop_percent: "%", boost_percent: "%", contrast: "", gamma: "" };
var LOWEST_BLOB = 0.4, HIGHEST_BLOB = 8, MOST_SPACING = 12, wantedPitch = null;
var PITCH_FLOOR = 0.6;
function smallestPitch(largest, lowestHeight, domeRatio) {
  var height = Math.max(lowestHeight, largest * domeRatio), radius = largest / 2;
  var volume = Math.PI * height / 6 * (3 * radius * radius + height * height);
  return Math.max(PITCH_FLOOR, Math.ceil(Math.sqrt(volume / height) / 0.1) / 10);
}

function setBounds(id, low, high) {
  // a range input clamps its value to its limits, so limits must be set before the value
  [el(id), el(id + "_slider")].forEach(function (e) { e.min = low; e.max = high; });
}

function showSlider(id) {
  var slider = el(id + "_slider"), value = el(id).value;
  if (isNaN(parseFloat(value))) return;
  slider.value = value;
  slider.setAttribute("aria-valuetext", (value + " " + SLIDERS[id]).trim());
}

function showSpacing(limit) {
  var shown = Math.max(wantedPitch, limit), note = el("spacingNote");
  el("pitch").value = shown;
  note.hidden = shown === wantedPitch;
  note.textContent = note.hidden ? "" : "Spacing raised to " + shown + " mm, the closest these blobs can be. It returns when the limit allows.";
}

function updateLimits() {
  var smallest = parseFloat(el("min_diameter").value), largest = parseFloat(el("max_diameter").value);
  var lowest = parseFloat(el("dot_height").value), dome = parseFloat(el("dome_percent").value);
  if ([smallest, largest, lowest, dome, wantedPitch].some(isNaN)) return;
  setBounds("min_diameter", LOWEST_BLOB, largest);
  setBounds("max_diameter", Math.ceil(smallest * 10) / 10, HIGHEST_BLOB);
  var limit = smallestPitch(largest, lowest, dome / 100);
  setBounds("pitch", limit, MOST_SPACING);
  showSpacing(limit);
  Object.keys(SLIDERS).forEach(showSlider);
}

function clampToLimits(id) {
  var e = el(id), value = parseFloat(e.value);
  if (!isNaN(value)) e.value = Math.min(parseFloat(e.max), Math.max(parseFloat(e.min), value));
}

function settled(id) {
  if (id === "pitch") wantedPitch = parseFloat(el(id).value);
  updateLimits();
}

function wireSlider(id) {
  el(id + "_slider").addEventListener("input", function () {
    el(id).value = el(id + "_slider").value;
    settled(id);
    request();
  });
  el(id).addEventListener("input", function () { showSlider(id); });
  el(id).addEventListener("change", function () { clampToLimits(id); settled(id); });
}

function wireLimitField(id) { el(id).addEventListener("change", updateLimits); }

function filamentAt(id) { return filaments[parseInt(el(id).value, 10) - 1]; }

function fillFilaments(list) {
  var key = JSON.stringify(list);
  if (key === filamentKey) return;
  filamentKey = key;
  ["base_filament", "art_filament"].forEach(function (id) {
    var e = el(id), keep = e.value;
    e.innerHTML = "";
    list.forEach(function (f) {
      var o = document.createElement("option");
      o.value = f.slot; o.textContent = f.slot + ": " + f.name;
      e.appendChild(o);
    });
    if (keep && parseInt(keep, 10) <= list.length) e.value = keep;
  });
  filaments = list;
  showFilaments();
}

function showFilaments() {
  var base = filamentAt("base_filament"), art = filamentAt("art_filament");
  if (base) { el("baseSwatch").style.background = base.color; el("stackBase").style.background = base.color; }
  if (art) { el("artSwatch").style.background = art.color; el("stackArt").style.background = art.color; }
  drawDots();
}

function luminance(hex) {
  var n = parseInt(hex.slice(1), 16);
  return 0.299 * (n >> 16 & 255) + 0.587 * (n >> 8 & 255) + 0.114 * (n & 255);
}

function check(done, title, detail) {
  var row = document.createElement("div"), mark = document.createElement("i"), body = document.createElement("div");
  row.className = done ? "ol-check" : "ol-check todo";
  mark.textContent = done ? "✓" : "!";
  body.textContent = title;
  if (detail) {
    var note = document.createElement("div");
    note.className = "ol-muted"; note.textContent = detail;
    body.appendChild(note);
  }
  row.appendChild(mark); row.appendChild(body);
  el("checks").appendChild(row);
}

function renderPrinterChecks() {
  if (!printer) return;
  var nozzleOk = Math.abs(printer.nozzle - printer.supported_nozzle) <= 0.001;
  check(nozzleOk, nozzleOk ? "Nozzle is " + printer.supported_nozzle + " mm" : "Use a " + printer.supported_nozzle + " mm nozzle",
    nozzleOk ? "" : "The printer preset has a " + printer.nozzle + " mm nozzle. The dots are tuned for " + printer.supported_nozzle + " mm.");
  if (printer.model && printer.model.indexOf(printer.target) < 0) check(false, "Not tested on this printer", "This version is tuned for the " + printer.target + ".");
}

function renderFilamentChecks() {
  var two = el("base_filament").value !== el("art_filament").value;
  check(two, two ? "Base and dots use different filaments" : "Choose two different filaments",
    two ? "" : "Add a second filament to the project if the list has only one.");
  if (two && tower !== null) {
    check(tower, tower ? "Prime tower is on" : "Turn on the prime tower",
      tower ? "" : "Without it the first blobs will print in the previous color. Process preset, Multimaterial, Prime tower: Enable.");
  }
  var base = filamentAt("base_filament"), art = filamentAt("art_filament");
  if (!two || !base || !art) return;
  var dark = luminance(art.color) < luminance(base.color), invert = el("invert").checked, good = dark !== invert;
  check(good, good ? "Tone suits the filament colors" : (invert ? "Turn Invert off" : "Turn Invert on"),
    good ? "" : (invert ? "The dots are darker than the base." : "The dots are lighter than the base, so the picture would be a negative."));
}

function renderChecks() {
  el("checks").innerHTML = "";
  check(!!image, image ? "Picture loaded" : "Pick a picture");
  renderPrinterChecks();
  renderFilamentChecks();
  if (selected !== null) {
    check(selected, selected ? "Slicing step is selected" : "Select the slicing step",
      selected ? "" : "Without it the top layer prints solid. Process preset, Others, Slicing Pipeline Plugin: add Dot Art G-code.");
  }
  if (dotCount > MANY_DOTS) check(false, "Very many dots", "Each blob retracts once, and a picture this large has not been test printed. Try a small one first.");
}

function renderStatus(status) {
  var e = el("lastSlice");
  if (!status) { e.textContent = NO_RESULT_TEXT; e.className = "ol-muted"; return; }
  e.textContent = status.message;
  e.className = status.ok ? "ol-muted" : "ol-error";
}

function renderStack(stack) {
  el("stack").textContent = "Base " + stack.base.toFixed(2) + " mm + dots " + stack.art.toFixed(2) + " mm = " + stack.total.toFixed(2) + " mm";
  el("stackBar").hidden = false;
  el("stackBase").style.width = (stack.base / stack.total * 100) + "%";
  el("stackArt").style.width = (stack.art / stack.total * 100) + "%";
}

function renderMetrics(s) {
  el("mDots").textContent = s.dots.toLocaleString("en-US");
  var minutes = Math.round(s.time_s / 60);
  el("mTime").textContent = minutes >= 60 ? Math.floor(minutes / 60) + " h " + (minutes % 60) + " min" : minutes + " min";
  el("mRetract").textContent = s.retractions.toLocaleString("en-US");
  el("mFilament").textContent = (s.filament_mm / 1000).toFixed(1) + " m";
}

function request() {
  if (!ready) return;
  clearTimeout(timer);
  timer = setTimeout(function () {
    if (!image) { msg("Pick a picture to see the dots."); return; }
    msg("Computing...");
    send({ cmd: "preview", params: params(), image: image });
  }, 350);
}

function decodeDots(dots) {
  var s = atob(dots.data), out = new Uint16Array(s.length / 2);
  for (var i = 0; i < out.length; i++) out[i] = s.charCodeAt(i * 2) | s.charCodeAt(i * 2 + 1) << 8;
  return { width: dots.width, height: dots.height, units: dots.units, outline: dots.outline, values: out };
}

function drawDots() {
  if (!lastDots) return;
  var box = el("previewBox"), room = Math.max(box.clientWidth - 24, 40), roomHigh = Math.max(box.clientHeight - 24, 40);
  var cssScale = Math.min(room / lastDots.width, roomHigh / lastDots.height);
  var ratio = window.devicePixelRatio || 1, scale = cssScale * ratio, c = el("c");
  c.width = Math.round(lastDots.width * scale); c.height = Math.round(lastDots.height * scale);
  c.style.width = (c.width / ratio) + "px"; c.style.height = (c.height / ratio) + "px";
  var base = filamentAt("base_filament"), art = filamentAt("art_filament"), g = c.getContext("2d");
  g.beginPath();
  lastDots.outline.forEach(function (p) { g.lineTo(p[0] * scale, c.height - p[1] * scale); });
  g.closePath();
  g.fillStyle = base ? base.color : "#f4f1e8";
  g.fill();
  g.strokeStyle = "rgba(128, 128, 128, 0.7)";
  g.lineWidth = ratio;
  g.stroke();
  g.fillStyle = art ? art.color : "#14213d";
  g.beginPath();
  var v = lastDots.values, unit = scale / lastDots.units;
  for (var i = 0; i < v.length; i += 3) {
    var x = v[i] * unit, y = c.height - v[i + 1] * unit, r = v[i + 2] * unit / 2;
    g.moveTo(x + r, y); g.arc(x, y, r, 0, 6.2832);
  }
  g.fill();
}
window.addEventListener("resize", drawDots);

function applyState(m) {
  if (m.filaments) fillFilaments(m.filaments);
  if (m.printer) printer = m.printer;
  if (typeof m.selected === "boolean") selected = m.selected;
  if (m.tower !== undefined) tower = m.tower;
  renderChecks();
}

var saveNotes = {
  added: "Saved. The base is being added to the plate; slice it when it appears.",
  present: "Saved. The base is already on the plate; slice it. If Slice is not active, move the base a little first.",
  stale: "Saved, but the base on the plate has an old size. Delete it from the plate and press the button again.",
  manual: "Saved. The base could not be added automatically; drop this file on the plate:"
};

window.orca.onMessage(function (m) {
  if (m.type === "init") {
    fillFilaments(m.filaments); setParams(m.params); showFilaments(); ready = true; msg("");
    applyState(m); renderStatus(m.status); request();
  } else if (m.type === "state") {
    applyState(m); renderStatus(m.status);
  } else if (m.type === "preview") {
    lastDots = decodeDots(m.dots); dotCount = m.dots.count;
    msg(""); renderStack(m.stack); renderMetrics(m.stats); applyState(m); drawDots();
  } else if (m.type === "saved") {
    msg(saveNotes[m.plate], m.plate === "stale");
    el("path").textContent = m.plate === "manual" ? m.path : "";
  } else if (m.type === "error") {
    msg(m.message, true);
  }
});

function num(id, low, high, fallback) {
  var v = parseFloat(el(id).value);
  return isNaN(v) ? fallback : Math.min(high, Math.max(low, v));
}

function artAspect() { return num("width", 1, 1000, 1) / num("height", 1, 1000, 1); }

function cropBox() {
  var aspect = artAspect(), zoom = num("zoom", 1, 8, 1);
  var fitsWide = source.width / source.height > aspect;
  var high = (fitsWide ? source.height : source.width / aspect) / zoom, wide = high * aspect;
  var freeX = (source.width - wide) / 2, freeY = (source.height - high) / 2;
  return { wide: wide, high: high, freeX: freeX, freeY: freeY,
    x: freeX + freeX * num("panx", -100, 100, 0) / 100, y: freeY + freeY * num("pany", -100, 100, 0) / 100 };
}

function drawCrop() {
  if (!source) return;
  var c = el("crop"), aspect = artAspect();
  c.width = aspect >= 1 ? CROP_LONG_SIDE : Math.round(CROP_LONG_SIDE * aspect);
  c.height = aspect >= 1 ? Math.round(CROP_LONG_SIDE / aspect) : CROP_LONG_SIDE;
  var b = cropBox();
  var g = c.getContext("2d");
  g.drawImage(source, b.x, b.y, b.wide, b.high, 0, 0, c.width, c.height);
  dimOutsideShape(g, c.width, c.height);
}

function encode() {
  clearTimeout(encodeTimer); encodeTimer = null;
  if (!source) return;
  var b = cropBox(), shrink = Math.min(IMAGE_LONG_SIDE / Math.max(b.wide, b.high), 1);
  var wide = Math.max(1, Math.round(b.wide * shrink)), high = Math.max(1, Math.round(b.high * shrink));
  var c = document.createElement("canvas"); c.width = wide; c.height = high;
  var g = c.getContext("2d");
  g.drawImage(source, b.x, b.y, b.wide, b.high, 0, 0, wide, high);
  var d = g.getImageData(0, 0, wide, high).data, out = new Uint8Array(wide * high);
  for (var i = 0; i < out.length; i++) out[i] = Math.round(0.299 * d[i * 4] + 0.587 * d[i * 4 + 1] + 0.114 * d[i * 4 + 2]);
  var s = ""; for (var k = 0; k < out.length; k += 8192) s += String.fromCharCode.apply(null, out.subarray(k, k + 8192));
  image = { width: wide, height: high, data: btoa(s) };
  renderChecks();
  request();
}

function moved() {
  drawCrop();
  clearTimeout(encodeTimer);
  encodeTimer = setTimeout(encode, 200);
}

// before the listeners below, so a one-size shape's height follows its width first
["width", "height"].forEach(function (id) { el(id).addEventListener("input", rememberSize); });
el("height").addEventListener("input", function () { heightTyped = true; });
document.querySelectorAll('input[name="shape"]').forEach(function (radio) { radio.addEventListener("change", shapeChanged); });
["zoom", "panx", "pany", "width", "height"].forEach(function (id) { el(id).addEventListener("input", moved); });

var drag = null;
el("crop").addEventListener("pointerdown", function (ev) {
  if (!source) return;
  drag = { x: ev.clientX, y: ev.clientY, panx: num("panx", -100, 100, 0), pany: num("pany", -100, 100, 0) };
  el("crop").setPointerCapture(ev.pointerId);
});
el("crop").addEventListener("pointermove", function (ev) {
  if (!drag) return;
  var b = cropBox(), scale = b.wide / el("crop").clientWidth;
  if (b.freeX > 0) el("panx").value = Math.round(Math.min(100, Math.max(-100, drag.panx - (ev.clientX - drag.x) * scale / b.freeX * 100)));
  if (b.freeY > 0) el("pany").value = Math.round(Math.min(100, Math.max(-100, drag.pany - (ev.clientY - drag.y) * scale / b.freeY * 100)));
  moved();
});
el("crop").addEventListener("pointerup", function () { drag = null; });
el("crop").addEventListener("wheel", function (ev) {
  if (!source) return;
  ev.preventDefault();
  el("zoom").value = (Math.min(8, Math.max(1, num("zoom", 1, 8, 1) * (ev.deltaY < 0 ? 1.1 : 0.9)))).toFixed(2);
  moved();
}, { passive: false });

["base_filament", "art_filament"].forEach(function (id) { el(id).addEventListener("change", showFilaments); });

el("file").addEventListener("change", function (ev) {
  var file = ev.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function () {
    var img = new Image();
    img.onload = function () {
      source = img;
      el("fileName").textContent = file.name;
      el("fileLabel").firstChild.textContent = "Choose another picture";
      el("zoom").value = 1; el("panx").value = 0; el("pany").value = 0;
      if (!isOneSize() && !heightTyped) {
        el("height").value = Math.round(num("width", 10, 1000, 60) * img.height / img.width);
        rememberSize();
      }
      drawCrop(); encode();
    };
    img.onerror = function () { msg("This image could not be read.", true); };
    img.src = reader.result;
  };
  reader.readAsDataURL(file);
});

// wired first, so a typed number is clamped before the preview below asks for it
Object.keys(SLIDERS).forEach(wireSlider);
["dot_height", "dome_percent"].forEach(wireLimitField);

directFields.concat(["drop_percent", "boost_percent", "dwell_ms", "dome_percent"]).forEach(function (f) {
  el(f).addEventListener("change", function () { renderChecks(); request(); });
});
el("save").addEventListener("click", function () {
  if (encodeTimer !== null) encode();
  send({ cmd: "save", params: params(), image: image });
});
el("refresh").addEventListener("click", function () { send({ cmd: "state" }); });

// The presets change on other tabs, so re-read them when this tab comes back and while it is shown.
document.addEventListener("visibilitychange", function () { if (!document.hidden) send({ cmd: "state" }); });
setInterval(function () { if (!document.hidden) send({ cmd: "state" }); }, 4000);
renderStatus(null);
send({ cmd: "init" });
</script>
</body>
</html>
"""

PAGE_HTML = _PAGE.replace("/*ONELINE_CSS*/", CSS)
