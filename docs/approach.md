# End-of-Turn Detection, an approach

This document presents the solution and the reasoning. The repo carries the depth: POLICY.md holds the turn policy, EVALS.md the gates and bands, data/README.md the dataset provenance, and iterations.md the audit trail of every run.

## The problem, priced

A turn detector can be wrong in exactly two ways, and pricing them is the first decision.

- Speak too early and it interrupts the caller. That is the error people remember.
- Wait too long and it leaves dead air. Every turn pays a little of that one.
- A trivial system is perfect on one axis, so a single accuracy number means nothing. The real decision is where to sit on the tradeoff curve.

I made the price explicit before training anything: one interruption costs as much caller annoyance as five sluggish responses. The ratio comes from my own production voice agent on a real phone number, where dead air, not interruptions, was the chronic complaint. It is written down so you can disagree with it.

Through the Bayes rule, 1:5 says speak at 83 percent confidence. Measured, the model runs under-confident, so the theoretical bar over-waits. The operating threshold therefore comes from the measured validation curve at the target cost ratio, recomputed every run and shipped as data next to the weights. The threshold is a dial, not a constant. Synthetic validation failed at setting it in both directions, one lane drifting high against human judgment and one leaked split picking a degenerate 0.33, so final selection moves to a small dev set built outside the training distribution.

## Data, policy first

Most of the thought went here, in this order: policy first, volume second.

- A taxonomy of eleven pause situations. Seven have obvious answers; four judgment classes have none.
- Sixty calibration cards, blind-labeled in a purpose-built booth, shuffled so the taxonomy could not bias me. Frozen as a gold set the model never trains on. That is the referee.
- The ruling I would defend on a whiteboard: "the broker said it was covered, supposedly" and "the detention was approved, or something" share a shape and have opposite answers. The difference is ownership. A claim attributed to someone else carries genuine doubt, so the agent speaks to confirm; a first-person claim with a trailing softener is settled politeness. Attribution markers are surface features a text model can learn, which makes the ruling trainable rather than philosophy.

Volume comes from a seeded, pure-code generator that expands the policy. Complete utterances are re-emitted truncated mid-sentence and labeled wait, because that is what ASR partials look like. Every sample ships lowercased with terminal punctuation stripped, so the model cannot cheat off periods. No LLM sits in the loop; the dataset regenerates byte-identically and every line can be audited.

Spanish is the multilingual bonus, chosen for the domain. A large share of US carriers run Spanish-first, and the banks use the register those calls actually have, Mexican-Spanish trucking speech with real Spanglish. The hedge ruling transfers because Spanish has the same attribution markers, "me dijeron que", "según ellos". Why created instead of found: public corpora carry the wrong distribution and no per-class policy labels, and the part that needed human judgment, sixty cards and the class policies, was small enough to do properly by hand.

## Models, three lanes

Three models train through one recipe; the measured curve picks what ships.

The first lane fine-tunes DistilBERT, 66M parameters, on the last agent line plus the caller's words so far. It is the safe recipe.

The second lane taught me the most: random init, own tokenizer trained on the task corpus, a 3.7M encoder, same recipe as the fine-tune so the comparison isolates pretraining. It failed twice, and each failure bought a finding.

- WordPiece learned only 1532 pieces from a template corpus, so unfamiliar text became walls of unknown tokens and the model output a constant: 0.9998 on synthetic validation, a coin-flip 0.50 on gold.
- Byte-level BPE fixed vocabulary, and a template-grouped split fixed a leak where fills of the same template sat on both sides, measuring memorization as generalization. With the mechanics honest, the verdict got harder: 0.99 synthetic, still 0.50 on gold. Coverage was no longer the problem. Knowledge was.
- A few hundred real caller turns took gold from 0.50 to 0.994, but unseen real calls stayed near 0.60. The real rows broke the collapse; they did not teach language.
- Language came from a fifteen-minute masked-language-model pretrain of our own. Warm-started, the model reads 0.973 on gold, a perfect Spanish slice, 0.825 on unseen real calls, and the widest guardrail-safe window in the build.

The full curve on unseen real calls, one named ingredient per step: 0.48 random init, 0.60 with real data, 0.825 with our own pretrain, 0.913 where the internet-pretrained fine-tune sits. The last gap is what a few billion pretraining tokens buy over our twenty-five megabytes. One tradeoff stays on the record: pretraining cost a sliver of gold, 0.994 down to 0.973, to buy 23 points on real calls.

<p align="center"><img src="../assets/pretrain-curve.svg" alt="What pretraining is worth, measured as PR-AUC on unseen real calls: 0.48 random init, 0.60 adding real calls, 0.83 adding a fifteen-minute pretrain, 0.91 web-pretrained" width="100%"></p>

The shipped default is picked by a written rule, not taste: scratch ships only if it lands within about 0.02 gold PR-AUC of the fine-tune, keeps false-speak at zero, holds recall, and does not collapse out of distribution. The rule decided against it for one reason. Scratch leads or ties on gold, Spanish, guardrail headroom, calibration, and latency, but its 0.825 on unseen real calls is not parity with 0.913, and the real-call referee is the one production trusts. So the fine-tuned English model ships, 0.949 on gold with zero false-speak and 0.913 on real calls, and the scratch gap is the thing production data volume closes.

The third lane fine-tunes multilingual DistilBERT on the bilingual corpus. On English gold it matches the English-only model, 0.960 against 0.958, so the multilingual vocabulary costs nothing where it matters. On the held-out Spanish slice the English-only model manages 0.911 with recall barely above half; the multilingual fine-tune separates it perfectly. Spanish support is a model swap, not a rebuild.

## Evaluation

<p align="center"><img src="../assets/referees.svg" alt="Three referees, one question each: a frozen gold set of 60 human-labeled cards for generalization, 6 probe-found regressions for memory, and 96 held-out real-call turns for discovery" width="100%"></p>

The referee structure matters more than any single number.

- The frozen gold set grades quality and is never trained on.
- A separate dev set picks thresholds, so the test referee stays untouched by selection. It is labeled by a certified judge panel: three independent models blind-label a shuffled batch, each certified by agreement with the sixty gold labels before its votes count, majority rules, disagreements marked unsure. One caveat travels with that: the policy doc quotes a handful of gold rulings, so the exam was partially open-book.
- A regression slice holds every failure found by live probing. A held-out Spanish slice at a different seed grades the bilingual claim.

<p align="center"><img src="../assets/judges.svg" alt="How the dev set was labeled and why to trust it: 60 gold cards with known human answers hidden among 30 fresh cards, three stock vendor judges with zero training, two-of-three majority, and the output feeds one file that tunes one number clamped by 12 human gates" width="100%"></p>

Then the referee that changed the build. Everything above lives near one distribution, so I pulled sixty real production calls from my own voice agent and let them label themselves: where the caller actually stopped is a true complete, a mid-turn prefix is a true wait. Four hundred rows, split by call, two thirds for training augmentation and one third locked as the real-call referee. The labels carry stated noise and read as a pessimistic bound; excluding sentence-boundary cuts moved the headline by only two points. The story: the fine-tuned model, 0.96 and zero false-speak on gold, scored 0.61 on real calls with false-speak around forty percent. Every offline referee agreed with each other, and the real world disagreed with all of them.

The fix ran inside the build. The training-side two thirds went back in as real-register augmentation, graded on the locked third. The shipping fine-tune went from 0.65 to 0.913 on the real referee with recall 0.959; the multilingual lane landed at 0.875; the scratch lane's movement is the pretraining curve above. Rows where the vendor's turn-taker answered against our written policy are relabeled to wait, marked and counted, so its behavior does not leak into the labels. The raw call content never enters the repo; only aggregates appear here.

Two baselines set the floor: always-speak-on-pause, which is what a plain VAD timeout does, interrupts on every true wait in the gold set, and a punctuation heuristic collapses on ASR-style text. Gates and bands live in EVALS.md, with industry anchors verified against LiveKit's and Pipecat's published numbers.

The scoreboard, all models on all referees. Thresholds are picked on the served int8 artifacts against the dev set, with the twelve tier-1 probes as constraints.

| Model | Params | Gold PR-AUC | Gold false-speak at op | Spanish PR-AUC | Real calls PR-AUC | Real calls at op (false-speak / recall) | Tier-1 window | ECE |
|---|---|---|---|---|---|---|---|---|
| Fine-tuned DistilBERT (ships) | 66M | 0.949 | 0.000 | not trained for | 0.913 | 0.234 / 0.959 | 58 of 99 at 0.42 | in band |
| Multilingual DistilBERT + real | 134M | 0.979 | 0.407 | 1.000 | 0.875 | 0.191 / 0.878 | 4 of 99 at 0.97 | 0.349 |
| From-scratch, own pretrain (7.4M) | 7.4M | 0.973 | 0.037 | 1.000 | 0.825 | 0.277 / 0.755 | 60 of 99 at 0.79 | 0.062 |
| From-scratch, no pretrain | 3.7M | 0.994 | 0.000 | 0.996 | 0.597 | collapse | not picked | 0.045 |

The verdict follows the written rule. The fine-tune ships because it leads the referee production trusts. The multilingual model is the Spanish-capable variant, its miscalibration stated rather than hidden. The pretrained scratch model is the guardrail-cleanest and fastest lane, and the measured argument for what pretraining is worth.

## Serving and latency

FastAPI over ONNX Runtime, dynamic int8, CPU only, one worker. Every response carries the probability, the decision, the threshold in force, and the model latency. The threshold is read from the model directory, so a retrain updates the dial without touching serving code. The same process serves a live probe page that re-scores as you type; several training-data gaps were found there. A Dockerfile builds the serving image with only the int8 model inside.

Measured on an M5 Pro laptop, single uvicorn worker, 1200 requests per level, in its late-night post-training thermal state, so these read conservative.

| Served artifact | c1 wall p50 | c8 wall p50 | c8 wall p95 | c8 req/s |
|---|---|---|---|---|
| Fine-tuned DistilBERT, 66M | 34.7 ms | 45.5 ms | 57.9 ms | 170 |
| Multilingual DistilBERT, 134M | 34.0 ms | 49.7 ms | 97.2 ms | 147 |
| From-scratch, 7.4M | 7.4 ms | 12.1 ms | 20.7 ms | 588 |

The stress harness is an async client at stepped concurrency; a single worker saturates at 32, which is a worker-count knob, not a model problem. The brief asked for under 100 milliseconds per request. The shipping model clears it at 57.9 ms p95 under eight-way concurrency, and the from-scratch lane clears it five times over, seven times faster at a fifth of the hardware per call.

## Monitoring at a million calls a month

Monitoring here means tracing decisions and converting failures into evals and guardrails, not dashboards. Every decision emits a trace: turn id, context, the prefix probability trajectory, the decision, the threshold in force, latency, and what the caller did next.

That last field is the special thing about this problem. Turn detection grades itself in production, seconds later, for free.

- A speak decision followed by the caller talking over the agent within about half a second was a false speak.
- A wait decision followed by dead air until a timeout forced the response was a false wait.
- Those two rates are the online eval, no annotation cost, and they map one to one onto the offline curve.

A small weekly human-audited sample keeps the auto-labels honest and feeds retraining, biased toward low-confidence decisions and every barge-in. Slice by language, accent, connection quality, and customer; alarm on score-distribution drift. Shipping stays boring: a candidate replays the recorded archive, then shadows live traffic, promotion happens on the measured curve, rollback is a pointer flip.

And the brief's direct question, whether we are limited by the datasets previously built: yes, deliberately, and only until launch. My synthesis encodes policy; production volume supplies distribution. At almost a million calls a month, the handoff from one to the other is the whole monitoring design.

## The discussion questions, answered in advance

The brief's five questions are answered here. What else a reviewer might raise sits in collapsed blocks at the bottom of the README: why DistilBERT, why int8 and what it cost, why 0.42, where verification actually happens, and an explicit list of what was not measured.

On limits. The ceiling of a text-only detector is prosody, and it sits in the input rather than the model: some utterances read identically whether the caller is finished or inhaling for more, and pitch decline, final lengthening, and breath never reach a text model. The system also inherits the transcriber's cadence, the gold referee is sixty cards so per-class intervals are wide, and the policy encodes one operator's judgment, a feature for coherence and a limit for customers whose callers behave differently.

On audio against text against multimodal, and why any of them beat VAD. A VAD knows only that sound stopped, so it buys safety with silence, and every setting of that timeout is wrong for half the cases. Text sees what was said, which is most of the turn signal, cheap to train and easy to debug, which is why I started there. Audio sees how it was said and can act before transcription lands. Multimodal is the real frontier and my next step, a small audio encoder fused with the text signal at the decision layer; the referee, cost ratio, and production proxies built here transfer to it unchanged, which is the point of building the referee first. The reference architecture makes the limit visible as wiring: one arrow enters the detector carrying final transcription while raw audio flows past it, so no better text model recovers a falling pitch. The fix is a second arrow.

On whether a transcriber could do this job. An ASR is trained to be invariant to prosody, because "yeah" spoken flat and "yeah" spoken rising must produce the same token, so the signal is discarded at the text bottleneck. Three tiers follow.

- Free today: vendor responses already carry word-level timestamps, and final-word lengthening plus pause duration are among the strongest endpoint cues in the phonetics literature. Feeding them to the current model adds no model and no latency.
- With Whisper: add an end-of-turn token to the decoder vocabulary, fine-tune on turn-annotated audio, and read that token's probability from the same forward pass that produces the transcript. Prosody arrives through the audio encoder.
- With a streaming RNN-T model like Parakeet: train an end-of-utterance token into the transducer vocabulary, or hang a small classifier head off the encoder states.

Both training recipes need audio with true turn boundaries, which is exactly what the production self-labeling loop produces. The tradeoff is coupling, one model owning two jobs on one latency budget, so I would keep the detector separate while iterating fast and consider distilling it into the transcriber once the policy stabilizes.

On integration into a voice agent. The detector sits between streaming ASR and the LLM trigger. Partials accumulate while the caller speaks; when VAD flags a pause, the detector scores the last agent line plus the transcript so far, and the probability maps to an endpoint delay. A high score commits after a short guard, a middling score waits longer, a low score holds toward a hard ceiling and re-scores on every new partial. Barge-in handling is untouched, and the model adds single-digit milliseconds co-located next to the orchestrator. Two refinements pay quickly: smoothing across the prefix trajectory keeps the decision from flapping between partials, and speculative generation, starting LLM inference the moment the score goes high and cancelling if the caller resumes, converts detector confidence directly into answer latency.

## Assumptions, written down

- The 1:5 cost ratio is a documented operating choice, not a law. Re-deriving the threshold for a different ratio is a one-line change.
- Inputs arrive ASR-style, lowercased, no terminal punctuation, with the last agent utterance available as context.
- The decision is binary, speak or wait. Response length and whether an acknowledgement ends a call are downstream policies, deliberately out of scope.
- Languages covered are English and Spanish.
- The latency budget is 100 milliseconds end to end on CPU, no GPU assumed anywhere.
