# Contributing to Power Agent Benchmark

Thank you for your interest in contributing to the Power Agent Biostatistics Benchmark! This document provides guidelines for various types of contributions.

## Types of Contributions

### 1. Adding New Tasks

New tasks expand the benchmark's coverage of statistical methods.

**Requirements:**
- Follow the [task schema](docs/task-schema.md)
- Provide R reference code that produces the ground truth
- Validate ground truth with at least 2 methods when possible
- Include appropriate tolerance based on method characteristics
- Document the source (R package vignette, textbook, etc.)

**Process:**
1. Fork the repository
2. Add task to appropriate tier's `tasks.json`
3. Add R validation script to `validation/`
4. Submit PR with:
   - Task JSON
   - Validation script
   - Explanation of tolerance choice

### 2. Ground Truth Corrections

If you find an incorrect ground truth:

**Before submitting:**
1. Verify with R code (provide script)
2. Run at least 500 simulation iterations for simr-based tasks
3. Check if the issue is tolerance vs. actual ground truth error

**Submission:**
1. Open an issue with:
   - Task ID
   - Current ground truth value
   - Proposed correction
   - R code demonstrating the correct value
2. Discussion will determine if correction is needed
3. If approved, submit PR with fix

### 3. Evaluator Improvements

Changes to the evaluation methodology require careful consideration.

**Guidelines:**
- Maintain backward compatibility with existing results
- Document any changes to scoring rubrics
- Add tests for new functionality
- Discuss significant changes in an issue first

### 4. Documentation Improvements

Documentation PRs are always welcome:
- Fixing typos or unclear explanations
- Adding examples
- Improving tier descriptions
- Translating documentation

## Task Quality Standards

### Ground Truth Validation

All ground truths must be:
1. **Reproducible**: R code provided that produces the exact value
2. **Verified**: Cross-checked with at least one alternative method when possible
3. **Documented**: Source clearly stated (package vignette, formula, simulation)

### Tolerance Guidelines

| Task Type | Tolerance Approach |
|-----------|-------------------|
| Analytical (pwr, pwrss) | ±5% or small absolute value |
| Simulation-based (simr) | ±8-10% to account for Monte Carlo variance |
| Prediction models (pmsampsize) | ±5% of sample size |

### Task Difficulty Classification

- **Basic**: Single function call, standard parameters
- **Intermediate**: Multiple steps, parameter derivation needed
- **Advanced**: Complex formulas, simulation, or multi-stage calculations

## Code Style

### JavaScript (Evaluator/Runner)
- Use ESLint with Prettier
- ES6+ syntax (modules, async/await)
- Meaningful variable names
- Comment complex logic

### R (Validation Scripts)
- Follow tidyverse style guide
- Include sessionInfo() output
- Set seeds for reproducibility
- Document package versions

### JSON (Task Files)
- 2-space indentation
- Consistent field ordering
- Escape special characters properly

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/add-new-task`
3. **Make** your changes
4. **Test** locally if applicable
5. **Commit** with clear messages
6. **Push** to your fork
7. **Submit** PR with:
   - Clear description of changes
   - Reference to any related issues
   - Validation evidence (for task changes)

## Review Process

- All PRs require at least one review
- Ground truth changes require R validation verification
- Evaluator changes require test coverage
- Documentation changes can be fast-tracked

## Questions?

- Open an issue for discussion
- Tag with appropriate labels (question, enhancement, bug)

## Code of Conduct

- Be respectful and constructive
- Focus on the technical merits
- Welcome newcomers
- Acknowledge contributions

Thank you for helping improve the Power Agent Benchmark!
