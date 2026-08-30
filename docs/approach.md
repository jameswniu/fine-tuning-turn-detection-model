# End-of-Turn Detection, an approach

The solution and the reasoning. The repo carries the depth: POLICY.md the turn policy, EVALS.md the gates, data/README.md the dataset provenance, iterations.md the audit trail of every run.

## The problem, priced

A turn detector can be wrong in exactly two ways, and pricing them is the first decision.

- Speak too early and it interrupts the caller. That is the error people remember.
- Wait too long and it leaves dead air. Every turn pays a little of that one.
- A trivial system is perfect on one axis, so a single accuracy number means nothing.

The price, written down before training anything: one interruption costs as much caller annoyance as five sluggish responses. The ratio comes from my own production voice agent on a real phone number, where dead air was the chronic complaint. It is written down so you can disagree with it.

Through the Bayes rule, 1:5 says speak at 83 percent confidence. Measured, the model runs under-confident, so the operating threshold comes from the measured validation curve instead, recomputed every run and shipped as data next to the weights. The threshold is a dial, not a constant. Synthetic validation failed at setting it in both directions, so final selection moves to a small dev set built outside the training distribution.

## Data, policy first

Most of the thought went here, policy first, volume second.

- A taxonomy of eleven pause situations. Seven have obvious answers; four judgment classes have none.
- Sixty calibration cards, blind-labeled in a purpose-built booth, shuffled so the taxonomy could not bias me. Frozen as a gold set the model never trains on. That is the referee.
- The ruling I would defend on a whiteboard: "the broker said it was covered, supposedly" and "the detention was approved, or something" share a shape and have opposite answers. The difference is ownership. An attributed claim carries genuine doubt, so the agent speaks to confirm; a first-person claim with a softener is settled politeness. Attribution markers are learnable surface features, which makes the ruling trainable rather than philosophy.

Volume comes from a seeded, pure-code generator. Complete utterances are re-emitted truncated mid-sentence and labeled wait, because that is what ASR partials look like; every sample ships lowercased with terminal punctuation stripped, so the model cannot cheat off periods. No LLM in the loop; the dataset regenerates byte-identically.

Spanish is the bonus, chosen for the domain: a large share of US carriers run Spanish-first, and the banks use that register, Mexican-Spanish trucking speech with real Spanglish. The hedge ruling transfers, "me dijeron que", "según ellos". Created instead of found because public corpora carry the wrong distribution and no policy labels, and the part needing human judgment was small enough to do by hand.

## Models, three lanes

Three models train through one recipe; the measured curve picks what ships.

Lane one fine-tunes DistilBERT, 66M parameters, on the last agent line plus the caller's words so far. The safe recipe.

Lane two taught me the most: random init, own tokenizer, a 3.7M encoder, same recipe so the comparison isolates pretraining. It failed twice, and each failure bought a finding.

- WordPiece learned only 1532 pieces from a template corpus; unfamiliar text became unknown-token walls and the model output a constant. 0.9998 synthetic, a coin-flip 0.50 on gold.
- Byte-level BPE fixed vocabulary; a template-grouped split fixed a leak that measured memorization as generalization. Honest mechanics, harder verdict: 0.99 synthetic, still 0.50 gold. Coverage was no longer the problem. Knowledge was.
- A few hundred real caller turns took gold from 0.50 to 0.994, but unseen real calls stayed near 0.60. The real rows broke the collapse; they did not teach language.
- A fifteen-minute masked-language-model pretrain of our own did: 0.973 gold, a perfect Spanish slice, 0.825 on unseen real calls, the widest guardrail-safe window in the build.

The full curve on unseen real calls, one named ingredient per step: 0.48 random init, 0.60 with real data, 0.825 with our own pretrain, 0.913 where the internet-pretrained fine-tune sits. The last gap is what a few billion pretraining tokens buy over our twenty-five megabytes. One tradeoff on the record: pretraining cost a sliver of gold, 0.994 down to 0.973, to buy 23 points on real calls.

<p align="center"><img src="../assets/pretrain-curve.svg" alt="What pretraining is worth, measured as PR-AUC on unseen real calls: 0.48 random init, 0.60 adding real calls, 0.83 adding a fifteen-minute pretrain, 0.91 web-pretrained" width="100%"></p>

The default is picked by a written rule, not taste: scratch ships only if it lands within about 0.02 gold PR-AUC of the fine-tune, keeps false-speak at zero, holds recall, and does not collapse out of distribution. Scratch leads or ties on gold, Spanish, guardrails, calibration, and latency, but 0.825 on real calls is not parity with 0.913, and the real-call referee is the one production trusts. The fine-tune ships, 0.949 gold with zero false-speak, 0.913 real; the scratch gap is the thing production volume closes.

Lane three fine-tunes multilingual DistilBERT on the bilingual corpus. On English gold it matches the English-only model, 0.960 against 0.958; on the held-out Spanish slice the English-only model manages 0.911 with recall barely above half, and the multilingual fine-tune separates it perfectly. Spanish support is a model swap, not a rebuild.

## Evaluation

<p align="center"><img src="../assets/referees.svg" alt="Three referees, one question each: a frozen gold set of 60 human-labeled cards for generalization, 6 probe-found regressions for memory, and 96 held-out real-call turns for discovery" width="100%"></p>

The referee structure matters more than any single number.

- The frozen gold set grades quality and is never trained on.
- A separate dev set picks thresholds, labeled by a certified judge panel: three independent models blind-label a shuffled batch, each certified against the sixty gold labels before its votes count, majority rules. One caveat: the policy doc quotes a few gold rulings, so the exam was partially open-book.
- A regression slice holds every failure found by live probing; a held-out Spanish slice at a different seed grades the bilingual claim.

<p align="center"><img src="../assets/judges.svg" alt="How the dev set was labeled and why to trust it: 60 gold cards with known human answers hidden among 30 fresh cards, three stock vendor judges with zero training, two-of-three majority, and the output feeds one file that tunes one number clamped by 12 human gates" width="100%"></p>

Then the referee that changed the build. I pulled sixty real production calls from my own voice agent and let them label themselves: where the caller stopped is a true complete, a mid-turn prefix is a true wait. Four hundred rows split by call, two thirds for augmentation, one third locked as the real-call referee. The labels carry stated noise and read as a pessimistic bound. The story: the fine-tuned model, 0.96 and zero false-speak on gold, scored 0.61 on real calls with false-speak around forty percent. Every offline referee agreed with each other, and the real world disagreed with all of them.

The fix ran inside the build. The training-side two thirds went back in as real-register augmentation, graded on the locked third: the shipping fine-tune went from 0.65 to 0.913 with recall 0.959, the multilingual lane landed at 0.875, and the scratch lane's movement is the curve above. Rows where the vendor's turn-taker answered against our written policy are relabeled to wait, marked and counted. The raw call content never enters the repo.

Two baselines set the floor: always-speak-on-pause, which is what a VAD timeout does, interrupts on every true wait in the gold set; a punctuation heuristic collapses on ASR-style text. Industry anchors are verified against LiveKit's and Pipecat's published numbers.

The scoreboard, all models on all referees, thresholds picked on the served int8 artifacts with the twelve tier-1 probes as constraints.

| Model | Params | Gold PR-AUC | Gold false-speak at op | Spanish PR-AUC | Real calls PR-AUC | Real calls at op (false-speak / recall) | Tier-1 window | ECE |
|---|---|---|---|---|---|---|---|---|
| Fine-tuned DistilBERT (ships) | 66M | 0.949 | 0.000 | not trained for | 0.913 | 0.234 / 0.959 | 58 of 99 at 0.42 | in band |
| Multilingual DistilBERT + real | 134M | 0.979 | 0.407 | 1.000 | 0.875 | 0.191 / 0.878 | 4 of 99 at 0.97 | 0.349 |
| From-scratch, own pretrain (7.4M) | 7.4M | 0.973 | 0.037 | 1.000 | 0.825 | 0.277 / 0.755 | 60 of 99 at 0.79 | 0.062 |
| From-scratch, no pretrain | 3.7M | 0.994 | 0.000 | 0.996 | 0.597 | collapse | not picked | 0.045 |

The verdict follows the rule. The fine-tune ships because it leads the referee production trusts. The multilingual model is the Spanish-capable variant, its miscalibration stated rather than hidden. The pretrained scratch model is the cleanest, fastest lane and the measured argument for what pretraining is worth.

## Serving and latency

FastAPI over ONNX Runtime, dynamic int8, CPU only, one worker. Every response carries the probability, the decision, the threshold in force, and the latency. The threshold is read from the model directory, so a retrain updates the dial without touching serving code. The same process serves a live probe page that re-scores as you type; several training-data gaps were found there. A Dockerfile builds the image with only the int8 model inside.

Measured on an M5 Pro laptop, single uvicorn worker, 1200 requests per level, in its late-night post-training thermal state, so these read conservative.

| Served artifact | c1 wall p50 | c8 wall p50 | c8 wall p95 | c8 req/s |
|---|---|---|---|---|
| Fine-tuned DistilBERT, 66M | 34.7 ms | 45.5 ms | 57.9 ms | 170 |
| Multilingual DistilBERT, 134M | 34.0 ms | 49.7 ms | 97.2 ms | 147 |
| From-scratch, 7.4M | 7.4 ms | 12.1 ms | 20.7 ms | 588 |

A single worker saturates at concurrency 32, a worker-count knob, not a model problem. The brief asked for under 100 milliseconds: the shipping model clears it at 57.9 ms p95 under eight-way concurrency, and the from-scratch lane clears it five times over, seven times faster at a fifth of the hardware per call.

## Monitoring at a million calls a month

Monitoring means tracing decisions and converting failures into evals and guardrails, not dashboards. Every decision emits a trace, including the prefix probability trajectory, the threshold in force, and what the caller did next.

That last field is the special thing about this problem. Turn detection grades itself in production, seconds later, for free.

- A speak decision followed by the caller talking over the agent within about half a second was a false speak.
- A wait decision followed by dead air until a timeout forced the response was a false wait.
- Those two rates are the online eval, no annotation cost, and they map one to one onto the offline curve.

A small weekly human-audited sample keeps the auto-labels honest and feeds retraining, biased toward low-confidence decisions and every barge-in. Slice by language, accent, connection quality, and customer; alarm on score-distribution drift. Shipping stays boring: replay the archive, shadow live traffic, promote on the measured curve, roll back with a pointer flip.

And the brief's direct question, whether we are limited by the datasets previously built: yes, deliberately, and only until launch. My synthesis encodes policy; production volume supplies distribution. At almost a million calls a month, that handoff is the whole monitoring design.

## The discussion questions, answered in advance

The brief's five questions are answered here. What else a reviewer might raise sits in collapsed blocks at the bottom of the README: why DistilBERT, why int8 and what it cost, why 0.42, where verification actually happens, and what was not measured.

On limits. The ceiling of a text-only detector is prosody, and it sits in the input rather than the model: some utterances read identically whether the caller is finished or inhaling for more, and pitch decline, final lengthening, and breath never reach a text model. The system also inherits the transcriber's cadence, the gold referee is sixty cards so per-class intervals are wide, and the policy encodes one operator's judgment.

On audio against text against multimodal. A VAD knows only that sound stopped, so it buys safety with silence, and every setting of that timeout is wrong for half the cases. Text sees what was said, most of the turn signal, cheap and debuggable, which is why I started there. Audio sees how it was said and can act before transcription lands. Multimodal is the frontier and my next step, a small audio encoder fused with the text signal at the decision layer; the referee, cost ratio, and production proxies built here transfer unchanged, which is the point of building the referee first. In the reference architecture the limit is visible as wiring: one arrow enters the detector carrying final transcription while raw audio flows past it. The fix is a second arrow.

On whether a transcriber could do this job. An ASR is trained to be invariant to prosody, "yeah" flat and "yeah" rising must produce the same token, so the signal is discarded at the text bottleneck. Three tiers follow.

- Free today: vendor responses already carry word-level timestamps, and final-word lengthening plus pause duration are among the strongest endpoint cues in the phonetics literature. Feeding them in adds no model and no latency.
- With Whisper: add an end-of-turn token to the decoder vocabulary, fine-tune on turn-annotated audio, read that token's probability from the same forward pass that produces the transcript.
- With a streaming RNN-T model like Parakeet: train an end-of-utterance token into the transducer vocabulary, or hang a small classifier head off the encoder states.

Both recipes need audio with true turn boundaries, which is what the production self-labeling loop produces. The tradeoff is coupling, one model owning two jobs on one latency budget, so I would keep the detector separate while iterating and consider distilling it into the transcriber once the policy stabilizes.

On integration into a voice agent. The detector sits between streaming ASR and the LLM trigger. Partials accumulate; when VAD flags a pause, the detector scores the last agent line plus the transcript so far, and the probability maps to an endpoint delay. High commits after a short guard, middling waits longer, low holds toward a hard ceiling and re-scores on every partial. Barge-in is untouched; the model adds single-digit milliseconds co-located next to the orchestrator. Two refinements pay quickly: smoothing across the prefix trajectory so the decision does not flap between partials, and speculative generation, starting LLM inference the moment the score goes high and cancelling if the caller resumes.

## Assumptions, written down

- The 1:5 cost ratio is a documented operating choice, not a law. Re-deriving the threshold for a different ratio is a one-line change.
- Inputs arrive ASR-style, lowercased, no terminal punctuation, with the last agent utterance available as context.
- The decision is binary, speak or wait. Response length and whether an acknowledgement ends a call are downstream policies, deliberately out of scope.
- Languages covered are English and Spanish.
- The latency budget is 100 milliseconds end to end on CPU, no GPU assumed anywhere.
