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

Results are automatically evaluated using the LLM-as-judge approach and saved to `results/`.

## Evaluation Methodology

Tasks are evaluated on **5 criteria** totaling **100 points**:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Template Selection | 20 | Correct statistical method identified for the question |
| Parameter Extraction | 20 | Parameters correctly parsed from the natural language prompt |
| Calculation Accuracy | 30 | Sample size/power within specified tolerance |
| Code Quality | 15 | Valid, executable R code produced |
| Interpretation | 15 | Clear, actionable recommendations with assumptions stated |

**Passing threshold**: 70 points with non-zero calculation accuracy.

### Tolerance Philosophy

- Tolerances are designed to accept valid numerical differences between R packages
- Simulation-based tasks (Tier 3 simr) have wider tolerances (±8% power) for Monte Carlo variance
- All tolerances are tight enough to catch real computational errors
- Task-specific tolerances override tier defaults when needed

See [Evaluation Methodology](docs/evaluation-methodology.md) for detailed scoring rubrics.

## Leaderboard

| Rank | Model | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Overall | Date |
|------|-------|--------|--------|--------|--------|---------|------|
| 1 | Power Agent (Claude Opus 4.5) | 100% | 100% | 100% | 100% | **100%** | 2025-02-06 |

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
