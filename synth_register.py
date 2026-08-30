"""Disfluent-register generator: the shapes real callers make, without shipping real calls.

The synthetic corpus teaches the model that a complete phrase means a complete
turn, because every complete phrase in it is one. Real callers break that rule
constantly. Measured on the real-call holdout, a synthetic-only fine-tune reads
0.65 PR-AUC and speaks over 77 percent of true waits, while the same recipe with
304 real turns mixed in reads 0.91 and 23 percent. The private data cannot ship,
so this file ships what it taught instead.

The load-bearing rule, learned by getting it wrong first: DISFLUENCY IS
ORTHOGONAL TO COMPLETION. A first version of this file emitted disfluent wait
rows only. It recovered about a third of the holdout gap and then broke the
announced-continuation guardrail, because a corpus where every disfluent row is
a wait teaches that disfluency predicts waiting. It does not. Real callers
stammer through finished turns as readily as unfinished ones, so "how many, how
many loads do you have" is a complete question and "all right. um," is not, and
the difference is the tail rather than the mess. Every shape below therefore
appears on both sides of the label wherever the shape allows it.

Four features carry the gap, and none occur in synth.py:

- Acknowledgement then continuation. "all right. um," is a complete phrase whose
  trailing filler is the entire signal that the caller is still going, while
  "all right, that works for me." is the same opening finished.
- Stutter and mid-word repair, mid-turn and also inside completed turns.
- Immediate word repetition, which happens in finished questions too.
- Multi-sentence turns, where every sentence but the last would score speak.

Minimal pairs do the teaching. The wait and speak banks share openings, so the
model cannot separate them on the opening, the filler, or the stammer. It has to
read what the utterance does at the end.

Content is freight and assistant domain, invented here. No phrasing is copied
from any real call; only the shapes are. Pure code, seeded, regenerates
byte-identically, same augmentation pipeline and gold-set collision guard as its
siblings.
"""

from __future__ import annotations

import argparse
import json
import random
import zlib
from pathlib import Path

ACKS = ["all right", "okay", "yeah", "right", "got it", "sure", "mm hm", "yep", "oh okay"]
FILLERS = ["um", "uh", "er", "hm"]
HEDGE_STARTS = ["so", "well", "i mean", "like", "actually", "but"]

CONTINUERS = [
    "then just call me",
    "can you also check",
    "one thing though",
    "what about the",
    "and the other load is",
    "hold on, what is the",
    "before that, is the",
    "let me ask about the",
    "the other thing is",
    "wait, does that mean the",
]

REPAIR_WORDS = [
    ("c", "call"), ("p", "pickup"), ("d", "delivery"), ("r", "rate"), ("b", "broker"),
    ("s", "schedule"), ("t", "trailer"), ("l", "lumper"), ("w", "weight"), ("m", "monday"),
]

REPEATED = ["why", "what", "when", "how", "who", "can you", "is it", "do i", "and then"]

SHORT_SENTENCES = [
    "that works", "that's funny", "i see", "makes sense", "no problem", "sounds right",
    "i got it", "that's fine", "sure thing", "understood",
]

TRAILING_FRAGMENTS = [
    "i don't", "can you", "but the", "about the", "and the", "so the", "what is",
    "is there", "do you", "would it",
]

TAIL_NOUNS = [
    "load number", "rate con", "pickup time", "delivery window", "lumper fee",
    "gate code", "dock number", "appointment", "detention", "trailer number",
]

# Endings that finish a turn. The wait banks reuse the same openings without them.
CLOSERS = [
    "that works for me", "i'll take it", "go ahead and book it", "that's all i needed",
    "send it over", "i'm good", "that answers it", "let's do that",
]

QUESTION_TAILS = [
    "do you have", "can you send", "is that covered", "what time is", "who do i call about",
]


def build(rng: random.Random, per_template: int) -> list[dict]:
    rows: list[dict] = []

    def wait(text: str, tpl: str) -> None:
        rows.append({"context": "", "text": text, "label": "wait", "cls": "R", "variant": "clean", "lang": "en", "tpl": tpl})

    def speak(text: str, tpl: str) -> None:
        rows.append({"context": "", "text": text, "label": "speak", "cls": "R", "variant": "clean", "lang": "en", "tpl": tpl})

    # 1. Acknowledgement openings, both finished and continuing, so the tail decides.
    for _ in range(per_template * 3):
        ack, f = rng.choice(ACKS), rng.choice(FILLERS)
        wait(f"{ack}. {f},", "reg-ack-filler")
        wait(f"{ack}, {f}...", "reg-ack-filler")
        speak(f"{ack}, {f}, {rng.choice(CLOSERS)}.", "reg-ack-filler")
        speak(f"{ack}. {f}. {rng.choice(CLOSERS)}.", "reg-ack-filler")

    for _ in range(per_template * 3):
        ack, f = rng.choice(ACKS), rng.choice(FILLERS)
        wait(f"{ack}. {f}, {rng.choice(CONTINUERS)}", "reg-ack-continue")
        wait(f"{ack}, {rng.choice(CONTINUERS)}", "reg-ack-continue")
        speak(f"{ack}, {rng.choice(CLOSERS)}.", "reg-ack-continue")

    # 2. Stutter and repair, unfinished and finished.
    for _ in range(per_template * 2):
        letter, word = rng.choice(REPAIR_WORDS)
        wait(f"{letter}-{word} me at,", "reg-repair")
        wait(f"what is {letter}- {word}", "reg-repair")
        wait(f"the {letter}- {word} is", "reg-repair")
        speak(f"the {letter}- {word} is all set.", "reg-repair")
        speak(f"can you check the {letter}- {word}?", "reg-repair")

    # 3. Word repetition, unfinished and finished. A stammered question is still a question.
    for _ in range(per_template * 2):
        w, noun = rng.choice(REPEATED), rng.choice(TAIL_NOUNS)
        wait(f"{w}, {w}", "reg-repeat")
        wait(f"{w}, {w}, {w} is", "reg-repeat")
        wait(f"{w}, {w} the {noun}", "reg-repeat")
        speak(f"{w}, {w} the {noun}, {rng.choice(QUESTION_TAILS)}?", "reg-repeat")
        speak(f"{w}, {w} is the {noun}?", "reg-repeat")

    # 4. Multi-sentence turns. Chained complete sentences that either trail off or land.
    for _ in range(per_template * 2):
        a, b, f = rng.choice(ACKS), rng.choice(SHORT_SENTENCES), rng.choice(FILLERS)
        wait(f"{a}. {b}. {rng.choice(TRAILING_FRAGMENTS)}", "reg-multisentence")
        wait(f"{a}. {a}. {b}. {rng.choice(TRAILING_FRAGMENTS)}", "reg-multisentence")
        wait(f"{a}. {b}. {f}, {rng.choice(TRAILING_FRAGMENTS)}", "reg-multisentence")
        speak(f"{a}. {b}. {rng.choice(CLOSERS)}.", "reg-multisentence")
        speak(f"{a}. {f}. {b}, {rng.choice(CLOSERS)}.", "reg-multisentence")

    # 5. Bare fragments hold; short complete replies do not, disfluency notwithstanding.
    for _ in range(per_template * 2):
        f = rng.choice(FILLERS)
        wait(rng.choice(TRAILING_FRAGMENTS), "reg-fragment")
        wait(f"{rng.choice(ACKS)}, {f},", "reg-fragment")
        wait(f"{rng.choice(HEDGE_STARTS)}, {f},", "reg-fragment")
        speak(f"{f}, {rng.choice(CLOSERS)}.", "reg-fragment")
        speak(f"{rng.choice(HEDGE_STARTS)}, {f}, {rng.choice(CLOSERS)}.", "reg-fragment")

    # 6. Announced continuation, the guardrail class the first version broke. It holds
    #    whether it arrives clean or stammered, so both forms are taught explicitly.
    for _ in range(per_template * 2):
        f = rng.choice(FILLERS)
        wait("actually, hold that thought.", "reg-announced")
        wait(f"{f}, actually, hold that thought.", "reg-announced")
        wait("wait, hold on, one more thing.", "reg-announced")
        wait(f"{rng.choice(ACKS)}. {f}, one more thing.", "reg-announced")
        wait("oh, before i forget, one more question.", "reg-announced")
        wait(f"{f}, sorry, one second, one more thing.", "reg-announced")

    return rows


def asr_variant(text: str) -> str:
    t = text.lower().strip()
    while t and t[-1] in ".?!":
        t = t[:-1].rstrip()
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/train_register.jsonl")
    ap.add_argument("--per-template", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--gold", default="data/gold_set.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    rows = build(rng, args.per_template)

    for r in rows:
        r["tpl"] = f"reg{zlib.crc32(r['tpl'].encode())}"

    for r in list(rows):
        t = asr_variant(r["text"])
        if t != r["text"]:
            rows.append({**r, "text": t, "variant": "asr"})

    gold = json.load(open(args.gold))
    gold_texts = {s["text"].strip().lower() for s in gold["samples"]}
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for r in rows:
        key = (r["context"], r["text"])
        if key in seen or r["text"].strip().lower() in gold_texts:
            continue
        seen.add(key)
        out.append(r)
    rng.shuffle(out)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    by_label = Counter(r["label"] for r in out)
    print(f"wrote {len(out)} samples to {args.out}")
    print("labels:", dict(by_label))


if __name__ == "__main__":
    main()
