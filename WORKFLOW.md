# End-of-Turn Detection: Workflow & Labeling Guide

The take-home in one sentence: build the model that decides, while a caller is talking, the exact moment the agent should start speaking.

## The loop (who does what)

```
taxonomy (below)
   -> calibration samples (~60, spread across the taxonomy)
   -> JAMES LABELS them (the human judgment that defines "good")
   -> frozen gold set + written policy per ambiguous class
   -> large-scale synthetic dataset (policy-guided, thousands of samples)
   -> fine-tune small encoder -> eval vs frozen sets -> iterate
   -> FastAPI serving + Dockerfile + stress test (<100ms budget)
   -> shadow comparison vs ElevenLabs turn_v3 on aj production transcripts
   -> approach doc + video script
```

James is the policy judge: labels the calibration set, sets the cost asymmetry, reviews iteration metrics whenever. Claude runs everything else. James is IN the loop at exactly two doors: the submission email, and any public push. Everything else is reversible.

## The decision being made

At every ASR update the detector sees the transcript-so-far of the caller's current utterance (plus recent conversation context) and outputs one of two actions: **SPEAK** (turn is complete, agent responds now) or **WAIT** (caller is still going).

Two ways to be wrong, and they cost different amounts:

- **Interrupt** (said SPEAK too early): the agent barges in mid-thought. Rude, derails the caller, the error people remember.
- **Lag** (said WAIT too long): dead air after the caller finished. Feels sluggish, and every single turn pays the price.

A dumb system can be perfect on either axis alone (never speak means zero interruptions; speak instantly means zero lag). Good means the tradeoff frontier. The labels below decide where we sit on it, class by class.

## Scenario taxonomy: label against these

Samples mix a freight-logistics world (carriers, loads, MC numbers, rates, appointments) with general assistant calls (aj's world). A trailing `...` marks where the caller pauses and the detector must decide.

**Anchor classes (expected to be easy; they sanity-check the labeler and the model):**

| Class | Shape | Example | Expected |
|---|---|---|---|
| A | Complete statement | "I need to reschedule my Tuesday pickup." ... | SPEAK |
| B | Complete question | "What time does the warehouse close?" ... | SPEAK |
| C | Backchannel / short ack | "Yeah, sounds good." ... | SPEAK |
| D | Mid-clause cutoff | "I was thinking we could..." | WAIT |
| E | Disfluent trail | "So, um, I wanted to, uh..." | WAIT |
| F | Mid-data pause | "My MC number is 415..." | WAIT |
| G | Connector-final | "I can do Thursday, but..." | WAIT |

**Judgment classes (your labels set the policy; there is no textbook answer):**

| Class | Shape | Example | The tension |
|---|---|---|---|
| H | Complete-then-maybe-more | "That rate works for me." ... | Grammatically done, but callers often keep going. Speak or give grace? |
| I | Trailing hedge | "That's all I need, I guess..." | Hedge words invite a beat of silence. How long? |
| J | Self-interrupt pivot | "Can you- actually, you know what..." | Restart in progress. When does patience expire? |
| K | Explicit hold | "Hang on, let me grab the load number..." | Caller asked for time. WAIT, but for how long before checking in? |

## What your labels produce

1. A **frozen gold set** the model is never trained on: the referee.
2. A **written policy per judgment class** that guides how thousands of training samples get labeled at scale.
3. The **cost ratio** (how many extra beats of silence one interruption is worth). This picks the operating threshold on the tradeoff curve.

## Measurement (the zero and the one)

Filled from the pairwise research pass (running). Baselines forming the zero: always-SPEAK-on-pause (what a plain VAD timeout does), and a punctuation/heuristic rule. The one: fine-tuned model beats both on the frontier, inside the <100ms serving budget, verified on the gold set plus real aj production transcripts.
