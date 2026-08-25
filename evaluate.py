"""Evaluate an exported end-of-turn detector against the frozen gold set or a jsonl file."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score
from transformers import AutoTokenizer

from common import LABEL2ID, build_input, load_gold, load_jsonl

THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.833, 0.9, 0.95]
REPORT_THRESHOLD = 0.833
BOUNDARY_BAND = (0.4, 0.9)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the end-of-turn detector.")
    parser.add_argument("--model", type=str, default="models/eot-distilbert-onnx-int8", help="Dir with model.onnx and tokenizer files")
    parser.add_argument("--data", type=str, default="data/gold_set.json", help="Path to gold_set.json or a jsonl file")
    parser.add_argument("--report", type=str, default="eval_report.json")
    return parser.parse_args()


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=-1, keepdims=True)


def load_session_and_tokenizer(model_dir: str):
    import onnxruntime as ort

    session = ort.InferenceSession(str(Path(model_dir) / "model.onnx"), providers=["CPUExecutionProvider"])
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    return session, tokenizer


def predict_speak_probs(session, tokenizer, contexts: list[str], texts: list[str]) -> list[float]:
    input_names = {i.name for i in session.get_inputs()}
    probs = []
    for context, text in zip(contexts, texts):
        model_input = build_input(context, text)
        encoded = tokenizer(model_input, truncation=True, padding="max_length", max_length=128, return_tensors="np")
        onnx_inputs = {name: value for name, value in encoded.items() if name in input_names}
        logits = session.run(None, onnx_inputs)[0]
        probs.append(float(softmax(logits)[0][LABEL2ID["speak"]]))
    return probs


def rate_of(labels: list[int], preds: list[int], true_value: int, pred_value: int) -> float:
    subset = [p for label, p in zip(labels, preds) if label == true_value]
    if not subset:
        return 0.0
    return sum(1 for p in subset if p == pred_value) / len(subset)


def sweep_thresholds(labels: list[int], probs: list[float]) -> list[dict]:
    rows = []
    for threshold in THRESHOLDS:
        preds = [1 if p >= threshold else 0 for p in probs]
        rows.append(
            {
                "threshold": threshold,
                "precision": precision_score(labels, preds, pos_label=LABEL2ID["speak"], zero_division=0),
                "recall": recall_score(labels, preds, pos_label=LABEL2ID["speak"], zero_division=0),
                "f1": f1_score(labels, preds, pos_label=LABEL2ID["speak"], zero_division=0),
                "false_speak_rate": rate_of(labels, preds, LABEL2ID["wait"], LABEL2ID["speak"]),
                "false_wait_rate": rate_of(labels, preds, LABEL2ID["speak"], LABEL2ID["wait"]),
            }
        )
    return rows


def per_class_accuracy(samples: list[dict], probs: list[float], labels: list[int], threshold: float) -> dict[str, float]:
    correct: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    for sample, prob, label in zip(samples, probs, labels):
        cls = sample.get("cls", "?")
        pred = 1 if prob >= threshold else 0
        total[cls] += 1
        if pred == label:
            correct[cls] += 1
    return {cls: correct[cls] / total[cls] for cls in sorted(total)}


def print_sweep_report(section: dict) -> None:
    print(f"n={section['n']} pr_auc={section['pr_auc']}")
    print(f"{'threshold':>10} {'precision':>10} {'recall':>10} {'f1':>10} {'false_speak':>12} {'false_wait':>11}")
    for row in section["threshold_sweep"]:
        print(
            f"{row['threshold']:>10} {row['precision']:>10.4f} {row['recall']:>10.4f} "
            f"{row['f1']:>10.4f} {row['false_speak_rate']:>12.4f} {row['false_wait_rate']:>11.4f}"
        )
    if "per_class_accuracy_at_threshold" in section:
        print(f"per-class accuracy at threshold {section['threshold_for_per_class']}:")
        for cls, acc in section["per_class_accuracy_at_threshold"].items():
            print(f"  {cls}: {acc:.4f}")


def print_boundary_report(section: dict) -> None:
    print(
        f"boundary n={section['n']} mean_p_speak={section['mean_p_speak']} "
        f"count_in_band={section['count_in_band']} band={section['band']}"
    )


def evaluate_gold(session, tokenizer, path: str) -> dict:
    gold = load_gold(path)
    samples = gold.get("samples", [])
    hard = [s for s in samples if s.get("label") in LABEL2ID]
    boundary = [s for s in samples if s.get("label") == "unsure"]

    hard_probs = predict_speak_probs(session, tokenizer, [s.get("context", "") for s in hard], [s["text"] for s in hard])
    hard_labels = [LABEL2ID[s["label"]] for s in hard]

    hard_section = {
        "n": len(hard),
        "pr_auc": average_precision_score(hard_labels, hard_probs) if hard_labels else None,
        "threshold_sweep": sweep_thresholds(hard_labels, hard_probs),
        "per_class_accuracy_at_threshold": per_class_accuracy(hard, hard_probs, hard_labels, REPORT_THRESHOLD),
        "threshold_for_per_class": REPORT_THRESHOLD,
    }

    if boundary:
        boundary_probs = predict_speak_probs(
            session, tokenizer, [s.get("context", "") for s in boundary], [s["text"] for s in boundary]
        )
        mean_p_speak = sum(boundary_probs) / len(boundary_probs)
        count_in_band = sum(1 for p in boundary_probs if BOUNDARY_BAND[0] < p < BOUNDARY_BAND[1])
    else:
        mean_p_speak = None
        count_in_band = 0

    boundary_section = {
        "n": len(boundary),
        "mean_p_speak": mean_p_speak,
        "count_in_band": count_in_band,
        "band": list(BOUNDARY_BAND),
    }

    print_sweep_report(hard_section)
    print_boundary_report(boundary_section)
    return {"hard": hard_section, "boundary": boundary_section}


def evaluate_jsonl(session, tokenizer, path: str) -> dict:
    rows = [r for r in load_jsonl(path) if r.get("label") in LABEL2ID]
    probs = predict_speak_probs(session, tokenizer, [r.get("context", "") for r in rows], [r["text"] for r in rows])
    labels = [LABEL2ID[r["label"]] for r in rows]

    section = {
        "n": len(rows),
        "pr_auc": average_precision_score(labels, probs) if labels else None,
        "threshold_sweep": sweep_thresholds(labels, probs),
    }
    print_sweep_report(section)
    return {"jsonl": section}


def main() -> None:
    args = parse_args()
    session, tokenizer = load_session_and_tokenizer(args.model)

    is_gold = args.data.endswith(".json") and not args.data.endswith(".jsonl")
    report: dict = {"model": args.model, "data": args.data}
    if is_gold:
        report.update(evaluate_gold(session, tokenizer, args.data))
    else:
        report.update(evaluate_jsonl(session, tokenizer, args.data))

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"report written to {args.report}")


if __name__ == "__main__":
    main()
