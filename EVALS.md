# Evals: the target bands the loop iterates against

The gold set (data/gold_set.json) defines what good means; POLICY.md defines the invariants. This file defines the ONE: pass/fail gates and numeric bands, so each iteration of the loop (synthesize, train, evaluate) has an unambiguous verdict. Industry anchors below were verified against primary sources by a two-engine research pass on 2026-08-24 (lead scan cross-refuted).

## Industry anchors (verified)

| Reference | Number | Source |
|---|---|---|
| LiveKit turn detector v1, false-cutoff at fixed latency budget | 9.9% at 300 ms, 4.5% at 600 ms | livekit.com/blog/solving-end-of-turn-detection |
| LiveKit v1, mean latency at fixed false-cutoff target | 543 ms at 5%, 295 ms at 10% | same post; eot-bench |
| LiveKit model card, per-language rates (text model) | TPR ~99%, TNR 85 to 96% | huggingface.co/livekit/turn-detector |
| LiveKit v1.2.2-en (text-only, third party) | 5 ms inference, 24 ms p90 | benchmarks.speko.ai |
| Smart Turn v2 per-language accuracy | 91 to 97% (EN 94.3%), 99% on held-out human English | huggingface.co/pipecat-ai/smart-turn-v2 |
| Smart Turn v2/v3 inference | 12 ms L40S (v2); 12 ms modern CPU, 59.8 ms small cloud CPU (v3) | daily.co blog |
| Named production operating points | 5% and 10% false-cutoff; 300/600 ms latency budgets | LiveKit benchmark framing |
| Published industry PR-AUC or F1 band | none exists; the field reports false-cutoff vs latency | confirmed absent by both engines |

Two framing consequences. The field's headline metric pair is false-cutoff rate versus endpoint latency, so ours is too, with classifier metrics as supporting detail. And since no public PR-AUC band exists, our PR-AUC bar is self-set above our own v1 baseline, stated as such.

## Tier 1: deterministic guardrails (code, hard pass/fail, every run must be all green)

These are the absolute rules from POLICY.md turned into gates. One red blocks the iteration from being called an improvement, whatever the aggregate metrics say.

| Gate | Check |
|---|---|
| Never interrupt a readout | zero false-speak across every F-class gold card and a fixed synthetic F probe set |
| Announced continuation holds | every "one more thing" style card predicts wait at the operating threshold |
| Frozen referee integrity | gold_set.json content hash unchanged; no gold text appears in train.jsonl |
| Reproducibility | synth.py regenerates train.jsonl byte-identically at the pinned seed |
| Serving contract | /predict returns p_complete, decision, threshold, model_latency_ms; /healthz ok; ONNX int8 loads on CPU; Docker image builds and serves |
| Latency budget (the brief's own bar) | end-to-end p95 under 100 ms at concurrency 8 on the dev machine |
| Probe-found regressions | every case in data/regressions.jsonl predicts its label at the operating threshold; this slice tests memory of fixed failures, not generalization, so overlap with training data is intended | check each run |

## Tier 2: statistical bands (measured every iteration; in-band = good, out = iterate)

| Metric | Band | v1 reading | Verdict |
|---|---|---|---|
| PR-AUC on gold hard set | at or above 0.95 | 0.961 | in band |
| False-speak rate at operating point | at or below 4% (LiveKit's best published is 4.5%) | 0% | in band |
| Recall of true speaks at operating point | 0.85 target, 0.90 stretch | 0.77 at the measured best point | ITERATE |
| Anchor classes (A to G) at operating point | each at or above 0.90 | A 0.67, B 0.75 at the uncalibrated 0.833 bar; re-read at the measured operating point after threshold fix | ITERATE |
| Judgment classes (H to K) at operating point | each at or above 0.60 | H 1.00, J 0.86, K 0.50, hedges 0.20 | ITERATE (hedges, K) |
| Boundary cards (the 7 unsure) | mean p in 0.35 to 0.65; zero confidently wrong (over 0.9 or under 0.1) | mean 0.44 | in band (verify zero-confident count each run) |
| ASR-robustness delta | asr-variant slice within 5 points of clean slice on recall | to be measured | measure in v2 |
| Model-only inference | p50 at or below 15 ms CPU (anchors: 12 ms smart-turn v3, 5 ms LiveKit text) | to be measured | measure in v2 |
| Throughput sanity | at or above 200 req/s single worker (1M calls/month at ~20 turns each averages under 10 decisions/s; 200 gives burst headroom) | to be measured | measure in v2 |
| Prefix stability (streaming) | at most 1 decision flip per utterance replayed word by word; no early commit before 60% of the utterance on true-speak cards | to be measured | measure in v2 |
| Calibration (ECE, 10 bins) | at or below 0.10 on gold hard set | to be measured (known under-confident) | measure in v2 |
| Context dependence slice | recall delta with vs without agent context within 10 points | to be measured | measure in v2 |
| Length slice | recall on 1-3 word utterances within 10 points of overall | to be measured | measure in v2 |
| Real-call OOD holdout (data/ood_test.jsonl, 96 turns from 60 production calls, self-labeled, never trained on) | PR-AUC at or above 0.85 and false-speak at or below 10% at the operating threshold; bands read as pessimistic bounds since labels derive from the vendor turn-taker and prefix cuts, and the small n gives wide intervals | v5 fine-tune reads PR-AUC 0.65, false-speak 0.57, recall 0.84 at the 0.81 threshold; the full 400-row slice reads 0.61 after sentence-boundary label cleanup, so the register gap is the model, not the labels | ITERATE (the v6 target: real-register augmentation from ood_train) |

A scoping note that is itself a finding: this eval suite needs no LLM-judge tier. Given fixed weights the model's output is a deterministic probability, so every check here is computable by code; the only non-determinism lives in training and is pinned by seeds. Judges are for outputs code cannot grade. At production scale the judge-shaped work reappears as human labeling of sampled live turns, not as an offline eval.

## The operating threshold rule

The cost ratio (1:5, from the gold set) picks the operating point ON THE MEASURED validation curve, minimizing expected cost 5*FP + FN, not the closed-form 0.833, because measured probabilities run under-confident. Each training run recomputes and records the cost-optimal threshold; serving reads it. Temperature calibration is the alternative route if the recomputed threshold drifts run to run.

## The loop

synthesize -> train -> evaluate against this file -> if any Tier 1 gate is red, fix that first -> else improve the worst out-of-band Tier 2 row, usually with data diversity, not architecture -> repeat. Each iteration appends one row (run id, data size, threshold, the two headline numbers, what changed) to iterations.md, so the improvement story is auditable end to end.
