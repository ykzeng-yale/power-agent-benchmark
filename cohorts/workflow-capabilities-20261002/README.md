# Source, plotting and verification capability cohort (new; no model runs yet)

This version adds a separate, prospective assessment after the six earlier cohorts. No previous question, oracle, tolerance, scorer, frozen protocol, attempt or result is modified. The tasks and public methods are known to developers; this is a small exploratory capability comparison, not an unseen or contamination-free holdout.

## What the prior comparison measured

The earlier18model-call/8R/300s comparison matched global operation/time ceilings. It did not give equal coding opportunity: multi-agent planning, review, repair and rereview consumed that ceiling, and required model verification was asymmetric with legacy single-agent defaults. It also did not match tokens or actual dollars. In the completed2.1.2 cohort, multi had9/20 budget-exhausted attempts versus1/20single; six multi candidates agreed numerically but remained incomplete. These observations motivate a new comparison; they do not establish that additional review will improve outcomes.

The new2×2 comparison fixes both contexts to `verificationPolicy:required` and uses the same scientific instructions, sources, R environment, search/read limits, artifact capabilities and phase ceilings. Single verification uses the author's conversation. Multi verification begins with a candidate-withheld numerical precheck, then reveals the candidate in a fresh review context. This topology and precheck are part of the tested workflow, not evidence that same-model errors are statistically independent.

| Profile | Global calls / total R / deadline | Planner calls | Solver calls / R | Verification calls / R per invocation | Repair calls / R |
|---|---|---|---|---|---|
| shared |18 /8 /300s |3 |6 /3 |4 /2 |3 /1 |
| expanded |26 /12 /540s |3 |9 /5 |5 /3 |4 /1 |

Both profiles and repair reservation apply identically to both modes. Verification caps apply to initial review and each rereview; repair covers coder repair. At most one repair is allowed. All R calls, including deterministic reference gates, count toward the global ceiling. Limits are ceilings clipped by remaining global capacity and repair/reference reservations, not promised operations. The configured planner/solver/review/repair/rereview maxima can total20calls/10R in shared and26calls/14R in expanded when including two reference checks; the hard18/8 and26/12global ceilings still prevail. Therefore every phase maximum cannot be used together. Report the effective phase limits, reservation decisions and actual usage from each record rather than claim a guaranteed full review/repair allowance. Expanded capacity is additional solver/check allowance to **both** modes. It measures workflow success versus resource capacity and reported cost/latency; there is no equal-dollar or architecture-only causal claim.

Search is bounded to6requests and document reading to4requests per attempt; globally80,000received source characters, with actual provider extraction/truncation scope and credit/cache receipts retained. Search and read access are identical. This evaluates actual named-primary-source retrieval and interpretation, not open-ended literature discovery. Providing the official URL is intentional and does not provide a reference answer.

## Tasks and sources

Eight tasks are evaluated under four conditions with two repeated calls per condition:64fixed planned attempts, using frozen random order and three workers. Six numerical tasks have four source-family labels; the two clarification cases have separate labels (six labels overall). The ANOVA and two Cox questions reproduce authentic official-manual examples plus new grids. The NIH question reproduces an authentic official-method worked example plus a new grid. The t and paired-t parameters, grids and missing-input cases are constructed; none is falsely described as a textbook answer. Related questions share their source-family label.

| Task | Source / scope | Required numerical/data work |
|---|---|---|
| pooled t |[R stats](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/power.t.test.html); constructed |Exact two-tail noncentral-t integer inversion;32-row power curve |
| paired t |same R family; constructed |Difference SD from correlation;4separate integer inversions |
| ANOVA |[R stats example](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/power.anova.test.html) |Documented between.var convention;21-row omnibus F curve |
| binary Cox |[Stata13 manual](https://www.stata.com/manuals13/ststpowercox.pdf) |Events versus equal-allocation recruitment;12HR/event-probability scenarios |
| continuous Cox |same Stata family |Coefficient, covariate SD, R² and censoring;12scenarios; continuous-first recruitment rounding |
| open-cohort SW |[NIH worked example](https://researchmethodsresources.nih.gov/sites/g/files/mnhszr246/files/PDFs/SWGRT-OpenCohortDiscreteTimeWorkedExample-FINAL-508.pdf) |Lag covariance, GLS variance,df and approximate MDE;5cluster-count scenarios |
| missing cluster |constructed |Ask for ICC and mean cluster size before definitive sizing |
| missing survival |constructed |Ask for event probability/follow-up; conditional event target allowed but no invented participant count |

The NIH published rounded answer is a t-quantile MDE approximation, not an exact noncentral-t80%power certificate. Cox calculations reproduce the manual's asymptotic formula. The suite is deterministic analytic power/design work; it does not test arbitrary Monte Carlo mixed models, fit-failure calibration or every design family. Both source and library dependence are reported. Developer-known public examples and constructed variants are not independent clinical validations.

`validation/independent-verification.json` records409passed cross-language checks:26scalar quantities, every sensitivity-grid cell, published rounded anchors and minimum-power crossings. Maximum R-versus-Python absolute difference is5.581182183078681e-10. Local reference runtime is R4.4.2/jsonlite2.0.0 versus Python3.9.6/SciPy1.13.1/NumPy1.26.4; the study's Linux runtime is frozen separately. Python noncentral distributions differ from R implementations. NIH scalar projected information is crosschecked against a full GLS normal-equation inverse. Cox shares the same documented scientific formula, so cross-language agreement is computation evidence, not independent proof of its assumptions.

## Scoring and artifact scope

`runner/score.py` is judge-free. All requested scalar quantities must have finite values, correct units and the frozen tolerances; integers are exact. Scalar power/MDE tolerance is1e-6; treatment variance1e-8; other continuous quantities use max(1e-6,abs(value)×1e-6). The CSV schema and every supplied grid row are checked; integers are exact and duplicate/missing/extra rows fail. Column-specific tolerances are stored with the oracle before outcomes.

The automatic primary outcome requires completed status, numerical/design agreement, current-round successful R and exact result linkage, required successful verification, the same document actually searched before it is read, a hashed bounded document receipt and linked citation (an identical-content search/read dedup retains its original excerpt scope and is accepted only through the matching actual `tavily_extract` read receipt; annotated, never promoted to a complete-PDF claim), and actual delivered CSV plus parseable PNG/PDF with verified bytes/size/SHA. Every answer evidence ID must still identify a successful current-round coder execution; only that set can ground answer numbers or artifacts. Reviewer `checked_evidence_ids` must be unique actual current-round coder IDs and cover every answer evidence ID; additional current-round successful or failed coder attempts may be inspected. Code inspection does not make a failed attempt a valid numerical or artifact producer. Reviewer `independent_check_evidence_ids` still require successful current-round numerical reviewer executions. It rejects stale, missing, wrong-role or duplicate inspection references, incomplete current review coverage, changed runtime dependencies, incorrect budget contracts and undispatched/transport failures. Missing-input tasks are scored for appropriate clarification separately from calculation accuracy. These tasks normally exit in the identical planner stage before reviewer topology diverges; their mode differences chiefly reflect stochastic planning/provider variation and cannot establish an effect of multi-agent precheck.

Hashing verifies exact captured bytes. Numeric CSV agreement verifies the companion dataset. PNG parsing validates CRC/zlib/dimensions; PDF parsing uses `pdfinfo`. Those checks do **not** establish that the visible chart plots the supplied data or that a cited source supports every claim. The separate, prospectively written [visual rubric](audited/visual-rubric.md) assesses axes, units, grid/curve coverage, plotted positions and scientific readability while mode/profile/status are withheld. Automatic primary outcomes never silently incorporate an unvalidated visual/model judge. Source acquisition is similarly receipt/citation linkage, not a claim that provider extraction inspected every PDF page or formula.

All64planned jobs remain in operational outcome denominators. Also report the48planned calculation attempts and16planned clarification attempts, completion, numeric versus completed-numeric results, source/artifact coverage, tool/phase usage, provider credits, token counts, observed latency and undispatched/capture failures. Paired source-family bootstrap intervals are descriptive selected-label variability, with only six labels, and do not estimate general capability. Show per-task outcomes and both repeats; never select the better response or tune tolerances after readout.

## Freeze and run

Do not freeze until the backend's seven runtime files, interfaces, source policy, R environment and immutable image are stable. `runner/freeze.py` requires an immutable image digest, successful oracle validation and exactly two repeats. It writes a question-only payload and64-job protocol containing SHA manifests for the seven runtime dependencies (including `scientific-sources.js`), evaluator, tasks, oracles, reference programs and source-provenance documents. Use a fresh output directory; existing protocols are never overwritten.

```sh
python3 cohorts/workflow-capabilities-20261002/runner/freeze.py \
  --runtime-dir '/ABSOLUTE/backend' \
  --runtime-image 'gcr.io/PROJECT/IMAGE@sha256:EXACT_DIGEST' \
  --out '/ABSOLUTE/prospective-wc64' --forecast-limit-usd 35
```

For a Cloud Run Job, build `FROM` that exact backend digest and `COPY` only `dispatch.py`, `public-questions.json` and `protocol.json`. **Do not include** tasks with evaluator annotations, oracles, reference scripts, scorer, private scans or old answer stores. The R workspace sees question-only stdin and immutable primary-tool receipts, with no oracle mounts. The inherited backend must be checked separately for old benchmark/reference stores; a small COPY allowlist does not establish that the parent image is clean.

```sh
python3 /study-runner/dispatch.py \
  --questions /study-runner/public-questions.json \
  --protocol /study-runner/protocol.json \
  --cli /app/scientific-harness-cli.js --out /study \
  --gcs-prefix 'gs://AUTHORIZED_BUCKET/jsm2026/workflow-capabilities/NEW_COHORT'
```

The runner writes and uploads exact stdout/stderr bytes before parsing. It requires the same seven-file hash both before and after each attempt, captures source/artifact bytes inside the original response, and never reruns a selected failed task. Use one Cloud Run task, no automatic retries, three internal workers. Preserve an interrupted cohort and all unknown/undispatched jobs; never restart into its directory.

The prospective dispatch forecast limit is US$35 for model-token estimates, with initialUS$0.20/job and subsequently max(US$0.20,mean completed cost), plus completed and outstanding work. This investigator-selected pre-study forecast threshold was raised before any main-cohort dispatch after a capability-development multi-agent pilot cost approximately US$0.33. It is not a user-imposed hard financial budget. This is a predictive dispatch stop, not a guaranteed final billing cap. In-flight jobs finish; undispatched jobs remain explicit planned stubs. Model cache tokens, input/output tokens and source-provider request credits are recorded separately. Search/read credit prices are not silently invented or included in a model-only dollar claim. All remaining jobs are marked `budget_not_started` rather than fabricated model statuses if dispatch stops.

Download all original objects before offline scoring. Verify raw stdout hashes and exact raw-provider record equality, source/protocol/request identities and the full planned set. Then:

```sh
python3 cohorts/workflow-capabilities-20261002/runner/analyze.py \
  --run '/ABSOLUTE/retrieved-wc64'
```

Original long provider-extracted document text remains in restricted raw storage. For publication, make separately hashed redacted derivatives with source receipt metadata/digests and required benchmark outputs; do not publish complete copyrighted manual content or claim a redacted derivative is identical to original raw stdout. The cohort source-provenance file identifies this distinction. Credentials never belong in payloads, protocols, logs or output.

## Local checks without model calls

```sh
.venv/bin/python cohorts/workflow-capabilities-20261002/validation/independent.py
Rscript cohorts/workflow-capabilities-20261002/validation/reference.R cohorts/workflow-capabilities-20261002
.venv/bin/python cohorts/workflow-capabilities-20261002/validation/verify.py
.venv/bin/python cohorts/workflow-capabilities-20261002/tests/test_capabilities.py
```

The 25 meaningful fixtures include actual local R-generated CSV/PNG and independently executed R verification, bad counts/units, stale/extra evidence, source hash/search order, forged artifact SHA, wrong/missing sensitivity rows, corrupt images, missing-input behavior, outer runtime drift (including null responses), the seventh dependency, raw-byte retention on invalid/non-object JSON, and a whole64job null-response capture→offline-scoring accounting fixture. Source fixtures are explicitly injected tests, not empirical provider retrievals or model responses.

To create public derivatives without source-text transcripts, use `runner/redact_public.py --scored /ABS/scored-results.json --out /ABS/NEW-public-results`. It preserves original-file/protocol links and produces separately hashed derivative JSON plus validated numeric CSVs. PNG/PDF export additionally requires `--figures-reviewed` after the blinded visual review; image hashes alone do not certify absence of document text in pixels. Originals remain unchanged and restricted.
