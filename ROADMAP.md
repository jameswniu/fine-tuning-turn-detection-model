# Roadmap: the environment ladder to production

Dictated by the policy owner on 2026-08-24. Four environments, each with a distinct job, ordered by how far judgment travels from its author. What exists tonight is marked; the rest is the trajectory the submission promises. The ladder is not hypothetical: it is transplanted from a production LLM system the author operated (local compose spinup, per-commit Kubernetes staging namespaces, record/replay fixtures gating CI, a release pipeline with an eval stage), re-sized for one model.

## dev (exists tonight)

Local conditions, everything reproducible on one machine: venv training on MPS, seeded synthesis, gold-set evaluation, and the serving container spun up locally (Docker now; the same container under a local Kubernetes spinup, kind or minikube, as the scale form). CI checks run locally before they run anywhere else. `make evals` executes the same tier 1 guardrails and tier 2 bands the pipeline gates on, so a laptop can veto a promotion for exactly the reasons CI would. A local CD copy can rehearse the deploy path when needed. A full loop iteration (synthesize, train, evaluate, log) runs in about two minutes, which is what makes the iteration log honest rather than aspirational.

## staging1: happy path, the user demo test (partially exists)

The containerized API driven end to end over the anchor scenarios the way a user would meet them: complete statements, questions, acks, readouts, connector-finals, each hitting /predict and asserting the expected decision at the operating threshold, plus the type-and-watch demo page a human can poke. The deterministic guardrails in EVALS.md are the gate; a red blocks promotion. Exists as evaluate.py plus the Dockerfile; the missing piece is the smoke suite pointed at the running container rather than the model files.

## staging2: synthetic edge cases, the stress test (partially exists)

The same container under adversarial and volume pressure: bench.py hammering /predict with synthesized payloads at stepped concurrency, latency percentiles and throughput against the bands, soak duration to catch leaks and tail drift, and the edge-case corpus (judgment classes, truncations, ASR-style variants) served as traffic rather than as files. Owning the synthetic generator pays twice here: the load corpus never runs dry, and no real caller data ever enters a test bed.

## production: online and offline testing (the trajectory)

The serving deployment, plus the two replay lanes that make promotion safe:

Offline replay: recorded traffic re-scored by any candidate model. Every recorded turn (first my own voice stack's transcripts, at scale the platform's production logs) becomes a regression corpus; a candidate must replay the archive and show its disagreements with the incumbent before it touches live traffic. This is the promotion gate, and it is also how a mistake found once stays found.

Online replay (shadow): the candidate scores live traffic in parallel with the incumbent, decisions logged and never acted on. Disagreement cases are mined, sampled for human labels, and fed back into training. Shadow first, promote on the measured curve, roll back by pointing the router at the previous checkpoint.

The two lanes answer different questions: offline replay asks "did we break anything we already knew," online replay asks "what does the live distribution know that our data does not." Production needs both, because the archive cannot contain drift and the live lane cannot contain the past.

## The thread through all four

Promotion up the ladder (dev, staging1, staging2, production) is gated by the same EVALS.md contract everywhere: tier 1 guardrails all green, tier 2 bands in range, one iterations.md row per attempt. The environments change; the referee does not.

## Post-submission chapters (the public repo phase)

The original first two chapters moved into the submission itself: the from-scratch lane ran (own tokenizer, small encoder from random init, and the two lessons it bought, the WordPiece out-of-vocabulary blowup and the template-leak validation split), and Spanish shipped under the same policy. What remains queued for after the process concludes:

1. Mandarin with native human labels through the same booth, and per-language scorecards in the style of the LiveKit and smart-turn model cards. Spanish shipped with a synthetic held-out referee; Mandarin is the language the author can native-label, so it carries the human-referee bar.
2. The shadow lanes at full size. Offline replay ran in miniature inside the submission, real-call slices from the author's production voice stack, split by call into an augmentation half and a held-out referee. What remains is online shadow against the vendor turn model on a real phone number, disagreements published. The vendor-versus-open bake-off with receipts.
3. The from-scratch frontier at scale: synthesis past 100k samples, the scratch-versus-fine-tuned curve at matched latency with per-register slices, extending the submission's first pass.
