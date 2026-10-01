# Task Schema Specification

This document describes the JSON schema used for task definitions in the Power Agent Benchmark.

## JSON Structure

Each task follows this structure:

```json
{
  "id": "t1-ttest-001",
  "template": "two_sample_ttest",
  "difficulty": "basic",
  "question": "I want to compare mean blood pressure between treatment and control groups...",
  "expected_template": "two_sample_ttest",
  "ground_truth": {
    "sample_size_per_group": 64,
    "total_sample_size": 128,
    "effect_size_d": 0.5,
    "power": 0.8,
    "alpha": 0.05
  },
  "tolerance": {
    "sample_size": 10,
    "power": 0.03
  },
  "source": "pwr package CRAN vignette",
  "reference_code": "library(pwr)\npwr.t.test(d=0.5, sig.level=0.05, power=0.80, type='two.sample')"
}
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier. Format: `t{tier}-{category}-{number}` (e.g., `t1-ttest-001`) |
| `template` | string | Statistical method category (e.g., `two_sample_ttest`, `logistic_regression`) |
| `difficulty` | enum | One of: `"basic"`, `"intermediate"`, `"advanced"` |
| `question` | string | Natural language prompt presented to the agent (min 20 characters) |
| `expected_template` | string | Template the agent should identify (usually matches `template`) |
| `ground_truth` | object | Expected numerical results (structure varies by task type) |
| `tolerance` | object | Acceptable deviation ranges for evaluation |
| `source` | string | Reference for ground truth derivation |
| `reference_code` | string | R code that produces the ground truth value |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `reference_code_note` | string | Additional notes about the reference code or methodology |

## ID Format

Task IDs follow the pattern: `t{tier}-{category}-{number}`

- **Tier**: 1-4
- **Category**: Short identifier for statistical method
- **Number**: 3-digit zero-padded sequence

Examples:
- `t1-ttest-001` - Tier 1, t-test category, first task
- `t2-logreg-003` - Tier 2, logistic regression, third task
- `t3-cluster-002` - Tier 3, cluster design, second task
- `t4-valid-007` - Tier 4, validation, seventh task

## Template Categories

### Tier 1
- `two_sample_ttest` - Independent samples t-test
- `paired_ttest` - Paired/dependent samples t-test
- `one_way_anova` - One-way ANOVA
- `two_proportions` - Two-sample proportion test
- `chi_square` - Chi-square test of independence
- `correlation` - Pearson correlation test

### Tier 2
- `linear_regression` - Multiple linear regression
- `logistic_regression` - Logistic regression
- `mixed_effects_lmm` - Linear mixed-effects models
- `survival_analysis` - Survival/time-to-event analysis
- `poisson_regression` - Poisson/count regression

### Tier 3
- `cluster_rct` - Cluster randomized trials
- `crossover` - Crossover trial designs
- `factorial` - Factorial designs
- `simr_simulation` - Simulation-based power (simr package)

### Tier 4
- `riley_binary` - Binary outcome prediction (pmsampsize)
- `riley_survival` - Survival outcome prediction (pmsampsize)
- `riley_continuous` - Continuous outcome prediction (pmsampsize)
- `external_validation` - Model validation (pmvalsampsize)

## Ground Truth Fields by Task Type

### Sample Size Tasks (most common)

```json
"ground_truth": {
  "sample_size_per_group": 64,
  "total_sample_size": 128,
  "effect_size_d": 0.5,
  "power": 0.8,
  "alpha": 0.05
}
```

### Power Calculation Tasks

```json
"ground_truth": {
  "power": 0.85,
  "given_sample_size": 100,
  "effect_size_d": 0.4,
  "alpha": 0.05
}
```

### Prediction Model Tasks (Tier 4)

```json
"ground_truth": {
  "sample_size": 662,
  "events": 115,
  "predictors": 24,
  "prevalence": 0.174,
  "cs_rsquared": 0.288,
  "max_shrinkage": 0.9
}
```

### External Validation Tasks

```json
"ground_truth": {
  "sample_size": 1831,
  "events": 403,
  "prevalence": 0.22,
  "cstatistic": 0.82,
  "cstat_ciwidth": 0.10,
  "calslope_ciwidth": 0.20,
  "binding_criterion": "calibration_slope"
}
```

## Tolerance Specification

Tolerances define acceptable ranges for numerical answers:

```json
"tolerance": {
  "sample_size": 10,    // Absolute tolerance: answer ± 10
  "power": 0.03         // Absolute tolerance: answer ± 0.03
}
```

### Tolerance Guidelines by Tier

| Tier | Sample Size | Power | Notes |
|------|-------------|-------|-------|
| 1 | ±3-10 or ±5% | ±0.03 | Analytical methods, tight tolerance |
| 2 | ±5-50 or ±5% | ±0.03 | Method-dependent ranges |
| 3 | ±5-20 or ±5% | ±0.08 | Wider for simulation variance |
| 4 | ±5% of GT | ±0.03 | Prediction model outputs |

### Percentage vs Absolute Tolerance

When evaluating, the system uses the **larger** of:
- Absolute tolerance specified
- 5% of ground truth value

This prevents overly strict tolerances for large sample sizes.

## Reference Code Requirements

Reference code must:
1. Be executable R code
2. Load required packages explicitly
3. Produce the ground truth value
4. Include comments explaining the calculation

Example:
```r
library(pwr)
# Two-sample t-test for d=0.5, power=0.80, alpha=0.05
result <- pwr.t.test(d = 0.5, sig.level = 0.05, power = 0.80, type = "two.sample")
# n per group = ceiling(result$n) = 64
```

## Validation

Tasks are validated using the JSON Schema at `tasks/schema.json`. All tasks must pass schema validation before being included in the benchmark.

## Examples

### Tier 1 Example (Basic t-test)

```json
{
  "id": "t1-ttest-001",
  "template": "two_sample_ttest",
  "difficulty": "basic",
  "question": "I want to compare mean blood pressure between treatment and control groups. I expect a medium effect size (Cohen's d = 0.5), want 80% power at alpha = 0.05 using a two-sided test. How many participants do I need per group?",
  "expected_template": "two_sample_ttest",
  "ground_truth": {
    "sample_size_per_group": 64,
    "total_sample_size": 128,
    "effect_size_d": 0.5,
    "power": 0.8,
    "alpha": 0.05
  },
  "tolerance": {
    "sample_size": 10,
    "power": 0.03
  },
  "source": "pwr package CRAN vignette",
  "reference_code": "library(pwr)\npwr.t.test(d=0.5, sig.level=0.05, power=0.80, type='two.sample')\n# n = 63.77 per group, ceiling = 64"
}
```

### Tier 4 Example (Riley Prediction Model)

```json
{
  "id": "t4-binary-001",
  "template": "riley_binary",
  "difficulty": "basic",
  "question": "We are developing a logistic regression model to predict liver cirrhosis. We have 24 candidate predictors and anticipate the outcome prevalence will be 0.174. We have estimated R^2_CS of 0.288. What is the minimum sample size?",
  "expected_template": "riley_binary",
  "ground_truth": {
    "sample_size": 662,
    "events": 115,
    "predictors": 24,
    "prevalence": 0.174,
    "cs_rsquared": 0.288,
    "max_shrinkage": 0.9
  },
  "tolerance": {
    "sample_size": 33,
    "events": 6
  },
  "source": "pmsampsize CRAN vignette - Example 1",
  "reference_code": "library(pmsampsize)\npmsampsize(type='b', csrsquared=0.288, parameters=24, prevalence=0.174)\n# N = 662, events = 115"
}
```
