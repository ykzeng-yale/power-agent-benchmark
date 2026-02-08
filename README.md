# Power Agent Biostatistics Benchmark

A comprehensive benchmark for evaluating AI agents on biostatistical power analysis and sample size calculation tasks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tasks: 106](https://img.shields.io/badge/Tasks-106-blue.svg)](tasks/)
[![Tiers: 4](https://img.shields.io/badge/Difficulty%20Tiers-4-green.svg)](docs/tier-descriptions.md)

## Overview

The Power Agent Benchmark evaluates language model agents on their ability to perform statistical power analysis calculations across a comprehensive range of biostatistical study designs. The benchmark covers **106 validated tasks** across **4 difficulty tiers**, from basic t-tests to advanced Riley prediction model sample size calculations.

### Key Features

- **106 R-validated tasks** covering fundamental to advanced statistical methods
- **4 difficulty tiers** with progressive complexity
- **LLM-as-judge evaluation** using Claude for nuanced, multi-criteria scoring
- **Strict tolerance checking** with method-appropriate acceptance ranges
- **Reproducible ground truths** with documented R reference code

### Statistical Methods Covered

| Category | Methods |
|----------|---------|
| **Basic Tests** | Two-sample t-test, paired t-test, ANOVA, proportions, chi-square, correlation |
| **Regression** | Linear regression, logistic regression (OR detection, interactions) |
| **Mixed Models** | Repeated measures, nested designs, growth curves, three-level hierarchies |
| **Survival** | Log-rank, Cox regression, competing risks, cure models, stratified analysis |
| **Count Data** | Poisson regression, negative binomial, zero-inflated, clustered counts |
| **Complex Designs** | Cluster RCT, crossover trials, factorial designs, stepped-wedge |
| **Prediction Models** | Riley binary/survival/continuous development, external validation (pmvalsampsize) |

## Task Distribution

| Tier | Name | Tasks | Focus Areas |
|------|------|-------|-------------|
| 1 | Basic Comparisons | 30 | t-tests, ANOVA, proportions, chi-square, correlation |
| 2 | Regression & Models | 35 | Linear, logistic, mixed effects, survival, Poisson |
| 3 | Advanced Designs | 20 | Cluster RCT, crossover, factorial, simulation-based (simr) |
| 4 | Prediction Models | 21 | Riley criteria (pmsampsize), external validation (pmvalsampsize) |
| **Total** | | **106** | |

## Quick Start

### Installation

```bash
git clone https://github.com/ykzeng-yale/power-agent-benchmark.git
cd power-agent-benchmark
cd runner && npm install
```

### Configuration

Set your API keys in environment variables:

```bash
export ANTHROPIC_API_KEY="your-key"
export POWER_AGENT_API_URL="your-agent-api-endpoint"
```

### Run the Benchmark

```bash
# Run all tiers
node runner/run-benchmark.js

# Run specific tier
node runner/run-benchmark.js --tier=1

# Run with verbose output
node runner/run-benchmark.js --tier=2 --verbose
```

### Evaluate Results

Results are evaluated by **direct numerical comparison** against ground truth values.

## Evaluation Methodology

### Primary Method: Value-Based Comparison

The benchmark uses **direct value comparison** — the same paradigm as MATH, GSM8K, and other quantitative benchmarks:

```
PASS if: |agent_value - ground_truth| ≤ tolerance
```

**We strongly encourage** agents to output structured results for direct evaluation:

```json
{"sample_size_per_group": 64, "power": 0.80}
```

### Tolerance by Task Type

| Task Type | Method | Ideal Tolerance | Rationale |
|-----------|--------|-----------------|-----------|
| **Analytical** | pwr, pwrss, pmsampsize | **±0-2** (exact match) | Closed-form formulas = identical results |
| **Simulation** | simr Monte Carlo | **±3-5%** | Monte Carlo SE ≈ 2% with nsim=500 |

For deterministic tasks, correct R code produces the **exact same answer**. For simulation tasks, tolerance accounts for random sampling variance.

Each task specifies its tolerance in `tasks.json`. See [Evaluation Methodology](docs/evaluation-methodology.md) for details.

### LLM-as-Judge (Optional)

An LLM-based evaluator is provided for:
- Extracting values from unstructured agent output
- Diagnostic scoring when debugging agent behavior

However, **value-based comparison is the primary evaluation method**. LLM judgment is supplementary.

## Leaderboard

| Rank | Model | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Overall | Date |
|------|-------|--------|--------|--------|--------|---------|------|
| 1 | Power Agent (Claude Opus 4.5) | 100% | 100% | 100% | 95.2% | **99.1%** | 2025-02-06 |
| 2 | ChatGPT Thinking Mode (no code exec) | 60.0% | 62.9% | 75.0% | 28.6% | **57.5%** | 2026-02-08 |
| 3 | ChatGPT Auto Mode (no code exec) | 56.7% | 65.7% | 70.0% | 28.6% | **56.6%** | 2026-02-08 |

*Power Agent: 105/106 tasks pass. Single intermittent failure on t4-binary-003 (rare outcome prediction).*
*ChatGPT Thinking: 61/106 tasks pass. Marginal improvement over Auto Mode (+1 task). Same core limitations: z-approximation (9), no R package access (15), wrong formulas (10). [Detailed report](test-results/evaluation/chatgpt-thinking/README.md)*
*ChatGPT Auto: 60/106 tasks pass. Primary failure modes: z-approximation (12), no R package access (15), wrong formulas (10). [Detailed report](test-results/evaluation/chatgpt-auto/README.md)*

*Submit your results via [pull request](leaderboard/README.md).*

## Citation

If you use this benchmark in your research, please cite:

```bibtex
@software{zeng2025poweragent,
  author = {Zeng, Yukang},
  title = {Power Agent Biostatistics Benchmark},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/ykzeng-yale/power-agent-benchmark},
  version = {1.0.0}
}
```

## Documentation

- [Task Schema Specification](docs/task-schema.md) - JSON format for task definitions
- [Evaluation Methodology](docs/evaluation-methodology.md) - Detailed scoring criteria
- [Tier Descriptions](docs/tier-descriptions.md) - Statistical methods by tier
- [Ground Truth Methodology](docs/ground-truth-methodology.md) - How ground truths are validated
- [Submitting Results](leaderboard/README.md) - How to submit to the leaderboard

## Repository Structure

```
power-agent-benchmark/
├── tasks/                    # Task definitions (106 tasks)
│   ├── tier1/               # Basic comparisons (30 tasks)
│   ├── tier2/               # Regression & models (35 tasks)
│   ├── tier3/               # Advanced designs (20 tasks)
│   └── tier4/               # Prediction models (21 tasks)
├── evaluator/               # LLM-as-judge evaluation code
├── runner/                  # Benchmark execution scripts
├── leaderboard/             # Results and submissions
├── docs/                    # Documentation
└── examples/                # Usage examples
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Adding new tasks
- Correcting ground truths
- Improving the evaluator
- Documentation improvements

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Evaluation powered by [Claude](https://www.anthropic.com/) (Anthropic)
- Statistical validation using [R](https://www.r-project.org/) and CRAN packages:
  - [pwr](https://cran.r-project.org/package=pwr) - Basic power analysis
  - [pwrss](https://cran.r-project.org/package=pwrss) - Advanced power/sample size
  - [simr](https://cran.r-project.org/package=simr) - Simulation-based power for mixed models
  - [pmsampsize](https://cran.r-project.org/package=pmsampsize) - Prediction model development
  - [pmvalsampsize](https://cran.r-project.org/package=pmvalsampsize) - External validation
