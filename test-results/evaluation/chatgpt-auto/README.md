# ChatGPT Auto Mode — Benchmark Evaluation

**Model:** ChatGPT Auto Mode (GPT; has Code Interpreter but did not use it)
**Date:** 2026-02-08
**Evaluator:** Claude Sonnet 4.5 (LLM-based value extraction) + deterministic tolerance comparison
**Benchmark:** power-agent-benchmark v1.0.0 (106 tasks, R-validated ground truths)

> **Note:** An earlier evaluation using regex-based extraction reported 14.6% (15/103). That extraction was
> deeply flawed (e.g., extracting "15" from a response that clearly stated "63 per group"). This evaluation
> uses Claude Sonnet 4.5 as an LLM judge for accurate value extraction from ChatGPT's natural language responses.

---

## Overall Results

| Tier | Description | Pass | Total | Rate |
|------|-------------|------|-------|------|
| Tier 1 | Basic Comparisons | 17 | 30 | **56.7%** |
| Tier 2 | Regression & Models | 23 | 35 | **65.7%** |
| Tier 3 | Advanced Designs | 14 | 20 | **70.0%** |
| Tier 4 | Prediction Models | 6 | 21 | **28.6%** |
| **Overall** | | **60** | **106** | **56.6%** |

---

## Failure Root Cause Analysis (46 failures)

| Root Cause | Count | Tasks | Description |
|------------|-------|-------|-------------|
| Z-approximation instead of exact t-distribution | 12 | t1-paired-002, t1-paired-003, t1-paired-004, t1-ttest-001, t1-ttest-002, t1-ttest-003, t1-ttest-004, t1-ttest-005, t1-ttest-006, t3-cross-002, t3-cross-003, t3-cross-004 | Uses z=1.96 instead of t-distribution, underestimates by 1-3 per group |
| No access to pmsampsize R package (Riley criteria) | 10 | t4-binary-001, t4-binary-003, t4-binary-004, t4-binary-005, t4-cont-003, t4-cont-004, t4-surv-001, t4-surv-002, t4-surv-003, t4-surv-005 | Riley multi-criteria require pmsampsize R package; used single-criterion approx |
| Wrong formula or major computation error | 7 | t1-anova-003, t1-anova-004, t1-chi-004, t2-linreg-006, t2-mixed-004, t2-mixed-006, t3-cluster-004 | Applied incorrect statistical formula or made major computation error |
| No access to pmvalsampsize R package | 5 | t4-valid-001, t4-valid-003, t4-valid-004, t4-valid-005, t4-valid-006 | Validation criteria require pmvalsampsize; used hand-derived approximations |
| Close answer but outside strict tolerance | 3 | t1-prop-004, t2-linreg-001, t2-linreg-003 | Answer is close but exceeds strict deterministic tolerance |
| Wrong statistical method for logistic regression | 3 | t2-logreg-002, t2-logreg-005, t2-logreg-006 | Used wrong sample size method (e.g., case-control instead of cohort) |
| Survival analysis formula error | 3 | t2-surv-004, t2-surv-005, t2-surv-008 | Incorrect survival analysis computation (dropout, accrual, stratification) |
| Task requires Monte Carlo simulation | 2 | t2-poisson-005, t3-simr-005 | Accurate answer requires Monte Carlo simulation, not analytical formula |
| Specialized design knowledge gap | 1 | t3-cluster-005 | Needs specialized design knowledge (stepped-wedge, frailty models) |

---

## Key Findings

### 1. Not Using Code Execution is the Core Limitation

ChatGPT Auto Mode has access to Code Interpreter but chose not to invoke it for any of the 106 tasks.
It computes everything analytically from parametric knowledge.
This creates systematic failures for:
- **Specialized R packages** (pmsampsize, pmvalsampsize, simr, swdpwr) — 18 tasks affected
- **Exact distributions** (t-distribution vs z-approximation) — 12 tasks affected
- **Simulation-dependent answers** — 3 tasks affected

### 2. Z-Approximation Is the Most Common Error Pattern

ChatGPT consistently uses z-critical values (z=1.96 for alpha=0.05) instead of t-distribution critical values.
This systematically underestimates sample size by 1 per group (2 total). With the benchmark's strict ±1
tolerance for deterministic tasks, these near-misses are correctly flagged as failures.

### 3. Riley Prediction Model Tasks Are Nearly Impossible Without Code

Tier 4 tasks require the `pmsampsize` or `pmvalsampsize` R packages, which implement Riley et al.'s
multi-criteria framework (shrinkage, optimism, precision). ChatGPT approximates using only the shrinkage
criterion, yielding answers that are sometimes close but usually outside the ±5 tolerance.

### 4. Wrong Methods Are More Dangerous Than Wrong Numbers

The most consequential failures are not small numerical errors but fundamentally wrong approaches:
- **t2-logreg-002:** 215 vs 522 (used case-control formula instead of cohort Demidenko method)
- **t2-mixed-004:** 750 vs 150 patients/cluster (5x error in design effect calculation)
- **t3-cluster-005:** 29 vs 7 per cluster-period (4x error in stepped-wedge formula)

### 5. Hypothetical: Relaxed Tolerance for Z-Approximation

If tolerances were relaxed by +2 to accommodate z-approximation (±3 instead of ±1):
- 12 additional tasks would pass
- Adjusted overall: **72/106 = 67.9%**
- Tier 1 would improve from 56.7% to **93.3%** (28/30)

---

## Comparison with Power Agent

| Metric | Power Agent (Claude Opus 4.5) | ChatGPT Auto Mode |
|--------|-------------------------------|-------------------|
| **Overall** | **99.1%** (105/106) | **56.6%** (60/106) |
| Tier 1 | 100% (30/30) | 56.7% (17/30) |
| Tier 2 | 100% (35/35) | 65.7% (23/35) |
| Tier 3 | 100% (20/20) | 70.0% (14/20) |
| Tier 4 | 95.2% (20/21) | 28.6% (6/21) |
| Approach | R code execution via Docker | Analytical formulas, did not invoke code |

---

## Detailed Per-Tier Reports

- [Tier 1 — Basic Comparisons](tier1.md) (30 tasks)
- [Tier 2 — Regression & Models](tier2.md) (35 tasks)
- [Tier 3 — Advanced Designs](tier3.md) (20 tasks)
- [Tier 4 — Prediction Models](tier4.md) (21 tasks)

---

## Methodology

### Value Extraction
Each ChatGPT raw text response was processed by **Claude Sonnet 4.5** with a structured extraction prompt.
The LLM was given the original question, ground truth field names (as hints), and the full response text.
It returned a JSON object mapping field names to extracted numerical values.

### Comparison
Extracted values were compared against ground truth using per-task tolerances:
- Deterministic tasks (pwr, pmsampsize): ±1 to ±5
- Simulation-based tasks (simr, Monte Carlo): ±8 to ±15 or ±0.08 to ±0.12 for power
- Survival analysis: ±5 to ±10

### Pass/Fail Determination
A task PASSES if ALL primary numerical fields (sample size, events, power) are within tolerance.
Metadata fields (alpha, effect size, predictors) are checked but do not determine pass/fail.

---

*Evaluation by Claude Opus 4.6 with Claude Sonnet 4.5 value extraction*
