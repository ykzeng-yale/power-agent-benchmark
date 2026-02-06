# Tier 3: Advanced Designs

## Overview

Tier 3 contains **20 tasks** covering complex real-world trial designs requiring specialized methods, often simulation-based.

## Task Categories

| Category | Count | Methods | Description |
|----------|-------|---------|-------------|
| Cluster RCT | 5 | Design effect, simulation | Cluster-randomized trials |
| Crossover trials | 4 | pwr (paired), adjusted d | AB/BA and Latin square designs |
| Factorial designs | 4 | pwr, simulation | 2×2, 2×2×2, interaction effects |
| Simulation-based | 7 | simr | Complex mixed models |

## Difficulty Distribution

- **Intermediate**: 8 tasks
- **Advanced**: 12 tasks

All Tier 3 tasks require advanced statistical knowledge.

## Key Concepts

1. **Cluster Randomization**
   - Design Effect: DE = 1 + (m-1) × ICC
   - Effective sample size: N_eff = N / DE
   - Cluster size vs number trade-offs

2. **Crossover Efficiency**
   - Within-subject correlation reduces variance
   - Adjusted effect: d_paired = d / √(2(1-ρ))
   - Carryover effects and washout periods

3. **Factorial Interactions**
   - Main effect power vs interaction power
   - Interaction f² = d²/16 (NOT d²/4!)
   - Requires larger samples than main effects

4. **simr Simulation**
   - Create model with makeLmer/makeGlmer
   - Extend along dimension of interest
   - powerCurve for sample size determination
   - Watch for VarCorr ordering with nested effects

## Example Tasks

### t3-cluster-001 (Intermediate)
> Cluster RCT: 20 clusters/arm. Find subjects per cluster for 80% power.

**Ground Truth**: 7 subjects per cluster

### t3-simr-002 (Advanced)
> Binary GLMM with random intercepts. Find n for 80% power.

**Ground Truth**: 60-70 per group

### t3-fact-002 (Advanced)
> 2×2 factorial to detect interaction. Main effect d=0.5, interaction d=0.4.

**Ground Truth**: 350 per cell

## Tolerance

Tier 3 tolerances are wider for simulation tasks:
- Analytical methods: ±5-10%
- simr simulation: ±8-10% power (Monte Carlo variance)
- Accept wider ranges when simulation is the only option
