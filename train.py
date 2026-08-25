"""Fine-tune a small encoder for end-of-turn detection (binary: wait vs speak)."""

import argparse
import json
import random
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import average_precision_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

from common import LABEL2ID, build_input, load_jsonl

FINAL_THRESHOLD = 0.833


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the end-of-turn detector.")
    parser.add_argument("--train", type=str, default="data/train.jsonl", required=True, help="Path to training jsonl file")
    parser.add_argument("--base", type=str, default="distilbert-base-uncased", help="Base encoder checkpoint")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--val-frac", type=float, default=0.1)
    parser.add_argument("--max-len", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="models/eot-distilbert")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class TurnDataset(Dataset):
    def __init__(self, encodings: dict[str, list[list[int]]], labels: list[int]):
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {key: torch.tensor(values[idx]) for key, values in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


def load_rows(path: str) -> tuple[list[str], list[int]]:
    rows = load_jsonl(path)
    rows = [r for r in rows if r.get("label") in LABEL2ID]
    texts = [build_input(r.get("context", ""), r["text"]) for r in rows]
    labels = [LABEL2ID[r["label"]] for r in rows]
    return texts, labels


def class_weights(labels: list[int], device: str) -> torch.Tensor:
    """Inverse-frequency weights so the rarer class does not get ignored by the loss."""
    counts = Counter(labels)
    total = len(labels)
    num_classes = len(LABEL2ID)
    weights = [total / (num_classes * counts.get(i, 1)) for i in range(num_classes)]
    return torch.tensor(weights, dtype=torch.float32, device=device)


def run_eval(model, loader: DataLoader, device: str) -> tuple[list[float], list[int]]:
    model.eval()
    probs: list[float] = []
    labels: list[int] = []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            batch_probs = torch.softmax(outputs.logits, dim=-1)[:, LABEL2ID["speak"]]
            probs.extend(batch_probs.detach().cpu().tolist())
            labels.extend(batch_labels.detach().cpu().tolist())
    return probs, labels


def metrics_at(labels: list[int], probs: list[float], threshold: float) -> dict[str, float]:
    preds = [1 if p >= threshold else 0 for p in probs]
    precision = precision_score(labels, preds, pos_label=LABEL2ID["speak"], zero_division=0)
    recall = recall_score(labels, preds, pos_label=LABEL2ID["speak"], zero_division=0)
    return {"precision_speak": precision, "recall_speak": recall}


def export_onnx(out_dir: str) -> None:
    """Export the saved checkpoint to ONNX, then attempt dynamic int8 quantization."""
    from optimum.onnxruntime import ORTModelForSequenceClassification

    onnx_dir = f"{out_dir}-onnx"
    ort_model = ORTModelForSequenceClassification.from_pretrained(out_dir, export=True)
    ort_model.save_pretrained(onnx_dir)
    tokenizer = AutoTokenizer.from_pretrained(out_dir)
    tokenizer.save_pretrained(onnx_dir)
    print(f"fp32 onnx model written to {onnx_dir}")

    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        int8_dir = f"{out_dir}-onnx-int8"
        Path(int8_dir).mkdir(parents=True, exist_ok=True)
        quantize_dynamic(
            model_input=str(Path(onnx_dir) / "model.onnx"),
            model_output=str(Path(int8_dir) / "model.onnx"),
            weight_type=QuantType.QInt8,
        )
        for item in Path(onnx_dir).glob("*"):
            if item.name != "model.onnx":
                shutil.copy(item, Path(int8_dir) / item.name)
        print(f"int8 quantized model written to {int8_dir}")
    except Exception as exc:
        print(f"int8 quantization failed ({exc}), the fp32 onnx model at {onnx_dir} is still usable")


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    texts, labels = load_rows(args.train)
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=args.val_frac, random_state=args.seed, stratify=labels
    )

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForSequenceClassification.from_pretrained(args.base, num_labels=2)
    model.to(device)

    train_encodings = tokenizer(train_texts, truncation=True, padding="max_length", max_length=args.max_len)
    val_encodings = tokenizer(val_texts, truncation=True, padding="max_length", max_length=args.max_len)
    train_loader = DataLoader(TurnDataset(train_encodings, train_labels), batch_size=args.batch, shuffle=True)
    val_loader = DataLoader(TurnDataset(val_encodings, val_labels), batch_size=args.batch, shuffle=False)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(0.1 * total_steps)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights(train_labels, device))

    epoch_reports = []
    best_pr_auc = -1.0
    best_probs: list[float] = []
    best_labels: list[int] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, batch_labels)
            loss.backward()
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()
        train_loss = total_loss / len(train_loader)

        val_probs, val_labels_out = run_eval(model, val_loader, device)
        val_preds = [1 if p >= 0.5 else 0 for p in val_probs]
        accuracy = sum(int(p == l) for p, l in zip(val_preds, val_labels_out)) / len(val_labels_out)
        at_half = metrics_at(val_labels_out, val_probs, 0.5)
        pr_auc = average_precision_score(val_labels_out, val_probs)

        print(
            f"epoch {epoch}: train_loss={train_loss:.4f} val_accuracy={accuracy:.4f} "
            f"val_precision_speak={at_half['precision_speak']:.4f} val_recall_speak={at_half['recall_speak']:.4f} "
            f"val_pr_auc={pr_auc:.4f}"
        )

        epoch_reports.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_accuracy": accuracy,
                "val_precision_speak": at_half["precision_speak"],
                "val_recall_speak": at_half["recall_speak"],
                "val_pr_auc": pr_auc,
            }
        )

        if pr_auc > best_pr_auc:
            best_pr_auc = pr_auc
            best_probs = val_probs
            best_labels = val_labels_out
            Path(args.out).mkdir(parents=True, exist_ok=True)
            model.save_pretrained(args.out)
            tokenizer.save_pretrained(args.out)

    final_at_threshold = metrics_at(best_labels, best_probs, FINAL_THRESHOLD)
    report = {
        "args": vars(args),
        "epochs": epoch_reports,
        "best_val_pr_auc": best_pr_auc,
        "final_val_precision_at_threshold": final_at_threshold["precision_speak"],
        "final_val_recall_at_threshold": final_at_threshold["recall_speak"],
        "final_threshold": FINAL_THRESHOLD,
    }
    with open(Path(args.out) / "training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"best checkpoint saved to {args.out} (val_pr_auc={best_pr_auc:.4f})")

    best_thr, best_cost = 0.5, float("inf")
    for i in range(1, 99):
        thr = i / 100
        fp = sum(1 for p, l in zip(best_probs, best_labels) if p >= thr and l == 0)
        fn = sum(1 for p, l in zip(best_probs, best_labels) if p < thr and l == 1)
        cost = 5 * fp + fn
        if cost < best_cost or (cost == best_cost and thr > best_thr):
            best_cost, best_thr = cost, thr
    thr_payload = {"threshold": best_thr, "cost_ratio": 5, "method": "cost-optimal on validation curve, cost = 5*FP + FN", "expected_val_cost": best_cost}
    with open(Path(args.out) / "threshold.json", "w", encoding="utf-8") as f:
        json.dump(thr_payload, f, indent=2)
    print(f"cost-optimal operating threshold: {best_thr} (val cost {best_cost})")

    op_metrics = metrics_at(best_labels, best_probs, best_thr)
    report["operating_threshold"] = best_thr
    report["operating_precision_speak"] = op_metrics["precision_speak"]
    report["operating_recall_speak"] = op_metrics["recall_speak"]
    with open(Path(args.out) / "training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    export_onnx(args.out)

    for suffix in ("-onnx", "-onnx-int8"):
        target_dir = Path(f"{args.out}{suffix}")
        if target_dir.exists():
            shutil.copy(Path(args.out) / "threshold.json", target_dir / "threshold.json")


if __name__ == "__main__":
    main()
