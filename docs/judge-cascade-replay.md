# Judge panel A/B: cascade vs full panel, replayed on recorded votes

The dev set was labeled by a three-judge panel (Claude, Gemini, GPT), each voting blind on a 90-card batch that shuffled the 60 frozen gold cards in with 30 fresh ones, final label by 2-of-3 majority. A design question came up afterward: should all three judges vote on every card, or should two vote first and the third be summoned only when they split? Both designs were run against the same recorded votes (`data/judge_votes.json`, committed), so the comparison is a replay, not a rerun; zero new model calls. Reproduce with `python judge_cascade_replay.py`.

## The two designs

Full panel: all three judges vote on every card, majority wins. Cascade: GPT and Claude vote first; if they agree on a hard label, that is the label at a cost of two calls; if they split or either abstains, Gemini is summoned and majority decides at a cost of three. Under simple majority the third vote is mathematically decisive only on a split, so the two designs must agree on every label. The open question is empirical: what does the full panel measure that the cascade throws away, and does that information ever matter?

## Results on the 90-card batch

| Measure | Value |
|---|---|
| GPT and Claude agreement | 83 of 90 |
| Cost, cascade vs full panel | 187 vs 270 calls, 31% saved |
| Final labels, cascade vs full panel | identical on 90 of 90 |
| Unanimous 3-0 cards | 81 of 90 |
| Hidden dissents (pair agreed, Gemini differed) | 2, and the pair was right both times |
| Pair-agreed-but-wrong, the cascade's blind spot | zero cases |
| Judge accuracy, gold hard cards | Claude 53/53, Gemini 53/53, GPT 53/53 |
| Judge accuracy, fresh cards vs majority | Claude 30/30, GPT 30/30, Gemini 28/30 |

The equivalence held exactly: the cascade produced the identical label sheet at 31% less cost, and the failure mode that motivates the full panel, both lead judges agreeing on a wrong label, did not occur once on either the gold or the fresh half.

One result belongs to the full panel alone, because the cascade never collects it. Every judge voted "unsure" on exactly 7 cards, and for all three judges those were exactly the 7 cards the human labeler had flagged as boundary cases in the gold set, a 7/7 overlap. The panel reproduced not just the labels but the uncertainty. The standing caveat applies here as everywhere: certification was partially open-book, since POLICY.md quotes some boundary examples, so part of that overlap may be learned from the policy text rather than independently converged.

## How the judges actually work, and why to trust an autonomous labeler

This section answers the question a careful reviewer should ask about any machine-labeled data: the dev set was labeled autonomously, so why trust it?

The judges are not trained on anything in this repo. No fine-tuning, no gradient ever touched them. They are three stock frontier models from three different vendors (Claude, Gemini, GPT), used as-is. Each judge received the frozen human policy, POLICY.md, in its prompt, plus one card at a time (the agent context and the caller utterance), and answered speak, wait, or unsure by applying the written rules. Stateless, no memory across cards, fully replaceable.

Certification is an exam, not training. The 90-card batch shuffled the 60 frozen gold cards, whose labels the human author fixed in advance, among the 30 fresh unlabeled cards, and the judges could not tell which were which. A judge's votes on the fresh cards counted only because its votes on the interleaved gold cards reproduced the human's judgment, 53 of 53 hard labels for all three judges, with all three independently answering unsure on exactly the 7 cards the human had flagged as boundary. The standing caveat travels with these numbers: POLICY.md quotes some boundary examples, so the exam was partially open-book.

The blast radius is one number. Judge output never became training data and never touched a referee. It labeled only dev_set.json, whose single job is selecting the operating threshold, and even that dial cannot move freely, because the pick is constrained so all twelve tier-1 probes, which encode the human policy's absolutes, must hold on the served artifact. The gold referee stays human-labeled, the regression referee stays probe-found, the real-call referee stays human-corrected. In the worst case, all three judges wrong in the same direction, the damage is a suboptimal threshold inside hard human guardrails, and the referees would surface it as an out-of-band reading.

On accuracy between the two designs: it cannot differ and did not, since the pair's agreement already decides a 2-of-3 majority, so the label sheets are identical by construction, 90 of 90 measured. On reliability: the panel's mechanism is not three tries of one model but one try each from three vendors, which buys uncorrelated blind spots rather than averaged noise, and the vote record keeps every non-unanimous card visible (81 of 90 ran unanimous). Retry variance, asking a single judge the same card three times, was not measured; all votes are single-pass, and the committed vote file is the baseline any re-run would be compared against.

## The design this argues for

Cascade by default, full panel on a sample. Bulk labeling runs the two-judge cascade and pays the third call only on splits. A periodic audit slice runs all three judges regardless, which keeps three things measurable that the cascade alone cannot see: the unanimity rate as a per-card confidence tier, the third judge's calibration (Gemini's two dissents here were both wrong, which is exactly the kind of drift an audit slice catches before the tie-breaker rots), and the correlated-error case where the lead pair agrees wrong, which was zero on this batch but is the one risk that grows silently if the two lead judges share blind spots. This is the same principle the production loop uses one level up: act on agreement cheaply, spend attention where voters differ, and keep a sampled slice fully instrumented so the instrument itself stays honest.
