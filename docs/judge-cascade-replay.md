# Judge panel A/B: cascade vs full panel, replayed on recorded votes

The dev set was labeled by a three-judge panel, Claude, Gemini, and GPT, voting blind, final label by 2-of-3 majority. The 90-card batch shuffled the 60 frozen gold cards in with the 30 fresh ones. A design question came up afterward: run all three judges on every card, or run two and summon the third only on splits? Both designs were run against the same recorded votes (`data/judge_votes.json`, committed), so this is a replay rather than a rerun, zero new model calls. Reproduce with `python judge_cascade_replay.py`.

## The two designs

Full panel: three votes per card, majority wins. Cascade: GPT and Claude vote first. If they agree on a hard label, that is the label, at a cost of two calls. If they split or either abstains, Gemini joins and majority decides, at three. Under simple majority the third vote is decisive only on a split, so the two designs must agree on every label. The open question is what the full panel measures that the cascade throws away, and whether it ever matters.

## Results on the 90-card batch

| Measure | Value |
|---|---|
| GPT and Claude agreement | 83 of 90 |
| Cost, cascade vs full panel | 187 vs 270 calls, 31% saved |
| Final labels, cascade vs full panel | Identical on 90 of 90 |
| Unanimous 3-0 cards | 81 of 90 |
| Hidden dissents (pair agreed, Gemini differed) | 2, and the pair was right both times |
| Pair-agreed-but-wrong, the cascade's blind spot | Zero cases |
| Judge accuracy, gold hard cards | Claude 53/53, Gemini 53/53, GPT 53/53 |
| Judge accuracy, fresh cards vs majority | Claude 30/30, GPT 30/30, Gemini 28/30 |

The equivalence held exactly. The cascade produced the identical label sheet at 31% less cost, and the pair never agreed on a wrong label, on either half of the batch.

One result belongs to the full panel alone, because the cascade never collects it. Every judge voted unsure on exactly 7 cards. For all three judges, those were exactly the 7 cards the human labeler had flagged as boundary in the gold set. The panel reproduced the uncertainty, not just the labels. The standing caveat applies: certification was partially open-book, since POLICY.md quotes some boundary examples.

## How the judges actually work, and why to trust an autonomous labeler

This section answers the question a careful reviewer should ask: the dev set was labeled autonomously, so why trust it?

The judges are not trained on anything in this repo. No fine-tuning, no gradient ever touched them. They are three stock frontier models from three vendors, used as-is. Each received the frozen human policy, POLICY.md, in its prompt, plus one card at a time, and answered speak, wait, or unsure by applying the written rules. Stateless, no memory across cards, fully replaceable.

Certification is an exam, not training. The batch hid the 60 gold cards, labels fixed by the human in advance, among the 30 fresh ones, and the judges could not tell which were which. A judge's votes on the fresh cards counted only because its votes on the hidden gold cards reproduced the human's judgment, 53 of 53 for all three. The open-book caveat above travels with those scores.

The blast radius is one number. Judge output never became training data and never touched a referee. It labeled only dev_set.json, whose single job is selecting the operating threshold. Even that dial cannot move freely, because the pick must keep all twelve tier-1 probes green on the served artifact, and those probes encode the human policy's absolutes. The gold referee stays human-labeled, the regression referee stays probe-found, the real-call referee stays human-corrected. Worst case, all three judges wrong in the same direction, the damage is a suboptimal threshold inside hard human guardrails, and the referees would show it as an out-of-band reading.

On accuracy between the designs: it cannot differ and did not, 90 of 90 identical by construction and by measurement. On reliability: the panel is not three tries of one model but one try each from three vendors. Diversity buys uncorrelated blind spots; retries only average one model's noise. Retry variance, one judge asked the same card three times, was not measured. All votes are single-pass, and the committed vote file is the baseline any re-run compares against.

## The design this argues for

Cascade by default, full panel on a sample. Bulk labeling runs the two-judge cascade and pays the third call only on splits. A periodic audit slice runs all three regardless, which keeps three things measurable that the cascade cannot see. The unanimity rate becomes a per-card confidence tier. The tie-breaker stays calibrated; Gemini's two dissents here were both wrong, the kind of drift an audit catches before it matters. And the correlated-error case, the lead pair agreeing wrong, stays watched; it was zero on this batch and grows silently if the lead judges share blind spots. The production loop uses the same principle one level up: act on agreement cheaply, spend attention where voters differ, and keep a sampled slice fully instrumented so the instrument stays honest.
