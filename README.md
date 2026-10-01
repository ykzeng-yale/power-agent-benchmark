# Power Agent scientific benchmark

Version 2 contains **20 curated deterministic tasks** with explicit assumptions, units and reference computations. It supports judge-free evaluation of the same Haiku harness in single-agent and genuine planner/coder/reviewer modes. The 106 legacy tasks remain available as historical data; they are **not certified ground truth**.

| Tier | Scope | Tasks | Sources |
|---|---|---:|---|
| 1 | Mean comparisons and proportion precision | 6 | Verma worked examples |
| 2 | Fixed general linear models | 6 | Verma worked examples |
| 3 | Repeated Gaussian designs | 4 | 3 Verma worked examples; 1 constructed variant |
| 4 | Prediction model development | 4 | 3 Riley/package illustrations; 1 constructed variant |

Of the 20 tasks, 15 paraphrase textbook worked examples, 3 reproduce official primary-method illustrations, and 2 are new parameter variants. The latter five are not described as textbook tasks. Tier labels organize coverage; their difficulty ordering has not been empirically established. This suite has limited coverage and does not establish reliability for arbitrary clinical designs, survival-power calculations, clustered trials, or simulation-based mixed models.

The evaluator requires a completed structured response, one unambiguous primary metric, the specified unit, matching design fields, correct numeric value, and a successful R execution linked to that result with a matching code hash. Sample sizes must match the smallest admissible integer exactly; power tolerance is absolute `0.0001`. Tolerances were set before model evaluation. No LLM judge, prose extraction, unit inference, round-down credit, or selection of successful retries is used.

## Reproduce reference calculations

Requires R 4.4.2 with `pwr 1.3.0`, `pmsampsize 1.1.3`, and `jsonlite` (versions recorded in the oracle artifact). The independent second implementation requires Python and `scipy 1.13.1`.

```bash
Rscript validation/reference.R .
python3 -m venv .venv
.venv/bin/python -m pip install -r validation/requirements.txt
.venv/bin/python validation/independent.py
python3 -m unittest discover -s tests -v
```

Reference reproduction is separate from an agent run. `audited/tasks.json` contains answer-free questions and provenance. `audited/reference-specifications.json` and `audited/oracles.json` are scorer-only resources. The runner sends the question and output conventions, including the explicitly prescribed method identifier, without reference values, task IDs, source locators or reference code. The evaluation therefore measures numerical execution under a supplied method, rather than autonomous method selection.

## Run a frozen evaluation

Use a command provider implementing the scientific-harness JSON contract, or a scientific-analysis HTTP endpoint. Every condition gets identical questions and fixed shared call/execution/repair/deadline limits. The multi-agent condition necessarily spends some of that budget on planning/review; report its token usage and latency.

```bash
python3 runner/audited_benchmark_v2_0_2.py \
  --cli /absolute/path/scientific-harness-cli.js \
  --split all --repeats 3 --workers 3 \
  --out results/new-frozen-run

python3 runner/audited_benchmark_v2_0_2.py \
  --endpoint https://your-service/api/scientific-analysis \
  --split evaluation --repeats 3 --out results/new-api-run
```

The current 2.0.2 runner writes `protocol.json` **before calls**, hashes questions/oracles/scorer/harness files, randomizes condition order, persists provider responses before scoring and counts every planned attempt. Null/malformed schemas fail without crashing scoring. Version-change failures are also written to disk without calling the provider. It refuses to overwrite a run. The exact original 2.0.0/2.0.1 study runners remain unchanged for audit. Missing or interrupted records count as failures on the planned denominator. Do not resume by replacing failed records with new responses.

The 9 development and 11 evaluation tasks use declared example-family labels; related sample-size and power questions stay together. Direct constructed variants share method templates with anchors, and two cross the nominal split. Both splits were inspected during construction and do not establish a semantic, unseen or contamination-free holdout. Freeze a new private source/method-family-disjoint set before future prompt optimization. The current experiment is exploratory. Declared-family bootstrap intervals keep related questions, repeats and modes together; a post-hoc sensitivity merges variants into anchors. Wilson intervals are only descriptive because attempts are dependent.

## Historical audit

[Per-task legacy audit](validation/legacy-audit.md) covers all 106 records. Thirty-nine supplied references contain no executable calculation; 67 execute. Only 59 reproduce their stored primary numerical value without a flagged known design defect, and this still does not verify their claimed published source or scientific validity. The remaining 47 are quarantined. The old runner sent expected answers to a model judge, used wide tolerances and retried missing analysis until a successful response. The prior 99.1% leaderboard claim is withdrawn as current scientific evidence. Its date, judge configuration and ground-truth revisions do not support a fresh accuracy claim.

See [protocol and provenance](docs/audited-methodology.md), [oracle files](audited/), and [legacy archive](historical/). Do not publish the full supplied textbook OCR. Questions here are short original paraphrases with verified chapter and illustration identities. Printed-page ranges are provisional; see `validation/source-locator-errata.json`.


## Separately frozen extensions

`cohorts/source-extension/` adds four tasks in three declared labels: Rosner/Freedman survival power and sample size (official-package reproduced textbook parameters), a Field Trials published cluster-rate example, and one explicitly constructed cluster-rate variant. The last two share a source/method anchor. Independent R/SciPy answers agree. Original and corrected whole 24-attempt cohorts are kept separate from one another and from the 120-attempt core.

Reference Monte Carlo calibration uses a constructed Gaussian random-intercept repeated-measurement DGP and a fixed pooled t test on participant means. `validation/monte-carlo-protocol.json` freezes 10000 trials per case/seed, three seeds and both null/alternative cases; outcomes include rejection/nonrejection/failure counts, all-trials power, MCSE and Wilson intervals. All six simulations pass the predeclared numerical calibration against analytic power. This does not establish agent performance on mixed-model simulations.

## Recorded study results and instrumentation audit

The clean, separately planned immutable Linux cohort captured all 40 responses: strict single-agent 8/20, multi-agent 5/20; numerical agreement 10/20 in each condition. Three multi-agent numerical agreements came from unfinished responses. This does not demonstrate a multi-agent accuracy gain. `results/haiku-linux-replication-20261001/scored-results.json` preserves the complete evidence.

The earlier Mac 120 cohort captured 105 responses and lost 15 after an eager null-answer fallback crashed scoring before persistence. The original source-extension 24 cohort captured 17 and lost 7 for the same reason. Planned denominators and exact missing job identities remain in separate derived accounting files; missing model status and usage are unknown. No failed job was selectively retried. A new raw-first runner captured an entirely fresh 24-attempt supplemental cohort (7/12 single strict passes; 1/12 multi). The Mac processes have unrestricted filesystem/network access; powerSurvEpi was installed into a shared library during the original extension. The corrected cohort records unchanged before/after package-version inventories but is not an immutable-container study.

`results/publication-analysis.json` contains conventional observed latency medians, all-planned counts, unknown capture-loss accounting, token-cost estimates and declared-label/merged-variant bootstrap sensitivity. `validation/publication_analysis.py` and `publication_plots.R` reproduce derived tables and scientific PDF figures without changing raw scores. The four cohorts remain separate, developer-exposed exploratory evaluations.

```sh
Rscript validation/monte_carlo.R .
.venv/bin/python validation/monte_carlo.py
```

Never regenerate reference files or edit hashed sources while a frozen model run is active. Reproduce references in a separate checkout, or after the run completes.

## Sources

Verma & Verma (2020), *Determining Sample Size and Power in Research Studies*. [Publisher and DOI](https://doi.org/10.1007/978-981-15-5204-5).

Riley et al. (2019), minimum sample size for prediction models: [continuous outcomes](https://doi.org/10.1002/sim.7993), [binary and time-to-event outcomes](https://doi.org/10.1002/sim.7992). Riley et al. (2020), [BMJ practical guidance](https://doi.org/10.1136/bmj.m441). Numerical illustrations and package semantics: [pmsampsize 1.1.3 manual](https://cran.r-project.org/web/packages/pmsampsize/pmsampsize.pdf).
