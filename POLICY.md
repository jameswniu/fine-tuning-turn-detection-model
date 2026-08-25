# Turn Policy (frozen 2026-08-24)

Extracted from the labeler's 60-card calibration session in the Turn Booth (https://claude.ai/code/artifact/09af6768-a6a6-4786-9359-ae6bbcd422eb). This file is the human-judgment ground truth that drives synthetic data generation and threshold choice. The labeled set itself is `data/gold_set.json`, frozen, never trained on.

## The cost ratio

One interruption is as costly as five sluggish responses (1:5). Bayes decision rule: the agent speaks when P(turn complete) > 5/6, so the operating threshold is 0.833 at a nominal pause. Rationale: dead air was the chronic breach in the labeler's own production voice stack while interruptions stayed rare, and barge-in recovery caps the cost of a wrong interrupt.

## Class policies as labeled

Anchors came back clean: 26 of 28 exactly as the textbook expects, 2 boundary. The labeler is internally consistent, so the judgment classes below are read as policy rather than noise.

1. Complete statements, complete questions, and bare acknowledgements get a response (speak). Acknowledgements are complete turns but never call-enders; ending is a separate decision outside this model.
2. Mid-clause cutoffs, disfluent trails, mid-data pauses, and connector-final utterances hold (wait). Data readouts are an absolute hold, however long the pause runs.
3. Complete-then-maybe-more (H, labeled 6 speak / 1 wait / 1 unsure): a grammatically complete statement gets a response, unless the caller explicitly announces continuation ("Actually yeah, one more thing." holds). The one exception in the labels is the rule working, not breaking.
4. Trailing hedges (I, labeled 4 speak / 1 wait / 3 unsure): hedges are handoffs by default, so speak. Hedged confirmations where a decision is still settling ("that should work, probably...") sit at the boundary. One open tension is recorded below.
5. Self-interrupt pivots (J, labeled 1 speak / 6 wait / 1 unsure): wait through restarts, the new thought is coming. A full retraction ("no, scratch that...") may earn a brief acknowledgement.
6. Explicit holds (K, labeled 4 speak / 4 wait): the split is systematic, not random. When the caller is retrieving something themselves ("let me grab the load number", "let me check my rate con") the agent holds silently. When the caller narrates an outside interruption or a handoff to a third party ("I'm pulling over", "the receiver is waving at me", "let me ask my dispatcher", "another call coming in") the agent gives a brief courtesy acknowledgement and keeps listening. In the binary model both acknowledgement cases score as speak; the response length is a downstream concern.

## Boundary set

Seven cards were labeled unsure: A4, D1, H3, I4, I5, I8, J7. These are excluded from hard accuracy grading. A good model sits near the threshold on them rather than being confidently wrong in either direction.

## Open question (one)

I3 ("The broker said it was covered, supposedly...") was labeled speak while I7 ("The detention was approved, or something...") was labeled wait. The two shapes are nearly identical: a reported fact plus an uncertainty hedge. Pending the labeler's call on which reading is policy; until resolved, both are treated as boundary alongside the unsure set.

## Production policy notes, in the labeler's words

Verbatim from the calibration session, carried over from a production voice stack on a real 8 kHz phone line: never interrupt a data readout; a bare acknowledgement is a complete turn but never a call-ender (on telephony audio "thanks" and "next" collide, and a misheard "thanks" once ended a live call); an announced hold extends patience well past the normal window, then a gentle check-in; hedges are usually handoffs, respond and let barge-in recovery cover the miss; a complete statement that answers a question gets an immediate response, one that opens a new topic gets a beat of grace; self-interrupts get extended patience; where costs are asymmetric, absolute rules beat conditional ones.
