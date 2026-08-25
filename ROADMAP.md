# Roadmap: the environment ladder to production

Dictated by the policy owner on 2026-08-24. Four environments, each with a distinct job, ordered by how far judgment travels from its author. What exists tonight is marked; the rest is the trajectory the submission promises.

## Dev (exists tonight)

Local conditions: venv on the laptop, MPS training, seeded synthesis, gold-set evaluation, the whole loop in one place. A full iteration (synthesize, train, evaluate, log) runs in about two minutes, which is what makes the iteration log honest rather than aspirational.

## Test 1: happy path (partially exists)

The containerized API driven end to end over the anchor scenarios: complete statements, questions, acks, readouts, connector-finals, each hitting /predict and asserting the expected decision at the operating threshold. The deterministic guardrails in EVALS.md are the gate; a red blocks promotion. Exists as evaluate.py plus the Dockerfile; the missing piece is wiring them as a smoke suite that runs against the running container rather than the model files.

## Test 2: stress, synthetic data (partially exists)

The same container under load: bench.py hammering /predict with synthesized payloads at stepped concurrency, latency percentiles and throughput against the bands, plus soak duration to catch leaks and drift in tail latency. The synthetic generator doubles as the load corpus, which is the point of owning it: the stress environment never runs dry and never leaks real caller data into a test bed.

## Production: serve plus both replay modes (the trajectory)

The serving container, plus the two replay lanes that make promotion safe:

Offline replay: recorded traffic re-scored by any candidate model. Every recorded turn (first my own voice stack's transcripts, at scale the platform's production logs) becomes a regression corpus; a candidate must replay the archive and show its disagreements with the incumbent before it touches live traffic. This is the promotion gate, and it is also how a mistake found once stays found.

Online replay (shadow): the candidate scores live traffic in parallel with the incumbent, decisions logged and never acted on. Disagreement cases are mined, sampled for human labels, and fed back into training. Shadow first, promote on the measured curve, roll back by pointing the router at the previous checkpoint.

The two lanes answer different questions: offline replay asks "did we break anything we already knew," online replay asks "what does the live distribution know that our data does not." Production needs both, because the archive cannot contain drift and the live lane cannot contain the past.

## The thread through all four

Promotion between environments is gated by the same EVALS.md contract everywhere: tier 1 guardrails all green, tier 2 bands in range, one iterations.md row per attempt. The environments change; the referee does not.
