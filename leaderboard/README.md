# Leaderboard

Current benchmark results and submission guidelines.

## Current Results

| Rank | Agent | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Overall | Date |
|------|-------|--------|--------|--------|--------|---------|------|
| 1 | Power Agent (Claude Opus 4.5) | 30/30 (100%) | 35/35 (100%) | 20/20 (100%) | 20/21 (95.2%) | **105/106 (99.1%)** | 2026-02-06 |
| 2 | ChatGPT Thinking Mode | 18/30 (60.0%) | 22/35 (62.9%) | 15/20 (75.0%) | 6/21 (28.6%) | **61/106 (57.5%)** | 2026-02-08 |
| 3 | ChatGPT Auto Mode | 17/30 (56.7%) | 23/35 (65.7%) | 14/20 (70.0%) | 6/21 (28.6%) | **60/106 (56.6%)** | 2026-02-08 |

See [results.json](results.json) for machine-readable results with detailed failure breakdowns.

## Scoring Breakdown

### Power Agent (Claude Opus 4.5)

| Tier | Tasks | Passed | Pass Rate |
|------|-------|--------|-----------|
| Tier 1: Basic Comparisons | 30 | 30 | 100% |
| Tier 2: Regression & Models | 35 | 35 | 100% |
| Tier 3: Advanced Designs | 20 | 20 | 100% |
| Tier 4: Prediction Models | 21 | 20 | 95.2% |
| **Overall** | **106** | **105** | **99.1%** |

*Single intermittent failure on t4-binary-003 (rare outcome prediction). Task passes on retry.*

## How to Submit

1. **Fork this repository**

2. **Run the benchmark**
   ```bash
   cd runner
   npm install
   node run-benchmark.js
   ```

3. **Create submission file**

   Copy `submissions/template.json` and fill in your results:
   ```bash
   cp submissions/template.json submissions/your-agent-name.json
   ```

4. **Submit Pull Request**

   Include:
   - Your completed submission JSON
   - Results JSON from `results/` directory
   - Brief description of your agent

## Submission Requirements

### Required Information

- **Agent Name**: Unique identifier for your agent
- **Model**: Base LLM used (if applicable)
- **Date**: Benchmark run date
- **Results**: Per-tier pass counts and scores

### Verification

Submissions are verified by:
1. Checking JSON format against schema
2. Spot-checking suspicious results
3. Optional: Independent rerun on sample tasks

### Rules

- Results must be from a single continuous run
- No manual intervention during benchmark
- Agent must answer all tasks (no cherry-picking)
- Report honest results (including failures)

## Submission Template

See `submissions/template.json` for the required format.

## Metrics Explained

### Pass Rate

A task passes if:
1. Total score >= 70/100
2. Calculation accuracy > 0 (within tolerance)

### Average Score

Mean of all task scores (0-100), weighted equally.

### Per-Tier Breakdown

- **Tier 1**: Basic tests (t-test, ANOVA, proportions, chi-square, correlation)
- **Tier 2**: Regression models (linear, logistic, mixed, survival, Poisson)
- **Tier 3**: Complex designs (cluster RCT, crossover, factorial, simr)
- **Tier 4**: Prediction models (Riley criteria, external validation)

## Historical Results

Results are archived in `results.json` with timestamps for tracking progress over time.

## Questions?

Open an issue if you have questions about:
- Benchmark methodology
- Submission process
- Disputed results
