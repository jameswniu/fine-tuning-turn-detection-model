# Video walkthrough script

Target about 9:30 spoken at natural pace, against the 10 minute cap. Bracketed lines are what is on screen, not spoken. Placeholders in double brackets get filled from the frozen reports before recording; do not record with a placeholder unfilled.

---

[Screen: repo README top]

Hi, I'm James. This is my end-of-turn detection build. The one-line version: I trained three models, a fine-tuned encoder, a multilingual variant, and one from complete scratch with its own tokenizer, judged them against three referees including real production phone calls, and served the winner over FastAPI at fifty-eight milliseconds p95, int8 on CPU, with the from-scratch lane five times faster still. And the most valuable thing in this submission is not a green number, it's what the real calls exposed and what I did about it. You capped this at ten minutes; the details live in the doc and the repo.

[Screen: POLICY.md, the two-errors section]

First, the framing, because everything downstream falls out of it. A turn detector can only be wrong in two ways. Speak too early, that's an interruption, the error callers remember. Wait too long, that's dead air, the error every turn pays a little of. Any trivial system is perfect on one axis, so a single accuracy number means nothing; the real decision is where you sit on the tradeoff curve. I made that explicit: one interruption costs as much as five sluggish responses, one to five. That ratio comes from my own production voice agent on a real phone number, where dead air, not interruptions, was the chronic complaint. Run it through the Bayes rule and it becomes a confidence bar. Except the bar is only correct if the probabilities are calibrated, and measured, they weren't, so the operating threshold comes from the measured curve, recomputed each run, shipped as data next to the weights. The threshold is a dial, not a constant.

[Screen: the Turn Booth labeling tool]

Data, where I spent the most thought. Policy first, volume second. I wrote a taxonomy of eleven pause situations, seven with obvious answers, four with none, blind-labeled sixty calibration cards in this booth, shuffled so the taxonomy couldn't bias me, and froze them as a gold set the model never trains on. The judgment classes produced real policy. My favorite: "the broker said it was covered, supposedly" versus "the detention was approved, or something." Nearly identical shape, opposite answers. The difference is ownership. A claim attributed to someone else is one the speaker doesn't own, the hedge is genuine doubt, jump in and confirm. A first-person claim with a softener is settled, the hedge is politeness. That's learnable from surface features, attribution markers versus first-person assertion, so it went straight into the generator.

[Screen: synth.py template banks, then synth_es.py]

The generator is pure code, seeded, byte-identical on every run, so every line is auditable. Complete utterances get re-emitted cut mid-sentence and labeled wait, because that's what ASR partials look like, and everything also ships lowercased with punctuation stripped so the model can't cheat off periods. The same policy, same pipeline, also generates Spanish, in the register Spanish-first carriers actually use, and the ownership ruling transfers because Spanish has the same attribution markers.

[Screen: train_scratch.py docstring]

Models. The fine-tuned encoder is the safe recipe. The interesting lane is the one I built from nothing, my own tokenizer, a four-layer encoder, three point seven million parameters, random init. It failed twice and each failure was worth more than a pass. First failure: the tokenizer learned only fifteen hundred pieces, because template corpora have few unique words, so real text turned into walls of unknown tokens and the model output a constant. Fix: byte-level BPE, nothing can be out of vocabulary. Second failure was subtler: my validation split leaked, different fills of the same template on both sides, memorization measured as generalization. Fix: group the split by template. And with the mechanics honest, the clean verdict: ninety-nine on its own distribution, a coin flip on the human gold set. Coverage wasn't the problem anymore. Knowledge was. Knowing an unfamiliar sentence is complete requires having seen a lot of language, and that is exactly what pretraining is. I set a written rule before running any of this, scratch ships only if it matches the pretrained lane on every referee. It didn't. The pretrained model ships, and now I can tell you precisely why, with the curve.

[Screen: eval table, the real-call OOD row highlighted]

Now the reality check, the best finding of the build. Everything so far, synthetic data, hand-written gold cards, lives near one distribution. So I pulled sixty real production calls from my own voice agent, calls label themselves, where the caller actually stopped is a true complete, a mid-turn prefix is a true wait, and held a third of them out as a referee no training ever touches. The fine-tuned model, ninety-six on gold, zero wrong interruptions, scored zero point six one on real calls, false-speak around forty percent. The labels are noisy in stated ways and read as a pessimistic bound, but the gap is real: every offline referee agreed with each other, and the real world disagreed with all of them. That sentence is the whole reason production monitoring exists, and instead of just writing that in a slide, I ran the fix inside the take-home: the other two thirds of the real calls went back into training as real-register augmentation, graded on the locked third. Real-register augmentation took the shipping model from zero point six five to zero point nine one on the real referee. And the scratch lane's full curve on unseen real calls ran fifty from random init, sixty with real data, eighty-three with a fifteen-minute pretrain of our own, against the ninety-one where internet-scale pretraining sits, each step one named ingredient.

[Screen: eval scoreboard, multilingual rows]

The multilingual bonus, quickly: the multilingual fine-tune matches the English model on the English gold set, ninety-six both, and takes the held-out Spanish slice from recall barely above half to clean separation. Spanish support is a model swap, not a rebuild.

[Screen: serve.py, live probe page, then bench output]

Serving. FastAPI over ONNX Runtime, dynamic int8, CPU, Dockerfile included, threshold read from the model directory. This live page re-scores on every keystroke, which is how several training gaps were found, type "nah bye" at a model that has never seen casual register and watch it go uncertain. Measured on my laptop: model inference thirty-two milliseconds, end to end forty-six median and fifty-eight p95 at concurrency eight, about a hundred and seventy requests a second, stress-tested with an async client. The from-scratch model does five milliseconds and nearly six hundred a second on the same box. Your brief asked for under a hundred milliseconds; there's real margin.

[Screen: the monitoring section of the doc]

Production, at your scale, a million calls a month. Turn detection grades itself in production, seconds later, for free. A caller talking over the agent right after it starts is a false speak. Dead air stretching before the agent answers is a false wait. Those two rates are the online eval, no annotation budget, and they map one to one to the offline curve. Sample the low-confidence turns and every barge-in for human labels, a few hundred a week, slice by language, accent, connection quality, and customer, ship shadow-first, promote on the measured curve, roll back by pointing at the previous checkpoint. And your question, whether I'm limited by the datasets I built: yes, deliberately, and only until launch. My synthesis encodes policy, production supplies distribution. You just watched that handoff run once, in miniature, with sixty calls. At a million a month it's the same loop with the volume turned up.

[Screen: repo file tree]

Everything's in the repo: the code, the Dockerfile, the frozen gold set, the booth I labeled it in, the iteration log including both failures, and the doc with every assumption written down where it's load-bearing. Thanks for a genuinely fun problem. Looking forward to talking through it.
