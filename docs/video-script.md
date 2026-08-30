# Video walkthrough script

Ten minute cap. The 29 second ad is the cold open; the spoken walkthrough targets about 9:10 at natural pace. Bracketed lines are what is on screen, not spoken; DOC means the approach Word document, REPO means the live repo surface named. Every number below is frozen from the reports; do not improvise numbers while recording. The brief's side notes are the rubric: they want to see how you think and approach the problem more than anything, with assumptions written down, so the walkthrough is organized around decisions, not metrics.

---

[0:00 Screen: the ad plays, full frame, sound up]

(No narration. The ad carries itself: the doorway collisions, the wait, the flow, her closer, the card.)

[0:29 Screen: REPO, README top, the hero]

That question, "is the caller done talking," is the whole problem. Hi, I'm James, and this is my build.

You said you wanted to see how I think, more than a polished benchmark. So this walkthrough is organized around the decisions, what each one cost, and the assumptions I wrote down as I went.

The shape in one breath: three models trained through one recipe, three referees judging them including real production phone calls, and the winner serving at fifty-eight milliseconds p95, int8 on CPU. The most valuable thing here is not a green number; it's what the real calls exposed, and what I did about it. I'll move between the doc and the repo.

[1:10 Screen: DOC, the problem priced]

First decision, the framing, because everything downstream falls out of it. A turn detector can only be wrong in two ways. Speak too early, that's an interruption, the error callers remember. Wait too long, that's dead air, the error every turn pays a little of. Any trivial system is perfect on one axis, so a single accuracy number means nothing.

The real decision is where you sit on the tradeoff curve, and I made that explicit: one interruption costs as much as five sluggish responses. That ratio is a written assumption, and it comes from my own production voice agent on a real phone number, where dead air, not interruptions, was the chronic complaint.

Run it through the Bayes rule and it becomes a confidence bar. Except the bar is only correct if the probabilities are calibrated. Measured, they weren't. So the operating threshold comes from the measured curve, recomputed each run, shipped as data next to the weights. The threshold is a dial, not a constant.

[2:20 Screen: REPO, the Turn Booth labeling tool]

Data, where I spent the most thought. Policy first, volume second. I wrote a taxonomy of eleven pause situations, seven with obvious answers, four with none. I blind-labeled sixty calibration cards in this booth, shuffled so the taxonomy couldn't bias me, and froze them as a gold set the model never trains on.

[2:45 Screen: DOC, the hedge ruling paragraph]

The judgment classes produced real policy. My favorite: "the broker said it was covered, supposedly" versus "the detention was approved, or something." Nearly identical shape, opposite answers.

The difference is ownership. A claim attributed to someone else is one the speaker doesn't own; the hedge is genuine doubt, so jump in and confirm. A first-person claim with a softener is settled; the hedge is politeness. That's learnable from surface features, attribution markers versus first-person assertion, so it went straight into the generator.

[3:25 Screen: REPO, synth.py template banks, then synth_es.py]

The generator is pure code, seeded, byte-identical on every run. Every line is auditable. Complete utterances get re-emitted cut mid-sentence and labeled wait, because that's what ASR partials look like. Everything also ships lowercased with punctuation stripped, so the model can't cheat off periods.

The same policy and pipeline also generate Spanish, in the register Spanish-first carriers actually use. The ownership ruling transfers, because Spanish has the same attribution markers.

[4:00 Screen: REPO, train_scratch.py docstring]

Models, and this is where "pick a reasonable path and ship" got tested. The fine-tuned encoder is the safe recipe. The interesting lane is the one I built from nothing: my own tokenizer, a four-layer encoder, random init.

It failed twice, and each failure was worth more than a pass. First, the tokenizer learned only fifteen hundred pieces, because template corpora have few unique words; real text turned into walls of unknown tokens and the model output a constant. Fix: byte-level BPE, nothing can be out of vocabulary. Second, subtler: my validation split leaked, different fills of the same template on both sides, memorization measured as generalization. Fix: group the split by template.

With the mechanics honest, the verdict came clean. Ninety-nine on its own distribution, a coin flip on the human gold set. Coverage wasn't the problem anymore; knowledge was. Knowing an unfamiliar sentence is complete requires having seen a lot of language, and that is exactly what pretraining is. I set a written rule before running any of this: scratch ships only if it matches the pretrained lane on every referee. It didn't. The pretrained model ships, and now I can tell you precisely why, with the curve.

[5:15 Screen: DOC, the real-call section, then REPO, iterations.md with the OOD row highlighted]

Now the reality check, the best finding of the build. Everything so far lives near one distribution, synthetic data and hand-written gold cards alike. So I pulled sixty real production calls from my own voice agent. Calls label themselves: where the caller actually stopped is a true complete, a mid-turn prefix is a true wait. A third of them became a referee no training ever touches.

The fine-tuned model, ninety-six on gold with zero wrong interruptions, scored zero point six one on real calls, false-speak around forty percent. The labels are noisy in stated ways and read as a pessimistic bound, but the gap is real. Every offline referee agreed with each other, and the real world disagreed with all of them. That sentence is the whole reason production monitoring exists.

Instead of writing it in a slide, I ran the fix inside the build. The other two thirds of the real calls went back into training as real-register augmentation, graded on the locked third. It took the shipping model from zero point six five to zero point nine one on the real referee.

And the scratch lane's full curve on unseen real calls: forty-eight from random init, sixty with real data, eighty-three with a fifteen-minute pretrain of our own, against the ninety-one where internet-scale pretraining sits. Each step, one named ingredient.

[6:50 Screen: REPO, the probe comparison page, scrolling slowly]

Both models, thirty-six probes, side by side on this page, scored one row at a time on the served int8 files exactly as the API does. They agree on thirty-two of thirty-six, and the row that fools both is an ASR-style question with no question mark, which is honest about where the ceiling is.

The multilingual bonus, quickly: the multilingual fine-tune matches the English model on the English gold set, and takes the held-out Spanish slice from recall barely above half to clean separation. Spanish support is a model swap, not a rebuild.

[7:25 Screen: REPO, the live probe page, typing a case]

Serving. FastAPI over ONNX Runtime, dynamic int8, CPU, Dockerfile included, threshold read from the model directory. This live page re-scores word by word, the same granularity streaming ASR gives you, and it's how several training gaps were found. Type "nah bye" at a model that has never seen casual register and watch it go uncertain.

Measured on my laptop: end to end fifty-eight p95 at concurrency eight, about a hundred and seventy requests a second, and the from-scratch model does five milliseconds and nearly six hundred a second on the same box. The brief asked for under a hundred milliseconds; there's real margin.

[8:10 Screen: DOC, the monitoring section]

Production, at your scale, a million calls a month. Turn detection grades itself in production, seconds later, for free. A caller talking over the agent right after it starts is a false speak. Dead air stretching before the agent answers is a false wait. Those two rates are the online eval, no annotation budget, and they map one to one to the offline curve.

Sample the low-confidence turns and every barge-in for human labels, a few hundred a week. Slice by language, accent, connection quality, and customer. Ship shadow-first, promote on the measured curve, roll back by pointing at the previous checkpoint.

And the question of whether I'm limited by the datasets I built: yes, deliberately, and only until launch. My synthesis encodes policy; production supplies distribution. You just watched that handoff run once, in miniature, with sixty calls. At a million a month it's the same loop with the volume turned up.

[9:15 Screen: REPO, file tree]

Everything's in the repo. The code, the Dockerfile, the frozen gold set, the booth I labeled it in, the iteration log including both failures, and the doc with every assumption written down where it's load-bearing. Thanks for a genuinely fun problem. Looking forward to talking through it.
