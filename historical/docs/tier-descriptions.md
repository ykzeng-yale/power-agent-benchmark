# Tier Descriptions

This document provides detailed descriptions of each benchmark tier, including statistical methods covered, key concepts tested, and example tasks.

## Tier 1: Basic Comparisons (30 tasks)

### Overview

Tier 1 covers fundamental power analysis methods with closed-form analytical solutions. These are the building blocks of biostatistical power analysis that every practitioner should master.

### Categories

| Category | Tasks | R Package | Key Parameters |
|----------|-------|-----------|----------------|
| Two-sample t-test | 6 | pwr | Cohen's d, power, alpha |
| Paired t-test | 4 | pwr | Cohen's d, power, alpha |
| One-way ANOVA | 5 | pwr | Cohen's f, k groups, power |
| Two proportions | 5 | pwr | p1, p2, power, alpha |
| Chi-square | 5 | pwr | Cohen's w, df, power |
| Correlation | 5 | pwr | r, power, alpha |

### Key Concepts Tested

1. **Effect size interpretation**
   - Cohen's d for means (0.2 small, 0.5 medium, 0.8 large)
   - Cohen's f for ANOVA
   - Cohen's w for chi-square
   - Cohen's h for proportions

2. **Power vs sample size trade-offs**
   - Higher power requires larger samples
   - Smaller effects require larger samples

3. **One-sided vs two-sided tests**
   - One-sided: directional hypothesis
   - Two-sided: non-directional (more common)

4. **Alpha level adjustments**
   - Standard 0.05
   - More conservative 0.01 or 0.025

### Example Tasks

**t1-ttest-001** (Basic)
> Detect medium effect (d=0.5) with 80% power at alpha=0.05.
- Expected: 64 per group
- Method: `pwr.t.test(d=0.5, power=0.80, sig.level=0.05)`

**t1-anova-003** (Intermediate)
> Compare 4 treatment groups, detect f=0.3, 85% power.
- Expected: 37 per group
- Method: `pwr.anova.test(k=4, f=0.3, power=0.85)`

---

## Tier 2: Regression & Models (35 tasks)

### Overview

Tier 2 covers more complex statistical models requiring variance decomposition, formula-based calculations, and sometimes simulation for validation.

### Categories

| Category | Tasks | R Package | Key Parameters |
|----------|-------|-----------|----------------|
| Linear regression | 6 | pwr | f², R², predictors |
| Logistic regression | 6 | pwrss | OR, baseline risk, prevalence |
| Mixed effects (LMM) | 8 | pwr/simr | ICC, measurements, design effect |
| Survival analysis | 8 | various | HR, event rate, follow-up |
| Poisson regression | 7 | pwrss | Rate ratio, baseline rate |

### Key Concepts Tested

1. **F² effect size for regression**
   - f² = R² / (1 - R²)
   - Incremental f² for adding predictors

2. **Variance Reduction Factor (VRF)**
   - For repeated measures: VRF = (1 + (m-1)×ICC) / m
   - Reduces required sample size

3. **Design Effect**
   - For clustered data: DE = 1 + (m-1)×ICC
   - Inflates required sample size

4. **Schoenfeld formula for survival**
   - Events = 4×(z_α/2 + z_β)² / log(HR)²
   - Convert events to sample size via event rate

5. **Odds ratio to probability conversion**
   - p1 = OR×p0 / (1 + (OR-1)×p0)

### Example Tasks

**t2-linreg-003** (Intermediate)
> Test if adding 3 predictors improves R² from 0.20 to 0.30.
- Expected: 85 subjects
- Method: Incremental f² = ΔR²/(1-R²_full)

**t2-mixed-005** (Advanced)
> Three-level model: sites/patients/measurements. What power?
- Expected: 58% power
- Method: simr simulation with correct variance structure

---

## Tier 3: Advanced Designs (20 tasks)

### Overview

Tier 3 covers complex real-world trial designs that require specialized methods, often simulation-based, to determine sample size or power.

### Categories

| Category | Tasks | R Package | Key Parameters |
|----------|-------|-----------|----------------|
| Cluster RCT | 5 | various | ICC, clusters, cluster size |
| Crossover trials | 4 | pwr | Within-subject correlation |
| Factorial designs | 4 | pwr/simulation | Main effects, interactions |
| Simulation-based | 7 | simr | Mixed models, complex structures |

### Key Concepts Tested

1. **Cluster randomization**
   - Design effect inflates sample size
   - ICC determines cluster correlation
   - Optimal cluster size vs number trade-offs

2. **Crossover efficiency**
   - Within-subject correlation reduces variance
   - d_paired = d / sqrt(2×(1-ρ))

3. **Factorial interaction power**
   - Interaction effect size: f² = d²/16 (NOT d²/4!)
   - Usually requires larger samples than main effects

4. **Simulation with simr**
   - Create model at pilot size
   - Extend along dimension of interest
   - Use powerCurve for sample size determination

### Example Tasks

**t3-cluster-002** (Intermediate)
> Cluster RCT with 20 clusters/arm, ICC=0.05. What power?
- Expected: 34.2% power
- Method: Design effect calculation

**t3-simr-001** (Advanced)
> Mixed model with random intercepts. Find n for 80% power.
- Expected: 50 subjects per group
- Method: simr powerCurve with extend

---

## Tier 4: Prediction Models (21 tasks)

### Overview

Tier 4 focuses on sample size for developing and validating clinical prediction models using Riley criteria (pmsampsize) and external validation (pmvalsampsize).

### Categories

| Category | Tasks | R Package | Key Parameters |
|----------|-------|-----------|----------------|
| Riley binary | 5 | pmsampsize | Predictors, prevalence, C-statistic/R² |
| Riley survival | 5 | pmsampsize | Event rate, predictors, timepoint |
| Riley continuous | 4 | pmsampsize | Predictors, R², intercept, SD |
| External validation | 7 | pmvalsampsize | C-statistic, CI widths, LP distribution |

### Key Concepts Tested

1. **Riley criteria for development**
   - Events per predictor (EPP) ≥ 10-15
   - Target shrinkage ≤ 10% (or 5% for conservative)
   - Margin of error in intercept

2. **C-statistic and R² relationship**
   - Can convert between using formulas
   - Cox-Snell vs Nagelkerke R²

3. **Precision-based validation sample size**
   - CI width for C-statistic
   - CI width for calibration slope
   - CI width for O/E ratio
   - Binding constraint determines final N

4. **Linear predictor distributions**
   - Normal: lpnormal(mean, SD)
   - Beta: lpbeta(alpha, beta)
   - SD not variance for lpnormal!

### Example Tasks

**t4-binary-003** (Intermediate)
> Rare outcome (5% prevalence), 12 predictors, C=0.80.
- Expected: 1679 subjects
- Method: `pmsampsize(type='b', prevalence=0.05, cstatistic=0.80, parameters=12)`

**t4-valid-001** (Basic)
> External validation with lpnormal(-1.75, 2.16), C=0.82.
- Expected: 1832 subjects
- Method: pmvalsampsize with calibration slope binding

---

## Difficulty Progression

### Basic Tasks
- Single function call
- Standard parameters explicitly stated
- Clear, unambiguous questions

### Intermediate Tasks
- Multiple calculation steps
- Parameter derivation required
- Some domain knowledge needed

### Advanced Tasks
- Complex formulas or simulation
- Multiple valid approaches
- Careful interpretation required

---

## R Package Summary

| Package | Purpose | Tiers |
|---------|---------|-------|
| pwr | Basic power analysis (closed-form) | 1, 2, 3 |
| pwrss | Advanced power with variance correction | 2 |
| simr | Simulation-based for mixed models | 2, 3 |
| survival | Survival analysis (Schoenfeld) | 2 |
| pmsampsize | Riley prediction model development | 4 |
| pmvalsampsize | External validation sample size | 4 |
| lme4 | Mixed model fitting (with simr) | 2, 3 |
