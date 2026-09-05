# Referee cards

One card per number a stranger sees, written from the code and the reports rather than the README. Audited on the `referee-card` branch off origin/master at 94fad40. Every score below comes from `models/eot-distilbert-onnx-int8/model.onnx`, sha256 `597de86f...814ed6`, at threshold 0.42. Each card is the eight spoken lines. The locations sit under it so the card stays sayable in a minute.

## Numbers on a surface that no script or report produces

- 0.968 gold (README line 115). The other half of that sentence, 0.966, is `eval_report_fresh_gold.json`. The fresh run's fp32 export scores 0.9650 on the same 53 cards single-row, and its int8 export 0.9665. Neither is 0.968.
- Every headline in the v1 to v8 rows (README lines 157 to 164, iterations.md lines 7 to 14). Gold 0.961, 0.964, 0.970, 0.969, 0.958, 0.955, ECE 0.114 through 0.169, and v6's real-call reading of 0.905. Each run overwrote the last report, so only the log carries them. The nine-row table is the repo's central story and none of it is checkable.

Absent from every surface here: "30MB", "135MB", "3.4 ms", "87 commits". origin/master is 89 commits.

## Mismatches

1. "zero false interruptions" carries no set label on the GitHub description or the README line 2 hero alt, README line 14 shortens it to "zero interruptions", and `hero.svg` says "zero false speaks" and sets it beside "0.913 real calls" as if the zero covered both. One number, three phrasings, no denominator. The same file at the same threshold interrupts 11 of 47 wait turns on the held-out real calls, 0.234, printed in the approach doc's own table and EVALS.md line 51.
2. 58 ms p95 is from `bench_report_distilen.json`, taken mid training load. README line 329, EVALS.md line 57 and iterations.md line 38 each say only quiet-machine benches get quoted. The quiet bench reads 32.8 ms. README line 207 says the opposite of the other three.
3. 58 ms is wall time at concurrency 8, not model time. The GitHub description reads "ONNX int8 on CPU at 58 ms p95". Model-only p95 at c8 is 48.2 ms loaded and 31.0 ms quiet.
4. Quiet-bench throughput is 320 req/s in EVALS.md line 57 against 316.35 in `bench_report.json`. README line 204's 316 is that value rounded and is fine.
5. `models/eot-distilbert-onnx-int8/threshold.json` records `admissible_count` 56 and a live sweep returns 56. approach.md line 52 says "58 of 99 at 0.42". Falsifiable from a file the reviewer already has.
6. Parameter counts, measured by summing ONNX initializer elements on the committed and local exports: 3.70M for scratch, 3.99M for scratch-real, 7.36M for scratch-pre, 66.96M for DistilBERT, 135.33M for the multilingual model. README line 14 and `band-models.svg` say 7.4M, which is right for scratch-pre only. approach.md line 29 calls the whole from-scratch effort 3.7M.
7. `pretrain-curve.svg` labels the 0.48 and 0.60 points "7.4M" via `draw_figures.py` lines 39 and 40. Those readings come from a 3.70M and a 3.99M model.
8. approach.md line 55's "From-scratch, no pretrain, 3.7M" row carries 0.994 gold, 0.996 Spanish, 0.597 real and ECE 0.045, which are scratch-real's numbers. scratch-real is 3.99M. The true 3.70M model reads 0.502 gold and 0.477 real and appears nowhere in that table.
9. Multilingual size is 135M in iterations.md line 24 and 134M in approach.md line 53. 135.33M measured, so iterations.md is right and the document is wrong.
10. "36 probes" shares a README line 51 table row with "31 of 35" and "34 of 35". The page shows 36 and grades 35 because the 36th is an unsure boundary card, and that reason sits only in the page footer.
11. The announced-continuation score is 0.035 in README line 32, 0.036 on the probe page, and "near 0.04" in the README line 77 alt. Different contexts, one apparent card, three values.
12. "two of ten" hedge cases (README line 91). Class I has 8 gold cards, 3 of them unsure, so 5 are scored and 1 is right. The 0.20 everywhere else is that rate, redressed here as a count.
13. "96 turns from 60 calls" appears in data/README.md line 23 and again as "96 turns from 60 production calls" in EVALS.md line 51. It is 96 turns from 19 calls. The 400-turn parent holds 59 calls, split 304 over 40 and 96 over 19, with no call on both sides.
14. data/README.md line 23 says the real-call rows were "Labeled by the author". `ood_from_elevenlabs.py` lines 121 to 142 assign every label by rule with no human pass, a full user turn becoming speak and a random non-sentence-final prefix becoming wait. EVALS.md line 51 and approach.md line 48 both say self-labeled. The doc that describes the data takes the wrong side of its own repo.
15. The `policy_corrected` filter (data/README.md line 23, README lines 287 and 306, "policy-corrected" in `referees.svg`) touched zero shipped rows. The code first appears at commit 0e15d5b on 2026-08-25 at 02:07 and is absent at 3d4975a at 00:26, while all three ood files were written at 01:12 between them, and iterations.md line 13 records "policy-filtered 0 vendor-behavior rows". No row in any ood file carries the key.
16. data/README.md line 23 says the repo ships "the loaders, the reports, and this description". `.gitignore` matches every report and `git ls-files` returns none, so nothing here is independently checkable.
17. "nah bye" after the fix is 0.978 in data/README.md and 0.985 on the probe page, which is the contexted row. README line 89's alt says 0.97, which is the bare row and reads 0.9718 live, a different input rather than a third value for the same one.
18. "the multilingual lane matches English gold (0.960 vs 0.958)" (approach.md line 38) pairs a model picked at 0.33, where its own gold false-speak is 0.889, against a v5 reading. Neither ships. The shipped pair is 0.979 and 0.949.
19. "scored 0.61 on real calls" (approach.md line 48) sits in the paragraph about the held-out third but is measured over all 400 turns at threshold 0.81, a different set.
20. EVALS.md line 43 declares a boundary band of 0.35 to 0.65 with "zero confidently wrong (over 0.9 or under 0.1)". `evaluate.py` line 16 measures a different interval, 0.4 to 0.9, and reports `count_in_band` 0, which reads as a pass. Scored one row at a time the seven cards read A4 0.985, D1 0.026, H3 0.986, I4 0.068, I5 0.021, I8 0.045 and J7 0.016, so all 7 of 7 are confidently wrong by the doc's own rule and none is in the declared band. The row still shows the v1 reading "Mean 0.44, In band" against a shipped mean of 0.307.
21. EVALS.md line 40 shows recall 0.77 against a 0.85 target. Shipped gold recall is 0.654, and the bands-landed paragraph never mentions it.
22. "12 of 12" counts pinned cards. EVALS.md's Tier 1 table lists 7 named checks.
23. "Flat 0.75" (README line 53) is not computed. The six Spanish probe scores are 0.814, 0.777, 0.731, 0.734, 0.798 and 0.768, mean 0.770.
24. "three eval referees on real calls" (GitHub description). The three test sets are gold, regressions and real calls. One of the three is real calls.
25. iterations.md line 32 calls the small model's tokenizer an "own WordPiece tokenizer". `train_scratch.py` line 14 says "Byte-level BPE, not WordPiece" and names the 1532-piece WordPiece attempt as the v1 failure it replaced. The committed `models/eot-scratch-pre-onnx-int8/tokenizer.json` is byte-level BPE with 16,000 pieces, which settles it.
26. README line 115's "two clean runs ... picked 0.71 and 0.63" is one run and two artifacts. `models/eot-distilbert-fresh-onnx/threshold.json` records 0.71 with 41 admissible values and `models/eot-distilbert-fresh-onnx-int8/threshold.json` records 0.63 with 32, both from the same retrain. The sentence reads as run-to-run variance and is fp32 against int8, which is the repo's own headline finding stated as its opposite.

## The submitted PDF against the repo

The PDF is the render of `docs/approach.md` at commit ae1d2d0, and that file is unchanged at HEAD. Comparing every numeric token, the two are identical apart from the two `width="100%"` figure attributes that do not survive rendering. Items 5, 6, 8, 9, 18 and 19 are therefore true of the PDF verbatim, and item 9 is the one a reviewer could have checked against `iterations.md` in the same repository.

## Reproduced live

Gold PR-AUC 0.9487856622228145 on n 53, gold false-speak 0.0 and recall 0.6538, per-class I 0.200 K 0.500 J 0.857, ECE 0.15956, the seven boundary cards individually and their 0.3068 mean, real calls 0.9129 with 0.2340 false-speak and 0.9592 recall on n 96, regressions 1.0 on n 6, all 12 pinned cards passing one row at a time, `admissible_count` 56, the quantization trio at 0.2629 fp32 single-row, 0.381 int8 batched and 0.4117 int8 single-row, the judge replay at 53/53 for all three vendors with 83/90 pair agreement and 31% saved, parameter counts by ONNX initializer sum, tokenizer vocabularies of 1,723 and 16,000, and `make serve` answering `/predict` with 0.4117 wait.

Not reproducible from a clean clone: every real-call number, because `data/ood_*.jsonl` is gitignored, and every report file for the same reason. A reviewer cloning the repo can regenerate the gold, regression, pinned-card and judge numbers and none of the real-call ones. Did not retrain, since `make train` builds a different model. CI covers figure constants, module parsing and gold-set integrity. It runs no eval, no threshold pick and no pinned-card check.

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
Appears at README line 2 alt, line 14, `hero.svg`, the GitHub description, README lines 163 and 164, EVALS.md line 57, iterations.md line 23, approach.md lines 38 and 52.

### Zero false interruptions

```
Claim     zero false interruptions, the second half of the headline
Unit      of the 27 gold cards labeled wait, none scores at or above 0.42, a rate of 0 over 27
Match     speak when p is at or above 0.42, so the boundary value speaks, at serve.py line 58 and pick_threshold.py line 63
Set       the same frozen cards, and 4 of those 27 are pinned rows the threshold was chosen to keep correct
Command   make eval, false_speak_rate at the 0.42 row of hard.threshold_sweep in eval_report_frozen_gold.json
Sibling   the same file at the same 0.42 interrupts 11 of 47 real turns, a rate of 0.234
Bound     zero seen in 27 puts the exact 95% upper bound at 0.105, so this is under roughly one in ten, never never
Knob      the threshold, since below 0.42 the pinned continuation card at 0.412 flips
```
Appears at the GitHub description, README line 2 alt, README line 14, `hero.svg`, README line 33, the False-speak column of README line 164 and iterations.md line 15, approach.md line 38.

### Gold recall 0.654 at the operating point

```
Claim     0.654, how much finished speech the model actually answers
Unit      of the 26 gold cards labeled speak, 17 clear 0.42, so 9 finished turns are left hanging
Match     the same served int8 file, one row per call, at or above 0.42 counts as speak
Set       the same frozen cards, the 26 speak ones, 7 unsure excluded, precision 1.0 alongside
Command   make eval, recall at the 0.42 row of hard.threshold_sweep, sklearn recall_score at evaluate.py line 91
Sibling   on held-out real calls the same file recalls 0.959, so the two recalls point opposite ways
Bound     EVALS.md line 40 targets 0.85, so this is far out of band and the summary paragraph never says so
Knob      the agent's last line, since recall is 1.00 with it and 0.47 without
```
Appears at the Recall column of iterations.md lines 13 to 15, and as "recall 0.58" and "recall to 0.81" in README lines 157 and 158.

### 0.913 on held-out real calls

```
Claim     0.913, the score on speech nobody wrote for this project
Unit      average precision over 96 turns of data/ood_test.jsonl, 49 speak and 47 wait
Match     the same served int8 file, one row per call, same input format
Set       400 turns cut from the author's own deployed agent, labels assigned by rule with no human pass at ood_from_elevenlabs.py lines 121 to 142, split by call into 304 and 96
Command   evaluate.py --data data/ood_test.jsonl, jsonl.pr_auc in eval_report_frozen_oodtest.json, and both data and report are gitignored
Sibling   0.949 on the gold set, where the small model reading 0.597 here reads 0.994
Bound     96 turns from 19 calls, one agent, one vendor, one language, and rows from a call are not independent
Knob      real-call rows in training, added at four-fold weight and grouped by call
```
Appears at README line 2 alt, line 14, `hero.svg`, iterations.md lines 15 and 23, EVALS.md line 51, approach.md lines 36, 48 and 52, and as "0.91" in `pretrain-curve.svg`.

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
Appears at approach.md line 52, iterations.md lines 14 and 15, EVALS.md line 51.

### 58 ms p95

```
Claim     58 ms p95, the speed number against the brief's 100 ms budget
Unit      95th percentile of end-to-end wall time per request at concurrency 8 over 1200 requests, not model-only time
Match     the served int8 file behind FastAPI and uvicorn, one worker, ONNX Runtime on CPU, one row per request
Set       bench_report_distilen.json, taken while a training run held the same box, against bench_report.json at 32.8 ms quiet
Command   make bench, which runs bench.py --n 1500 --concurrency 1,8,32, and the report is gitignored
Sibling   model-only p95 is 48.2 ms loaded and 31.0 ms quiet, and at concurrency 32 the loaded wall p95 is 421 ms
Bound     one laptop, no GPU, two runs disagreeing by 25 ms, and three places in the repo demand an idle box
Knob      what else the machine is doing, since nothing about the model changed
```
Appears at `hero.svg` twice, README line 2 alt, README line 14, the GitHub description, and as 57.9 ms at README line 205, EVALS.md line 57 and approach.md's serving table.

### 12 of 12 pinned cards

```
Claim     12 of 12 green on the served artifact
Unit      12 constraint rows with required decisions, all correct at 0.42, counting cards not the 7 named checks
Match     each row scored alone, admissible when (prob >= t) equals (required == "speak") at pick_threshold.py line 63
Set       derived by make_tier1_probes.py from 4 readout cards, gold H5, dev dH4 and 6 regression rows, rebuilt by rule after the original was lost
Command   make tier1 then make threshold, re-run live here at 12 of 12
Sibling   the same 12 read 11 of 12 at v8 and red at v7 on identical weights, so only the measurement changed
Bound     12 hand-picked cards, 6 of them already in the training data, so this tests memory rather than generalization
Knob      the batch shape, since batched these score dH4 at 0.381 and one at a time 0.412
```
Appears at the README line 9 badge, iterations.md line 15, EVALS.md line 57, README line 267, `hero.svg`, `judges.svg`.

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
Appears at the README line 7 badge, `band-judged.svg`, `referees.svg`, README lines 34 and 196, data/README.md line 11.

### Three vendor judges, 53 of 53 on 90 blind cards

```
Claim     53 of 53, the exam all three machine labelers passed
Unit      each judge labeled 90 cards, and 53 is the scorable gold ones, with all three unsure on exactly the other 7
Match     no threshold, votes are speak, wait or unsure, and majority() at judge_cascade_replay.py line 19 ignores unsure
Set       60 gold and 30 fresh cards shuffled, judged by stock Claude, Gemini and GPT with the policy in the prompt, votes committed
Command   python judge_cascade_replay.py, re-run live at 53/53 for all three and 83/90 pair agreement
Sibling   Gemini is the outlier at 28 of 30 on fresh cards, and both hidden dissents went the pair's way
Bound     one vote per judge per card, no retry variance, which README line 327 lists as not measured
Knob      the prompt, whose quoted boundary examples make 53 of 53 easier than it sounds
```
Appears at the README line 10 badge, README line 34, `judges.svg`, docs/judge-cascade-replay.md.

### 7.4M and 3.7M from scratch

```
Claim     7.4M and 3.7M, the sizes of the models built from nothing
Unit      parameter count, measured as 3.70M for scratch, 3.99M for scratch-real, 7.36M for scratch-pre, 66.96M for DistilBERT, 135.33M multilingual
Match     summed ONNX initializer elements on the committed and local exports, so 7.36M is the only one that rounds to 7.4M
Set       trained by train_scratch.py on a byte-level BPE tokenizer built in repo, pretrained by pretrain_scratch.py
Command   python -c "import onnx;from onnx import numpy_helper as n;m=onnx.load(P);print(sum(n.to_array(t).size for t in m.graph.initializer))"
Sibling   7.36M reads 0.973 gold and 0.825 real, 3.99M reads 0.994 and 0.597, and 3.70M reads 0.502 and 0.477
Bound     no committed report prints a count, so every figure label rests on memory and three are wrong once measured
Knob      the pretrain step, the only difference between the small models, worth 23 points of real-call score
```
Appears at README line 14, `band-models.svg`, `pretrain-curve.svg` three times, approach.md lines 29, 53, 54 and 55, iterations.md lines 24 to 27.

### The pretraining curve, 0.48 to 0.60 to 0.825 to 0.913

```
Claim     0.48, 0.60, 0.825 and 0.913, what pretraining is worth
Unit      average precision on the same 96 held-out real turns, four models, everything else held fixed
Match     four served int8 files scored one row at a time, at 3.70M, 3.99M, 7.36M and 66.96M, with only the last two in git
Set       data/ood_test.jsonl, gitignored, 96 turns over 19 calls with rule-assigned labels, so no reader can regenerate any of the four
Command   evaluate.py per model dir into eval_report_scratch_oodtest.json at 0.4773, scratchreal 0.5971, scratchpre 0.8253, distilen 0.9129
Sibling   on gold the same four read 0.502, 0.994, 0.973 and 0.949, the opposite ordering
Bound     four points, one seed each, no error bars, and the 0.48 model also has a 1,723-piece vocabulary against 16,000
Knob      language exposure, and the figure rounds 0.825 to 0.83 and 0.913 to 0.91
```
Appears at README line 46 alt, `pretrain-curve.svg`, approach.md lines 33 and 36, iterations.md line 36.

### Spanish, 0.960 against 0.958 and flat 0.75

```
Claim     0.960 against 0.958, and a flat 0.75 on the Spanish probes
Unit      0.960 is gold average precision for the first multilingual model, 0.958 the v5 English reading, and 0.75 is six probe scores between 0.731 and 0.814
Match     0.960 from models/eot-mdistilbert-onnx-int8 at its own 0.33, and the probes from the shipped English int8 file at 0.42
Set       the 53 gold cards for 0.960, 187 rows of data/eval_es.jsonl for the Spanish 1.000, six hand-written probes for the 0.75
Command   evaluate.py per model, where eval_report_mdistil.json reads 0.959987 and mdistilreal2_es reads 1.0
Sibling   that model's gold false-speak at its own threshold is 0.889, and neither model in the comparison ships
Bound     the Spanish 1.000 is synthetic Spanish under the policy the model trained on, so it measures template fit
Knob      the base model, since English DistilBERT is uncased English WordPiece
```
Appears at approach.md lines 38 and 53 to 55, README line 53, iterations.md line 24.

### 36 probes, 31 of 35, mean 16.6 ms

```
Claim     31 of 35 against 34 of 35, on a page that shows 36
Unit      36 rows shown and 35 graded, the 36th unsure and excluded at probe_compare.py line 103, with 16.6 ms the mean of 36 single-row timings
Match     both models scored one row at a time on their own int8 file at their own threshold, a cell wrong when it disagrees with the policy
Set       36 probes hand-written in probe_compare.py lines 32 to 69, the author's own, not held out
Command   python probe_compare.py, which writes docs/probe-comparison.html and prints the counts
Sibling   the two tie at 28 each on English and share one miss, an unpunctuated yes-no question
Bound     35 self-written probes are a demonstration, no interval worth quoting and no independent labeler
Knob      the probe list, since one row moves the fraction three points with no model change
```
Appears at README lines 40 and 51, docs/probe-comparison.html header and lead.

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
Appears at `hero.svg`, README lines 33 and 272, iterations.md lines 13 to 15, EVALS.md lines 57 and 61, data/gold_set.json.

### The judgment classes, 0.20 hedges and 0.50 holds

```
Claim     0.20 on hedges and 0.50 on holds, the two classes the README calls weak
Unit      per-class accuracy at 0.42, where I is 1 of 5, K 4 of 8, J 6 of 7 and H 7 of 7
Match     the same served int8 file, one row per call, per_class_accuracy at evaluate.py line 100
Set       the frozen gold cards by assigned class, where H, I, J and K hold 8 each but 5 unsure ones drop out
Command   make eval, per_class_accuracy_at_threshold and slices in eval_report_frozen_gold.json, re-run live and matching
Sibling   the same hedge shape passes on the probe page at 0.981, so page and gold disagree about the weakest class
Bound     5 cards for the class the weakness paragraph leads with, where one card is 20 points
Knob      the agent's last line, since recall goes 1.00 to 0.47 without it
```
Appears at README lines 32, 91 and 297, EVALS.md lines 42 and 57, the Hedge and K columns of iterations.md lines 7 to 15.

### The quantization trio, 0.26 and 0.381 and 0.412

```
Claim     0.26, 0.381 and 0.412, one card under three execution paths
Unit      P(speak) for dev row dH4, "Actually, hold that thought." after "Agent: Anything else before I let you go?"
Match     0.2629 is fp32 single-row, 0.381 is int8 with all 12 pinned rows batched, 0.4117 is int8 single-row as serve.py does
Set       one card, not a set, and it is the pinned row that fixes the operating point
Command   reproduced live against both export dirs and through /predict, which returned 0.4117 and wait
Sibling   the continuation card beside it reads 0.035 single-row and 0.036 batched, so the batch effect shows up only near the threshold
Bound     one card proves the failure mode exists, not how often, and nothing measures batch sensitivity across the set
Knob      batch composition under dynamic int8 quantization, so score the way you serve
```
Appears at README lines 35, 243 and 266, iterations.md lines 13 and 14.
