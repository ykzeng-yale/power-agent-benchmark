# Audited scientific evaluation protocol (v2.0.0)

## Scientific target and coverage

The primary outcome is correct numerical execution of one requested quantity under a fully specified statistical method and design. Method identifiers and output units are included in the request. This does not test autonomous selection of a method from an underspecified clinical narrative.

The deterministic core has 20 tasks from 15 declared example-family labels: 15 short Verma worked-example paraphrases (10 illustration families), 3 official pmsampsize illustrations and 2 new parameter variants. There are 6/6/4/4 tasks across tiers. The 9 development and 11 evaluation tasks are grouped by declared label; paired questions from the same illustration stay together. Direct constructed variants share source/method anchors, and two cross the nominal split. A post-hoc sensitivity merges direct variants into anchors (13 core labels; 2 extension anchors), preserving frozen labels and all scores. Both splits were exposed to developers during curation, and their source examples are public. A split label is not evidence of an unseen holdout. Report the current comparison as exploratory, without claims about the absence of training-data contamination.

The supplied textbook contains examples in more topic areas than the present core. `validation/textbook-inventory.json` inventories all 81 previously extracted questions; only the explicitly curated core received the two-implementation audit described here. Previous extraction is not automatically certification. Prediction development examples come from Riley's methods and official package documentation, not the Verma textbook. This distinction is recorded per task.

## Reference answers and rounding

Each task has a source locator, an explicit numerical specification and a scorer-only oracle. R and SciPy implementations use independently written expressions for the specified noncentral t/F distributions or Riley criteria. Sample-size inversion searches the feasible integer allocation grid, rather than accepting floor/round in place of ceiling. Source answers are stored separately and compared to the independently recomputed value. Display-rounded powers are not mistaken for exact mathematical values. The primary tolerance is **0 participants** for integer sample sizes and **0.0001 absolute probability** for deterministic power. No relative tolerance, threshold calibration on agent answers or post-evaluation relaxation is allowed.

Riley criteria use explicit default precision targets: 95% confidence, R-squared difference 0.05, outcome-risk absolute margin 0.05, residual-SD MMOE 1.1 and mean-outcome MMOE 1.1 for continuous outcomes. The continuous residual-SD criterion is independently solved from the chi-square MMOE equation in Riley et al. (2019), rather than merely asserting `234 + p`. The survival risk-only precision minimum is independently computed and checked at the returned final sample size. pmsampsize 1.1.3 itself labels its survival third criterion as the maximum of the first two and reports an achieved risk interval; do not claim its placeholder is an independently inverted precision formula. For the curated survival example, the independently computed precision minimum is 141, smaller than the binding shrinkage minimum 5143, so the final answer agrees. Criteria are retained in `audited/oracles.json` for inspection. The continuous fourth row starts at the maximum of the first three constraints; its 918 entry is a sequential check, not a standalone mean-precision minimum. The mean-only constraint minimum is independently 38 for that example; shrinkage determines the final 918. See `validation/riley-component-audit.json`.

Agreement of R and SciPy implementations checks programming and numerical calculations under the chosen method. It does not prove that the chosen approximations achieve exact finite-sample operating characteristics or that all possible study designs are supported. The package implementation remains a third crosscheck for the Riley examples, with its version recorded.

## Primary structural and numerical gates

The primary pass indicator is the conjunction of:

1. `scientificStatus == completed` and `success == true`.
2. Exactly one finite numeric result for the requested primary metric; an integer positive sample size when required.
3. Matching reported unit. There is no inference of whether an unlabelled number means per arm or total.
4. Matching design method, alpha, sidedness and allocation ratio when applicable. Predeclared typographical aliases only are normalized. For omnibus F tests, `omnibus` and `not-applicable` are equivalent sidedness labels.
5. Agreement with the frozen numerical oracle within its task tolerance.
6. A successful coder R execution with a matching SHA-256 code hash, and the exact final metric/value/unit linked to that execution's structured `POWER_AGENT_RESULT`.

Auxiliary metrics are retained but do not add subjective credit. Report numeric agreement and structural-gate failures separately as diagnostic outcomes, while keeping the strict conjunction as the primary outcome. A model review is part of the multi-agent system; it is not the evaluation oracle.

## Frozen paired experiment and denominator

The runner writes a protocol before model calls, including task/condition/repeat order, fixed budgets, model/harness hashes and analysis definition. It uses 3 repeated fresh calls per task per condition, without carrying conversation state across attempts. Single and multi share questions, model, R environment, deadlines and call/execution/repair budgets. Multi adds an independently prompted planner/coder/reviewer sequence and an independently executed reviewer check. Same-model reviewers can share systematic errors; execution/review does not guarantee correctness.

Conditions and repeats are shuffled with seed 20261001. **Every planned attempt is in the denominator**, including provider errors, exhausted budgets, clarification/review failure, malformed outputs and missing results. No response is replaced because it failed. Subsequent infrastructure fixes require a new frozen version/cohort, with the original failures preserved. Record source/harness changes; do not pool changed versions under one label.

The full-suite protocol plans 20 × 3 × 2 = 120 runs. The separate 8-task pilot option is for infrastructure checks and must not be confused with a full suite. The output contains per-task repeat rates, per-tier counts, token usage and latency. Aggregate errors cannot be excluded as 'intermittent' to improve accuracy.

## Dependence and uncertainty

Attempts from one question are repeated outcomes, and sample-size/power questions from one illustration share a source family. The paired analysis averages the task-level repeat pass-rate difference (multi minus single) and bootstraps source families, keeping both modes, related questions and all repeats together. With only 15 purposively selected declared labels and related method templates, this is descriptive uncertainty for this suite, rather than an estimate of a clinical-design population. Wilson intervals for all attempts are labelled descriptive because independent Bernoulli assumptions do not hold.

Monte Carlo simulation tasks require a separate extension protocol. A power estimate must report seed, trials, rejection count, fitting failures, an all-trials denominator, MCSE and an interval. Do not use a range of guessed sample sizes as a Monte Carlo oracle. Freeze the DGP, fitted test and power-grid decision rule before calls. No stochastic mixed-model accuracy claim follows from the deterministic core.

## Leakage controls and limits

The provider sees only the answer-free question and output conventions. It receives no oracle, source answer, reference program, task ID or source locator. Each CLI request starts in a fresh temporary directory and R workers start in fresh workspaces without model/cloud credentials. No retrieval callback is enabled in the local evaluation provider. Review exported code/trace for file/network reads and copied constants; retain any suspicious attempt as a failure or a separately labelled validity problem.

The local executor is process isolation, not an OS-level sandbox. Filesystem and external network access are not technically prohibited. Thus the run cannot claim full blind isolation. Future confirmatory evaluation should use a restricted container without mounted oracle/benchmark files, a source-access policy, private source-family holdout, recorded retrieval and novel parameter variants generated before prompting changes. Public textbook examples may already be in model training data.

## Audit provenance and literature

The 106-task legacy execution audit is complete and separately labelled. Numeric reproduction alone is not design/source certification. Known defects include undefined tests, missing interaction/equivalence specifications, averaging powers from different tests, and a two-arm survival formula missing its allocation factor. Previous performance logs also contain ground-truth revision and post-failure retesting; historical records must not support a fresh 99.1% claim.

Primary source links: [Verma publisher](https://doi.org/10.1007/978-981-15-5204-5), [pmsampsize manual](https://cran.r-project.org/web/packages/pmsampsize/pmsampsize.pdf), [Riley continuous criteria](https://doi.org/10.1002/sim.7993), [Riley binary/survival criteria](https://doi.org/10.1002/sim.7992), [Riley practical guidance](https://doi.org/10.1136/bmj.m441). For public-source leakage concerns, see [Han et al., Search-Time Data Contamination](https://arxiv.org/abs/2508.13180). The latter informs the protocol; it does not establish contamination in Power Agent.

## Instrumentation corrections and completed cohorts

The original Mac 120 retained 105 provider records and lost 15 before raw persistence; the original Mac extension 24 retained 17 and lost 7. Missing job identities and unknown model status/usage are kept separate from observed records. A raw-first null-safe runner 2.0.1 captured a new entire 24 extension, without selected replacement. The current 2.0.2 runner also persists version-change failures. Both original study runners and all 105 valid historical judgments remain unchanged.

A separately prospective question-only immutable Linux 40 captured all 40 attempts and scored locally with the same numerical/design/unit/evidence gates. It used R 4.4.1 and harness 2.0.1-cloud, distinct from Mac R 4.4.2 and original harness 2.0.0. Strict passes 8/20 single and 5/20 multi do not establish improvement; numeric matches 10/20 each include 3 unfinished multi responses. Full derived artifacts in `results/publication-analysis.json` keep all four cohorts separate and distinguish numerical agreement, completed numerical agreement and strict success.
