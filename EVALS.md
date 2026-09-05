# Evals: the target bands the loop iterates against

The gold set (data/gold_set.json) defines what good means; POLICY.md defines the invariants. This file defines the ONE: pass/fail gates and numeric bands, so each iteration of the loop (synthesize, train, evaluate) has an unambiguous verdict. Industry anchors below were verified against primary sources by a two-engine research pass on 2026-08-24 (lead scan cross-refuted).

## Industry anchors (verified)

| Reference | Number | Source |
|---|---|---|
| LiveKit turn detector v1, false-cutoff at fixed latency budget | 9.9% at 300 ms, 4.5% at 600 ms | Livekit.com/blog/solving-end-of-turn-detection |
| LiveKit v1, mean latency at fixed false-cutoff target | 543 ms at 5%, 295 ms at 10% | Same post; eot-bench |
| LiveKit model card, per-language rates (text model) | TPR ~99%, TNR 85 to 96% | Huggingface.co/livekit/turn-detector |
| LiveKit v1.2.2-en (text-only, third party) | 5 ms inference, 24 ms p90 | Benchmarks.speko.ai |
| Smart Turn v2 per-language accuracy | 91 to 97% (EN 94.3%), 99% on held-out human English | Huggingface.co/pipecat-ai/smart-turn-v2 |
| Smart Turn v2/v3 inference | 12 ms L40S (v2); 12 ms modern CPU, 59.8 ms small cloud CPU (v3) | Daily.co blog |
| Named production operating points | 5% and 10% false-cutoff; 300/600 ms latency budgets | LiveKit benchmark framing |
| Published industry PR-AUC or F1 band | None exists; the field reports false-cutoff vs latency | Confirmed absent by both engines |

Two framing consequences. The field's headline metric pair is false-cutoff rate versus endpoint latency, so ours is too, with classifier metrics as supporting detail. And since no public PR-AUC band exists, our PR-AUC bar is self-set above our own v1 baseline, stated as such.

## Tier 1: deterministic guardrails (code, hard pass/fail, every run must be all green)

These are the absolute rules from POLICY.md turned into gates. One red blocks the iteration from being called an improvement, whatever the aggregate metrics say.

| Gate | Check |
|---|---|
| Never interrupt a readout | Zero false-speak across every F-class gold card and a fixed synthetic F probe set |
| Announced continuation holds | Every "one more thing" style card predicts wait at the operating threshold |
| Frozen referee integrity | Gold_set.json content hash unchanged; no gold text appears in train.jsonl |
| Reproducibility | Synth.py regenerates train.jsonl byte-identically at the pinned seed |
| Serving contract | /predict returns p_complete, decision, threshold, model_latency_ms; /healthz ok; ONNX int8 loads on CPU; Docker image builds and serves |
| Latency budget (the brief's own bar) | End-to-end p95 under 100 ms at concurrency 8 on the dev machine |
| Probe-found regressions | Every case in data/regressions.jsonl predicts its label at the operating threshold; this slice tests memory of fixed failures, not generalization, so overlap with training data is intended | Check each run |

## Tier 2: statistical bands (measured every iteration; in-band = good, out = iterate)

| Metric | Band | Reading on the shipped v9 int8 artifact at 0.42 | Verdict |
|---|---|---|---|
| PR-AUC on gold hard set | At or above 0.95 | 0.949 on the 53 hard cards | 0.001 under the band, accepted under the promotion rule's 0.02 tolerance |
| False-speak rate at operating point | At or below 4% (LiveKit's best published is 4.5%) | 0 of the 27 gold wait cards, and 11 of the 47 real-call wait turns, a rate of 0.234 | In band on gold, out of band on real calls |
| Recall of true speaks at operating point | 0.85 target, 0.90 stretch | 0.654, 17 of the 26 gold speak cards | ITERATE |
| Anchor classes (A to G) at operating point | Each at or above 0.90 | A through G all 1.00 | In band |
| Judgment classes (H to K) at operating point | Each at or above 0.60 | H 1.00, J 0.857, K 0.50, hedges (I) 0.20 | ITERATE (hedges, K) |
| Boundary cards (the 7 unsure) | Every card inside the 0.4 to 0.9 interval `evaluate.py` measures as `BOUNDARY_BAND`, which is what `count_in_band` counts, and zero confidently wrong (over 0.9 or under 0.1). That constant dates from the scaffold commit, when the threshold was the closed-form 0.833 that `train.py` line 23 still carries, and it was never re-centred on 0.42, so its floor now sits on the decision line | Mean 0.307, and 0 of 7 land inside the interval. Scored one row at a time the seven read 0.985, 0.026, 0.986, 0.068, 0.021, 0.045 and 0.016, so 7 of 7 are confidently wrong | ITERATE. A `count_in_band` of 0 is the worst reading here, not a pass |
| ASR-robustness delta | Asr-variant slice within 5 points of clean slice on recall | Not measured, since the gold set carries no asr-variant slice | Still open |
| Model-only inference | P50 at or below 15 ms CPU (anchors: 12 ms smart-turn v3, 5 ms LiveKit text) | 16.5 ms at concurrency 1 and 22.4 ms at concurrency 8, on the shipped file | ITERATE, and the 7.36M lane reads about 5 ms |
| Throughput sanity | At or above 200 req/s single worker (1M calls/month at ~20 turns each averages under 10 decisions/s; 200 gives burst headroom) | 312 req/s at concurrency 8, on the shipped file | In band |
| Prefix stability (streaming) | At most 1 decision flip per utterance replayed word by word; no early commit before 60% of the utterance on true-speak cards | Mean flips 0.58, max 4, early-commit rate 0.231 on true speaks | In band on flips, out on early commit |
| Calibration (ECE, 10 bins) | At or below 0.10 on gold hard set | 0.160, the model runs under-confident | ITERATE, temperature scaling is the queued fix |
| Context dependence slice | Recall delta with vs without agent context within 10 points | Recall 1.00 with context against 0.47 bare, a 53-point gap | ITERATE, the widest gap in the table |
| Length slice | Recall on 1-3 word utterances within 10 points of overall | 1.00 against 0.654 overall | Outside the band on the safe side, so not a risk |
| Real-call OOD holdout (data/ood_test.jsonl, 96 turns from 19 production calls, labels assigned by rule with no human pass, never trained on) | PR-AUC at or above 0.85 and false-speak at or below 10% at the operating threshold; bands read as pessimistic bounds since labels derive from the vendor turn-taker and prefix cuts, and the small n gives wide intervals | V9 at 0.42 on the served int8 reads PR-AUC 0.913, recall 0.959, false-speak 0.234 (v5 read 0.65 before real-register augmentation, so the gap closed by 26 points) | PR-AUC in band; false-speak reads above the line against this deliberately pessimistic referee, whose labels inherit the vendor turn-taker's cut points and were never corrected, since the policy filter matched no rows. The production-loop fix is disagreement-sampled human labels, not more synthesis |

A scoping note that is itself a finding: this eval suite needs no LLM-judge tier. Given fixed weights the model's output is a deterministic probability, so every check here is computable by code; the only non-determinism lives in training and is pinned by seeds. Judges are for outputs code cannot grade. At production scale the judge-shaped work reappears as human labeling of sampled live turns, not as an offline eval.

## Where the bands landed (v9 freeze, 2026-08-25)

Tier 1 is 12/12 on the served int8 artifact scored single-row, which is the only reading that counts. The 12 counts constraint cards, not the 7 named checks in the table above. `make_tier1_probes.py` expands those checks into 12 rows with a required decision each. On tier 2: gold PR-AUC 0.949 sits 0.001 under the 0.95 band, inside the promotion rule's 0.02 tolerance; that hair was traded knowingly for the casual-register and guardrail gains between v5 and v9. Prefix stability is in band (mean flips 0.58 against a ceiling of 1). Serving clears the brief's bar with margin. Benched against the shipped int8 file with the dev box at a load average near 4 of its 18 cores, the worst of four passes reads end-to-end wall p95 33.1 ms at concurrency 8 against the 100 ms budget, with model-only p95 30.4 ms and 312 req/s. The same file re-read mid-training-load gave wall p95 57.9 ms, model p95 48.2 ms and 170 req/s, which is a finding about the machine rather than a model change. The lighter-load number is the one quoted everywhere, and it names the box state instead of claiming an idle one. Every row that misses its band says so in the table above and carries its fix there. The three that matter most: gold recall reads 0.654 against the 0.85 target, 17 of the 26 speak cards, and the gap is the model leaving finished turns hanging rather than talking over anyone. Calibration reads ECE 0.160, the model runs under-confident, and the measured-curve threshold compensates today while temperature scaling is the queued fix. The context-dependence slice reads recall 1.00 with agent context against 0.47 bare, the known weak slice the casual-register work keeps chipping at. The fleet-wide scoreboard and the verdict under the promotion rule (the v9 fine-tune ships as default, mdistilbert-real2 is the multilingual variant, scratch-pre is the guardrail-clean small lane) live in iterations.md.

## The operating threshold rule

The cost ratio (1:5, from the gold set) picks the operating point ON THE MEASURED validation curve, minimizing expected cost 5*FP + FN, not the closed-form 0.833, because measured probabilities run under-confident. Each training run recomputes and records the cost-optimal threshold; serving reads it. Temperature calibration is the alternative route if the recomputed threshold drifts run to run.

## The loop

synthesize -> train -> evaluate against this file -> if any Tier 1 gate is red, fix that first -> else improve the worst out-of-band Tier 2 row, usually with data diversity, not architecture -> repeat. Each iteration appends one row (run id, data size, threshold, the two headline numbers, what changed) to iterations.md, so the improvement story is auditable end to end.
