<p align="center">
  <img src="assets/hero.svg" alt="fine-tuning-turn-detection-model: an end-of-turn detector for voice agents that scores 0.949 on a frozen human gold set with zero false interruptions, 0.913 on held-out real calls, and answers in 58 ms p95 on int8 CPU at threshold 0.42" width="100%">
</p>

<p align="center">
  <a href="https://github.com/jameswniu/fine-tuning-turn-detection-model/actions/workflows/ci.yml"><img alt="ci" src="https://github.com/jameswniu/fine-tuning-turn-detection-model/actions/workflows/ci.yml/badge.svg?branch=master"></a>
  <img alt="gold set: 60 cards, frozen" src="https://img.shields.io/badge/gold_set-60_cards_%C2%B7_frozen-f5b342?style=flat-square&labelColor=0b0d10">
  <img alt="referees: gold, regressions, real calls" src="https://img.shields.io/badge/referees-gold_%C2%B7_regressions_%C2%B7_real_calls-5c5853?style=flat-square&labelColor=0b0d10">
  <img alt="tier-1 gates: 12 of 12 green on the served artifact" src="https://img.shields.io/badge/tier--1_gates-12%2F12_served_int8-5c5853?style=flat-square&labelColor=0b0d10">
  <img alt="judge panel: 3 vendors, 90 blind cards" src="https://img.shields.io/badge/judges-3_vendors_%C2%B7_90_blind_cards-5c5853?style=flat-square&labelColor=0b0d10">
  <img alt="figures: regenerated from constants, checked in CI" src="https://img.shields.io/badge/figures-from_constants_%C2%B7_CI_checked-5c5853?style=flat-square&labelColor=0b0d10">
</p>

**Given the agent's last line and the caller's words so far, decide whether the caller is done talking.** The fine-tuned DistilBERT ships, as int8: 0.949 PR-AUC on a frozen human gold set with zero interruptions, 0.913 on held-out real calls, 58 ms p95 on CPU. A 7.4M encoder trained from scratch beat it on the policy probes and lost on unseen real calls, the referee that matters most.

Watch it score a call below. Read the write-up in [docs/approach.md](docs/approach.md). Run it with `make serve`. Every claim here is checked against the artifact that ships, at the [six places listed in the Q&A](#qa). The depth sits next to the code: [POLICY.md](POLICY.md) is the human turn policy everything hangs off, [EVALS.md](EVALS.md) the gates and bands, [iterations.md](iterations.md) the audit trail of every run including the failures, [data/README.md](data/README.md) the dataset card.

## The five hard problems in end-of-turn detection

Deciding whether a caller has finished is not a punctuation problem. Five things make it hard. Four are answered here; the honest status of the fifth is in the right column.

| | The problem | Where this stack stands |
|---|---|---|
| 1 | **A complete sentence is not a complete turn.** "Anything else?" answered with "actually yeah, one more thing." is grammatically finished and conversationally wide open. | Answered. Announced continuation is its own policy class and one of the twelve tier-1 constraints on the served artifact. It scores 0.035 and holds. |
| 2 | **The two mistakes do not cost the same.** Interrupting a caller is a different failure from making one wait, so accuracy is the wrong objective. | Answered. The threshold comes from a 1:5 cost ratio rather than 0.5, landing at 0.42, and the model speaks over none of the 27 wait cards in the gold set. |
| 3 | **There is no ground truth, only a policy.** Two careful annotators disagree about the same pause. A label set with no written rule behind it is one person's ear. | Answered. [POLICY.md](POLICY.md) came before the data: sixty cards blind-labeled against it, seven marked unsure on purpose, and three vendor judges hit 53 of 53 while going unsure on exactly those seven. |
| 4 | **The model you measure is not the model you ship.** Quantization moves scores near the threshold, so a number picked on the checkpoint can be wrong on the artifact in the container. | Answered, after two red iterations. One constraint card read 0.26 on the fp32 checkpoint, 0.381 batched, and 0.412 through the serving path. Picking on the checkpoint left tier-1 red; re-picking on the int8 stayed red because the guardrail check was itself batching all twelve rows into one call. Selection now scores one row at a time, the way serving does. |
| 5 | **Text has no prosody.** Falling pitch and a trailing vowel are what a human hears. A transcript carries neither. | Not answered, because it cannot be answered here. The ceiling is the input, not the model. Trailing hedges score 0.20, time requests 0.50, and recall falls from 1.00 to 0.47 when the agent's last line is missing. The fix is an audio path into the detector, and there are three in rising cost. Word timings from the ASR response give final lengthening for free, a small parallel audio model gives the rest, and tapping the ASR encoder gives it at zero marginal compute if you host your own. |

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

make synth        # regenerate the English training set (seeded, byte-identical)
make tier1        # derive the twelve guardrail rows from the committed data
make train        # fine-tune the DistilBERT lane, export ONNX + int8
make threshold    # re-pick the operating point on the served int8 file, one row per call
make eval         # score a model against the frozen gold set
make serve        # FastAPI on :8000, with a live probe page at /
make bench        # async stress test, latency percentiles + throughput
make docker-build && make docker-run && make smoke   # the int8 model in a container
make corpus       # one-time, builds the scratch lane's data (adds the datasets package)
make pretrain     # ~15 min, our own masked-language-model base
make scratch      # fine-tune that base into the 7.4M from-scratch model
```

**What a clean clone reproduces.** Run that block top to bottom.

- `make synth` rewrites `data/train.jsonl` byte for byte.
- `make tier1` derives the same twelve guardrail rows.
- The probe cases below come out wait, speak and wait as described.

**What it will not reproduce is the digits.** Weights are not committed and `models/` is ignored, so `make train` builds a new model rather than restoring the frozen v9 one.

- Two clean-clone runs on this laptop read 0.968 and 0.966 gold PR-AUC, against the 0.949 quoted here.
- They picked 0.71 and 0.63 where the frozen artifact sits at 0.42. Expect that spread rather than a matching number.
- `make threshold` re-picks the operating point on whatever you just built, under the same twelve constraints, which is the path that produced 0.42.

**Two files stay out of reach by design.** `data/ood_test.jsonl` and `data/ood_train.jsonl` are real call content that never leaves this machine, which is what the [dataset card](data/README.md) says. So `make scratch` in a clean clone trains on the synthetic corpus alone, without the real-register augmentation that carried the shipped model from 0.60 to 0.825 on real calls.

Every figure here is regenerated from the frozen artifacts, so the README describes the v9 freeze rather than whatever your box just trained.

The `/` page re-scores as you type, at most once per word, against the served int8 model. Word granularity is what streaming ASR hands a detector. Eight cases from the gold set, one clip each, results first. Every one of these is a case you can type yourself once `make serve` is up.

**A complete statement speaks.** The agent opened the call and the caller says why they are calling.

<p align="center"><img src="assets/probe-statement.gif" alt="Typing a full sentence confirming a pickup after the agent's greeting: the score climbs to 0.99 and the chip flips to speak" width="100%"></p>

**A mid-readout holds.** The agent asked for the MC number and the caller is halfway through the digits; the policy makes this an absolute wait.

<p align="center"><img src="assets/probe-readout.gif" alt="Typing yeah it is four one five after the agent asks for an MC number: the score stays near 0.01 and the chip reads keep listening" width="100%"></p>

**A complete question speaks.**

<p align="center"><img src="assets/probe-question.gif" alt="Typing a full question about detention policy: the score climbs to 0.99 and the chip flips to speak" width="100%"></p>

**A complete answer speaks.** The agent asked about an appointment and the caller answered it.

<p align="center"><img src="assets/probe-complete.gif" alt="Typing yeah, I can make it after the agent asks about an appointment: the score climbs to 0.99 and the chip flips to speak" width="100%"></p>

**An announced continuation holds, even though the sentence is complete.** The agent asked "Anything else?" and the caller says there is more coming.

<p align="center"><img src="assets/probe-onemore.gif" alt="Typing actually yeah, one more thing after the agent asks anything else: the score stays near 0.04 and the chip reads keep listening" width="100%"></p>

**A self-interrupt holds.** The caller restarts mid-sentence; the new thought is coming.

<p align="center"><img src="assets/probe-restart.gif" alt="Typing can you, actually, you know what: the score stays near 0.01 and the chip reads keep listening" width="100%"></p>

**An explicit hold holds silently.** The caller is retrieving something themselves.

<p align="center"><img src="assets/probe-hold.gif" alt="Typing hang on, let me grab the load number: the score stays near 0.01 and the chip reads keep listening" width="100%"></p>

**A casual closer speaks.** "nah bye" is the miss a live poke found in v5, and the regression slice now guards it.

<p align="center"><img src="assets/probe-nahbye.gif" alt="Typing nah bye: the score climbs to 0.97 and the chip flips to speak" width="100%"></p>

Where it is weak, stated plainly: the judgment-class speaks. A reported-speech hedge ("the broker said it was covered, supposedly..."), a full retraction ("no, scratch that..."), and a narrated interruption ("the receiver is waving at me...") all score under the threshold today, which is what the hedge 0.20 and K 0.50 rows in EVALS.md say and what the Q&A below explains. The from-scratch and Spanish lanes have their own entry points, listed in the map below.

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
| Spanish probes (6) | Flat 0.75 on all six, three wrong | All six right |

On the 29 English probes the two tie at 28 each and share one miss, an unpunctuated yes-no question both read as a cutoff; the margin is entirely Spanish, which the shipping model never trained for. The fine-tune ships because it leads on unseen real calls, the referee that matters most. [docs/probe-comparison.html](docs/probe-comparison.html) holds every probe, regenerated by `probe_compare.py`.

## How the operating point is chosen

The model outputs a probability that the caller is done. The threshold is the line where the agent starts speaking, and it is the most consequential number in the system, so a written rule picks it and every run re-derives it. Three steps.

1. **Start from the cost ratio.** The policy says one interruption costs as much as five slow replies. So the sweep tries every threshold from 0.01 to 0.99 on the 30 judged dev cards and keeps the one with the lowest cost, counted as five times the false-speak rate plus the false-wait rate. Rates rather than counts, so a lopsided card mix cannot tilt the answer.
2. **Throw out any threshold that breaks a rule that must never break.** Twelve cards are pinned: every gold readout card, the gold "one more thing" card, its dev-set twin, and the six misses a live poke found. A threshold that gets any of them wrong is off the table, whatever its cost score. If none survive, the run fails loudly instead of shipping a broken guardrail.
3. **Score the artifact that ships, the way it ships.** The int8 model's scores shift with whatever else is in the batch, so every pinned card is scored alone, exactly as serving does. In v8 the same card read 0.381 in a batch and 0.412 alone, and 0.412 is the one that matters. The winner is written to `threshold.json` next to the weights, and `serve.py` reads it at startup.

The table is the audit trail: nine runs, the threshold each picked, and what it taught. ECE is calibration error, lower is better.

| Run | Threshold | Gold PR-AUC | False-speak | ECE | What it taught |
|---|---|---|---|---|---|
| v1 | 0.833 | 0.961 | 0.00 | N/A | The textbook 5/6 bar assumes a calibrated model; this one is under-confident, so recall was only 0.58 |
| v2 | 0.61 | 0.964 | 0.00 | 0.114 | Picking the threshold on the measured curve instead brought recall to 0.81 |
| v3 | 0.87 | 0.970 | 0.00 | 0.067 | Picking it on synthetic validation data pushed it high; that data is easier than real speech |
| v4 | 0.86 | 0.969 | 0.00 | 0.070 | Switching the objective from counts to rates did not fix it; the synthetic set itself was the problem |
| v5 | 0.81 | 0.958 | 0.00 | 0.092 | A human typing "nah bye" into the live page got wait; casual speech was added and the regression file started |
| v6 | 0.18 | 0.955 | 0.037 | 0.169 | A judged dev set and real-call rows replaced synthetic validation; the threshold collapsed and "one more thing" started getting interrupted |
| v7 | 0.27 | 0.949 | 0.00 | 0.160 | The twelve pinned cards became hard constraints; passed on the fp32 model, failed on the int8 model that actually serves |
| v8 | 0.40 | 0.949 | 0.00 | 0.160 | Re-picked on int8, 11 of 12; the picker scored cards in a batch while serving scores one at a time |
| v9 | 0.42 | 0.949 | 0.00 | 0.160 | Scored one card at a time, 12 of 12; real calls 0.913 PR-AUC, recall 0.959 |

The last three rows share one set of weights. Nothing about the model changed between v7 and v9; the measuring instrument did. That is what the loop exists to surface. The eval gets debugged as hard as the model, and every fix was the same fix: measure the artifact that ships, in the shape it ships.

## The policy, as rows

Sixty blind labels became eleven classes with a rule each, and `synth.py` turns the rules into rows. Every training line traces to one of these.

| Class | Shape | Example, from the gold set | Decision |
|---|---|---|---|
| A | Complete statement | "Hey, I'm calling to confirm the pickup for load four seven two tomorrow morning." | Speak |
| B | Complete question | "What's the detention policy if I'm stuck at the dock past two hours?" | Speak |
| C | Bare acknowledgement | "Okay, got it." | Speak; a complete turn but never a call-ender |
| D | Mid-clause cutoff | "Can you tell the receiver that my ETA is now..." | Wait |
| E | Disfluent trail | "Yeah so, um, the thing is, uh..." | Wait |
| F | Mid-data readout | "Yeah, it's seven one five..." after "Can I get your MC number?" | Wait, absolute, however long the pause runs |
| G | Connector-final | "I can pick up Thursday morning, but..." | Wait |
| H | Complete, then maybe more | "Yeah, I can make it." speaks; "Actually yeah, one more thing." after "Anything else?" holds | Speak, unless continuation is announced |
| I | Trailing hedge | "That's all I need, I guess..." | Speak by default; a decorative softener on an owned claim mid-narrative holds |
| J | Self-interrupt restart | "Can you- actually, you know what..." holds; "I need the- no, scratch that..." speaks | Wait; a full retraction may earn a brief acknowledgement |
| K | Explicit hold | "Hang on, let me grab the load number..." holds; "Hold on, the receiver is waving at me..." speaks | Self-retrieval holds silently; a narrated outside interruption gets a courtesy acknowledgement |

Class I is the judgment call worth reading, because it looked like a contradiction in the labels and turned out to be the rule. "The broker said it was covered, supposedly..." was labeled speak; "The detention was approved, or something..." was labeled wait. The hedge word carries no turn signal. What decides is stance and ownership. A claim attributed to someone else is a question in disguise, so the agent speaks to confirm. An owned first-person claim with a habitual softener is just a statement, so it follows the statement rules. Attribution markers versus first-person assertion are surface features a text model can learn, which is why the ruling is trainable and not only philosophy.

**Four augmentations bake in deployment realism.**

- Complete utterances are re-emitted truncated mid-sentence and labeled wait, the shape of an ASR partial.
- Every row ships lowercased with terminal punctuation stripped, so the model cannot lean on periods.
- Contexted rows are emitted bare as well, so it works with and without the agent's last line.
- From v6, real-call rows from the author's production voice agent join the training half at four-fold weight, grouped by call so no call leaks into the referee.

The counts: 1,586 training rows, 60 gold cards (53 hard, 7 boundary), 30 judged dev cards, 6 regressions, 400 real turns split 304 to 96 by call.

## Serving, measured

The contract is one endpoint. `POST /predict` takes `{context, text}` and returns `{p_complete, decision, threshold, model_latency_ms}`; `/healthz` reports the model directory. The model runs as ONNX Runtime with dynamic int8 quantization on CPU, and the Docker image serves only the int8 artifact. Two bench runs are quoted on purpose, because they disagree and the disagreement is a finding.

| Box state | C1 req/s, p95 | C8 req/s, p95 | Model p50 at c8 |
|---|---|---|---|
| Quiet machine | 55, 21.2 ms | 316, 32.8 ms | 21.7 ms |
| Mid training load | 28, 42.5 ms | 170, 57.9 ms | 39.5 ms |

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
assets/             the figures and the eight probe clips
data/               gold set (frozen), generated training sets, judge votes, dataset card
docs/               approach doc, judge replay, probe page, video script
```

Generated reports (eval_report*.json, bench_report*.json, regression_report.json) are build artifacts and stay untracked; every number in the figures and the docs comes from them at freeze time, and `make figures-check` fails if a figure drifts from its constants.

## Q&A

Short answers, expandable. Every number in them has a source in the docs linked above.

<details>
<summary><b>Where do you actually verify this?</b></summary>

At six places, and the rule at every one is to check the artifact that ships, not the one that trained.

- CI checks the data before any training runs. The gold set must be exactly 60 cards at its frozen threshold, and no gold text may appear in `data/train.jsonl`, so the referee cannot leak into what it referees.
- The labels were verified before they were trusted. The 30 dev cards went to three vendor judges with the 60 human gold cards hidden among them, and a judge's dev votes counted only because it reproduced the human's call 53 times out of 53.
- The threshold is picked against the served int8 file, one row per call, the shape `serve.py` actually sends. That is the fix for the bug that ate two iterations. The fp32 checkpoint held a card at 0.26, batched int8 scoring said 0.381, and the real one-row path returned 0.412, which crossed the line and spoke over the caller.
- Twelve tier-1 cards encode the policy's absolutes and must be green on the served artifact every run. When no threshold satisfies all twelve, `pick_threshold.py` fails loud instead of shipping a number.
- Three referees score a model that trained on none of them: 60 frozen gold cards, 6 regression cards each traced to a live miss, and 96 turns from 60 real calls. `make eval` prints all three.
- `make bench` hits the exact container artifact, on an idle machine. A bench taken right after training read 274 req/s where a clean re-run minutes later read 588, so every quoted number comes from a quiet box.

Then by hand, at `make serve`. Typing at the live page is what found the casual-register gap: "nah bye" scored 0.34 and held the turn. That became a regression card, then training data, then a fix.

Every figure here is regenerated from those same artifacts, and `python draw_figures.py --check` fails the build when a number drifts.

</details>

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

Not head-to-head yet, on purpose. The shipped model uses the vendor's transcripts, overrules its decisions where they contradict the policy, and saves the bake-off for shadow deployment.

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
