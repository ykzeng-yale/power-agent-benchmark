# Tier 4: Prediction Models

## Overview

Tier 4 contains **21 tasks** focusing on sample size for developing and validating clinical prediction models using Riley criteria.

## Task Categories

| Category | Count | R Package | Description |
|----------|-------|-----------|-------------|
| Riley binary | 5 | pmsampsize | Binary outcome development |
| Riley survival | 5 | pmsampsize | Time-to-event prediction |
| Riley continuous | 4 | pmsampsize | Continuous outcome prediction |
| External validation | 7 | pmvalsampsize | Model validation sample size |

## Difficulty Distribution

- **Basic**: 7 tasks - Standard pmsampsize usage
- **Intermediate**: 8 tasks - Multiple criteria consideration
- **Advanced**: 6 tasks - Complex validation scenarios

## Key Concepts

1. **Riley Development Criteria**
   - Events per predictor (EPP): ≥10-15 typically
   - Shrinkage target: ≤10% (shrinkage=0.90) or ≤5% (shrinkage=0.95)
   - Intercept precision criterion
   - **Binding constraint** determines final N

2. **R² Specifications**
   - Cox-Snell R² (csrsquared): bounded by max value
   - Nagelkerke R² (nagrsquared): rescaled to 0-1
   - Must use correct parameter name in pmsampsize

3. **External Validation (pmvalsampsize)**
   - Precision-based (not power-based!)
   - CI width for C-statistic
   - CI width for calibration slope
   - CI width for O/E ratio
   - LP distribution: Normal(mean, **SD**) or Beta(α, β)

4. **Linear Predictor Distribution**
   - lpnormal: c(mean, SD) - note: SD not variance!
   - lpbeta: c(alpha, beta) for bounded probabilities
   - Affects calibration slope sample size

## Example Tasks

### t4-binary-001 (Basic)
> Predict liver cirrhosis. 24 predictors, prevalence 17.4%, R²_CS=0.288.

**Ground Truth**: 662 subjects, 115 events

### t4-surv-001 (Basic)
> VTE recurrence model. 30 predictors, event rate 6.5%, R²_CS=0.051.

**Ground Truth**: 5143 subjects, 692 events

### t4-valid-001 (Basic)
> External validation. C=0.82, prevalence=22%, lpnormal=c(-1.75, 2.16).

**Ground Truth**: 1832 subjects (calibration slope binds)

## Tolerance

Tier 4 tolerances are tight (pmsampsize is deterministic):
- Sample size: ±5%
- Events: ±5%
- Accept exact pmsampsize/pmvalsampsize output
