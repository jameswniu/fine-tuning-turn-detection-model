# Referee cards

One card per number a stranger sees, written from the code and the reports rather than the README. First audited on the `referee-card` branch off origin/master at 94fad40, then re-audited after the corrections at f5cfcb4. Every score below comes from `models/eot-distilbert-onnx-int8/model.onnx`, sha256 `597de86f...814ed6`, at threshold 0.42. Each card is the eight spoken lines. The locations sit under it so the card stays sayable in a minute.

## Numbers on a surface that no script or report produces

None survive. The two entries that stood here at 94fad40 were settled like this.

- **0.968 gold, and its "two clean runs picked 0.71 and 0.63" pairing (README line 115 at 94fad40). REMOVED and replaced with the measurement.** There was one clean retrain, not two. Its fp32 export reads 0.9650 on the 53 gold cards and its int8 export 0.9665, both re-scored live one row at a time, and the two thresholds are 0.71 from `models/eot-distilbert-fresh-onnx/threshold.json` at 41 admissible values and 0.63 from `models/eot-distilbert-fresh-onnx-int8/threshold.json` at 32. The README now says that plainly, as one set of weights read through two execution paths, which is this repo's own headline finding rather than run-to-run variance.
- **The v1 to v8 headline numbers (README lines 157 to 164 and iterations.md lines 7 to 14 at 94fad40). KEPT, and labelled for what they are.** Each run wrote its report to the same filename and the next run overwrote it, so no file backs those readings today. Both tables now carry a line saying so, and both name v9 as the only row that regenerates from the committed artifact. The history stays because a build log is worth more than a hole, and the gold recall column that was missing from the README table is back.

Nowhere on any surface here do "30MB", "135MB", "3.4 ms" or "87 commits" appear. origin/master is 89 commits.

## Mismatches

None remain. All 26 entries from the 94fad40 audit are resolved in the files, and a second adversarial pass over the corrected diff found ten more, all of them also resolved. The two that mattered were the published `gh-pages` copies still serving four of the removed numbers, and a headline latency labelled as the shipped artifact that had been measured on an earlier build. What each fix was is in the cards below.

Three greps still match and none is a claim. `WORKFLOW.md` line 30 uses "zero interruptions" to describe a hypothetical system that never speaks, not this model. `ood_from_elevenlabs.py` keeps the `policy_corrected` key because the filter is real code, and the correction was to the prose that claimed it had fired. `docs/probe-comparison.html` rows 25 and 26 read 0.978 and 0.968, which are measured probe scores for unrelated rows rather than the removed 0.968 gold claim.

One claim was outside the working tree but inside the repository. The `gh-pages` branch serves the page the README links to, and both `index.html` and `probe-comparison.html` there were byte-identical to `docs/probe-comparison.html` at 43a5649, so a reader one click from the README still saw 16.6 ms, 2.8 ms, 66M and 7.4M after this pass had removed all four. Both files are now copies of the corrected `docs/probe-comparison.html`, committed on `gh-pages` and unpushed.

Two claims sit outside the repository and no commit can reach them.

- **The GitHub repository description**, set in the GitHub web UI rather than in any tracked file, still reads "zero false interruptions", "ONNX int8 on CPU at 58 ms p95" and "three eval referees on real calls". All three are wrong for the same reasons items 1, 3 and 24 named. The replacement the coordinator supplied is 352 characters, not 349, and it still carries the 32.8 ms quiet-box claim that defect 3 removed, so this is that text with the re-benched number and the false machine-state claim dropped, at 337 characters. `End-of-turn detection for voice agents. Fine-tuned DistilBERT, int8 on CPU at threshold 0.42, 0.949 PR-AUC on a frozen 53-card human gold set, no false speaks on its 27 wait cards, and 0.913 on 96 held-out real-call turns, speaking over 11 of 47. Three referees, gold, regressions and real calls. 33.1 ms end-to-end p95 at concurrency 8.`
- **The submitted PDF** is the render of `docs/approach.md` at commit ae1d2d0. That file has now changed, so the PDF is a frozen copy of the pre-audit text and still carries items 5, 6, 8, 9, 18 and 19 verbatim. Nothing in this repository can correct a PDF already sent. Anyone re-rendering it should render the current `docs/approach.md`.

## Reproduced live at f5cfcb4

Gold PR-AUC 0.9487856622228145 on n 53, gold false-speak 0.0 and recall 0.6538, per-class A through H 1.000 with I 0.200, J 0.857 and K 0.500, ECE 0.15956, the seven boundary cards individually and their 0.3068 mean, real calls 0.9129 with 0.2340 false-speak and 0.9592 recall on n 96 split 49 speak and 47 wait, regressions 1.0 on n 6, all 12 pinned cards passing one row at a time, `admissible_count` 56 from a live `make threshold` that rewrote `threshold.json` byte-identically, the quantization trio at 0.2629 fp32 single-row, 0.3813 int8 batched and 0.4117 int8 single-row, the judge replay at 53/53 for all three vendors with 83/90 pair agreement and 31% saved, parameter counts by ONNX initializer sum, tokenizer vocabularies of 1,723 byte-level BPE for the random-init lane and 16,000 byte-level BPE for the pretrained one, `python draw_figures.py --check` green on all six figures, `python probe_compare.py` at 31/35 and 34/35, `make serve` answering `/predict` with 0.4117 and wait, and four `make bench` passes against the shipped int8 file reading c8 wall p95 33.1, 31.0, 31.3 and 30.6 ms at 312 to 321 req/s with the box at a load average near 4 of its 18 cores.

A clean clone cannot reproduce any real-call number, because `data/ood_*.jsonl` is gitignored, nor any report file for the same reason. It also cannot reproduce most of the fleet, since `models/*` is gitignored except two directories, the shipped `eot-distilbert-onnx-int8` and `eot-scratch-pre-onnx-int8`. So the gold, regression, pinned-card, threshold and judge numbers regenerate for those two lanes only. The gold and Spanish figures at approach.md lines 53, 55 and 56 and iterations.md lines 26, 28 and 29 do not, and neither does the fp32 half of the 0.26 reading, since `eot-distilbert-onnx` is gitignored too. Did not retrain, since `make train` builds a different model. CI covers figure constants, module parsing and gold-set integrity. It runs no eval, no threshold pick and no pinned-card check, which is why only two badges remain on the README and the CI answer block says so.

## Cards

### 0.949 gold PR-AUC

```
Claim     0.949, the headline score on the frozen gold set
Unit      average precision of P(speak) over the 53 gold cards labeled speak or wait, the 7 unsure ones outside the denominator
Match     the served int8 file, sha256 597de86f...814ed6, ONNX Runtime on CPU, one row per call, padded to 128 tokens
Set       60 cards labeled blind by James in the booth on 2026-08-24 and frozen, against a policy he also wrote
Command   make eval, average_precision_score at evaluate.py line 258, hard.pr_auc in eval_report_frozen_gold.json, gitignored
Sibling   0.913 on held-out real calls, where the no-pretrain small model that reads 0.994 here collapses to 0.597
Bound     one card is two points of the whole, no public band exists, and the self-set bar is this project's own v1 at 0.961
Knob      the training mix, which took gold from 0.958 down to 0.949 and real calls up
```
Appears at README line 2 alt, line 10, line 153, `hero.svg`, EVALS.md lines 38 and 57, iterations.md lines 17 and 25, approach.md lines 38 and 52.

### No false speaks on the 27 gold wait cards

```
Claim     zero, and the number it now travels with, 0.234 on real calls
Unit      of the 27 gold cards labeled wait, none scores at or above 0.42, a rate of 0 over 27
Match     speak when p is at or above 0.42, so the boundary value speaks, at serve.py line 58 and pick_threshold.py line 63
Set       the same frozen cards, and 4 of those 27 are pinned rows the threshold was chosen to keep correct
Command   make eval, false_speak_rate at the 0.42 row of hard.threshold_sweep in eval_report_frozen_gold.json
Sibling   the same file at the same 0.42 interrupts 11 of 47 real turns, a rate of 0.234, and both now sit in the same sentence
Bound     zero seen in 27 puts the exact 95% upper bound at 0.105, so this is under roughly one in ten, never never
Knob      the threshold, since below 0.42 the pinned continuation card at 0.412 flips
```
Appears at README line 2 alt, line 10, line 21, `hero.svg` as the "0 of 27 false speaks" stat, EVALS.md line 39, approach.md line 38. The bare phrases "zero false interruptions" and "zero false speaks" appear nowhere in the repo now. "zero interruptions" survives only at WORKFLOW.md line 30, describing a system that never speaks, which is not a claim about this model.

### Gold recall 0.654 at the operating point

```
Claim     0.654, how much finished speech the model actually answers
Unit      of the 26 gold cards labeled speak, 17 clear 0.42, so 9 finished turns are left hanging
Match     the same served int8 file, one row per call, at or above 0.42 counts as speak
Set       the same frozen cards, the 26 speak ones, 7 unsure excluded, precision 1.0 alongside
Command   make eval, recall at the 0.42 row of hard.threshold_sweep, sklearn recall_score at evaluate.py line 91
Sibling   on held-out real calls the same file recalls 0.959, so the two recalls point opposite ways
Bound     EVALS.md line 40 targets 0.85, so this is far out of band, and both the table and the summary now say so
Knob      the agent's last line, since recall is 1.00 with it and 0.47 without
```
Appears at README line 10, the Gold recall column of the README run table at lines 145 to 153, EVALS.md lines 40, 50 and 57, iterations.md lines 9 to 17.

### 0.913 on held-out real calls

```
Claim     0.913, the score on speech nobody wrote for this project
Unit      average precision over 96 turns of data/ood_test.jsonl, 49 speak and 47 wait
Match     the same served int8 file, one row per call, same input format
Set       400 turns cut from the author's own deployed agent over 59 calls, labels assigned by rule with no human pass at ood_from_elevenlabs.py lines 121 to 142, split by call into 304 over 40 and 96 over 19
Command   evaluate.py --data data/ood_test.jsonl, jsonl.pr_auc in eval_report_frozen_oodtest.json, and both data and report are gitignored
Sibling   0.949 on the gold set, where the small model reading 0.597 here reads 0.994
Bound     96 turns from 19 calls, one agent, one vendor, one language, and rows from a call are not independent
Knob      real-call rows in training, added at four-fold weight and grouped by call
```
Appears at README line 2 alt, line 10, line 153, `hero.svg`, iterations.md lines 17 and 25, EVALS.md line 51, approach.md lines 34, 38 and 52, and as "0.91" in `pretrain-curve.svg`.

### 0.234 false-speak and 0.959 recall at threshold 0.42

```
Claim     0.234 and 0.959, what the shipped setting does on real callers
Unit      11 of 47 real turns labeled wait clear 0.42, and 47 of the 49 labeled speak do
Match     the same served int8 file, one row per call, boundary value speaks
Set       the same 96 held-out turns over 19 calls, labels assigned by rule and never reviewed by hand
Command   evaluate.py on data/ood_test.jsonl, the 0.42 row of jsonl.threshold_sweep in eval_report_frozen_oodtest.json
Sibling   0.000 false-speak on the gold cards, same file, same threshold, and that gap is the whole audit
Bound     EVALS.md line 51 draws the line at 10%, and 11 of 47 is Wilson 0.136 to 0.372 or exactly 0.123 to 0.380
Knob      the threshold, since 0.9 drops false-speak to 0.085 and recall to 0.735
```
Appears at README line 2 alt, line 10, line 21, `hero.svg` as the 0.234 stat with its "11 of 47 wait turns" label, approach.md lines 38 and 52, iterations.md lines 16 and 17, EVALS.md lines 39 and 51.

### 33.1 ms end-to-end p95

```
Claim     33.1 ms p95, the speed number against the brief's 100 ms budget
Unit      95th percentile of end-to-end wall time per request at concurrency 8 over 1500 requests, the client's clock, not model-only time
Match     the shipped int8 file behind FastAPI and uvicorn, one worker, ONNX Runtime on CPU, one row per request
Set       four passes benched on 2026-09-04 with the dev box at a load average near 4 of its 18 cores, worst of the four quoted
Command   make bench, which runs bench.py --n 1500 --concurrency 1,8,32, and the report is gitignored
Sibling   model-only p95 is 30.4 ms on the same pass, and the same file under a training load read 57.9 ms wall and 48.2 ms model
Bound     one box, no GPU, and the four passes spanned 30.6 to 33.1 ms, so the spread inside one machine state is 2.5 ms
Knob      what else the machine is doing, since nothing about the model changed between the two states
```
Appears at README line 2 alt, line 10, line 192, line 195, `hero.svg` twice, EVALS.md line 57, approach.md line 70. The 57.9 ms loaded reading sits beside it at README line 193, EVALS.md line 57 and approach.md line 71, labelled as the loaded box. "58 ms" and "32.8 ms" appear nowhere now.

The number this replaces was worse than wrong, it was the right defect in the wrong file. `bench_report.json` was written 2026-08-24 at 21:23:01 and the shipped `model.onnx` at 2026-08-25 at 01:04:10, so the quiet bench this pass first promoted to the headline had never touched the artifact it was labelling. The only bench of the shipped file was the loaded one at 01:16:14. Re-benching was the fix, and the mtime check is the check that catches it.

### 12 of 12 pinned cards

```
Claim     12 of 12 green on the served artifact
Unit      12 constraint rows with required decisions, all correct at 0.42, counting cards not the 7 named checks
Match     each row scored alone, admissible when (prob >= t) equals (required == "speak") at pick_threshold.py line 63
Set       derived by make_tier1_probes.py from 4 readout cards, gold H5, dev dH4 and 6 regression rows, rebuilt by rule after the original was lost
Command   make tier1 then make threshold, re-run live here at 12 of 12
Sibling   the same 12 read 11 of 12 at v8 and red at v7 on identical weights, so only the measurement changed
Bound     12 hand-picked cards, 6 of them already in the training data, so this tests memory rather than generalization
Knob      the batch shape, since batched these score dH4 at 0.3813 and one at a time 0.4117
```
Appears at README lines 88, 129, 138, 153, 254 and 263, EVALS.md line 57 where the 12-against-7 difference is now stated inline, iterations.md lines 17 and 25, `hero.svg`, `judges.svg`. The README badge that carried it is gone, because CI never ran this check.

### 60-card frozen gold set, 7 unsure

```
Claim     60 cards, frozen, 53 scored and 7 unsure
Unit      60 rows, 27 wait, 26 speak, 7 unsure, and every headline uses the 53
Match     labels are strings, no matching rule, and evaluate.py line 251 routes unsure to its own section
Set       labeled by James in labeling-booth.html on 2026-08-24 against POLICY.md, shuffled so the class list could not order the judgments
Command   CI asserts 60 samples and no gold text in train.jsonl, the only metric-adjacent thing CI checks
Sibling   the 7 unsure cards read 0.985, 0.026, 0.986, 0.068, 0.021, 0.045 and 0.016, all confidently wrong by the EVALS.md line 43 rule
Bound     one labeler and one policy author, no second annotator, so this measures fidelity to one written policy
Knob      the policy, and class I is where it bites and where the model scores 1 of 5
```
Appears at the README line 7 badge, README lines 10, 22 and 184, `band-judged.svg`, `referees.svg`, data/README.md line 11, approach.md line 18. This is the one badge kept beside CI, because the CI job asserts it.

### Three vendor judges, 53 of 53 on 90 blind cards

```
Claim     53 of 53, the exam all three machine labelers passed
Unit      each judge labeled 90 cards, and 53 is the scorable gold ones, with all three unsure on exactly the other 7
Match     no threshold, votes are speak, wait or unsure, and majority() at judge_cascade_replay.py line 19 ignores unsure
Set       60 gold and 30 fresh cards shuffled, judged by stock Claude, Gemini and GPT with the policy in the prompt, votes committed
Command   python judge_cascade_replay.py, re-run live at 53/53 for all three and 83/90 pair agreement
Sibling   Gemini is the outlier at 28 of 30 on fresh cards, and both hidden dissents went the pair's way
Bound     one vote per judge per card, no retry variance, which the README's measured-and-not block lists as not measured
Knob      the prompt, whose quoted boundary examples make 53 of 53 easier than it sounds
```
Appears at README lines 22, 123 to 129, `judges.svg`, data/README.md line 15, docs/judge-cascade-replay.md lines 19 and 32. The README badge that carried it is gone, because CI never runs the replay.

### The measured parameter counts

```
Claim     3.70M, 3.99M, 7.36M, 66.96M and 135.33M, the sizes of every lane
Unit      parameter count, the sum of the ONNX initializer elements of each committed or local export
Match     3.70M scratch at random init, 3.99M scratch-real, 7.36M scratch-pre, 66.96M DistilBERT, 135.33M multilingual
Set       trained by train_scratch.py on a byte-level BPE tokenizer built in repo, pretrained by pretrain_scratch.py
Command   python -c "import onnx;from onnx import numpy_helper as n;m=onnx.load(P);print(sum(n.to_array(t).size for t in m.graph.initializer))"
Sibling   7.36M reads 0.973 gold and 0.825 real, 3.99M reads 0.994 and 0.597, and 3.70M reads 0.502 and 0.477
Bound     no committed report prints a count, so every figure label rests on this one command being re-run
Knob      the pretrain step, the only difference between the 3.99M and 7.36M lanes, worth 23 points of real-call score
```
Appears at README lines 10, 37 and 97, `band-models.svg` at "66.96M vs 7.36M params", the four sub-labels of `pretrain-curve.svg`, approach.md lines 29, 34, 52 to 58 and 70 to 73, iterations.md lines 25 to 29 and 38. The label "7.4M" appears nowhere in the repo now, and the from-scratch row in approach.md that carried scratch-real's numbers under a 3.7M label is relabelled 3.99M, with the true 3.70M model given its own row.

### The pretraining curve, 0.48 to 0.60 to 0.825 to 0.913

```
Claim     0.48, 0.60, 0.825 and 0.913, what pretraining is worth
Unit      average precision on the same 96 held-out real turns, four models, same encoder throughout, vocabulary 1,723 then 2,841 then 16,000
Match     four served int8 files scored one row at a time, at 3.70M, 3.99M, 7.36M and 66.96M, with only the last two in git
Set       data/ood_test.jsonl, gitignored, 96 turns over 19 calls with rule-assigned labels, so no reader can regenerate any of the four
Command   evaluate.py per model dir into eval_report_scratch_oodtest.json at 0.4773, scratchreal 0.5971, scratchpre 0.8253, distilen 0.9129
Sibling   on gold the same four read 0.502, 0.994, 0.973 and 0.949, the opposite ordering
Bound     four points, one seed each, no error bars, and the 0.48 model also has a 1,723-piece vocabulary against 16,000
Knob      language exposure, and the figure rounds 0.825 to 0.83 and 0.913 to 0.91
```
Appears at README line 34 alt, `pretrain-curve.svg`, approach.md lines 34 and 36, iterations.md line 38.

### Spanish, six probe scores averaging 0.770

```
Claim     six Spanish probe scores between 0.731 and 0.814, mean 0.770, three of them wrong
Unit      P(speak) on six hand-written Spanish probes, scored one row at a time, wrong when the decision at 0.42 disagrees with the policy
Match     the shipped English int8 file at 0.42, which is the point, since English DistilBERT was never trained for Spanish
Set       six rows of probe_compare.py, the author's own, not held out
Command   python probe_compare.py, which prints them into docs/probe-comparison.html at 0.814, 0.777, 0.731, 0.734, 0.798 and 0.768
Sibling   the multilingual lane separates the 187-row Spanish eval perfectly at 1.000, and it ships as the variant
Bound     six self-written probes, no interval worth quoting, and the "flat 0.75" this replaces was never computed at all
Knob      the base model, since English DistilBERT is uncased English WordPiece
```
Appears at README line 41, docs/probe-comparison.html rows 30 to 35. The separate multilingual comparison at approach.md line 38 now names the two models that ship, 0.979 against 0.949, instead of two that never did.

### 36 probes, 31 of 35, mean 17.8 ms

```
Claim     31 of 35 against 34 of 35, on a page that shows 36
Unit      36 rows shown and 35 graded, the 36th unsure and excluded at probe_compare.py line 103, with 17.8 ms the mean of 36 single-row timings
Match     both models scored one row at a time on their own int8 file at their own threshold, a cell wrong when it disagrees with the policy
Set       36 probes hand-written in probe_compare.py lines 32 to 69, the author's own, not held out
Command   python probe_compare.py, which writes docs/probe-comparison.html and prints the counts
Sibling   the two tie at 28 each on English and share one miss, an unpunctuated yes-no question
Bound     35 self-written probes are a demonstration, no interval worth quoting and no independent labeler
Knob      the probe list, since one row moves the fraction three points with no model change, and the mean latency moves a millisecond every run
```
Appears at README lines 28, 30 alt, 39 and 40, docs/probe-comparison.html header and lead, and the `gh-pages` copies of that file at `index.html` and `probe-comparison.html`, which is where the README line 30 link actually lands. The "36 probes" label beside "31 of 35" now carries its reason in the same sentence, and the README says the latency row is one run on one laptop.

### The 1:5 cost ratio, threshold 0.42, ECE 0.160

```
Claim     0.42, picked by a 1:5 cost ratio, on a model whose ECE is 0.160
Unit      cost is 5 times the false-speak rate plus the false-wait rate, both class-conditional, and ECE is 10-bin error on 53 cards
Match     thresholds swept at i/100 from 1 to 99, ties preferring the lower, admissible only when all 12 pinned cards land correctly
Set       scored on data/dev_set.json, 30 fresh judge-labeled cards disjoint from gold, with 1:5 a written choice from the author's production agent
Command   make threshold, writing models/eot-distilbert-onnx-int8/threshold.json, re-run live at 0.42 with 56 admissible
Sibling   the closed-form answer for 1:5 is 0.833, and on synthetic validation the same machinery picked 0.87 then 0.86
Bound     30 cards is a thin objective, and 0.42 is the lowest admissible value, so the pick sits on a wall
Knob      the ratio, which is a one-line change
```
Appears at `hero.svg`, README lines 21, 121, 137, 259, 261 and 263, EVALS.md lines 36, 57 and 61, iterations.md lines 15 to 17, data/gold_set.json, approach.md line 52. The admissible count is 56 everywhere now, matching `threshold.json` and a live sweep, and the "58 of 99" in approach.md is gone.

### The judgment classes, 1 of 5 hedges and 4 of 8 holds

```
Claim     0.20 on hedges and 0.50 on holds, the two classes the README calls weak
Unit      per-class accuracy at 0.42, where I is 1 of 5, K 4 of 8, J 6 of 7 and H 7 of 7
Match     the same served int8 file, one row per call, per_class_accuracy at evaluate.py line 100
Set       the frozen gold cards by assigned class, where H, I, J and K hold 8 each but 5 unsure ones drop out, so class I scores 5
Command   make eval, per_class_accuracy_at_threshold and slices in eval_report_frozen_gold.json, re-run live and matching
Sibling   the same hedge shape passes on the probe page at 0.981, so page and gold disagree about the weakest class
Bound     5 cards for the class the weakness paragraph leads with, where one card is 20 points
Knob      the agent's last line, since recall goes 1.00 to 0.47 without it
```
Appears at README lines 79 and 175, EVALS.md line 42, the Hedge and K columns of iterations.md lines 9 to 17. The README's "two of ten" is now "1 of the 5 scored hedge cards", which is the same 0.20 read as the rate it is.

### The quantization trio, 0.2629 and 0.3813 and 0.4117

```
Claim     0.26, 0.38 and 0.41, one card under three execution paths
Unit      P(speak) for dev row dH4, "Actually, hold that thought." after "Agent: Anything else before I let you go?"
Match     0.2629 is fp32 single-row, 0.3813 is int8 with all 12 pinned rows batched, 0.4117 is int8 single-row as serve.py does
Set       one card, not a set, and it is the pinned row that fixes the operating point
Command   reproduced live against both export dirs and through /predict, which returned 0.4117 and wait
Sibling   the continuation card beside it reads 0.035 single-row on the live page, so the batch effect shows up only near the threshold
Bound     one card proves the failure mode exists, not how often, and nothing measures batch sensitivity across the set
Knob      batch composition under dynamic int8 quantization, so score the way you serve
```
Appears at README lines 23, 232 and 253, iterations.md lines 15 and 16.

### The announced-continuation score, 0.035

```
Claim     0.035, the card the tier-1 continuation gate exists for
Unit      P(speak) for "actually yeah, one more thing." after "Anything else?", scored one row at a time, which the live page renders as 3.5%
Match     the served int8 file through serve.py, the same path the gif recorded
Set       one card, and the probe page runs a longer sibling, the same words cased after "Anything else I can help with?", which reads 0.036
Command   POST /predict with that context and text, or read row 16 of docs/probe-comparison.html for the sibling
Sibling   the same class holds at 0.015 on the second announced-continuation probe, so the class is not carried by one card
Bound     one card, and the whole class is 8 gold rows with one labeled unsure
Knob      the agent's last line, since the same words with no context read 0.013
```
Appears at README line 20 and the line 65 gif alt, both now at 0.035, and docs/probe-comparison.html row 16 at 0.036 for its different input. The "near 0.04" phrasing is gone.
