"""FastAPI serving for the end-of-turn detector."""

import os
import time

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer

from common import LABEL2ID, build_input, gold_threshold

MODEL_DIR = os.environ.get("EOT_MODEL_DIR", "models/eot-distilbert-onnx-int8")
THRESHOLD = float(os.environ.get("EOT_THRESHOLD", gold_threshold()))
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
