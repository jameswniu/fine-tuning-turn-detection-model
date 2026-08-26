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

## The design this argues for

Cascade by default, full panel on a sample. Bulk labeling runs the two-judge cascade and pays the third call only on splits. A periodic audit slice runs all three judges regardless, which keeps three things measurable that the cascade alone cannot see: the unanimity rate as a per-card confidence tier, the third judge's calibration (Gemini's two dissents here were both wrong, which is exactly the kind of drift an audit slice catches before the tie-breaker rots), and the correlated-error case where the lead pair agrees wrong, which was zero on this batch but is the one risk that grows silently if the two lead judges share blind spots. This is the same principle the production loop uses one level up: act on agreement cheaply, spend attention where voters differ, and keep a sampled slice fully instrumented so the instrument itself stays honest.
