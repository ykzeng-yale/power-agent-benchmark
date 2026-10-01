# Changelog

All notable changes to the Power Agent Biostatistics Benchmark will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-06

### Added
- Initial release with 106 validated tasks across 4 tiers
- **Tier 1**: 30 basic comparison tasks (t-tests, ANOVA, proportions, chi-square, correlation)
- **Tier 2**: 35 regression and model tasks (linear, logistic, mixed effects, survival, Poisson)
- **Tier 3**: 20 advanced design tasks (cluster RCT, crossover, factorial, simr simulation)
- **Tier 4**: 21 prediction model tasks (Riley binary/survival/continuous, external validation)
- LLM-as-judge evaluation using Claude Sonnet
- 5-criterion scoring system (100 points total)
- Strict tolerance checking with method-appropriate ranges
- GitHub-based leaderboard with submission process
- Comprehensive documentation

### Validated
- All ground truths verified with R code
- Tolerances calibrated based on method characteristics
- 100% pass rate achieved with Power Agent baseline

## [Unreleased]

### Planned
- Additional Tier 2 tasks for advanced regression scenarios
- Bayesian power analysis tasks
- Adaptive design sample size calculations
- Multi-language documentation
