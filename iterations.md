# Iteration Log

One row per loop iteration; the bands live in EVALS.md.

Read v1 through v8 as a build log rather than as reproducible measurements. Every run wrote its report to the same filename and the next run overwrote it, so no report file backs those readings today. The v9 row is the exception: it regenerates from the committed int8 artifact with `make eval`, `make tier1` and `make threshold`.

| Run | Date | Train size | Operating threshold | PR-AUC (gold hard) | False-speak rate at op | Recall at op | Hedge class acc | K class acc | Mean flips | ECE | What changed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 2026-08-24 | 914 | 0.833 (uncalibrated) | 0.961 | 0.00 | 0.577 | 0.20 | 0.50 | N/A | N/A | First full pass, Bayes threshold, found under-confidence |
| v2 | 2026-08-24 | 1133 | 0.61 | 0.964 | 0.00 | 0.808 | 0.60 | 0.75 | 0.38 | 0.114 | Cost-optimal threshold, hedge/K/general bank expansion, streaming + calibration evals added |
| v3 | 2026-08-24 | 1423 | 0.87 | 0.970 | 0.00 | 0.654 | 0.20 | 0.50 | 0.34 | 0.067 | Context-dropout augmentation targeting the bare-utterance recall gap |
| v4 | 2026-08-24 | 1423 | 0.86 | 0.969 | 0.00 | 0.654 | 0.20 | 0.50 | 0.34 | 0.070 | Threshold objective from counts to class-conditional rates after v3 showed selection was tracking synthetic label balance, not the model |
| v5 | 2026-08-24 | 1492 | 0.81 | 0.958 | 0.00 | 0.731 | 0.40 | 0.625 | 0.45 | 0.092 | Casual-register templates + Agent-prefix context normalization, found by live probe; regression slice added |
| v6 | 2026-08-25 | 1524 | 0.18 | 0.955 | 0.037 | 0.654 | 0.20 | 0.50 | 0.87 | 0.169 | Dev-set threshold from judge panel; ood_train x4 grouped by call; tpl-grouped split; texting register; ood_test PR-AUC 0.905 false-speak 0.34 recall 0.98; regressions 6/6 |
| v7 | 2026-08-25 | 1586 | 0.27 | 0.949 | 0.00 | 0.654 | 0.20 | 0.50 | 0.75 | 0.160 | Guardrail-constrained dev threshold via pick_threshold.py (12 tier-1 cards, admissible 71/99); policy-filtered 0 vendor-behavior rows from extra; announced-continuation bank reinforced (+6 templates); ood_test PR-AUC 0.913 false-speak 0.277 recall 0.980; regressions 6/6; tier1 announced-continuation RED on the served int8 model (F1-F4 and gold H5 hold at wait, but dev dH4 flips to speak at p=0.41 under int8 quantization even though the fp32 checkpoint used for constrained selection correctly holds it at p=0.26, just under the 0.27 threshold; the guardrail was enforced against the wrong artifact) |
| v8 | 2026-08-25 | 1586 | 0.4 | 0.949 | 0.00 | 0.654 | 0.20 | 0.50 | 0.62 | 0.160 | Threshold re-picked on the served int8 artifact via pick_threshold CLI (quantization shifts near-threshold scores; verify the artifact that ships); tier1 11/12 RED, dH4 still fails (pick_threshold's own guardrail check batches all 12 constraint rows into one inference call and scored dH4 at p=0.381, accepting 0.4 as admissible; int8 dynamic quantization is batch-composition-dependent, so that batched score does not match what serve.py's real one-row-at-a-time path returns, which is p=0.412, crossing 0.4 to speak; verified by direct single-row scoring of all 12 probes against the int8 model, matching serve.py's request shape); ood_test PR-AUC 0.913 false-speak 0.234 recall 0.959; regressions 6/6 |
| v9 | 2026-08-25 | 1586 | 0.42 | 0.949 | 0.00 | 0.654 | 0.20 | 0.50 | 0.58 | 0.160 | Selection now scores one row per call matching serving (pick_threshold.py) (int8 quantization is batch-composition-dependent); threshold 0.42; tier1 12/12; ood_test PR-AUC 0.913 false-speak 0.234 recall 0.959; regressions 6/6 |

## Fleet lanes (2026-08-25 freeze)

The from-scratch and multilingual lanes ran in a second session against the same referees, the same POLICY.md, and the same pick_threshold CLI (single-row int8 scoring). One scoreboard, one verdict under the written promotion rule: within 0.02 gold PR-AUC of the incumbent, no gold false-speak regression that a guardrail cannot explain, no OOD collapse.

| Model | Params | Op threshold (int8, single-row) | Gold PR-AUC | Spanish eval PR-AUC | Real-call PR-AUC (n 96) | ECE | Tier-1 | Role |
|---|---|---|---|---|---|---|---|---|
| eot-distilbert v9 | 66.96M | 0.42 | 0.949 | N/A (EN only) | 0.913 | 0.160 | 12/12 | Ships as the default |
| mdistilbert-real2 | 135.33M | 0.97 | 0.979 | 1.00 | 0.875 | 0.35 | Pass (4 admissible) | Multilingual variant |
| scratch-pre | 7.36M | 0.79 | 0.973 | 1.00 | 0.825 | 0.062 | Pass (guardrail-clean) | Small fast lane |
| scratch-real | 3.99M | 0.95 | 0.994 | 0.996 | 0.597 | N/A | N/A | Tradeoff exhibit (no pretrain) |
| scratch-pre2 | 7.36M | 0.98 | 0.976 | 1.00 | 0.810 | 0.107 | Unsatisfiable | Replication attempt |

Per-lane notes, kept honest:

- mdistilbert-real2 is the vintage-bank retrain that fixed the hold-that-thought inversion: its predecessor was tier1_unsatisfiable, this one has 4 admissible thresholds. Per-class perfect on gold except J 0.57 and K 0.875. Its ood_test moved 0.912 to 0.875 against the first real mix; read as small-n movement at n 96, stated rather than hidden. Calibration (ECE 0.35) is its weak point.
- scratch-pre (own byte-level BPE tokenizer at 16,000 pieces, small encoder, fifteen-minute MLM pretrain on our own corpora, real-call augmentation) is the from-scratch flagship: constrained dev-set pick at 0.79 with 60 admissible thresholds. At that operating point: gold false-speak 0.037 (one wait card of 27) with recall 0.923, Spanish false-speak 0.000 with recall 1.000, real calls false-speak 0.277 with recall 0.755. The checkpoint dir briefly carried a training-time 0.95 pick and the served dir won, per the same verify-the-artifact rule v8 bought. Served bench on the exact shipped artifact, end-to-end wall time from the client: 588 req/s at concurrency 8, wall p50 12.1 ms and wall p95 20.7 ms, model p50 about 5 ms.
- scratch-real (same architecture, real-call augmentation, no pretrain) holds the best gold sweep of the fleet, 0.994 with zero false-speak, and collapses to 0.597 on unseen real calls. That pairing is the story: pretraining traded a sliver of gold-set fit for 23 points on the referee that matters.
- scratch-pre2 is the replication attempt on the refreshed banks and it lost ground where it counts: ECE 0.107 vs 0.062, ood 0.810 vs 0.825, and tier-1 went unsatisfiable. The same refresh that fixed the multilingual model destabilized a small model that was already balanced; a data fix is not monotone across model sizes, so every lane re-runs the referees after a shared bank change.

The pretraining curve, measured as ood_test PR-AUC on unseen real calls with everything else held fixed: 0.48 random init at 3.70M, 0.60 adding real-call augmentation at 3.99M, 0.83 adding the fifteen-minute MLM pretrain at 7.36M, 0.91 for the internet-pretrained fine-tune at 66.96M. Parameter counts come from summing the ONNX initializer elements of each export. Each step is paid for in language exposure, not architecture.

Two instrument notes from the freeze. The pick_threshold CLI can segfault at interpreter teardown (exit 139) after its result printed and threshold.json was written; the artifact verified intact on disk both times, same torch plus onnxruntime teardown class as the v6 export mitigation in train.py. And the first scratch-pre2 bench read 274 req/s at concurrency 8 where the clean re-bench of scratch-pre minutes later read 588: back-to-back trainings had heated the box, so every quoted bench comes from a quiet machine on the exact artifact that ships. The same rule settles the fine-tune's own two readings, 32.8 ms wall p95 quiet against 57.9 ms loaded, and the quiet one is what the README and the hero carry.
