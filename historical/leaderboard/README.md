# Leaderboard

Current benchmark results and submission guidelines.

## Current Results

| Rank | Agent | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Overall | Date |
|------|-------|--------|--------|--------|--------|---------|------|
| 1 | Power Agent (Claude Opus 4.5) | 30/30 (100%) | 35/35 (100%) | 20/20 (100%) | 21/21 (100%) | **106/106 (100%)** | 2025-01-26 |

## Scoring Breakdown

### Power Agent (Claude Opus 4.5)

| Tier | Tasks | Passed | Pass Rate | Avg Score |
|------|-------|--------|-----------|-----------|
| Tier 1: Basic Comparisons | 30 | 30 | 100% | 97.2 |
| Tier 2: Regression & Models | 35 | 35 | 100% | 95.8 |
| Tier 3: Advanced Designs | 20 | 20 | 100% | 94.1 |
| Tier 4: Prediction Models | 21 | 21 | 100% | 96.5 |
| **Overall** | **106** | **106** | **100%** | **95.9** |

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
