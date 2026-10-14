# Benchmark v2.1 - Published-Source Edition

**989 tasks** across 4 tiers, constructed from **500 published examples** and 489 supplementary tasks, all R-verified.

## Overview

This benchmark edition prioritizes tasks constructed from **published sources** including R package help pages, CRAN vignettes, GitHub repositories, published papers, educational sites, textbooks, and software documentation.

## Tier Distribution

| Tier | Tasks | Description |
|------|-------|-------------|
| Tier 1 | 296 | Basic comparisons (t-tests, ANOVA, proportions, chi-squared, correlation) |
| Tier 2 | 295 | Regression & models (logistic, Poisson, survival, mediation, SEM) |
| Tier 3 | 298 | Complex designs (bioequivalence, group sequential, multilevel RCT, non-inferiority) |
| Tier 4 | 100 | Prediction & specialized (Riley prediction models, precision-based CI, diagnostic accuracy) |

## Real Source Breakdown

| Source Type | Count |
|-------------|-------|
| Educational sites | 92 |
| CRAN vignettes | 100 |
| GitHub repositories | 84 |
| Published papers | 77 |
| R help pages | 66 |
| Software documentation | 56 |
| Textbooks | 25 |

## Quality Assurance

- All ground truths R-verified (100% spot-check pass rate)
- Zero R function/package name leaks in questions
- Zero Q-GT type mismatches
- All tasks have structured source metadata
- Questions read as natural researcher queries

## Task Schema

```json
{
  "id": "t1-real-pwr-pwrttest-001",
  "template": "two_sample_ttest",
  "difficulty": "basic",
  "question": "A researcher plans a two-sample t-test to detect a medium effect size (d=0.5) between treatment and control groups, with 80% power and a two-sided significance level of 0.05. What is the required sample size per group?",
  "expected_template": "two_sample_ttest",
  "ground_truth": { "n_per_group": 64 },
  "tolerance": { "n_per_group": 2 },
  "source": {
    "package": "pwr",
    "function": "pwr.t.test",
    "origin": "Cohen (1988) classic example",
    "source_type": "textbook"
  },
  "reference_code": "pwr.t.test(d=0.5, sig.level=0.05, power=0.80, type='two.sample')",
  "tier": 1
}
```

## Tolerance Rules

- **Deterministic** (pwr, pwrss, WebPower): max(1, ceil(0.02 * GT)) or max(0.005, 0.02 * val) for proportions
- **Iterative** (gsDesign, rpact, PowerTOST, TrialSize): max(2, ceil(0.05 * GT))
- **Simulation-based** (Superpower, simr): max(5, ceil(0.10 * GT))

## R Packages Covered

pwr, PowerTOST, pwrss, gsDesign, powerSurvEpi, PowerUpR, TrialSize, presize, MKpower, powerMediation, longpower, pmsampsize, Superpower, WebPower, rpact, pmvalsampsize, stats
