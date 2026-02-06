# Ground Truth Methodology

This document describes how ground truth values are established and validated for the Power Agent Benchmark.

## Validation Philosophy

Every ground truth in this benchmark is:
1. **Reproducible**: R code provided that produces the exact value
2. **Verified**: Cross-checked with alternative methods when possible
3. **Documented**: Source clearly stated with validation date
4. **Toleranced**: Appropriate acceptance range for the method type

## Primary Sources

### 1. R Package Vignettes and Documentation

The primary source for ground truths is official R package documentation:

- **pwr package**: CRAN vignette examples for basic tests
- **pwrss package**: Documented examples with Demidenko variance correction
- **pmsampsize package**: Riley criteria examples from package vignette
- **pmvalsampsize package**: External validation examples

### 2. Analytical Formulas

For well-established methods, analytical formulas serve as ground truth:

**Schoenfeld Formula (Survival)**
```
Events = 4 × (z_α/2 + z_β)² / log(HR)²
```

**Design Effect (Clustered Data)**
```
DE = 1 + (m - 1) × ICC
```

**Variance Reduction Factor (Repeated Measures)**
```
VRF = (1 + (m - 1) × ICC) / m
```

### 3. Simulation Verification

For complex scenarios, Monte Carlo simulation validates analytical results:

- Minimum 500 iterations for basic verification
- 2000+ iterations for precise power estimates
- Multiple seeds tested for robustness

## Validation Process

### Step 1: Initial Calculation

Run reference code to obtain ground truth:

```r
library(pwr)
result <- pwr.t.test(d = 0.5, power = 0.80, sig.level = 0.05, type = "two.sample")
gt_value <- ceiling(result$n)  # 64
```

### Step 2: Cross-Validation

When possible, verify with alternative method:

```r
# Alternative: simulation
simulate_power <- function(n, d, nsim = 5000) {
  rejections <- 0
  for (i in 1:nsim) {
    x1 <- rnorm(n, mean = 0, sd = 1)
    x2 <- rnorm(n, mean = d, sd = 1)
    p <- t.test(x1, x2)$p.value
    if (p < 0.05) rejections <- rejections + 1
  }
  return(rejections / nsim)
}

# Verify n=64 gives ~80% power
simulate_power(64, 0.5)  # Should be ~0.80
```

### Step 3: Documentation

Record in task JSON:
- `source`: Origin of ground truth
- `reference_code`: Reproducible R code
- `reference_code_note`: Additional methodology notes (if needed)

### Step 4: Tolerance Calibration

Set tolerance based on method characteristics:

| Method Type | Tolerance | Rationale |
|-------------|-----------|-----------|
| Analytical (deterministic) | ±5 or 5% | Package differences |
| Simulation-based | ±8-10% | Monte Carlo variance |
| Multi-step calculation | ±5-10% | Compounding differences |

## Validation Dates

Ground truths include validation dates to track currency:

```json
"source": "pwr package (R-validated 2025-02-06)"
```

This indicates:
- The source package
- The date of R verification
- Implicit R version (current at validation date)

## Common Validation Challenges

### 1. Package Version Differences

Different package versions may give slightly different results:
- Use current CRAN versions
- Document any version-specific behavior
- Set tolerances to accommodate minor variations

### 2. Rounding Conventions

Different conventions for final sample size:
- `ceiling()` - round up (most conservative)
- `round()` - standard rounding
- Some packages return exact non-integer

**Policy**: Accept answers that are within tolerance of the ceiling value.

### 3. Unit Ambiguity

Sample size can be reported as:
- Per group
- Total across groups
- Per cluster/cell

**Policy**: Tasks explicitly state expected unit. Evaluator extracts and converts as needed.

### 4. Formula Variations

Some formulas have multiple valid expressions:
- Schoenfeld with/without factor of 4
- Different ICC interpretations
- Various effect size conversions

**Policy**: Use the most common/accepted formula. Document alternatives in notes.

## Simulation-Based Validation

For Tier 3 simr tasks, simulation is the primary validation:

### Simulation Requirements

1. **Sufficient iterations**: Minimum 500, prefer 2000+
2. **Multiple seeds**: Test with different seeds to assess variance
3. **Confidence intervals**: Report power estimate with CI
4. **Model specification**: Exact lme4/simr syntax documented

### Simulation Variance

With nsim = 500:
- Standard error ≈ 0.022 (for power around 0.8)
- 95% CI width ≈ ±4.4%

This informs tolerance settings for simulation tasks.

### Example Validation

```r
library(simr)
library(lme4)

# Create model
model <- makeLmer(y ~ treatment + (1|subject),
                  fixef = c(0, 0.5),
                  VarCorr = 0.5,
                  sigma = 1,
                  data = expand.grid(treatment = c(0,1),
                                    subject = 1:50))

# Run power simulation
power_result <- powerSim(model, nsim = 500, progress = FALSE)

# Extract power with CI
power_result
# Power: 82.4% (78.7%, 85.7%)
```

## Ground Truth Updates

Ground truths may be updated when:
1. Errors are discovered and verified
2. Better validation methods become available
3. Package behavior changes significantly

### Update Process

1. Open issue describing the problem
2. Provide R verification code
3. Discuss in issue before making changes
4. Update with PR including:
   - New ground truth value
   - Updated reference code
   - New validation date
   - Changelog entry

## Quality Assurance

### Automated Validation

Schema validation ensures:
- All required fields present
- ID format correct
- Tolerance values reasonable

### Manual Review

New tasks require:
- Independent verification of ground truth
- Review of tolerance appropriateness
- Check of question clarity

### Periodic Revalidation

Annual review to:
- Test with current R package versions
- Identify any regressions
- Update validation dates

## Reproducibility

All ground truths can be reproduced by:

1. Installing specified R packages
2. Running reference code
3. Comparing to documented ground truth

The repository includes validation scripts in `validation/` for batch verification.
