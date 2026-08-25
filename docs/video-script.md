# Video walkthrough script

Target length about 8 minutes spoken at natural pace, against the 10 minute cap. Bracketed lines are what is on screen, not spoken. The latency placeholders [MODEL-MS], [P50], [P95], [C], [RPS] get filled from bench_report.json before recording.

---

[Screen: repo README top]

Hi, I'm James. This is my end-of-turn detection build. The one-line result: on a held-out, human-labeled test set, the model produces zero wrong interruptions at every operating threshold, it beats both a VAD-style baseline and a punctuation heuristic on the tradeoff curve, and it serves over FastAPI at 32.8 milliseconds p95, int8 on CPU. You capped this at ten minutes; I'll use about eight, and the details live in the doc and the repo.

[Screen: POLICY.md, the two-errors section]

First, how I framed the problem, because everything downstream falls out of this. A turn detector can only be wrong in two ways. It speaks too early, that's an interruption, the error callers remember. Or it waits too long, that's dead air, the error every single turn pays a little of. And any trivial system is perfect on one axis: never speak, zero interruptions; speak instantly, zero delay. So a single accuracy number means nothing here. The real decision is where you sit on the tradeoff curve, and I made that decision explicit and wrote it down: one interruption costs as much caller annoyance as five sluggish responses. One to five. Run through the Bayes decision rule, that ratio becomes a confidence bar: speak when the model is at least eighty-three percent sure the turn is over. The five isn't arbitrary. I run a production voice agent on a real phone number as a side project, and its dashboards showed dead air, not interruptions, was the chronic breach. It's a documented assumption you're welcome to disagree with, which is exactly why it's documented.

[Screen: the Turn Booth labeling tool]

Data creation, where I spent the most thought. Policy first, volume second. Step one, a taxonomy of eleven pause situations: seven anchors where the answer is obvious, complete statements, questions, a caller halfway through reading out a number. And four judgment classes with no textbook answer: a complete sentence that might continue, trailing hedges, self-interrupted restarts, and a caller asking for time. Step two, I built this small labeling tool and blind-labeled sixty calibration cards myself, shuffled so the taxonomy couldn't bias me. Those sixty labels are frozen as a gold set the model never trains on. That's the referee.

Step three is the part I'd call the heart of the build: the judgment classes produced real policy. Take hedges. "The broker said it was covered, supposedly" versus "the detention was approved, or something." Nearly identical shape, opposite correct answers. The difference is ownership. A claim attributed to someone else is a claim the speaker doesn't own; the hedge is genuine doubt, and jumping in to confirm is helpful. A first-person claim with a softener is settled; the hedge is politeness. That distinction lives in surface features a text model can learn, attribution markers versus first-person assertion, so it went straight into the data generator.

[Screen: synth.py, the template banks]

Step four, a seeded, pure-code synthesis generator expands the policy into about nine hundred training samples. Every judgment rule is encoded, and there are two robustness moves worth naming: complete utterances get re-emitted truncated mid-sentence and labeled wait, because that's exactly what ASR partials look like, and every sample also ships in an ASR-style variant, lowercased, punctuation stripped, so the model can't cheat off periods. No LLM in the loop, so the dataset regenerates byte-identically and every line can be audited.

[Screen: train.py]

Model selection. Text-based, DistilBERT, sixty-six million parameters, fine-tuned as a binary classifier over the last agent line plus the caller's words so far. Why text first: it clears the hundred-millisecond budget with room to spare once quantized, it's cheap to iterate and debug, and the open-source state of the art, LiveKit's turn detector and Pipecat's smart-turn, validates the recipe. The honest ceiling of text: the class where the words are identical whether the caller is finished or inhaling for more. That signal is prosody, it lives in audio, and audio or multimodal is the evolution I'd pursue next. I've written how in the discussion section.

[Screen: eval scoreboard]

Evaluation. Two baselines set the floor. Always-speak-on-pause, which is what a plain VAD timeout does, interrupts on all twenty-seven true waits in the gold set. Unusable, which is the whole reason this problem exists. A punctuation heuristic is respectable on clean text, interrupts once, misses about a third of true speaks, and collapses entirely on unpunctuated ASR text. The model: precision one point zero at every threshold in the sweep, zero wrong interruptions, with recall seventy-seven percent at the best measured operating point.

And the eval surfaced my favorite finding of the build: the theoretical eighty-three percent bar over-waits, because the model's probabilities run under-confident. The Bayes threshold is only correct if the probabilities are calibrated, and measured, they weren't. So the operating point comes from the measured tradeoff curve at the target cost ratio, not from the formula. The threshold is a dial, not a constant, and in production it's a dial you keep your hand on. I also report where the model is still weak: the two subtlest judgment classes, hedges and hold requests, are exactly where the errors concentrate, and the fix is data diversity, not architecture. That iteration loop is running.

[Screen: serve.py, then the bench output]

Serving and performance. FastAPI, ONNX runtime, dynamic int8 quantization, Dockerfile included. Model inference 21.7 milliseconds; end to end over HTTP, 23.4 median and 32.8 p95 at concurrency 8, about 320 requests a second on my laptop, stress-tested with an async client hammering real payloads. Details and the full latency table are in the doc.

[Screen: the monitoring section of the doc]

Production. You handle about a million calls a month, so here's how I'd run this for real. The two error types have live proxies you already log. A caller barging in right after the agent starts speaking is a false speak. A long gap between caller silence and agent response is a false wait. Those two rates are the online eval, no labels required, and they map one-to-one to the offline curve. Then the flywheel: sample the lowest-confidence turns plus every barge-in for human labeling, a few hundred a week, and retrain on real distribution. Slice everything by language, accent, connection quality, and customer, because turn-taking drifts differently per slice. Ship checkpoints shadow-first: the candidate scores live traffic silently next to the incumbent, you compare disagreement on real calls, and promote on the measured curve. And to the question in your brief, am I limited by the datasets I built? Yes, deliberately. My synthesis encodes policy; your production volume supplies distribution. The handoff from one to the other is the whole monitoring design.

[Screen: repo file tree]

Everything is in the submission: the code, the Dockerfile, the labeled gold set, the labeling tool itself, and the doc with every assumption written down where it's load-bearing. Thanks for a genuinely fun problem. Looking forward to talking through it.
