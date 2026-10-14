# Tier 3 — Advanced Designs (cluster RCT, crossover, factorial, simr)

## Results: 14/20 PASS (70.0%)

| Task ID | Result | Extracted Value | Ground Truth | Tolerance | Diff | Root Cause |
|---------|--------|-----------------|--------------|-----------|------|------------|
| t3-cluster-001 | **PASS** | total_subjects=280 | 280 | ±1 | 0.0 | — |
| t3-cluster-002 | **PASS** | detectable_effect_d=0.35 | 0.35 | ±5 | 0.0 | — |
| t3-cluster-003 | **PASS** | power=0.95 | 0.94 | ±0.05 | 0.0 | — |
| t3-cluster-004 | **FAIL** | total_subjects=1128 | 1152 | ±3 | 24.0 | Wrong formula or major computation error |
| t3-cluster-005 | **FAIL** | subjects_per_cluster_period=29 | 7 | ±5 | 22.0 | Specialized design knowledge gap |
| t3-cross-001 | **PASS** | subjects=20 | 21 | ±1 | 1.0 | — |
| t3-cross-002 | **FAIL** | subjects=117 | 119 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t3-cross-003 | **FAIL** | subjects=40 | 42 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t3-cross-004 | **FAIL** | subjects=74 | 76 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t3-fact-001 | **PASS** | total_sample_size=200 | 200 | ±2 | 0.0 | — |
| t3-fact-002 | **PASS** | total_sample_size=1396 | 1400 | ±5 | 4.0 | — |
| t3-fact-003 | **PASS** | total_sample_size=132 | 132 | ±1 | 0.0 | — |
| t3-fact-004 | **PASS** | power=0.931 | 0.93 | ±0.03 | 0.0 | — |
| t3-simr-001 | **PASS** | subjects_per_group=53 | 50 | ±15 | 3.0 | — |
| t3-simr-002 | **PASS** | subjects_per_group=54 | 58 | ±20 | 4.0 | — |
| t3-simr-003 | **PASS** | power=0.3 | 0.32 | ±0.12 | 0.0 | — |
| t3-simr-004 | **PASS** | power=0.59 | 0.6 | ±0.08 | 0.0 | — |
| t3-simr-005 | **FAIL** | power=0.32 | 0.58 | ±0.08 | 0.3 | Task requires Monte Carlo simulation |
| t3-simr-006 | **PASS** | subjects_per_group=50 | 55 | ±15 | 5.0 | — |
| t3-simr-007 | **PASS** | power=0.8 | 0.82 | ±0.1 | 0.0 | — |

---

## Detailed Per-Task Judgments

### ✅ t3-cluster-001

**Question:** We're planning a cluster randomized trial with 20 clinics per arm. Based on pilot data, the ICC is about 0.05 and we expect a treatment effect of d = 0.4. How many patients do we need per clinic to ac...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_subjects | 280 | 280 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t3-cluster-002

**Question:** We're designing a school-based intervention with 15 schools per arm, averaging 30 students per school. The ICC is estimated at 0.08. What is the minimum detectable effect size (Cohen's d) with 80% pow...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_clusters_per_arm | 15 | 15 | ±5 | 0.00 |
| given_subjects_per_cluster | 30 | 30 | ±5 | 0.00 |
| given_total_subjects | 900 | 900 | ±5 | 0.00 |
| detectable_effect_d | 0.35 | 0.35 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t3-cluster-003

**Question:** Our cluster RCT will have variable cluster sizes (CV = 0.4 in cluster sizes). We have 25 clusters per arm with a mean of 20 subjects per cluster. With ICC = 0.03 and effect size d = 0.3, what power do...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_clusters_per_arm | 25 | 25 | ±5 | 0.00 |
| given_mean_cluster_size | 20 | 20 | ±5 | 0.00 |
| cv_cluster_size | 0.4 | 0.4 | ±5 | 0.00 |
| given_total_subjects | 1000 | 1000 | ±5 | 0.00 |
| power | 0.95 | 0.94 | ±0.05 | 0.01 |

### ❌ t3-cluster-004

**Question:** We're running a cluster trial with a binary outcome: 30% response in control, 20% expected in treatment. We have 12 clinics per arm and the ICC is 0.02. How many patients per clinic for 80% power at a...

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_subjects | 1128 | 1152 | ±3 | 24.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| control_rate | 0.3 | 0.3 |
| power | 0.8 | 0.8 |

### ❌ t3-cluster-005

**Question:** We're designing a stepped-wedge trial with 6 clusters over 4 time periods. Two clusters switch to treatment each period. Within-period ICC is 0.05, between-period correlation is 0.025. We want to dete...

**Result: FAIL**
**Root Cause:** Specialized design knowledge gap

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects_per_cluster_period | 29 | 7 | ±5 | 22.00 | value_incorrect |
| total_subjects | 696 | 168 | ±1 | 528.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| clusters | 6 | 6 |
| periods | 4 | 4 |
| switches_per_period | 2 | 2 |
| power | 0.8 | 0.8 |

### ✅ t3-cross-001

**Question:** I'm planning a 2x2 crossover trial where the between-subject effect size is d = 0.5 and the within-subject correlation is 0.7. How many subjects total do I need for 80% power at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects | 20 | 21 | ±1 | 1.00 |
| periods | 2 | 2 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ❌ t3-cross-002

**Question:** I'm planning a simple 2-period crossover trial (AB/BA design) to compare two treatments. I expect a standardized within-subject effect of d = 0.3 (the treatment difference divided by within-subject SD...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects | 117 | 119 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| periods | 2 | 2 |
| power | 0.9 | 0.9 |

### ❌ t3-cross-003

**Question:** I'm designing a 3-treatment Latin square crossover study. The primary comparison is treatment A vs control, with expected effect d = 0.4 and period-to-period correlation of 0.6. How many subjects for ...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects | 40 | 42 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| treatments | 3 | 3 |
| periods | 3 | 3 |
| period_correlation | 0.6 | 0.6 |
| power | 0.8 | 0.8 |

### ❌ t3-cross-004

**Question:** We're designing a 4-period replicate crossover study (ABAB/BABA) for a bioequivalence trial. The treatment effect is d = 0.35 (where d = mean difference divided by within-subject SD). How many subject...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects | 74 | 76 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| periods | 4 | 4 |
| within_subject_sd | 1 | 1 |
| power | 0.85 | 0.85 |

### ✅ t3-fact-001

**Question:** We're running a 2×2 factorial trial where we want to detect a main effect of one factor with d = 0.4. We need 80% power at per-comparison alpha = 0.05 (no multiplicity adjustment). How many subjects p...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 200 | 200 | ±2 | 0.00 |
| per_cell | 50 | 50 | ±5 | 0.00 |
| factors | 2 | 2 | ±5 | 0.00 |
| levels_per_factor | 2 | 2 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t3-fact-002

**Question:** In our 2×2 factorial, the main effects are d = 0.5 but we're primarily interested in detecting the interaction (d = 0.3). How many per cell for 80% power on the interaction at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 1396 | 1400 | ±5 | 4.00 |
| per_cell | 349 | 350 | ±5 | 1.00 |
| main_effect_d | 0.5 | 0.5 | ±5 | 0.00 |
| interaction_d | 0.3 | 0.3 | ±5 | 0.00 |
| power_interaction | 0.8 | 0.8 | ±5 | 0.00 |

### ✅ t3-fact-003

**Question:** We have a 3×2 factorial design (3 doses × 2 formulations) and want to test the linear dose-response trend (effect size f = 0.25). How many total subjects for 80% power at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 132 | 132 | ±1 | 0.00 |
| per_cell | 22 | 22 | ±5 | 0.00 |
| dose_levels | 3 | 3 | ±5 | 0.00 |
| formulations | 2 | 2 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t3-fact-004

**Question:** We're running a 2^4 fractional factorial (resolution IV, 8 runs) with 3 replicates per run. The standardized main effect is delta = 1.5 (in sigma units). What power do we have for detecting main effec...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| runs | 8 | 8 | ±5 | 0.00 |
| replicates_per_run | 3 | 3 | ±5 | 0.00 |
| total_observations | 24 | 24 | ±5 | 0.00 |
| factors | 4 | 4 | ±5 | 0.00 |
| standardized_effect | 1.5 | 1.5 | ±5 | 0.00 |
| power | 0.931 | 0.93 | ±0.03 | 0.00 |

### ✅ t3-simr-001

**Question:** I'm planning a mixed-effects study with 5 measurements per subject. The treatment effect is 0.5 units, random intercept SD is 0.8, and residual SD is 1.0. How many subjects per group do I need for 80%...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 53 | 50 | ±15 | 3.00 |
| total_subjects | 106 | 100 | ±15 | 6.00 |
| measurements_per_subject | 5 | 5 | ±5 | 0.00 |
| fixed_effect | 0.5 | 0.5 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.08 | 0.00 |

### ✅ t3-simr-002

**Question:** I'm powering a study with a binary outcome analyzed using a mixed-effects logistic model. Each subject provides 3 observations, the treatment OR is 2.0, baseline probability is 30%, and the random int...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 54 | 58 | ±20 | 4.00 |
| total_subjects | 108 | 116 | ±20 | 8.00 |
| observations_per_subject | 3 | 3 | ±5 | 0.00 |
| treatment_or | 2 | 2 | ±5 | 0.00 |
| baseline_prob | 0.3 | 0.3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.08 | 0.00 |

### ✅ t3-simr-003

**Question:** I have a random slopes model with 6 time points (0-5). I want to detect a slope difference of 0.1 per time unit between groups. Random intercept SD = 1.0, random slope SD = 0.2, residual SD = 1.0. Wit...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_subjects_per_group | 40 | 40 | ±5 | 0.00 |
| time_points | 6 | 6 | ±5 | 0.00 |
| power | 0.3 | 0.32 | ±0.12 | 0.02 |

### ✅ t3-simr-004

**Question:** We have a three-level educational study: students in classrooms in schools. Per arm: 10 schools, 4 classrooms per school, 25 students per classroom. Effect size d = 0.3, school variance = 0.05, classr...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_schools_per_arm | 10 | 10 | ±5 | 0.00 |
| given_classrooms_per_school | 4 | 4 | ±5 | 0.00 |
| given_students_per_classroom | 25 | 25 | ±5 | 0.00 |
| given_total_students | 2000 | 2000 | ±5 | 0.00 |
| school_icc | 0.05 | 0.05 | ±5 | 0.00 |
| classroom_icc | 0.1 | 0.1 | ±5 | 0.00 |
| power | 0.59 | 0.6 | ±0.08 | 0.01 |

### ❌ t3-simr-005

**Question:** I'm analyzing clustered survival data with gamma frailty. We have 20 clusters per arm, 15 subjects per cluster, frailty variance = 0.5. We want to detect HR = 0.7 over 2-year follow-up (baseline 2-yea...

**Result: FAIL**
**Root Cause:** Task requires Monte Carlo simulation

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| power | 0.32 | 0.58 | ±0.08 | 0.26 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| given_clusters_per_arm | 20 | 20 |
| given_subjects_per_cluster | 15 | 15 |
| given_total_subjects | 600 | 600 |
| frailty_variance | 0.5 | 0.5 |

### ✅ t3-simr-006

**Question:** I'm analyzing a multivariate mixed model with 2 correlated outcomes (r = 0.6). Treatment effect is 0.4 on the primary outcome and 0.3 on secondary. Each subject has 4 timepoints, random intercept SD =...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 50 | 55 | ±15 | 5.00 |
| total_subjects | 100 | 110 | ±15 | 10.00 |
| outcomes | 2 | 2 | ±5 | 0.00 |
| outcome_correlation | 0.6 | 0.6 | ±5 | 0.00 |
| primary_effect | 0.4 | 0.4 | ±5 | 0.00 |
| secondary_effect | 0.3 | 0.3 | ±5 | 0.00 |
| timepoints | 4 | 4 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.08 | 0.00 |

### ✅ t3-simr-007

**Question:** In our cluster trial, we have 15 clusters per arm with 20 subjects each, measured at 4 time points (0,1,2,3). The treatment effect on the slope is 0.15 per time unit. Random intercept SD = 0.5, random...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_clusters_per_arm | 15 | 15 | ±5 | 0.00 |
| given_subjects_per_cluster | 20 | 20 | ±5 | 0.00 |
| given_total_subjects | 600 | 600 | ±5 | 0.00 |
| time_points | 4 | 4 | ±5 | 0.00 |
| slope_effect | 0.15 | 0.15 | ±5 | 0.00 |
| power | 0.8 | 0.82 | ±0.1 | 0.02 |

