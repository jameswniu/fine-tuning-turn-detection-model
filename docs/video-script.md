# Video walkthrough script

The 29 second ad is the cold open; the spoken walkthrough runs about 3:40 at natural pace, total near 4:15, well inside the ten minute cap. Bracketed lines are what is on screen, not spoken; DOC means the approach Word document, REPO means the live repo surface named. Every number below is frozen from the reports; do not improvise numbers while recording. The rubric from the brief's side notes: they want to see how you think, with assumptions written down, so every beat is a decision and what it cost.

---

[0:00 Screen: the ad plays, full frame, sound up]

(No narration. The ad carries itself: the doorway collisions, the wait, the flow, her closer, the card.)

[0:29 Screen: REPO, README top, the hero]

That question, "is the caller done talking," is the whole problem. Hi, I'm James. You said you wanted to see how I think, more than a polished benchmark, so this is organized around the decisions and what each one cost. The shape in one breath: three models through one recipe, three referees including real production calls, and the winner serving at fifty-eight milliseconds p95, int8 on CPU.

[0:55 Screen: DOC, the problem priced]

First decision, the price of being wrong. Speak too early, that's an interruption, the error callers remember. Wait too long, that's dead air, the error every turn pays a little of. I set the ratio explicitly, one interruption to five sluggish responses, from my own production voice agent. Run it through Bayes and it becomes a confidence bar; measured, the model wasn't calibrated, so the threshold ships as a measured dial, recomputed every run.

[1:25 Screen: REPO, the Turn Booth, then DOC, the hedge ruling]

Data, policy first. Eleven pause situations, seven obvious, four with no obvious answer. I blind-labeled sixty cards and froze them as a gold set the model never trains on. My favorite ruling: "the broker said it was covered, supposedly" versus "the detention was approved, or something." Same shape, opposite answers. Ownership decides. An attributed claim is real doubt, so jump in and confirm; a first-person softener is politeness. That's learnable surface, so it went straight into the seeded, byte-identical generator, along with Spanish in the register carriers actually use.

[2:00 Screen: REPO, train_scratch.py docstring]

Models, where "pick a reasonable path and ship" got tested. The fine-tuned encoder is the safe recipe; the interesting lane trains from nothing. It failed twice, and each failure was worth more than a pass: a tokenizer that turned real text into walls of unknown tokens, then a leaked split that measured memorization as generalization. Fixed, the verdict came clean, ninety-nine on its own distribution, a coin flip on human gold. Knowledge, not coverage, was the gap, and knowledge is exactly what pretraining is. The curve on unseen real calls: forty-eight from scratch, sixty with real data, eighty-three with our own fifteen-minute pretrain, ninety-one where internet-scale pretraining sits.

[2:45 Screen: DOC, the real-call section, then REPO, iterations.md OOD row]

The best finding. Everything offline lives near one distribution, so I pulled sixty real calls from my own agent. Calls label themselves, where the caller stopped is a true complete. The model that read ninety-six on gold with zero wrong interruptions scored zero point six one on real calls. Every offline referee agreed with each other, and the real world disagreed with all of them. So the fix ran inside the build: two thirds of the calls became training augmentation, graded on the locked third, and the shipping model went from zero point six five to zero point nine one on the referee production trusts.

[3:30 Screen: REPO, the live probe page, typing a case]

Serving is FastAPI over ONNX, int8 on CPU, Dockerfile included. This live page re-scores word by word, and it's how several training gaps were found. Fifty-eight milliseconds p95 at concurrency eight against your hundred-millisecond budget, and the from-scratch lane does five milliseconds on the same box.

[3:50 Screen: DOC, monitoring, then REPO, file tree]

At your scale, turn detection grades itself, seconds later, for free. A caller talking over the agent was a false speak; dead air until a timeout was a false wait. Those two rates are the online eval, and they map straight onto the offline curve. Ship shadow-first, promote on the measured curve, roll back by pointer. Am I limited by the datasets I built? Yes, deliberately, until launch; you just watched the handoff run once with sixty calls. Everything's in the repo, both failures included. Thanks for a genuinely fun problem.
