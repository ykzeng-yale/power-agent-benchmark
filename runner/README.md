# Benchmark Runner

Automated benchmark execution system for evaluating power analysis agents.

## Overview

The runner orchestrates:
1. Loading tasks from JSON files
2. Sending queries to the agent API
3. Collecting responses via Server-Sent Events (SSE)
4. Invoking the LLM evaluator
5. Aggregating and saving results

## Quick Start

```bash
# Install dependencies
npm install

# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export POWER_AGENT_API_URL="https://your-agent-api.com"

# Run all tiers
node run-benchmark.js

# Run specific tier
node run-benchmark.js --tier=1

# Run with options
node run-benchmark.js --tier=2 --concurrency=3 --verbose
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--tier=N` | Run only tier N (1-4) | All tiers |
| `--concurrency=N` | Parallel task execution | 2 |
| `--verbose` or `-v` | Detailed output | false |

## Configuration

The runner uses these environment variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (with defaults)
POWER_AGENT_API_URL=https://your-api.com
```

## Agent API Requirements

Your agent API must:

1. Accept POST requests to `/api/analyze-biostat`
2. Request body: `{ "query": "...", "mode": "full_analysis", "sessionId": "..." }`
3. Return Server-Sent Events (SSE) stream with analysis steps

### Expected SSE Events

```
data: {"step": "chatbot_intro_stream", "text": "..."}
data: {"step": "executing", "output": "..."}
data: {"step": "chatbot_conclusion_stream", "text": "..."}
data: {"step": "outputs", "files": [...]}
```

## Output

Results are saved to `results/benchmark_{timestamp}.json`:

```json
{
  "runId": "benchmark_1706789012345",
  "timestamp": "2026-02-01T12:00:00.000Z",
  "tiers": [
    {
      "tier": 1,
      "results": [...],
      "evaluations": [...],
      "passed": 28,
      "avgScore": 94.2,
      "duration": 120000
    }
  ],
  "summary": {
    "totalPassed": 100,
    "totalTasks": 106,
    "avgScore": 92.5
  }
}
```

## Console Output

```
╔══════════════════════════════════════════════════════════════════════╗
║           POWER AGENT BENCHMARK EVALUATION                           ║
╚══════════════════════════════════════════════════════════════════════╝

API: https://power-agent-api.com
Tiers: 1, 2, 3, 4
Concurrency: 2

══════════════════════════════════════════════════════════════════════
TIER 1: Basic Comparisons
══════════════════════════════════════════════════════════════════════
Tasks: 30, Concurrency: 2
──────────────────────────────────────────────────────────────────────

Batch 1: Tasks 1-2
  [1] Starting: t1-ttest-001
  [2] Starting: t1-ttest-002
  [1] Completed: t1-ttest-001 (15.2s, 12 steps)
  [2] Completed: t1-ttest-002 (14.8s, 11 steps)
  Evaluating batch...
    ✓ t1-ttest-001: 95/100 val=64
    ✓ t1-ttest-002: 100/100 val=86
```

## Retry Logic

The runner includes automatic retry for:
- HTTP 529 (API overloaded)
- HTTP 503 (Service unavailable)
- Empty responses (agent timeout)

Retry strategy: Exponential backoff (10s, 20s, 40s)

## Customization

### Custom Agent Adapter

To test a different agent implementation, modify `runTask()`:

```javascript
async function runTask(task, taskIndex, verbose = false) {
  // Your custom agent call here
  const response = await yourAgent.analyze(task.question);

  return {
    taskId: task.id,
    success: true,
    response: {
      introText: response.intro,
      analysisOutput: response.analysis,
      conclusionText: response.conclusion
    }
  };
}
```

## Dependencies

See `package.json` for required packages.
