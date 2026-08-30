# End-of-Turn Detection, an approach

How I built it and why. The repo carries the depth: POLICY.md the turn policy, EVALS.md the gates, data/README.md the data provenance, iterations.md every run.

## The problem, priced

A turn detector can only be wrong two ways.

- Speak too early and it interrupts, the error people remember.
- Wait too long and it leaves dead air, the error every turn pays a little of.
- A trivial system is perfect on one axis, so a single accuracy number means nothing.

I wrote the price down before training anything: one interruption costs as much as five sluggish responses. The ratio comes from my own production voice agent, where dead air was the chronic complaint. Bayes turns 1:5 into speak-at-83-percent, but the model measures under-confident, so the operating threshold comes from the measured curve instead, recomputed every run and shipped as data beside the weights. The threshold is a dial, not a constant.

## Data, policy first

- Eleven pause situations: seven obvious, four judgment classes.
- I blind-labeled sixty cards and froze them as a gold set the model never trains on. That is the referee.
- The ruling I would defend on a whiteboard: "the broker said it was covered, supposedly" speaks, "the detention was approved, or something" waits. Ownership decides. An attributed claim is genuine doubt; a first-person softener is politeness. Attribution markers are learnable surface, so the ruling is trainable.

Volume comes from a seeded, pure-code generator, byte-identical on every run, no LLM in the loop.

- Complete utterances are re-emitted truncated and labeled wait, because that is what ASR partials look like.
- Everything ships lowercased with punctuation stripped, so nothing cheats off periods.
- Spanish rides the same policy in the register Spanish-first carriers actually use; the hedge ruling transfers, "me dijeron que".

## Models, three lanes

Fine-tuned DistilBERT (66M) is the safe lane. The lane I built from nothing (3.7M, my own tokenizer, same recipe so the comparison isolates pretraining) failed twice, and each failure bought a finding.

- A 1532-piece tokenizer turned real text into walls of unknown tokens, and the model output a constant.
- A leaked template split put fills of the same template on both sides, measuring memorization as generalization.

Mechanics fixed, the verdict came clean: 0.99 on its own distribution, a coin flip on gold. Coverage was not the problem. Knowledge was. The curve on unseen real calls, one named ingredient per step: 0.48 random init, 0.60 with real data, 0.825 with a fifteen-minute pretrain of our own, 0.913 where the internet-pretrained fine-tune sits.

<p align="center"><img src="../assets/pretrain-curve.svg" alt="What pretraining is worth, measured as PR-AUC on unseen real calls: 0.48 random init, 0.60 adding real calls, 0.83 adding a fifteen-minute pretrain, 0.91 web-pretrained" width="100%"></p>

The default follows a written rule, not taste: scratch ships only at parity on every referee. Its 0.825 on real calls is not the fine-tune's 0.913, so the fine-tune ships, 0.949 gold with zero false-speak. The multilingual lane matches English gold (0.960 vs 0.958) and separates the Spanish slice perfectly, so Spanish is a model swap, not a rebuild.

## Evaluation

<p align="center"><img src="../assets/referees.svg" alt="Three referees, one question each: a frozen gold set of 60 human-labeled cards for generalization, 6 probe-found regressions for memory, and 96 held-out real-call turns for discovery" width="100%"></p>

- The frozen gold set grades quality and is never trained on.
- A separate dev set picks thresholds, labeled by three vendor judges, each certified against the gold cards before its votes count.
- A regression slice holds every failure found by live probing.

Then the referee that changed the build. I pulled sixty real production calls from my own agent and let them label themselves: where the caller stopped is a true complete, a mid-turn prefix is a true wait, one third locked away. The model that read 0.96 with zero false-speak on gold scored 0.61 on real calls. Every offline referee agreed with each other, and the real world disagreed with all of them. The fix ran inside the build: the other two thirds became training augmentation, graded on the locked third, and the shipping model went from 0.65 to 0.913 with recall 0.959. Raw call content never enters the repo.

| Model | Params | Gold PR-AUC | Gold false-speak at op | Spanish PR-AUC | Real calls PR-AUC | Real calls at op (false-speak / recall) | Tier-1 window | ECE |
|---|---|---|---|---|---|---|---|---|
| Fine-tuned DistilBERT (ships) | 66M | 0.949 | 0.000 | not trained for | 0.913 | 0.234 / 0.959 | 58 of 99 at 0.42 | in band |
| Multilingual DistilBERT + real | 134M | 0.979 | 0.407 | 1.000 | 0.875 | 0.191 / 0.878 | 4 of 99 at 0.97 | 0.349 |
| From-scratch, own pretrain (7.4M) | 7.4M | 0.973 | 0.037 | 1.000 | 0.825 | 0.277 / 0.755 | 60 of 99 at 0.79 | 0.062 |
| From-scratch, no pretrain | 3.7M | 0.994 | 0.000 | 0.996 | 0.597 | collapse | not picked | 0.045 |

## Serving and latency

- FastAPI over ONNX Runtime, dynamic int8, CPU, one worker.
- The threshold reads from the model directory, so a retrain updates the dial without touching serving code.
- A Dockerfile ships only the int8 model; the same process serves a live probe page that re-scores as you type.

The brief asked for under 100 ms. Measured on my laptop:

| Served artifact | c1 wall p50 | c8 wall p50 | c8 wall p95 | c8 req/s |
|---|---|---|---|---|
| Fine-tuned DistilBERT, 66M | 34.7 ms | 45.5 ms | 57.9 ms | 170 |
| Multilingual DistilBERT, 134M | 34.0 ms | 49.7 ms | 97.2 ms | 147 |
| From-scratch, 7.4M | 7.4 ms | 12.1 ms | 20.7 ms | 588 |

## Monitoring at a million calls a month

Turn detection grades itself in production, seconds later, for free.

- A speak decision followed by the caller talking over the agent was a false speak.
- A wait decision followed by dead air until a timeout was a false wait.
- Those two rates are the online eval, no annotation cost, mapping one to one onto the offline curve.

A small audited weekly sample keeps them honest; slice by language, accent, connection, customer. Ship shadow-first, promote on the measured curve, roll back with a pointer flip. And the brief's direct question, whether the datasets built here are the limit: yes, deliberately, until launch. My synthesis encodes policy, production volume supplies distribution, and that handoff is the whole monitoring design.

## The discussion questions

The ceiling of text-only is prosody, and it sits in the input, not the model: pitch decline, final lengthening, and breath never reach it, so some finished and unfinished utterances read identically. Multimodal is my next step, a small audio encoder fused at the decision layer, and the referees built here transfer to it unchanged, which is the point of building the referee first.

Could the transcriber do the job? ASR is trained prosody-invariant, so the signal dies at the text bottleneck. Three tiers follow.

- Free today: vendor word-level timestamps carry final-word lengthening and pause duration, two of the strongest endpoint cues. Feeding them in adds no model and no latency.
- Whisper: learn an end-of-turn token, read its probability from the same forward pass that produces the transcript.
- Streaming RNN-T: an end-of-utterance token in the transducer vocabulary, or a classifier head off the encoder states.

All need true boundaries, which the self-labeling loop produces. I would keep the detector separate while iterating and consider distilling later, since coupling puts two jobs on one latency budget.

Integration: the detector sits between streaming ASR and the LLM trigger; VAD flags a pause, the score maps to an endpoint delay, high commits, middling waits, low holds and re-scores per partial. Barge-in stays untouched, and the model adds single-digit milliseconds sitting next to the orchestrator. What else a reviewer might raise sits in collapsed blocks at the bottom of the README.

## Assumptions, written down

- The 1:5 cost ratio is a documented operating choice, not a law; a different ratio is a one-line change.
- Inputs arrive ASR-style, lowercased, no terminal punctuation, last agent utterance as context.
- The decision is binary, speak or wait; response policies are out of scope.
- Languages are English and Spanish.
- The latency budget is 100 ms end to end on CPU, no GPU anywhere.
