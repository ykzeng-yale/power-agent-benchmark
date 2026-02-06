# Evaluation Methodology

This document describes how agent responses are evaluated against the Power Agent Benchmark ground truths.

## Core Principle: Value-Based Evaluation

**The primary evaluation method is direct numerical comparison** of the agent's output against the ground truth value with appropriate tolerance.

This benchmark follows the same evaluation paradigm as MATH, GSM8K, and other quantitative benchmarks:
- Extract the agent's numerical answer
- Compare it to the ground truth
- Apply method-appropriate tolerance
- Report pass/fail based on tolerance match

## Primary Evaluation Method

### Direct Value Comparison

```python
def evaluate_task(agent_value, ground_truth, tolerance):
    """Primary evaluation: direct numerical comparison."""
    if agent_value is None:
        return {"passed": False, "error": "No value extracted"}

    diff = abs(agent_value - ground_truth)
    within_tolerance = diff <= tolerance

    return {
        "passed": within_tolerance,
        "agent_value": agent_value,
        "ground_truth": ground_truth,
        "tolerance": tolerance,
        "difference": diff,
        "percent_error": 100 * diff / ground_truth
    }
```

### Expected Agent Output

We **strongly encourage** agent developers to produce structured output that includes the final numerical answer explicitly:

```json
{
  "sample_size_per_group": 64,
  "total_sample_size": 128,
  "power": 0.80,
  "method": "pwr.t.test"
}
```

Or at minimum, a clearly extractable final answer:

```
FINAL ANSWER: 64 subjects per group
```

This enables direct automated evaluation without requiring LLM interpretation.

## Tolerance Specifications

### Two Categories of Tasks

| Category | Method | Tolerance | Rationale |
|----------|--------|-----------|-----------|
| **Analytical (Deterministic)** | Closed-form formulas (pwr, pwrss, pmsampsize) | ±5% or small absolute | Results are mathematically exact |
| **Simulation-Based (Stochastic)** | Monte Carlo (simr) | ±8-10% | Inherent variance from random sampling |

### Why These Tolerances?

**Analytical tasks** (Tier 1, most of Tier 2, Tier 4):
- R packages use exact formulas
- Minor differences from rounding, ceiling/floor choices
- Example: `pwr.t.test` returns 63.77, agent reports 64 (ceiling) → **PASS**

**Simulation tasks** (Tier 3 simr, some Tier 2):
- Monte Carlo results vary by random seed
- With 500 simulations: SE ≈ 0.02 for power around 0.80
- 95% CI width ≈ ±4%, so ±8% tolerance is appropriate
- Example: Ground truth power = 0.80, agent reports 0.77 → **PASS** (within ±0.08)

### Tolerance by Tier

| Tier | Task Types | Typical Tolerance |
|------|-----------|-------------------|
| Tier 1 | pwr package (t-test, ANOVA, etc.) | ±5 subjects or 5% |
| Tier 2 | pwrss, mixed models, survival | ±5-10% (per-task) |
| Tier 3 | simr simulation | ±8% power, ±15% sample size |
| Tier 4 | pmsampsize, pmvalsampsize | ±5% (deterministic) |

### Task-Level Tolerance Override

Each task specifies its own tolerance in `tasks.json`:

```json
{
  "id": "t3-simr-002",
  "ground_truth": {
    "subjects_per_group": 58
  },
  "tolerance": {
    "sample_size": 20,  // ±20 for simulation task
    "power": 0.08       // ±8% for power estimates
  }
}
```

**The task-level tolerance takes precedence** over tier defaults.

## Value Extraction

### Option 1: Structured Output (Recommended)

If your agent produces structured output (JSON, key-value pairs), extract directly:

```javascript
function extractFromStructured(output) {
  if (output.sample_size_per_group) return output.sample_size_per_group;
  if (output.sample_size) return output.sample_size;
  if (output.power) return output.power;
  return null;
}
```

### Option 2: Pattern Matching

For free-text output, use regex patterns:

```javascript
function extractFromText(text) {
  const patterns = [
    /sample\s*size[:\s]+(\d+)/i,
    /(\d+)\s*(?:per\s*group|subjects|participants)/i,
    /n\s*[=:]\s*(\d+)/i,
    /power[:\s]+(\d+\.?\d*)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return parseFloat(match[1]);
  }
  return null;
}
```

### Option 3: LLM-Based Extraction (Fallback)

For complex unstructured output where pattern matching fails, an LLM can extract the final value:

```javascript
const extractionPrompt = `
Extract the FINAL numerical answer from this power analysis response.
Return ONLY a JSON object: {"value": <number>, "unit": "<per-group|total|power>"}

Response:
${agentOutput}
`;
```

**Note**: This is a fallback option. We encourage structured output to avoid LLM interpretation overhead and potential extraction errors.

## Simple Evaluator Implementation

Here is a minimal evaluator that implements direct value comparison:

```javascript
// simple-evaluator.js
import { readFile } from 'fs/promises';

async function evaluateTier(tier, getAgentAnswer) {
  const data = JSON.parse(await readFile(`tasks/tier${tier}/tasks.json`));
  const results = [];

  for (const task of data.tasks) {
    // Get agent's answer for this task
    const agentValue = await getAgentAnswer(task.question);

    // Get ground truth and tolerance
    const gt = task.ground_truth;
    const tol = task.tolerance;

    // Determine expected value
    const expected = gt.sample_size_per_group || gt.sample_size ||
                     gt.subjects_per_group || gt.subjects || gt.power;
    const tolerance = tol.sample_size || tol.power || expected * 0.05;

    // Direct comparison
    const diff = Math.abs(agentValue - expected);
    const passed = diff <= tolerance;

    results.push({
      id: task.id,
      passed,
      agentValue,
      expected,
      tolerance,
      diff,
      percentError: (100 * diff / expected).toFixed(1)
    });
  }

  return results;
}
```

## Pass/Fail Criteria

A task is **PASSED** if and only if:

```
|agent_value - ground_truth| ≤ tolerance
```

That's it. No subjective judgment, no partial credit for "close" answers.

### Aggregate Metrics

| Metric | Definition |
|--------|------------|
| **Pass Rate** | Tasks passed / Total tasks |
| **Tier Pass Rate** | Per-tier pass counts |
| **Mean Absolute Error** | Average |agent - GT| across tasks |
| **Mean Percent Error** | Average % error across tasks |

## Validation Examples

### Example 1: Analytical Task (Tier 1)

```
Task: t1-ttest-001
Question: "...Cohen's d = 0.5, power = 0.80, alpha = 0.05..."
Ground Truth: 64 per group
Tolerance: ±10

Agent Answer: 64
Difference: 0
Result: PASS ✓
```

### Example 2: Simulation Task (Tier 3)

```
Task: t3-simr-002
Question: "...GLMM binary, OR=2.0, nsim=200..."
Ground Truth: 58 per group
Tolerance: ±20 (wider for simulation)

Agent Answer: 65
Difference: 7
Result: PASS ✓ (7 ≤ 20)
```

### Example 3: Outside Tolerance

```
Task: t2-linreg-001
Question: "...5 predictors, R²=0.10, power=0.80..."
Ground Truth: 122
Tolerance: ±6

Agent Answer: 114
Difference: 8
Result: FAIL ✗ (8 > 6)
```

## LLM-as-Judge: Optional Enhancement

The repository includes an LLM-based evaluator (`evaluator/llm-judge.js`) that provides:

1. **Value extraction** from unstructured output
2. **Diagnostic scoring** across 5 criteria (for debugging)
3. **Justification** for failures

However, this is **supplementary** to the core value-based evaluation:

| Component | Purpose | Required? |
|-----------|---------|-----------|
| Value extraction | Parse agent output | Only if unstructured |
| Tolerance check | Pass/fail decision | **Yes (core metric)** |
| 5-criteria scoring | Diagnostic/debugging | No (optional) |
| LLM justification | Explain failures | No (optional) |

### When to Use LLM-as-Judge

- Your agent produces natural language output without structured answers
- You want diagnostic breakdown of where the agent went wrong
- You're debugging agent behavior

### When NOT to Use LLM-as-Judge

- Your agent outputs structured JSON with numerical values
- You only need pass/fail metrics
- You want faster evaluation (no API calls)
- You want fully reproducible evaluation (no LLM variance)

## Recommended Evaluation Pipeline

```
1. Agent produces response to task question
                    ↓
2. Extract numerical value (structured > regex > LLM fallback)
                    ↓
3. Compare to ground_truth with tolerance
                    ↓
4. Record pass/fail
                    ↓
5. (Optional) Run LLM-as-judge for diagnostics on failures
```

## Reproducibility

### Deterministic Components

- Ground truths are R-validated and fixed
- Tolerances are specified in task JSON
- Value comparison is exact arithmetic
- Results are reproducible across runs

### Stochastic Components (if used)

- LLM-based extraction may vary slightly
- Simulation-based agent answers vary by seed
- These are handled by appropriate tolerances

## Summary

| Aspect | Approach |
|--------|----------|
| **Primary evaluation** | Direct numerical comparison with tolerance |
| **Agent output** | Structured format strongly encouraged |
| **Tolerances** | Tight for analytical, wider for simulation |
| **Pass criterion** | Within tolerance (no partial credit) |
| **LLM-as-judge** | Optional, for extraction and diagnostics |

The benchmark is designed to be simple, objective, and reproducible. If your agent can produce the right number within tolerance, it passes.
