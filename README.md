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

## How the operating point is chosen

The threshold is the product decision, so it is picked by a written rule, on the artifact that ships, and re-derived every run. `pick_threshold.py` sweeps thresholds from 0.01 to 0.99 on the 30-card judged dev set and minimizes `5 * FPR + FNR`, class-conditional rates so label imbalance cannot steer it. Twelve pinned cards act as constraints: every gold readout card, the gold "one more thing" card, the dev-set announced continuation, and the six probe-found regressions must each land on their required decision, or the threshold is inadmissible. If no admissible threshold exists the sweep says so and fails the run rather than shipping a broken guardrail. Scoring happens on the served int8 artifact, one row per call, because int8 dynamic quantization is batch-composition-dependent. In v8 the same card read 0.381 in a batch and 0.412 alone, and 0.412 is what serving sees. The result ships as `threshold.json` beside the weights, and `serve.py` reads it at startup.

The trajectory is the audit trail. Nine runs, one lesson each, all from the same frozen referee.

| run | threshold | gold PR-AUC | false-speak | ECE | what it taught |
|---|---|---|---|---|---|
| v1 | 0.833 | 0.961 | 0.00 | n/a | the closed-form Bayes bar fails on an under-confident model; recall 0.58 |
| v2 | 0.61 | 0.964 | 0.00 | 0.114 | cost-optimal on the measured curve recovers recall to 0.81 |
| v3 | 0.87 | 0.970 | 0.00 | 0.067 | selection on synthetic validation drifts high; the val set is too easy |
| v4 | 0.86 | 0.969 | 0.00 | 0.070 | rate-based objective, still tracking synthetic label balance rather than the model |
| v5 | 0.81 | 0.958 | 0.00 | 0.092 | a live poke found "nah bye" scoring wait; casual register added, regression slice born |
| v6 | 0.18 | 0.955 | 0.037 | 0.169 | judged dev set plus real-call rows; the dial collapsed and the "one more thing" gate broke |
| v7 | 0.27 | 0.949 | 0.00 | 0.160 | twelve guardrail constraints and a vendor-behavior filter; red on served int8, green on fp32 |
| v8 | 0.40 | 0.949 | 0.00 | 0.160 | re-picked on int8, 11 of 12; batched scoring disagreed with single-row serving |
| v9 | 0.42 | 0.949 | 0.00 | 0.160 | single-row scoring, 12 of 12; real calls 0.913 PR-AUC, recall 0.959 |

Three of those nine steps changed nothing about the model. v7 through v9 are the same weights; what moved was the instrument. That is the finding the loop exists to surface. The eval has to be debugged with the same rigor as the model, and the fix each time was to measure the artifact that ships, in the shape it ships.

## The policy, as rows

Sixty blind labels became eleven classes with a rule each, and `synth.py` turns the rules into rows. Every training line traces to one of these.

| class | shape | decision |
|---|---|---|
| A | complete statement | speak |
| B | complete question | speak |
| C | bare acknowledgement | speak; a complete turn but never a call-ender |
| D | mid-clause cutoff | wait |
| E | disfluent trail | wait |
| F | mid-data readout | wait, absolute, however long the pause runs |
| G | connector-final ("and then...") | wait |
| H | complete, then maybe more | speak, unless continuation is announced ("one more thing" holds) |
| I | trailing hedge | speak by default; a decorative softener on an owned claim mid-narrative holds |
| J | self-interrupt restart | wait; a full retraction may earn a brief acknowledgement |
| K | explicit hold | self-retrieval holds silently; a narrated outside interruption gets a courtesy acknowledgement |

Class I is the judgment call worth reading, because it looked like a contradiction in the labels and turned out to be the rule. "The broker said it was covered, supposedly..." was labeled speak; "The detention was approved, or something..." was labeled wait. The hedge word carries no turn signal. What decides is stance and ownership. A claim attributed to someone else is a question in disguise, so the agent speaks to confirm. An owned first-person claim with a habitual softener is just a statement, so it follows the statement rules. Attribution markers versus first-person assertion are surface features a text model can learn, which is why the ruling is trainable and not only philosophy.

Four augmentations bake in deployment realism. Complete utterances are re-emitted truncated mid-sentence and labeled wait, the shape of an ASR partial. Every row also ships lowercased with terminal punctuation stripped, so the model cannot lean on periods. Contexted rows are emitted bare as well, so it works with and without the agent's last line. And from v6, real-call rows from the author's production voice agent join the training half at four-fold weight, grouped by call so no call leaks into the referee. The counts: 1,586 training rows, 60 gold cards (53 hard, 7 boundary), 30 judged dev cards, 6 regressions, 400 real turns split 304 to 96 by call.

## Serving, measured

The contract is one endpoint. `POST /predict` takes `{context, text}` and returns `{p_complete, decision, threshold, model_latency_ms}`; `/healthz` reports the model directory. The model runs as ONNX Runtime with dynamic int8 quantization on CPU, and the Docker image serves only the int8 artifact. Two bench runs are quoted on purpose, because they disagree and the disagreement is a finding.

| box state | c1 req/s, p95 | c8 req/s, p95 | model p50 at c8 |
|---|---|---|---|
| quiet machine | 55, 21.2 ms | 316, 32.8 ms | 21.7 ms |
| mid training load | 28, 42.5 ms | 170, 57.9 ms | 39.5 ms |

The hero quotes the worse p95, 58 ms, against the brief's 100 ms budget, so the headline holds on a busy box. The gap between the rows is bench hygiene, not the model; quoted benches come from an idle machine, and a third run polluted by back-to-back trainings was discarded. Not yet measured is fp32 against int8 latency on one box.

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

## Q&A

Short answers, expandable. Every number in them has a source in the docs linked above.

<details>
<summary><b>Why DistilBERT, and why not something else?</b></summary>

Because iteration speed won the night. It is the smallest mature encoder whose fine-tune runs in two minutes on this data, and the field already ships this model class.

- The class was set by what production systems ship. LiveKit's text turn detector runs at 5 ms inference, smart-turn at 12 ms on CPU.
- 66M parameters in six layers, about 97% of BERT-base on its paper's benchmarks, with the most mature Hugging Face and ONNX path of any small encoder.
- Two-minute fine-tunes bought nine audited iterations in one night. The uncased variant matches ASR text, lowercase with no punctuation.
- Not compared: MiniLM-L6, DeBERTa-v3-small, ELECTRA-small, ModernBERT, SmolLM2-135M. The from-scratch lane is the one comparison that ran.

</details>

<details>
<summary><b>Why int8, and what did it cost?</b></summary>

Standard CPU serving economics. Smaller artifact, faster inference, near-zero accuracy loss, and the one real cost it charged is documented and fixed.

- Dynamic int8 through ONNX Runtime quantizes the linear layers; classification tolerates it well.
- The bill: quantization moved a near-threshold score from 0.26 to 0.41 and broke a tier-1 gate twice.
- The fix: v9 picks the threshold on the served int8 artifact, one row at a time, because int8 dynamic quantization is batch-composition-dependent. The gate went 12 of 12.
- Not measured: fp32 against int8 latency head-to-head on one box.

</details>

<details>
<summary><b>Why 0.42, and not 0.5 or the 0.83 the cost ratio implies?</b></summary>

Because the model runs under-confident (ECE 0.16), the 1:5 cost ratio is applied to the measured curve instead of the closed-form 0.833 it implies.

- The pick minimizes five false speaks plus one false wait on the judged dev set.
- The sweep is constrained, not free: all twelve tier-1 probes must stay green on the served artifact.
- Selection on synthetic validation drifted the dial to 0.87 twice, in v3 and v4. That lesson is why the dev set exists.
- The dial ships as data next to the weights and every run re-derives it.

</details>

<details>
<summary><b>Why create the data instead of finding a dataset?</b></summary>

Because no public end-of-turn dataset exists. The builders in this space, LiveKit and pipecat, each made their own.

- Policy-driven synthesis buys auditability (every row traces to a written rule), byte-reproducibility (seeded, no LLM), and zero personal data.
- Mining YouTube was rejected on licensing and cleaning cost inside a four-day window.
- The known cost of synthesis, a creator's blind spots, is what the three referees exist to catch.
- Caught once in the act: the model learned the vendor's barge-in after "one more thing" from real-call rows. A policy filter and a relabel removed it.

</details>

<details>
<summary><b>What is the honest ceiling of a text-only model?</b></summary>

Prosody. The question-ness of an unpunctuated yes-no question lives in the caller's rising tone, and the ASR discards it before the model ever sees the turn.

- Both models miss the same probe, "do i need a lumper receipt for this one", scoring about 0.02 as a cutoff.
- Agent context fixes it today: recall 1.00 with context against 0.47 bare, the known weak slice.
- Audio features are the roadmap answer.
- It enters the regression slice paired with its fix, since that file's contract is that every row passes.

</details>

<details>
<summary><b>Did you benchmark against the vendor's turn-taker?</b></summary>

Not head-to-head yet, on purpose. The submission uses the vendor's transcripts, overrules its decisions where they contradict the policy, and saves the bake-off for shadow deployment.

- Real-call slices ride the vendor's ASR output, which is the deployment condition.
- Where the vendor turn-taker contradicted the written policy, the label was corrected and flagged policy_corrected.
- The residual bias is stated in EVALS.md: cut points still come from the vendor stack, so the real-call bands read as pessimistic bounds.
- The roadmap chapter is online shadow on a real phone number, disagreements published.

</details>

<details>
<summary><b>How does this run at a million calls a month?</b></summary>

Shadow the incumbent, mine the disagreements, and spend human review only where the two models differ.

- Twenty million monthly decisions cannot be reviewed, and agreements are cheap; disagreements are the information-dense turns.
- Sampled disagreements get human labels against the policy, then feed back as training rows and referee rows.
- The disagreement rate itself is a drift alarm that fires before anyone labels anything.
- The pattern already ran here three times in miniature: the vendor-import catch, the judge panel's splits, and the probe page's shared miss. ROADMAP.md has the ladder.

</details>

<details>
<summary><b>What was measured, and what was not?</b></summary>

Every number on this page is measured on the served int8 artifact. Four things are explicitly not, so silence never reads as a claim.

- Not measured: fp32 against int8 latency on one box.
- Not measured: judge retry variance. Each judge voted once per card, and three vendors is diversity, not retries.
- Not measured: base-model alternatives to DistilBERT.
- One bench was discarded as thermal pollution after back-to-back trainings; every quoted bench comes from a quiet machine.

</details>
