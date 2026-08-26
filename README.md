# eot-detector

An end-of-turn detector for voice agents. Given the agent's last line and the caller's words so far, it answers one question fast: is the caller done talking, or still going. Built for the HappyRobot AI/ML engineering task.

The result in one breath: the shipped model reads 0.949 on a frozen human-labeled gold set with zero wrong interruptions at its operating point and 0.913 on held-out real production calls, serving at 58 ms p95 under eight-way concurrency, int8 on CPU. Next to it, a 7.4M-parameter model built here from absolute scratch, own tokenizer, own fifteen-minute pretrain, holds 0.973 on gold with a perfect Spanish slice at 4.8 ms model latency, and the measured distance between those two models is the doc's answer to what pretraining is actually worth.

The short document presenting the solution is [docs/approach.md](docs/approach.md). The depth lives next to the code: [POLICY.md](POLICY.md) is the human-labeled turn policy the whole build hangs off, [EVALS.md](EVALS.md) the gates and bands every iteration is judged against, [iterations.md](iterations.md) the audit trail of every training run including the failures, and [data/README.md](data/README.md) the dataset card.

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

make synth        # regenerate the English training set (seeded, byte-identical)
make train        # fine-tune the DistilBERT lane, export ONNX + int8
make eval         # score a model against the frozen gold set
make serve        # FastAPI on :8000, with a live probe page at /
make bench        # async stress test, latency percentiles + throughput
```

The from-scratch lane and the Spanish data have their own entry points:

```bash
.venv/bin/python synth_scale.py     # English at scale (larger slot pools, same templates)
.venv/bin/python synth_es.py        # Spanish under the same policy
.venv/bin/python train_scratch.py   # own tokenizer + small encoder from random init
.venv/bin/python pretrain_scratch.py  # 15-minute MLM pretrain; then train_scratch.py --init-from models/eot-scratch-base
```

Docker, serving only the int8 model:

```bash
make docker-build && make docker-run
make smoke
```

Try the API directly:

```bash
curl -s -X POST localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"context": "What is your MC number?", "text": "yeah it is four one five"}'
```

That example should say wait (a caller mid-readout), and the same text ending in a complete thought should say speak. The `/` page re-scores as you type, which is how several training-data gaps were found.

## How it is judged

Three referees, each answering a different question. A frozen 60-card gold set, human-labeled and never trained on, grades curated generalization. A regression slice holds every failure found by live probing, so a fix stays fixed. And a held-out slice of real production calls from the author's own voice agent, where turns label themselves, grades the thing synthetic data cannot: the real world. Real-call files stay out of git for privacy; only aggregates appear in the docs.

The operating threshold is not a constant. It comes from a written cost ratio (one interruption costs five sluggish responses) applied to the measured curve, and it ships as data next to the weights. The dev set that picks it was labeled by a certified judge panel, and the panel design itself was A/B tested by replay ([docs/judge-cascade-replay.md](docs/judge-cascade-replay.md)): a two-judge cascade produced identical labels to all three judges at 31 percent less cost, with zero cases where an agreeing pair was wrong, and all three judges independently marked unsure on exactly the seven boundary cards the human labeler had flagged.

## The judge panel, in software terms

Part of the data here was labeled by models rather than people, so this section says plainly what that means and why it can be trusted. The three judges are stock Claude, Gemini, and GPT, from three different vendors. None of them was trained on anything in this repo. Training would mean updating a model's weights, and no weights moved. Each judge simply received the written spec (POLICY.md, the human-authored turn rules) in its prompt, read one card at a time, and voted speak, wait, or unsure. Two of three wins.

Before any vote counted, each judge passed a blind exam. The batch shuffled 60 cards with known human answers in among the 30 real work cards, and the judges could not tell them apart. All three scored 53 of 53 on the hard cards, and all three flagged unsure on exactly the seven cards the human labeler had marked as genuinely ambiguous, so the panel reproduced the human's uncertainty as well as his answers. One honest caveat travels with those scores. The spec quotes a few of the boundary examples, so the exam was partially open-book.

Containment does the rest of the trust work, the way staging contains a deploy. Judge output feeds exactly one file, the dev set, which tunes exactly one number, the operating threshold, and that number is clamped by twelve hard human-policy gates that run in `make evals`. The training data and all three referees stay human-grounded. If every judge were somehow wrong in the same direction, the worst case is a slightly suboptimal threshold inside hard guardrails, and the eval bands would surface it. Full mechanics, the cost A/B between panel designs, and the raw votes live in [docs/judge-cascade-replay.md](docs/judge-cascade-replay.md).

## Two models, one glance

[docs/probe-comparison.html](docs/probe-comparison.html) scores the shipping fine-tune and the from-scratch model side by side on 36 hand-written probes, every policy class plus off-template assistant speech, texting register, and Spanish, one row at a time on the served int8 files at their own picked thresholds. Open it locally (GitHub shows the source) or regenerate it with `.venv/bin/python probe_compare.py`.

| | Fine-tuned DistilBERT, 66M | From-scratch, 7.4M |
|---|---|---|
| Match the written policy | 31 of 35 | 34 of 35 |
| Model latency, mean | 16.6 ms | 2.8 ms |
| Spanish probes (6) | flat 0.75 on all six, three wrong | all six right |

On the 29 English probes the two tie at 28 each and share one miss, an unpunctuated yes-no question ("do i need a lumper receipt for this one") that both read as a cutoff. The three-probe margin is entirely Spanish, which the shipping model was never trained for. The fine-tune still ships because it leads on unseen real calls, the referee that matters most; the page shows where the small model already wins.

## Map

```
synth.py            policy-driven English generator (the template banks ARE the policy)
synth_scale.py      same templates, larger slot pools, an order of magnitude more volume
synth_es.py         Spanish banks under the same policy, Spanglish register included
ood_from_elevenlabs.py  real-call eval slice builder (self-labeling turns; local only)
train.py            fine-tune lane (DistilBERT or any HF encoder via --base)
train_scratch.py    from-scratch lane: byte-level BPE tokenizer + small encoder
evaluate.py         gold-set and jsonl evaluation: sweeps, classes, calibration, stability
serve.py            FastAPI serving over ONNX int8, plus the live probe page
bench.py            async stress harness, stepped concurrency
probe_compare.py    side-by-side probe page for two served models (docs/probe-comparison.html)
judge_cascade_replay.py  replays the dev-set labeling panel two ways over recorded votes, two-judge cascade vs all three, checks the labels match
pick_threshold.py   dev-set threshold selection under tier-1 guardrail constraints, scored single-row on the served artifact
fetch_pretrain_corpus.py  license-clean bilingual Wikipedia slices for the scratch pretrain
pretrain_scratch.py masked-language-model pretraining for the from-scratch lane
labeling-booth.html the calibration booth the gold set was labeled in
data/               gold set (frozen), generated training sets, dataset card
docs/               approach doc and the video script
```

Generated reports (eval_report*.json, bench_report.json, regression_report.json) are build artifacts and stay untracked; the numbers quoted in the docs come from them at freeze time.
