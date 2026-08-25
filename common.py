"""Shared helpers for the end-of-turn detector: input formatting and data loading."""

import json
from pathlib import Path
from typing import Any

LABEL2ID = {"wait": 0, "speak": 1}

DEFAULT_SPEAK_THRESHOLD = 0.8333


def build_input(context: str, text: str) -> str:
    """Build the model input string from conversation context and the caller utterance so far."""
    if context:
        return f"agent: {context} caller: {text}"
    return f"caller: {text}"


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a jsonl file, one JSON object per line, skipping blank lines."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_gold(path: str | Path = "data/gold_set.json") -> dict[str, Any]:
    """Load the frozen gold set: cost_ratio, speak_threshold, and labeled samples."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gold_threshold(path: str | Path = "data/gold_set.json") -> float:
    """Return the speak_threshold recorded in the gold set, falling back if absent or unreadable."""
    try:
        gold = load_gold(path)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_SPEAK_THRESHOLD
    return gold.get("speak_threshold", DEFAULT_SPEAK_THRESHOLD)


def load_threshold(model_dir: str | Path) -> float:
    """Operating threshold for a model dir: its threshold.json if present, else the gold-set default."""
    p = Path(model_dir) / "threshold.json"
    if p.exists():
        try:
            return json.load(open(p, encoding="utf-8"))["threshold"]
        except (json.JSONDecodeError, KeyError):
            pass
    return gold_threshold()
