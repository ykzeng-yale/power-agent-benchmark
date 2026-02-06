# Evaluation Methodology

This document describes how the Power Agent Benchmark evaluates agent responses using an LLM-as-judge approach with strict tolerance enforcement.

## Overview

The evaluation system uses a two-stage approach:
1. **LLM Scoring**: Claude Sonnet evaluates responses across 5 criteria
2. **Tolerance Enforcement**: Strict numerical validation against ground truth

## Scoring Criteria

Tasks are evaluated on **5 criteria** totaling **100 points**:

### 1. Template Selection (20 points)

Evaluates whether the agent identified the correct statistical method.

| Score | Criteria |
|-------|----------|
| 20 | Exact template match (e.g., correctly identifies "two-sample t-test") |
| 10 | Acceptable alternative method that would produce valid results |
| 0 | Incorrect method that would lead to wrong conclusions |

**Examples:**
- Full credit: Using `pwr.t.test` for a two-sample t-test question
- Partial: Using simulation when analytical formula exists
- Zero: Using ANOVA for a two-group comparison without justification

### 2. Parameter Extraction (20 points)

Evaluates whether the agent correctly extracted parameters from the natural language prompt.

| Score | Criteria |
|-------|----------|
| 20 | All parameters correctly identified and interpreted |
| 15 | Most parameters correct, minor errors in interpretation |
| 10 | Key parameters identified but some errors |
| 5 | Significant parameter errors affecting calculation |
| 0 | Critical parameters missing or wrong |

**Key parameters by task type:**
- t-tests: effect size (d), power, alpha, one/two-sided
- Regression: R², number of predictors, alpha
- Mixed models: ICC, number of measurements, design effect
- Survival: hazard ratio, event rate, follow-up time

### 3. Calculation Accuracy (30 points)

The **primary metric** - evaluates whether the numerical answer is within tolerance.

| Score | Criteria |
|-------|----------|
| 30 | Within specified tolerance of ground truth |
| 20-25 | Close but slightly outside tolerance |
| 10-15 | Reasonably close, correct order of magnitude |
| 0-10 | Far from correct answer |

**Critical rule**: If the answer is outside tolerance, this criterion is forced to 0 during post-evaluation validation, regardless of LLM scoring.

### 4. Code Quality (15 points)

Evaluates the R code produced by the agent.

| Score | Criteria |
|-------|----------|
| 15 | Correct, executable code using appropriate package |
| 10 | Code would execute with minor fixes |
| 5 | Conceptually correct but has errors |
| 0 | Code would not produce correct results |

**Note**: Any valid R package is acceptable (pwr, pwrss, simr, etc.). The agent is NOT penalized for choosing a different package than the reference code.

### 5. Interpretation Quality (15 points)

Evaluates the agent's explanation and recommendations.

| Score | Criteria |
|-------|----------|
| 15 | Clear recommendations with assumptions stated |
| 10 | Good interpretation, some assumptions missing |
| 5 | Basic interpretation without context |
| 0 | Missing or misleading interpretation |

**Good interpretation includes:**
- Clear statement of the sample size/power result
- Key assumptions (e.g., normality, equal variances)
- Practical recommendations (e.g., "recruit N per group")
- Acknowledgment of limitations when relevant

## Pass/Fail Determination

A task is **PASSED** if:
1. Total score ≥ 70 points, AND
2. Calculation accuracy > 0 (i.e., within tolerance)

Both conditions must be met. An agent could score 75 on other criteria but still fail if the numerical answer is outside tolerance.

## Tolerance Philosophy

### Why Tolerances?

Different R packages and methods can produce slightly different results:
- `pwr.t.test` vs custom simulation
- Analytical formulas vs Monte Carlo estimation
- Different variance approximations in pwrss

Tolerances allow for these valid variations while catching actual errors.

### Tolerance Calibration

| Task Type | Tolerance Approach | Rationale |
|-----------|-------------------|-----------|
| Analytical (pwr) | ±5 or 5% | Formulas are deterministic |
| Variance-corrected (pwrss) | ±5% | Minor formula differences |
| Simulation (simr) | ±8-10% | Monte Carlo variance |
| Prediction models | ±5% | pmsampsize is deterministic |

### Tolerance Application

The evaluation uses the **larger** of:
- The absolute tolerance specified in the task
- 5% of the ground truth value

This prevents overly strict tolerances for large sample sizes.

Example:
- Ground truth: 1000, Tolerance: 50
- Actual tolerance used: max(50, 0.05 × 1000) = 50
- Acceptable range: 950-1050

## LLM-as-Judge Implementation

### Model Configuration

- **Model**: Claude Sonnet 4
- **Temperature**: 0 (deterministic)
- **Max tokens**: 4000

### Prompt Structure

The evaluation prompt includes:
1. Task question
2. Expected template and ground truth
3. Tolerance ranges
4. Agent's complete response
5. Scoring rubric

### Value Extraction

The LLM extracts:
- `agentValue`: The final numerical answer
- `agentValueUnit`: Unit type (per-group, total, etc.)
- `sampleSizeError`: Error magnitude if wrong
- Score for each criterion

### Post-Evaluation Validation

After LLM scoring:
1. Extract `agentValue` from LLM response
2. Compare to ground truth with tolerance
3. If within tolerance: ensure calculation accuracy ≥ 30
4. If outside tolerance: force calculation accuracy = 0
5. Recalculate total score
6. Apply pass/fail determination

## Reproducibility

### Deterministic Evaluation

- Temperature = 0 ensures consistent LLM responses
- Same input produces same scores
- Tolerance checks are exact numerical comparisons

### Logging

All evaluations are logged with:
- Full agent response
- LLM evaluation response
- Extracted values
- Score breakdown
- Pass/fail status
- Timestamp

## Edge Cases

### Multiple Valid Answers

Some questions may have multiple valid interpretations:
- Per-group vs total sample size
- Different rounding conventions
- Alternative valid methods

The evaluator handles this through:
- Unit-aware value extraction
- Tolerance ranges that accommodate valid variations
- LLM judgment for method acceptability

### Missing Output

If the agent fails to produce a numerical answer:
- Calculation accuracy = 0
- Task automatically fails
- Other criteria still evaluated for diagnostic purposes

### Extreme Values

Values that are orders of magnitude off:
- Likely parameter misinterpretation
- Zero score for calculation accuracy
- Partial credit possible for correct methodology

## Tier-Specific Considerations

### Tier 1 (Basic)
- Tight tolerances (deterministic formulas)
- High expectation for exact answers
- Any valid R package acceptable

### Tier 2 (Regression/Models)
- Moderate tolerances
- Method-dependent ranges
- Some tasks have multiple valid approaches

### Tier 3 (Advanced/Simulation)
- Wider tolerances for simr tasks
- Accept simulation variance
- Focus on correct setup over exact number

### Tier 4 (Prediction Models)
- pmsampsize outputs are deterministic
- Tight tolerances appropriate
- Watch for criteria confusion (which constraint binds)
