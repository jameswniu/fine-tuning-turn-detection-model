# Iteration Log

One row per loop iteration; the bands live in EVALS.md.

| run | date | train size | operating threshold | PR-AUC (gold hard) | false-speak rate at op | recall at op | hedge class acc | K class acc | mean flips | ECE | what changed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 2026-08-24 | 914 | 0.833 (uncalibrated) | 0.961 | 0.00 | 0.577 | 0.20 | 0.50 | n/a | n/a | first full pass, Bayes threshold, found under-confidence |
| v2 | 2026-08-24 | 1133 | 0.61 | 0.964 | 0.00 | 0.808 | 0.60 | 0.75 | 0.38 | 0.114 | cost-optimal threshold, hedge/K/general bank expansion, streaming + calibration evals added |
| v3 | 2026-08-24 | 1423 | 0.87 | 0.970 | 0.00 | 0.654 | 0.20 | 0.50 | 0.34 | 0.067 | context-dropout augmentation targeting the bare-utterance recall gap |
