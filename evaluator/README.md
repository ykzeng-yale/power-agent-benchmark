# Evaluator

LLM-as-Judge evaluation system for the Power Agent Benchmark.

## Overview

The evaluator uses Claude Sonnet as an automated judge to score agent responses against ground truth values. This approach provides nuanced assessment across multiple criteria while maintaining strict tolerance checking for numerical accuracy.

## Components

| File | Description |
|------|-------------|
| `llm-judge.js` | Core LLM evaluation logic |
| `scoring.js` | Aggregate statistics and reporting |
| `config.js` | Configuration settings |

## Evaluation Criteria

The evaluator scores responses on 5 criteria (100 points total):

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Template Selection | 20 | Correct analysis type identified |
| Parameter Extraction | 20 | Parameters correctly parsed from question |
| Calculation Accuracy | 30 | Final answer within tolerance |
| Code Quality | 15 | R code would execute correctly |
| Interpretation | 15 | Results properly explained |

## Tolerance Checking

Strict tolerance enforcement is applied after LLM scoring:

1. **Within Tolerance**: If the agent's value is within the specified tolerance, `calculationAccuracy` is boosted to full score (30/30)
2. **Outside Tolerance**: If outside tolerance, `calculationAccuracy` is forced to 0 and the task fails regardless of total score

### Tolerance Philosophy

- Tolerances are set per-task in `tasks.json`
- Typical tolerances: ±5% for analytical methods, ±8-10% for simulation
- The evaluator extracts the agent's final recommended value (not intermediate calculations)

## Usage

### Evaluate a Single Task

```javascript
import { evaluateTask } from './llm-judge.js';

const result = await evaluateTask(task, agentResponse);
console.log(result.passed);      // true/false
console.log(result.totalScore);  // 0-100
console.log(result.agentValue);  // Extracted value
```

### Batch Evaluation

```javascript
import { batchEvaluate } from './llm-judge.js';

const results = await batchEvaluate(tasks, responses, {
  concurrency: 3,
  useQuickFilter: true
});
```

### Generate Statistics

```javascript
import { computeAggregateStats, generateSummary } from './scoring.js';

const stats = computeAggregateStats(evaluations);
const report = generateSummary(stats);
console.log(report);
```

## Configuration

Key settings in `config.js`:

```javascript
{
  llmJudge: {
    model: 'claude-sonnet-4-20250514',
    maxTokens: 4000,
    temperature: 0,  // Deterministic scoring
  },
  scoring: {
    passingThreshold: 70,  // Minimum score to pass
  }
}
```

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for LLM judge calls

## Output Format

Each evaluation returns:

```json
{
  "taskId": "t1-ttest-001",
  "passed": true,
  "totalScore": 95,
  "scores": {
    "templateSelection": 20,
    "parameterExtraction": 20,
    "calculationAccuracy": 30,
    "codeQuality": 15,
    "interpretationQuality": 10
  },
  "agentValue": 64,
  "withinTolerance": true,
  "justification": "..."
}
```

## Customization

To use a different LLM as judge:

1. Modify `config.js` with new model settings
2. Update the API call in `llm-judge.js`
3. Ensure the prompt format is compatible

## Dependencies

- `@anthropic-ai/sdk`: Anthropic API client
