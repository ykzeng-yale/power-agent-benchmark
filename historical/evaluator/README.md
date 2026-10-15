# Evaluator

Evaluation tools for the Power Agent Benchmark.

## Evaluation Philosophy

**Value-based evaluation is primary.** The benchmark evaluates agents by direct numerical comparison:

```
PASS if: |agent_value - ground_truth| ≤ tolerance
```

LLM-based evaluation is optional, primarily useful for extracting values from unstructured output.

## Two Evaluators

| Evaluator | Use Case | Dependencies |
|-----------|----------|--------------|
| `simple-evaluator.js` | **Primary** - Direct value comparison | None (pure JS) |
| `llm-judge.js` | Optional - Value extraction + diagnostics | Anthropic API |

## 1. Simple Evaluator (Recommended)

The simple evaluator performs direct numerical comparison with tolerance checking.

### Input Format

Provide a JSON file with agent answers:

```json
{
  "t1-ttest-001": 64,
  "t1-ttest-002": 86,
  "t1-paired-001": 34,
  "t2-linreg-001": 122
}
```

Or with structured output:

```json
{
  "t1-ttest-001": { "value": 64, "unit": "per_group" },
  "t1-ttest-002": { "value": 86, "unit": "per_group" }
}
```

### Usage

```bash
node evaluator/simple-evaluator.js my-results.json
```

### Output

```
======================================================================
POWER AGENT BENCHMARK - VALUE-BASED EVALUATION
======================================================================

FAILED TASKS:
----------------------------------------------------------------------
  t2-linreg-001: agent=114, expected=122 (diff=8, tol=6)

SUMMARY:
----------------------------------------------------------------------
  Total tasks:  106
  Passed:       105 (99.1%)
  Failed:       1
  Missing:      0

BY TIER:
----------------------------------------------------------------------
  tier1: 30/30 (100.0%)
  tier2: 34/35 (97.1%)
  tier3: 20/20 (100.0%)
  tier4: 21/21 (100.0%)

======================================================================
OVERALL PASS RATE: 99.1%
======================================================================
```

### Generating Agent Results

Your agent should output values that can be collected into the results JSON:

```javascript
// Example: Running your agent on all tasks
const results = {};
for (const task of tasks) {
  const answer = await myAgent.analyze(task.question);
  results[task.id] = answer.sample_size;  // Extract the numerical answer
}
await writeFile('my-results.json', JSON.stringify(results, null, 2));
```

## 2. LLM-as-Judge (Optional)

Use this when your agent produces unstructured natural language output.

### When to Use

- Agent output is free-text without structured values
- You need diagnostic scoring to debug failures
- You want justifications for why tasks failed

### When NOT to Use

- Agent outputs structured JSON (use simple evaluator)
- You want fast, reproducible evaluation
- You want to avoid API costs

### Usage

```javascript
import { evaluateTask } from './llm-judge.js';

const result = await evaluateTask(task, agentResponse);
console.log(result.passed);       // true/false
console.log(result.agentValue);   // Extracted value
console.log(result.totalScore);   // 0-100 diagnostic score
```

### Environment

```bash
export ANTHROPIC_API_KEY="your-key"
```

### Diagnostic Scoring

The LLM judge provides diagnostic scores (for debugging, not pass/fail):

| Criterion | Points | Purpose |
|-----------|--------|---------|
| Template Selection | 20 | Did agent identify correct method? |
| Parameter Extraction | 20 | Were parameters parsed correctly? |
| Calculation Accuracy | 30 | Is value within tolerance? |
| Code Quality | 15 | Would R code execute? |
| Interpretation | 15 | Are recommendations clear? |

**Important**: Pass/fail is determined by tolerance check, not total score.

## Tolerance Reference

### Ideal Tolerances

| Task Type | Method | Ideal Tolerance | Rationale |
|-----------|--------|-----------------|-----------|
| **Deterministic** | pwr, pwrss, pmsampsize | **±0-2** | Same formula = same answer |
| **Simulation** | simr Monte Carlo | **±3-5%** | Monte Carlo SE ≈ 2% |

### Current Task Tolerances

The `tasks.json` files contain tolerances set during development. Some are more generous:

| Tier | Current | Ideal |
|------|---------|-------|
| Tier 1 (pwr) | 5-35% | ±1-2 subjects |
| Tier 3 (simr) | 8-35% | ±5% power |
| Tier 4 (pmsampsize) | 5% | ±1-2 subjects |

For strict evaluation, see [Evaluation Methodology](../docs/evaluation-methodology.md).

### Task-Level Override

Each task in `tasks.json` specifies its own tolerance:

```json
{
  "id": "t3-simr-002",
  "ground_truth": { "subjects_per_group": 58 },
  "tolerance": { "sample_size": 20 }
}
```

The task-level tolerance takes precedence.

## Integrating with Your Agent

### Option A: Structured Output (Best)

Configure your agent to output structured results:

```python
# In your agent
result = {
    "sample_size_per_group": 64,
    "total_sample_size": 128,
    "method": "pwr.t.test",
    "r_code": "pwr.t.test(d=0.5, power=0.8, sig.level=0.05)"
}
print(json.dumps(result))
```

Then evaluate with simple-evaluator:

```bash
node evaluator/simple-evaluator.js my-results.json
```

### Option B: Regex Extraction

Extract from free-text using patterns:

```javascript
function extractValue(text) {
  const patterns = [
    /sample\s*size[:\s]+(\d+)/i,
    /(\d+)\s*(?:per\s*group|subjects)/i,
    /n\s*[=:]\s*(\d+)/i
  ];
  for (const p of patterns) {
    const m = text.match(p);
    if (m) return parseFloat(m[1]);
  }
  return null;
}
```

### Option C: LLM Extraction (Fallback)

Use llm-judge.js when pattern matching fails:

```javascript
import { evaluateTask } from './llm-judge.js';
const result = await evaluateTask(task, agentOutput);
const value = result.agentValue;
```

## Files

| File | Description |
|------|-------------|
| `simple-evaluator.js` | **Primary** - Value-based evaluation |
| `llm-judge.js` | Optional - LLM extraction + diagnostics |
| `scoring.js` | Aggregate statistics |
| `config.js` | Configuration settings |

## Best Practices

1. **Use structured output** - Avoid LLM extraction overhead
2. **Run simple-evaluator first** - It's fast and deterministic
3. **Use LLM-judge for debugging** - When you need to understand failures
4. **Report pass rate** - The primary metric is % tasks within tolerance
