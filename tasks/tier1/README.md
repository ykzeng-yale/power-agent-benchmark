# Tier 1: Basic Comparisons

## Overview

Tier 1 contains **30 tasks** covering fundamental power analysis methods with closed-form analytical solutions using the `pwr` R package.

## Task Categories

| Category | Count | Description |
|----------|-------|-------------|
| Two-sample t-test | 6 | Independent samples comparison |
| Paired t-test | 4 | Pre-post or matched pairs designs |
| One-way ANOVA | 5 | Multiple group comparisons |
| Two proportions | 5 | Binary outcome comparisons |
| Chi-square | 5 | Categorical association tests |
| Correlation | 5 | Linear relationship tests |

## Difficulty Distribution

- **Basic**: 12 tasks - Standard parameters, single function call
- **Intermediate**: 12 tasks - Parameter derivation required
- **Advanced**: 6 tasks - Non-standard scenarios, multiple steps

## Key Concepts

1. **Effect Sizes**
   - Cohen's d: 0.2 (small), 0.5 (medium), 0.8 (large)
   - Cohen's f: 0.1 (small), 0.25 (medium), 0.4 (large)
   - Cohen's w: 0.1 (small), 0.3 (medium), 0.5 (large)

2. **Power Parameters**
   - Power: typically 0.80 or 0.90
   - Alpha: typically 0.05, sometimes 0.01 or 0.025

3. **Test Types**
   - One-sided vs two-sided tests
   - Equal vs unequal variance assumptions

## Example Tasks

### t1-ttest-001 (Basic)
> Compare blood pressure between treatment and control groups. Effect size d=0.5, power=0.80, alpha=0.05, two-sided.

**Ground Truth**: 64 per group

### t1-anova-003 (Intermediate)
> Compare 4 treatment groups for pain scores. Detect f=0.3 with 85% power.

**Ground Truth**: 37 per group

### t1-paired-004 (Advanced)
> Bioequivalence crossover study. Effect d=0.25, power=0.95, alpha=0.01.

**Ground Truth**: 289 subjects

## Tolerance

Standard tolerance for Tier 1: ±5% or small absolute value (±3-10)

All ground truths are computed with `pwr` package and are deterministic.
