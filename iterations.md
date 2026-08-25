# Iteration Log

One row per loop iteration; the bands live in EVALS.md.

| run | date | train size | operating threshold | PR-AUC (gold hard) | false-speak rate at op | recall at op | hedge class acc | K class acc | mean flips | ECE | what changed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 2026-08-24 | 914 | 0.833 (uncalibrated) | 0.961 | 0.00 | 0.577 | 0.20 | 0.50 | n/a | n/a | first full pass, Bayes threshold, found under-confidence |
| v2 | 2026-08-24 | 1133 | 0.61 | 0.964 | 0.00 | 0.808 | 0.60 | 0.75 | 0.38 | 0.114 | cost-optimal threshold, hedge/K/general bank expansion, streaming + calibration evals added |
| v3 | 2026-08-24 | 1423 | 0.87 | 0.970 | 0.00 | 0.654 | 0.20 | 0.50 | 0.34 | 0.067 | context-dropout augmentation targeting the bare-utterance recall gap |
| v4 | 2026-08-24 | 1423 | 0.86 | 0.969 | 0.00 | 0.654 | 0.20 | 0.50 | 0.34 | 0.070 | threshold objective from counts to class-conditional rates after v3 showed selection was tracking synthetic label balance, not the model |
| v5 | 2026-08-24 | 1492 | 0.81 | 0.958 | 0.00 | 0.731 | 0.40 | 0.625 | 0.45 | 0.092 | casual-register templates + Agent-prefix context normalization, found by live probe; regression slice added |
| v6 | 2026-08-25 | 1524 | 0.18 | 0.955 | 0.037 | 0.654 | 0.20 | 0.50 | 0.87 | 0.169 | dev-set threshold from judge panel; ood_train x4 grouped by call; tpl-grouped split; texting register; ood_test PR-AUC 0.905 false-speak 0.34 recall 0.98; regressions 6/6 |
| v7 | 2026-08-25 | 1586 | 0.27 | 0.949 | 0.00 | 0.654 | 0.20 | 0.50 | 0.75 | 0.160 | guardrail-constrained dev threshold via pick_threshold.py (12 tier-1 cards, admissible 71/99); policy-filtered 0 vendor-behavior rows from extra; announced-continuation bank reinforced (+6 templates); ood_test PR-AUC 0.913 false-speak 0.277 recall 0.980; regressions 6/6; tier1 announced-continuation RED on the served int8 model (F1-F4 and gold H5 hold at wait, but dev dH4 flips to speak at p=0.41 under int8 quantization even though the fp32 checkpoint used for constrained selection correctly holds it at p=0.26, just under the 0.27 threshold; the guardrail was enforced against the wrong artifact) |
