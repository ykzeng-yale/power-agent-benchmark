# Tier 2: Regression & Models

## Overview

Tier 2 contains **35 tasks** covering complex statistical models requiring variance decomposition, formula-based calculations, and advanced power analysis packages.

## Task Categories

| Category | Count | R Package | Description |
|----------|-------|-----------|-------------|
| Linear regression | 6 | pwr | Multiple regression, R² detection |
| Logistic regression | 6 | pwrss | Odds ratio, binary outcomes |
| Mixed effects (LMM) | 8 | pwr/simr | Repeated measures, hierarchical data |
| Survival analysis | 8 | various | Log-rank, Cox regression |
| Poisson regression | 7 | pwrss | Count outcomes, rate ratios |

## Difficulty Distribution

- **Basic**: 8 tasks - Standard model applications
- **Intermediate**: 15 tasks - Multi-step calculations
- **Advanced**: 12 tasks - Complex variance structures

## Key Concepts

1. **Regression Power**
   - f² = R² / (1 - R²) for overall model test
   - Incremental f² for added predictors
   - pwr.f2.test for linear, pwrss for logistic

2. **Mixed Models**
   - ICC (Intraclass Correlation Coefficient)
   - Design Effect: DE = 1 + (m-1) × ICC
   - Variance Reduction Factor: VRF = (1 + (m-1) × ICC) / m

3. **Survival Analysis**
   - Schoenfeld formula for events needed
   - Event probability from exponential model
   - Hazard ratio to sample size conversion

4. **Poisson Regression**
   - Rate ratios (exp(β))
   - Exposure time (person-years)
   - pwrss.z.poisson with correct dist parameter

## Example Tasks

### t2-linreg-003 (Intermediate)
> Test adding 3 predictors to a model with 4 existing. R² improves from 0.20 to 0.30.

**Ground Truth**: 85 subjects

### t2-mixed-005 (Advanced)
> Three-level model: measurements within patients within sites. What is the power?

**Ground Truth**: 58% power

### t2-surv-001 (Basic)
> Detect HR=0.7 with 3-year accrual, 2-year follow-up. Control median survival 2 years.

**Ground Truth**: 198 per arm

## Tolerance

Tier 2 tolerances vary by method:
- Analytical methods: ±5%
- Mixed models: ±5-10 subjects
- Survival: ±20 subjects (event rate uncertainty)
