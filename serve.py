"""FastAPI serving for the end-of-turn detector."""

import os
import time

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from transformers import AutoTokenizer

from common import LABEL2ID, build_input, load_threshold

MODEL_DIR = os.environ.get("EOT_MODEL_DIR", "models/eot-distilbert-onnx-int8")
THRESHOLD = float(os.environ.get("EOT_THRESHOLD", load_threshold(MODEL_DIR)))
MAX_LEN = 128

app = FastAPI(title="eot-detector")

# Loaded once at import time, kept as module globals for the life of the process.
_sess_options = ort.SessionOptions()
_sess_options.intra_op_num_threads = 1
session = ort.InferenceSession(f"{MODEL_DIR}/model.onnx", sess_options=_sess_options, providers=["CPUExecutionProvider"])
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
INPUT_NAMES = {i.name for i in session.get_inputs()}


class PredictRequest(BaseModel):
    context: str = ""
    text: str


class PredictResponse(BaseModel):
    p_complete: float
    decision: str
    threshold: float
    model_latency_ms: float


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=-1, keepdims=True)


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    model_input = build_input(request.context, request.text)

    start = time.perf_counter()
    encoded = tokenizer(model_input, truncation=True, padding="max_length", max_length=MAX_LEN, return_tensors="np")
    onnx_inputs = {name: value for name, value in encoded.items() if name in INPUT_NAMES}
    logits = session.run(None, onnx_inputs)[0]
    model_latency_ms = (time.perf_counter() - start) * 1000

    p_complete = float(softmax(logits)[0][LABEL2ID["speak"]])
    decision = "speak" if p_complete >= THRESHOLD else "wait"
    return PredictResponse(p_complete=p_complete, decision=decision, threshold=THRESHOLD, model_latency_ms=model_latency_ms)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "model_dir": MODEL_DIR}


# Small standalone demo page. Plain HTML/CSS/JS, no build step, no external assets.
# It only talks to the /predict JSON API above; it does not change that contract.
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EoT Live Probe</title>
<style>
  :root {
    --bg: #1D1512;
    --card: #2E241C;
    --line: #4A3B2E;
    --cream: #F2E9DB;
    --dim: #B5A48E;
    --faint: #8A7A66;
    --gold: #C9A45C;
    --gold-ink: #241A10;
    --slate: #5F7A92;
    --rust: #B85C42;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--cream);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    padding: 64px 20px;
  }
  .wrap { width: 100%; max-width: 540px; }
  h1 { font-size: 26px; font-weight: 650; letter-spacing: 0.01em; margin: 0 0 8px; }
  .sub { font-size: 14px; color: var(--dim); line-height: 1.5; margin: 0 0 32px; max-width: 48ch; }
  .field { margin-bottom: 16px; }
  label {
    display: block; font-size: 11.5px; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: var(--faint); margin-bottom: 6px;
  }
  input[type="text"] {
    width: 100%;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    color: var(--cream);
    font-family: inherit;
    font-size: 16px;
    padding: 13px 14px;
  }
  input[type="text"]::placeholder { color: var(--faint); }
  input[type="text"]:focus-visible { outline: 2px solid var(--gold); outline-offset: 1px; border-color: var(--gold); }
  #text { font-size: 18px; }
  .result { margin-top: 40px; }
  .pct {
    font-size: 56px; font-weight: 700; font-variant-numeric: tabular-nums;
    line-height: 1; color: var(--cream); transition: color 0.15s ease;
  }
  .bar {
    position: relative; margin-top: 20px; height: 14px;
    background: var(--card); border: 1px solid var(--line); border-radius: 8px; overflow: visible;
  }
  .fill {
    position: absolute; left: 0; top: 0; bottom: 0; width: 0%;
    background: var(--slate); border-radius: 7px;
    transition: width 0.12s ease, background 0.15s ease;
  }
  .marker {
    position: absolute; top: -4px; bottom: -4px; width: 2px;
    background: var(--cream); opacity: 0.6; left: 0%; display: none;
  }
  .row { margin-top: 20px; }
  .chip {
    display: inline-block; font-size: 13px; font-weight: 700; letter-spacing: 0.08em;
    padding: 9px 18px; border-radius: 999px; border: 1px solid var(--line);
    color: var(--faint); background: transparent;
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
  }
  .captions {
    margin-top: 18px; display: flex; justify-content: space-between; gap: 12px;
    font-size: 12.5px; color: var(--faint); font-variant-numeric: tabular-nums; flex-wrap: wrap;
  }
</style>
</head>
<body>
<main class="wrap">
  <h1>EoT Live Probe</h1>
  <p class="sub">Type as the caller would speak it. Every keystroke re-scores P(turn complete) against the live ONNX model.</p>
  <div class="field">
    <label for="ctx">Agent context</label>
    <input id="ctx" type="text" placeholder="Agent's last line (optional)" autocomplete="off">
  </div>
  <div class="field">
    <label for="text">Caller</label>
    <input id="text" type="text" placeholder="Type what the caller says..." autocomplete="off" autofocus>
  </div>
  <section class="result">
    <div class="pct" id="pct">...</div>
    <div class="bar" id="bar">
      <div class="fill" id="fill"></div>
      <div class="marker" id="marker"></div>
    </div>
    <div class="row">
      <span class="chip" id="chip">IDLE</span>
    </div>
    <div class="captions">
      <span id="threshCaption">threshold pending (from the 1:5 cost ratio)</span>
      <span id="latencyCaption">model: pending</span>
    </div>
  </section>
</main>
<script>
(function () {
  var ctxInput = document.getElementById('ctx');
  var textInput = document.getElementById('text');
  var pctEl = document.getElementById('pct');
  var fillEl = document.getElementById('fill');
  var markerEl = document.getElementById('marker');
  var chipEl = document.getElementById('chip');
  var threshEl = document.getElementById('threshCaption');
  var latEl = document.getElementById('latencyCaption');

  var GOLD = '#C9A45C';
  var SLATE = '#5F7A92';
  var INK = '#241A10';
  var FAINT = '#8A7A66';
  var LINE = '#4A3B2E';
  var RUST = '#B85C42';
  var CREAM = '#F2E9DB';

  var debounceTimer = null;
  var requestSeq = 0;
  var knownThreshold = null;

  function setThresholdCaption() {
    if (knownThreshold === null) {
      threshEl.textContent = 'threshold pending (from the 1:5 cost ratio)';
      markerEl.style.display = 'none';
    } else {
      threshEl.textContent = 'threshold ' + knownThreshold.toFixed(2) + ' (from the 1:5 cost ratio)';
      markerEl.style.left = (knownThreshold * 100).toFixed(2) + '%';
      markerEl.style.display = 'block';
    }
  }

  function renderIdle() {
    pctEl.textContent = '...';
    pctEl.style.color = CREAM;
    fillEl.style.width = '0%';
    fillEl.style.background = SLATE;
    chipEl.textContent = 'IDLE';
    chipEl.style.background = 'transparent';
    chipEl.style.color = FAINT;
    chipEl.style.borderColor = LINE;
    latEl.textContent = 'model: pending';
    setThresholdCaption();
  }

  function renderResult(data) {
    var pct = Math.max(0, Math.min(100, data.p_complete * 100));
    var speak = data.decision === 'speak';
    var accent = speak ? GOLD : SLATE;
    pctEl.textContent = pct.toFixed(1) + '%';
    pctEl.style.color = accent;
    fillEl.style.width = pct.toFixed(2) + '%';
    fillEl.style.background = accent;
    chipEl.textContent = speak ? 'SPEAK' : 'KEEP LISTENING';
    chipEl.style.background = accent;
    chipEl.style.color = INK;
    chipEl.style.borderColor = accent;
    latEl.textContent = 'model: ' + data.model_latency_ms.toFixed(1) + ' ms';
    knownThreshold = data.threshold;
    setThresholdCaption();
  }

  function renderError() {
    chipEl.textContent = 'ERROR';
    chipEl.style.background = 'transparent';
    chipEl.style.color = RUST;
    chipEl.style.borderColor = RUST;
    pctEl.textContent = '...';
    pctEl.style.color = CREAM;
    fillEl.style.width = '0%';
    latEl.textContent = 'model: pending';
  }

  function runCheck() {
    var text = textInput.value;
    if (text.trim() === '') {
      renderIdle();
      return;
    }
    var seq = ++requestSeq;
    fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ context: ctxInput.value, text: text })
    }).then(function (res) {
      if (!res.ok) throw new Error('bad response');
      return res.json();
    }).then(function (data) {
      if (seq === requestSeq) renderResult(data);
    }).catch(function () {
      if (seq === requestSeq) renderError();
    });
  }

  function scheduleCheck() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runCheck, 120);
  }

  ctxInput.addEventListener('input', scheduleCheck);
  textInput.addEventListener('input', scheduleCheck);

  renderIdle();
})();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)
