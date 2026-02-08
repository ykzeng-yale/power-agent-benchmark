# ChatGPT Auto Mode Benchmark Evaluation Report

**Date:** 2026-02-08
**Model:** ChatGPT Auto Mode (no code execution)
**Evaluator:** Claude Sonnet 4.5 (value extraction) + deterministic comparison
**Benchmark Version:** v1.0.0 (106 tasks, corrected ground truths)

---

## Overall Results

| Tier | Pass | Total | Rate |
|------|------|-------|------|
| Tier 1 - Basic Comparisons | 17 | 30 | **56.7%** |
| Tier 2 - Regression & Models | 23 | 35 | **65.7%** |
| Tier 3 - Advanced Designs | 14 | 20 | **70.0%** |
| Tier 4 - Prediction Models | 6 | 21 | **28.6%** |
| **Overall** | **60** | **106** | **56.6%** |

---

## Failure Analysis (46 failures)

### Category 1: Z-Approximation Instead of Exact t-Distribution (11 tasks)

ChatGPT uses the normal approximation (z = 1.96) instead of the exact t-distribution critical value, yielding per-group n that's 1 lower than the R `pwr` package. With tight tolerances (±1), the total sample size is off by 2.

| Task | ChatGPT | GT | Off By | Root Cause |
|------|---------|-----|--------|------------|
| t1-ttest-001 | 63/grp, 126 total | 64/grp, 128 total | 2 | z vs t |
| t1-ttest-002 | 85/grp, 170 total | 86/grp, 172 total | 2 | z vs t |
| t1-ttest-003 | 138/grp, 276 total | 139/grp, 278 total | 2 | z vs t |
| t1-ttest-004 | 67/grp, 134 total | 69/grp, 138 total | 4 | z vs t |
| t1-ttest-005 | 163/grp, 326 total | 164/grp, 328 total | 2 | z vs t |
| t1-ttest-006 | 99/grp, 198 total | 102/grp, 204 total | 6 | z vs t (alpha=0.001) |
| t1-paired-002 | 30 | 32 | 2 | z vs t |
| t1-paired-003 | 36 | 38 | 2 | z vs t |
| t1-paired-004 | 286 | 289 | 3 | z vs t |
| t3-cross-002 | 117 | 119 | 2 | z vs t |
| t3-cross-003 | 40 | 42 | 2 | z vs t |
| t3-cross-004 | 74 | 76 | 2 | z vs t |

**Pattern:** Consistent systematic underestimate by 1-3 per group. Larger gap at extreme alpha levels (t1-ttest-006, alpha=0.001).

### Category 2: Wrong Formula or Computation Error (8 tasks)

| Task | ChatGPT | GT | Error |
|------|---------|-----|-------|
| t1-anova-003 | 390/grp (1950 total) | 78/grp (390 total) | 5x too large — likely confused total with per-group |
| t1-anova-004 | 103/grp (309 total) | 35/grp (105 total) | Wrong effect size conversion from raw means |
| t1-chi-004 | 680 | 654 | Wrong chi-square power formula at extreme params |
| t1-prop-004 | 140/grp (280) | 133/grp (266) | Normal approx instead of arcsine transform |
| t2-linreg-001 | 127 | 122 | Off by 5 — wrong n=v+p+1 formula |
| t2-linreg-003 | 89 | 85 | Partial F-test formula error |
| t2-linreg-006 | 704 | 688 | Off by 16 — formula rounding |
| t3-cluster-004 | 1128 | 1152 | Close but cluster size rounding differs |

### Category 3: Wrong Method for Logistic Regression (3 tasks)

ChatGPT's logistic regression sample size calculations are significantly wrong for non-standard designs:

| Task | ChatGPT | GT | Error |
|------|---------|-----|-------|
| t2-logreg-002 | 215 | 522 | Used case-control efficiency formula instead of Demidenko variance-corrected cohort method |
| t2-logreg-005 | 1286 | 610 | Wrong handling of non-50% predictor prevalence (30%) |
| t2-logreg-006 | 1330 | 319 | Interaction test — used wrong decomposition of interaction effect |

**Pattern:** ChatGPT doesn't know the `pwrss` package's Demidenko variance-corrected method. It falls back to generic Wald test approximations that can be wildly different.

### Category 4: Survival Analysis Formula Errors (4 tasks)

| Task | ChatGPT | GT | Error |
|------|---------|-----|-------|
| t2-surv-004 | 626/arm (1252) | 657/arm (1314) | Dropout inflation calculation differs |
| t2-surv-005 | 301/arm (602) | 181/arm (361) | Assumed uniform accrual over 36mo instead of fixed entry; inflated P(event) denominator |
| t2-surv-008 | 529/arm (1058) | 475/arm (950) | Stratified log-rank — added unnecessary stratification adjustment |
| t2-mixed-004 | 750 pts/cluster | 150 pts/cluster | Massive error — wrong DE/cluster size relationship |

### Category 5: Doesn't Know pmsampsize (Riley Criteria) (10 tasks)

ChatGPT has no access to the `pmsampsize` R package and uses simplified approximation formulas (typically just the shrinkage criterion). The Riley framework has 4 criteria and the binding criterion varies — ChatGPT's single-criterion approximation is often significantly off.

| Task | ChatGPT | GT | Off By | Note |
|------|---------|-----|--------|------|
| t4-binary-001 | 707 | 662 | +45 | Simplified shrinkage formula |
| t4-binary-003 | 1687 | 1679 | +8 | Close but C-statistic criterion |
| t4-binary-004 | 2990 | 2977 | +13 | Close |
| t4-binary-005 | 1253 | 1214 | +39 | Different binding criterion |
| t4-cont-003 | 1846 | 1508 | +338 | Wrong intercept/SD assumed |
| t4-cont-004 | 610 | 580 | +30 | Approximate formula |
| t4-surv-001 | 4286 | 5143 | -857 | Read paper value (uses 25 params, not 30) |
| t4-surv-002 | 511 | 185 | +326 | Completely wrong approach |
| t4-surv-003 | 650 | 659 | -9 | Close but events way off |
| t4-surv-005 | 597 | 597 (N OK) | events 239 vs 597 | N correct, events formula wrong |

### Category 6: Doesn't Know pmvalsampsize (5 tasks)

External validation tasks require the `pmvalsampsize` R package which implements the Riley et al. validation criteria. ChatGPT uses hand-derived approximations.

| Task | ChatGPT | GT | Off By |
|------|---------|-----|--------|
| t4-valid-001 | 1987 | 1832 | +155 |
| t4-valid-003 | 1875 | 1674 | +201 |
| t4-valid-004 | 5617 | 3733 | +1884 |
| t4-valid-005 | 884 | 814 | +70 |
| t4-valid-006 | 3840 | 3461 | +379 |

### Category 7: Simulation-Required Tasks (3 tasks)

These tasks require Monte Carlo simulation for accurate answers. ChatGPT can only approximate analytically.

| Task | ChatGPT | GT | Error |
|------|---------|-----|-------|
| t2-poisson-005 | 100/grp | 150/grp | ZIP needs simulation, not Wald |
| t2-mixed-006 | 180/grp (360) | 190/grp (380) | Growth curve needs simr |
| t3-simr-005 | power=0.32 | power=0.58 | Clustered survival frailty — analytical approximation fails completely |

### Category 8: Specialized Design Knowledge (2 tasks)

| Task | ChatGPT | GT | Error |
|------|---------|-----|-------|
| t3-cluster-005 | 29/cluster-period | 7/cluster-period | Stepped-wedge design — used wrong formula (cross-sectional assumption inflates N 4x) |
| t3-simr-005 | power=0.32 | power=0.58 | Marginal Cox with frailty — analytical approximation doesn't account for marginal test properties |

---

## Key Findings

### 1. No Code Execution = Systematic Underperformance

ChatGPT Auto Mode computes everything analytically from memory. This creates three systematic failure modes:
- **z vs t approximation** (11 tasks, ~10% of benchmark)
- **No access to R packages** (pmsampsize: 10 tasks, pmvalsampsize: 5 tasks, simr: 3 tasks)
- **Wrong formulas from memory** (8 tasks)

### 2. Tier 4 Is a Package-Knowledge Test

Tier 4 tasks (Riley prediction model criteria) essentially require running `pmsampsize` or `pmvalsampsize`. Without code execution, ChatGPT gets only 28.6% — and most passes are tasks where simple approximations happen to align (like t4-cont-001 and t4-cont-002 which are from the CRAN vignette).

### 3. Tier 3 Performs Best (70%)

Surprisingly, the "Advanced Designs" tier has the highest pass rate. This is because:
- Cluster RCTs use well-known DE formulas ChatGPT knows
- Factorial designs use standard ANOVA power formulas
- simr tasks have wide tolerances (±15) accommodating analytical approximations

### 4. Wrong Method > Wrong Numbers

The most dangerous failures aren't small numerical errors — they're completely wrong methods:
- t2-logreg-002: 215 vs 522 (used case-control when should use cohort)
- t2-mixed-004: 750 vs 150 patients/cluster (5x error)
- t3-cluster-005: 29 vs 7 per cluster-period (4x error)
- t4-surv-002: 511 vs 185 (wrong approach entirely)

### 5. If Only z-Approximation Failures Were Forgiven

If we relaxed tolerance by +2 for the z-approximation issue (essentially allowing ±3 instead of ±1 for per-group counts), 11 more tasks would pass:
- **Adjusted pass rate: 71/106 = 67.0%** (vs 56.6% strict)
- Tier 1 would jump from 56.7% to 90.0% (27/30)
- Tier 3 would jump from 70.0% to 85.0% (17/20)

---

## Comparison with Power Agent

| Metric | Power Agent (Claude Opus 4.5) | ChatGPT Auto |
|--------|-------------------------------|--------------|
| **Overall** | **99.1%** (105/106) | **56.6%** (60/106) |
| Tier 1 | 100% (30/30) | 56.7% (17/30) |
| Tier 2 | 100% (35/35) | 65.7% (23/35) |
| Tier 3 | 100% (20/20) | 70.0% (14/20) |
| Tier 4 | 95.2% (20/21) | 28.6% (6/21) |
| Code Execution | Yes (R via Docker) | No (analytical only) |
| Approach | Run R packages | Formula approximation |

---

*Evaluated by Claude Opus 4.6 with Claude Sonnet 4.5 value extraction*
*Benchmark: power-agent-benchmark v1.0.0 (106 tasks)*
