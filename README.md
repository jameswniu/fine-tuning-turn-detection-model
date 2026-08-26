# eot-detector

An end-of-turn detector for voice agents, built for the HappyRobot AI/ML engineering task. Given the agent's last line and the caller's words so far, it answers one question fast: is the caller done talking, or still going.

The shipped model reads 0.949 on a frozen human-labeled gold set with zero wrong interruptions at its operating point, and 0.913 on held-out real production calls. It serves at 58 ms p95 under eight-way concurrency, int8 on CPU. Next to it sits a 7.4M-parameter model built here from absolute scratch, own tokenizer, own fifteen-minute pretrain: 0.973 on gold, a perfect Spanish slice, 4.8 ms model latency. The measured distance between those two is the answer to what pretraining is actually worth.

The write-up is [docs/approach.md](docs/approach.md). The depth sits next to the code: [POLICY.md](POLICY.md) is the human turn policy everything hangs off, [EVALS.md](EVALS.md) the gates and bands, [iterations.md](iterations.md) the audit trail of every run including the failures, [data/README.md](data/README.md) the dataset card.

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

That example should say wait, a caller mid-readout. The same text ending in a complete thought says speak. The `/` page re-scores as you type, which is how several training-data gaps were found.

## How it is judged

Three referees, one question each. A frozen 60-card human gold set, never trained on, grades generalization. A regression slice keeps every failure found by live probing fixed. A held-out slice of real calls from the author's own production voice agent grades what synthetic data cannot. Real-call files stay out of git; only aggregates appear in the docs.

The operating threshold is data, not a constant. A written cost ratio (one interruption costs five sluggish responses) is applied to the measured curve, and the result ships next to the weights. The dev set behind that pick was labeled by a certified judge panel, and the panel design was itself A/B tested by replay: identical labels at 31 percent less cost ([docs/judge-cascade-replay.md](docs/judge-cascade-replay.md)).

## The judge panel, in software terms

Part of the data was labeled by models rather than people, so here is exactly what that means. The judges are stock Claude, Gemini, and GPT, three vendors, zero training: no weights moved, each simply applied the written spec (POLICY.md) from its prompt and voted speak, wait, or unsure. Before any vote counted, each judge passed a blind exam, 60 cards with known human answers shuffled among the 30 work cards, indistinguishable. All three scored 53 of 53 and flagged unsure on exactly the seven cards the human had marked ambiguous. The spec quotes a few boundary examples, so the exam was partially open-book, stated wherever the scores appear.

Containment does the rest of the trust work, the way staging contains a deploy. Judge output feeds one file, the dev set. The dev set tunes one number, the operating threshold. That number is clamped by twelve human-policy gates in `make evals`, and the training data plus all three referees stay human-grounded. Worst case, every judge wrong the same way, is a slightly suboptimal threshold inside hard guardrails, and the eval bands would surface it.

## Two models, one glance

[docs/probe-comparison.html](docs/probe-comparison.html) scores both served int8 models on 36 hand-written probes at their own picked thresholds, one row at a time. Open it locally (GitHub shows the source) or regenerate with `.venv/bin/python probe_compare.py`.

| | Fine-tuned DistilBERT, 66M | From-scratch, 7.4M |
|---|---|---|
| Match the written policy | 31 of 35 | 34 of 35 |
| Model latency, mean | 16.6 ms | 2.8 ms |
| Spanish probes (6) | flat 0.75 on all six, three wrong | all six right |

On the 29 English probes the two tie at 28 each, sharing one miss: an unpunctuated yes-no question both read as a cutoff. The margin is entirely Spanish, which the shipping model never trained for. The fine-tune still ships because it leads on unseen real calls, the referee that matters most; the page shows where the small model already wins.

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
