# Evaluation Methodology

This document describes how agent responses are evaluated against the Power Agent Benchmark ground truths.

## Core Principle: Value-Based Evaluation

**The primary evaluation method is direct numerical comparison** of the agent's output against the ground truth value with appropriate tolerance.

```
PASS if: |agent_value - ground_truth| ≤ tolerance
```

This benchmark follows the same evaluation paradigm as MATH, GSM8K, and other quantitative benchmarks.

## Tolerance Philosophy

### Two Categories of Tasks

| Category | Method | Ideal Tolerance | Rationale |
|----------|--------|-----------------|-----------|
| **Analytical (Deterministic)** | pwr, pwrss, pmsampsize | **±0-2** (or exact match) | Closed-form formulas produce identical results |
| **Simulation-Based (Stochastic)** | simr Monte Carlo | **±3-5%** | Inherent variance from random sampling |

### Why Near-Zero for Deterministic?

Deterministic R functions produce **exact, reproducible results**:

```r
pwr.t.test(d = 0.5, power = 0.80, sig.level = 0.05)$n
# Always returns 63.76561
ceiling(63.76561)  # Always 64
```

If an agent uses the same formula with the same parameters, it **must** get the same answer. Valid reasons for small differences (±1-2):
- `ceiling()` vs `round()` vs `floor()` conventions
- Minor R package version differences

Invalid reasons that indicate agent error:
- Wrong formula or package
- Parameter misinterpretation
- Calculation mistakes

**Recommended tolerance for deterministic tasks: ±1-2 subjects, or exact match with rounding flexibility.**

### Why 3-5% for Simulation?

Monte Carlo simulation (simr) has inherent statistical variance:

```
With nsim = 500 and true power ≈ 0.80:
- Standard Error = sqrt(0.8 × 0.2 / 500) ≈ 0.018
- 95% CI width ≈ ±3.5%
```

**Recommended tolerance for simulation tasks: ±5% power (conservative) or ±3% (strict).**

## Current Task Tolerances

The current `tasks.json` files contain tolerances that were set during benchmark development. Some are more generous than the ideal values above:

| Tier | Current Range | Ideal |
|------|---------------|-------|
| Tier 1 (pwr) | 5-35% | ±1-2 subjects |
| Tier 2 (mixed) | 5-33% | ±1-2 (analytical), ±5% (simulation) |
| Tier 3 (simr) | 8-35% | ±5% power |
| Tier 4 (pmsampsize) | 5% | ±1-2 subjects |

### Strict Evaluation Option

For stricter evaluation, users can override tolerances:

```javascript
function strictEvaluate(task, agentValue) {
  const gt = getExpectedValue(task.ground_truth);

  // Strict tolerance based on task type
  let strictTolerance;
  if (task.template.includes('simr') || task.id.includes('simr')) {
    strictTolerance = gt.value * 0.05;  // 5% for simulation
  } else {
    strictTolerance = 2;  // ±2 for deterministic
  }

  const diff = Math.abs(agentValue - gt.value);
  return diff <= strictTolerance;
}
```

## Value Extraction

### Option 1: Structured Output (Recommended)

Agents should produce structured output for direct evaluation:

```json
{
  "sample_size_per_group": 64,
  "total_sample_size": 128,
  "power": 0.80,
  "method": "pwr.t.test"
}
```

### Option 2: Pattern Matching

For free-text output:

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

### Option 3: LLM Extraction (Fallback)

For complex unstructured output, an LLM can extract values. This is a fallback option - structured output is preferred.

## Pass/Fail Criteria

A task is **PASSED** if:

```
|agent_value - ground_truth| ≤ tolerance
```

No partial credit. No subjective judgment.

### Aggregate Metrics

| Metric | Definition |
|--------|------------|
| **Pass Rate** | Tasks passed / Total tasks |
| **Mean Absolute Error** | Average |agent - GT| |
| **Mean Percent Error** | Average % error |

## Validation Examples

### Example 1: Deterministic Task (Tier 1)

```
Task: t1-ttest-001
Question: "...Cohen's d = 0.5, power = 0.80, alpha = 0.05..."
Ground Truth: 64 per group

Agent Answer: 64 → PASS (exact match)
Agent Answer: 63 → PASS (ceiling vs round difference, if tolerance allows)
Agent Answer: 70 → FAIL (wrong calculation)
```

### Example 2: Simulation Task (Tier 3)

```
Task: t3-simr-002
Question: "...GLMM binary, OR=2.0, nsim=200..."
Ground Truth: 58 per group
Tolerance: ±5% = ±2.9 → ±3

Agent Answer: 60 → PASS (within 5%)
Agent Answer: 55 → PASS (within 5%)
Agent Answer: 70 → FAIL (>5% error)
```

### Example 3: Deterministic with Strict Tolerance

```
Task: t4-binary-001
Ground Truth: 662 (pmsampsize is deterministic)
Ideal Tolerance: ±2

Agent Answer: 662 → PASS
Agent Answer: 660 → PASS (minor rounding)
Agent Answer: 630 → FAIL (calculation error)
```

## LLM-as-Judge: Optional

The `evaluator/llm-judge.js` provides:
- Value extraction from unstructured output
- Diagnostic scoring for debugging

**This is supplementary, not primary.** Value-based comparison determines pass/fail.

## Simple Evaluator

Use `evaluator/simple-evaluator.js` for direct value comparison:

```bash
# Create results JSON with agent answers
echo '{"t1-ttest-001": 64, "t1-ttest-002": 86}' > results.json

# Evaluate
node evaluator/simple-evaluator.js results.json
```

## Best Practices

1. **Use structured output** - Avoid extraction ambiguity
2. **Match the exact formula** - For deterministic tasks, use the same R function
3. **Run sufficient simulations** - For simr tasks, use nsim ≥ 500
4. **Report exact values** - Don't round intermediate calculations

## Summary

| Aspect | Approach |
|--------|----------|
| **Primary evaluation** | Direct numerical comparison |
| **Deterministic tolerance** | ±0-2 (exact or near-exact) |
| **Simulation tolerance** | ±3-5% |
| **Pass criterion** | Within tolerance |
| **LLM-as-judge** | Optional, for extraction only |

The benchmark rewards agents that produce **correct numerical answers**. For deterministic tasks, there is one right answer.
