<p align="center">
  <img src="assets/hero.svg" alt="fine-tuned-turn-detection-transformers: an end-of-turn detector for voice agents that scores 0.949 on a frozen human gold set with zero false interruptions, 0.913 on held-out real calls, and answers in 58 ms p95 on int8 CPU at threshold 0.42" width="100%">
</p>

<p align="center">
  <a href="https://github.com/jameswniu/fine-tuned-turn-detection-transformers/actions/workflows/ci.yml"><img alt="ci" src="https://github.com/jameswniu/fine-tuned-turn-detection-transformers/actions/workflows/ci.yml/badge.svg?branch=master"></a>
  <img alt="gold set: 60 cards, frozen" src="https://img.shields.io/badge/gold_set-60_cards_%C2%B7_frozen-f5b342?style=flat-square&labelColor=0b0d10">
  <img alt="referees: gold, regressions, real calls" src="https://img.shields.io/badge/referees-gold_%C2%B7_regressions_%C2%B7_real_calls-5c5853?style=flat-square&labelColor=0b0d10">
  <img alt="tier-1 gates: 12 of 12 green on the served artifact" src="https://img.shields.io/badge/tier--1_gates-12%2F12_served_int8-5c5853?style=flat-square&labelColor=0b0d10">
  <img alt="judge panel: 3 vendors, 90 blind cards" src="https://img.shields.io/badge/judges-3_vendors_%C2%B7_90_blind_cards-5c5853?style=flat-square&labelColor=0b0d10">
  <img alt="figures: regenerated from constants, checked in CI" src="https://img.shields.io/badge/figures-from_constants_%C2%B7_CI_checked-5c5853?style=flat-square&labelColor=0b0d10">
</p>

**One written policy, three referees, and an int8 model that answers in 58 ms.** Built for the HappyRobot AI/ML engineering task: given the agent's last line and the caller's words so far, decide whether the caller is done talking.

Watch it score a call below. Read the write-up in [docs/approach.md](docs/approach.md). Run it with `make serve`. The depth sits next to the code: [POLICY.md](POLICY.md) is the human turn policy everything hangs off, [EVALS.md](EVALS.md) the gates and bands, [iterations.md](iterations.md) the audit trail of every run including the failures, [data/README.md](data/README.md) the dataset card.

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

make synth        # regenerate the English training set (seeded, byte-identical)
make train        # fine-tune the DistilBERT lane, export ONNX + int8
make eval         # score a model against the frozen gold set
make serve        # FastAPI on :8000, with a live probe page at /
make bench        # async stress test, latency percentiles + throughput
make docker-build && make docker-run && make smoke   # the int8 model in a container
```

<p align="center">
  <img src="assets/live-probe.gif" alt="The live probe page re-scoring as a caller types: a mid-readout holds at wait, a complete thought flips to speak, an announced continuation holds at wait, and a casual closer flips to speak" width="100%">
</p>

<sub>The `/` page re-scores after every keystroke. A mid-readout holds. "okay, got it." speaks. "actually yeah, one more thing." holds, because the policy says an announced continuation waits. "nah bye" speaks, the miss a live poke found and the regression slice now guards. The from-scratch and Spanish lanes have their own entry points, listed in the map below.</sub>

```bash
curl -s -X POST localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"context": "What is your MC number?", "text": "yeah it is four one five"}'
```

<p align="center"><img src="assets/band-judged.svg" alt="The referees" width="100%"></p>

## How it is judged

<p align="center">
  <img src="assets/referees.svg" alt="Three referees, one question each: a frozen gold set of 60 human-labeled cards for generalization, 6 probe-found regressions for memory, and 96 held-out real-call turns for discovery" width="100%">
</p>

Real-call files stay out of git; only aggregates appear in the docs. The operating threshold is data, not a constant: a written cost ratio (one interruption costs five sluggish responses) applied to the measured curve, picked on the served int8 artifact one row at a time, and shipped next to the weights.

## The judge panel, in software terms

<p align="center">
  <img src="assets/judges.svg" alt="How the dev set was labeled and why to trust it: 60 gold cards with known human answers hidden among 30 fresh cards, three stock vendor judges with zero training, two-of-three majority, and the output feeds one file that tunes one number clamped by 12 human gates" width="100%">
</p>

Part of the data was labeled by stock models rather than people. No weights moved; the written spec rode in the prompt, the exam was blind, and the vote was two of three. Containment does the trust work the way staging contains a deploy: judge output reaches one file, which tunes one number, which twelve human-policy gates clamp. One caveat travels with the exam score. The spec quotes a few boundary examples, so certification was partially open-book. Mechanics, the cost A/B between panel designs, and the raw votes: [docs/judge-cascade-replay.md](docs/judge-cascade-replay.md).

<p align="center"><img src="assets/band-models.svg" alt="Two models" width="100%"></p>

## Two models, one glance

<p align="center">
  <img src="assets/pretrain-curve.svg" alt="What pretraining is worth, measured as PR-AUC on unseen real calls: 0.48 random init, 0.60 adding real calls, 0.83 adding a fifteen-minute pretrain, 0.91 web-pretrained" width="100%">
</p>

| | Fine-tuned DistilBERT, 66M | From-scratch, 7.4M |
|---|---|---|
| Match the written policy, 36 probes | 31 of 35 | 34 of 35 |
| Model latency, mean | 16.6 ms | 2.8 ms |
| Spanish probes (6) | flat 0.75 on all six, three wrong | all six right |

On the 29 English probes the two tie at 28 each and share one miss, an unpunctuated yes-no question both read as a cutoff; the margin is entirely Spanish, which the shipping model never trained for. The fine-tune ships because it leads on unseen real calls, the referee that matters most. [docs/probe-comparison.html](docs/probe-comparison.html) holds every probe, regenerated by `probe_compare.py`.

## Map

```
synth.py            policy-driven English generator (the template banks ARE the policy)
synth_scale.py      same templates, larger slot pools, an order of magnitude more volume
synth_es.py         Spanish banks under the same policy, Spanglish register included
ood_from_elevenlabs.py  real-call eval slice builder (self-labeling turns; local only)
train.py            fine-tune lane (DistilBERT or any HF encoder via --base)
train_scratch.py    from-scratch lane: byte-level BPE tokenizer + small encoder
pretrain_scratch.py masked-language-model pretraining for the from-scratch lane
fetch_pretrain_corpus.py  license-clean bilingual Wikipedia slices for the scratch pretrain
evaluate.py         gold-set and jsonl evaluation: sweeps, classes, calibration, stability
pick_threshold.py   dev-set threshold selection under tier-1 guardrail constraints, scored single-row on the served artifact
serve.py            FastAPI serving over ONNX int8, plus the live probe page
bench.py            async stress harness, stepped concurrency
probe_compare.py    side-by-side probe page for two served models (docs/probe-comparison.html)
judge_cascade_replay.py  replays the dev-set labeling panel two ways over recorded votes, checks the labels match
draw_figures.py     emits every figure above from counted constants; --check fails CI on drift or a font under the 75% floor
labeling-booth.html the calibration booth the gold set was labeled in
assets/             the figures, their GIF, and its mp4
data/               gold set (frozen), generated training sets, judge votes, dataset card
docs/               approach doc, judge replay, probe page, video script
```

Generated reports (eval_report*.json, bench_report*.json, regression_report.json) are build artifacts and stay untracked; every number in the figures and the docs comes from them at freeze time, and `make figures-check` fails if a figure drifts from its constants.

## Questions a reviewer will ask

Short answers, expandable. Every number in them has a source in the docs linked above.

<details>
<summary><b>Why DistilBERT, and why not something else?</b></summary>

The field had converged on small text transformers for this job before this build started. LiveKit's shipped turn detector runs at 5 ms inference and 24 ms p90 on text alone, and pipecat's smart-turn at 12 ms on a modern CPU. Given a transcript-so-far as input, a 100 ms budget, and nine hours, a small pretrained encoder fine-tuned as a two-way classifier was the workhorse choice. DistilBERT specifically brings 66M parameters in six layers, about 97% of BERT-base on its paper's benchmarks, the most mature Hugging Face and ONNX path of any small encoder, and a fine-tune that finishes in about two minutes here on 1,500 rows. Those two minutes are why nine audited iterations fit in one night. The uncased variant matches ASR text, which arrives lowercase with no punctuation. Not measured, and stated as such, are MiniLM-L6, DeBERTa-v3-small, ELECTRA-small, ModernBERT, and SmolLM2-135M, the base LiveKit built on. The only architecture comparison that ran is the from-scratch lane, and it is on the chart above.

</details>

<details>
<summary><b>Why int8, and what did it cost?</b></summary>

Dynamic int8 quantization of the linear layers through ONNX Runtime is the standard CPU serving move, buying a smaller artifact and lower CPU latency for negligible accuracy loss on classification. It was not free, and the repo shows the bill. Quantization moved a near-threshold probability from 0.26 to 0.41 and broke a tier-1 guardrail twice, once because the threshold had been picked on the fp32 checkpoint, and once because the picker scored its constraint rows in a batch while serving scores one row at a time, and int8 dynamic quantization is batch-composition-dependent. v9 picks the threshold on the served int8 artifact, single-row, and the gate went 12 of 12. Not measured is fp32 against int8 latency head-to-head on the same box.

</details>

<details>
<summary><b>Why 0.42, and not 0.5 or the 0.83 the cost ratio implies?</b></summary>

The 1:5 cost ratio gives a closed-form bar of 0.833 only for a calibrated model, and this one runs under-confident (ECE 0.16). So the bar is applied to the measured curve instead, as the threshold that minimizes five false speaks plus one false wait on the judged dev set, constrained so all twelve tier-1 probes hold on the served artifact. Selection on synthetic validation data drifted the dial to 0.87 twice, in v3 and v4, which is why the dev set exists. The dial ships as data next to the weights and every run re-derives it.

</details>

<details>
<summary><b>Why create the data instead of finding a dataset?</b></summary>

No public end-of-turn dataset existed to download; LiveKit and pipecat each built their own. Mining YouTube was rejected for licensing and cleaning cost inside four days. Policy-driven synthesis buys auditability, since every row traces to a written rule, byte-reproducibility, since it is seeded with no LLM in the loop, and zero personal data. Its known cost, a creator's blind spots, is handled by the three referees rather than by hope. The real-call slice is where synthesis got caught: the model had learned the vendor turn-taker's habit of barging in after "one more thing", and a policy filter plus a relabel removed it.

</details>

<details>
<summary><b>What is the honest ceiling of a text-only model?</b></summary>

Both models miss the same probe, "do i need a lumper receipt for this one" with no context and no punctuation, scoring about 0.02 as a cutoff. An unpunctuated yes-no question ending in a pronoun looks like a mid-sentence prefix, because the question lives in the caller's rising tone, and the ASR discards it. Agent context fixes it today (recall 1.00 with context against 0.47 bare, the known weak slice); audio features are the roadmap answer. It is deliberately not in the regression slice yet, because that file's contract is that every row passes, so it enters paired with its fix.

</details>

<details>
<summary><b>Did you benchmark against the vendor's turn-taker?</b></summary>

Not head-to-head in this submission. The real-call slices use the vendor's ASR transcripts, which is the deployment condition, and deliberately overrule the vendor turn-taker's decisions where they contradict the policy, with each overruled row carrying a policy_corrected flag. The residual bias is stated in EVALS.md. Cut points still come from the vendor stack, so the real-call bands read as pessimistic bounds, and those numbers inherit that ASR's error distribution. The bake-off with receipts, online shadow on a real phone number with disagreements published, is the roadmap chapter.

</details>

<details>
<summary><b>How does this run at a million calls a month?</b></summary>

Twenty million turn decisions a month cannot be human-reviewed and do not need to be. The candidate shadows the incumbent on live traffic, decisions logged and never acted on. Where the two agree, the turn is cheap; where they disagree, it is information-dense, so humans label only sampled disagreements, adjudicated against the policy, and those feed back as training rows and referee rows. The disagreement rate itself is a drift alarm that fires before anyone has labeled anything. The same pattern already ran here in miniature three times, in the vendor-import catch, the judge panel's 2-of-3 splits, and the probe page's shared miss. ROADMAP.md has the environment ladder.

</details>

<details>
<summary><b>What was measured, and what was not?</b></summary>

Measured is every number on this page, from the reports listed above, on the served int8 artifact. Not measured, stated so nobody reads silence as a claim, are fp32 versus int8 latency on one box; judge retry variance, since each judge voted once per card and three vendors is diversity rather than retries; and base-model alternatives to DistilBERT. One bench was discarded as thermal pollution after back-to-back trainings, so every quoted bench comes from a quiet machine, which is a bench-hygiene finding rather than a model result.

</details>
