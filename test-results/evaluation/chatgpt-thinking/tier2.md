# Tier 2 — Regression & Models (linear, logistic, mixed effects, survival, Poisson)

**Model:** ChatGPT Thinking Mode (GPT with extended thinking, no code execution)

## Results: 22/35 PASS (62.9%)

| Task ID | Result | Extracted Value | Ground Truth | Tolerance | Diff | Root Cause |
|---------|--------|-----------------|--------------|-----------|------|------------|
| t2-linreg-001 | **FAIL** | sample_size=127 | 122 | ±1 | 5.0 | Close answer but outside strict tolerance |
| t2-linreg-002 | **FAIL** | sample_size=66 | 62 | ±1 | 4.0 | Close answer but outside strict tolerance |
| t2-linreg-003 | **PASS** | sample_size=85 | 85 | ±1 | 0.0 | — |
| t2-linreg-004 | **PASS** | sample_size=174 | 174 | ±1 | 0.0 | — |
| t2-linreg-005 | **FAIL** | sample_size=210 | 208 | ±1 | 2.0 | Close answer but outside strict tolerance |
| t2-linreg-006 | **PASS** | sample_size=688 | 688 | ±1 | 0.0 | — |
| t2-logreg-001 | **PASS** | sample_size=344 | 347 | ±10 | 3.0 | — |
| t2-logreg-002 | **FAIL** | sample_size=505 | 522 | ±10 | 17.0 | Wrong formula or major computation error |
| t2-logreg-003 | **PASS** | sample_size=196 | 204 | ±10 | 8.0 | — |
| t2-logreg-004 | **PASS** | sample_size=996 | 999 | ±15 | 3.0 | — |
| t2-logreg-005 | **PASS** | sample_size=606 | 610 | ±15 | 4.0 | — |
| t2-logreg-006 | **FAIL** | sample_size=1330 | 319 | ±16 | 1011.0 | Wrong statistical method for logistic regression |
| t2-mixed-001 | **PASS** | subjects_per_group=40 | 40 | ±2 | 0.0 | — |
| t2-mixed-002 | **FAIL** | subjects_per_group=63 | 80 | ±5 | 17.0 | Wrong formula or major computation error |
| t2-mixed-003 | **PASS** | subjects_per_group=86 | 87 | ±3 | 1.0 | — |
| t2-mixed-004 | **FAIL** | patients_per_cluster=750 | 150 | ±50 | 600.0 | Wrong formula or major computation error |
| t2-mixed-005 | **PASS** | power=0.59 | 0.58 | ±0.08 | 0.0 | — |
| t2-mixed-006 | **FAIL** | total_subjects=360 | 380 | ±18 | 20.0 | Wrong formula or major computation error |
| t2-mixed-007 | **PASS** | subjects=17 | 17 | ±1 | 0.0 | — |
| t2-mixed-008 | **PASS** | subjects_per_group=66 | 67 | ±3 | 1.0 | — |
| t2-poisson-001 | **PASS** | subjects_per_group=40 | 40 | ±2 | 0.0 | — |
| t2-poisson-002 | **PASS** | subjects_per_group=27 | 27 | ±1 | 0.0 | — |
| t2-poisson-003 | **PASS** | subjects_per_group=229 | 230 | ±23 | 1.0 | — |
| t2-poisson-004 | **PASS** | subjects_per_group=50 | 50 | ±5 | 0.0 | — |
| t2-poisson-005 | **FAIL** | subjects_per_group=100 | 150 | ±15 | 50.0 | Task requires Monte Carlo simulation |
| t2-poisson-006 | **PASS** | subjects_per_group=103 | 103 | ±5 | 0.0 | — |
| t2-poisson-007 | **PASS** | power=0.9999 | 0.99 | ±0.03 | 0.0 | — |
| t2-surv-001 | **PASS** | subjects_per_arm=198 | 198 | ±5 | 0.0 | — |
| t2-surv-002 | **PASS** | subjects_per_arm=200 | 201 | ±5 | 1.0 | — |
| t2-surv-003 | **PASS** | sample_size=460 | 460 | ±5 | 0.0 | — |
| t2-surv-004 | **PASS** | subjects_per_arm=656 | 657 | ±10 | 1.0 | — |
| t2-surv-005 | **FAIL** | total_subjects=603 | 361 | ±10 | 242.0 | Survival analysis formula error |
| t2-surv-006 | **FAIL** | total_subjects=280 | 300 | ±15 | 20.0 | Survival analysis formula error |
| t2-surv-007 | **FAIL** | subjects_per_arm=485 | 474 | ±10 | 11.0 | Wrong formula or major computation error |
| t2-surv-008 | **FAIL** | subjects_per_arm=529 | 475 | ±10 | 54.0 | Survival analysis formula error |

---

## Detailed Per-Task Judgments

### ❌ t2-linreg-001

**Question:** I'm planning a study where I'll use multiple regression with 5 predictors to predict patient outcomes. I want to be able to detect if these predictors together explain at least 10% of the variance in ...

**Result: FAIL**
**Root Cause:** Close answer but outside strict tolerance

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 127 | 122 | ±1 | 5.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.8 | 0.8 |

### ❌ t2-linreg-002

**Question:** I want to test whether a single biomarker predicts disease severity. If the biomarker explains about 15% of the variance in severity scores, how many patients do I need to detect this with 90% power a...

**Result: FAIL**
**Root Cause:** Close answer but outside strict tolerance

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 66 | 62 | ±1 | 4.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.9 | 0.9 |

### ✅ t2-linreg-003

**Question:** I have a regression model with 4 predictors that explains 20% of the variance in patient recovery time. I want to test whether adding 3 new genetic markers improves the model to explain 30% of the var...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 85 | 85 | ±1 | 0.00 |
| r2_full | 0.3 | 0.3 | ±5 | 0.00 |
| r2_reduced | 0.2 | 0.2 | ±5 | 0.00 |
| predictors_tested | 3 | 3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-linreg-004

**Question:** We're building a prediction model with 10 predictors. We want to detect a medium effect size (Cohen's f² = 0.15) with 85% power at a more stringent alpha = 0.01. What sample size do we need?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 174 | 174 | ±1 | 0.00 |
| f2 | 0.15 | 0.15 | ±5 | 0.00 |
| power | 0.85 | 0.85 | ±0.03 | 0.00 |

### ❌ t2-linreg-005

**Question:** In my regression model with 8 predictors, I want to test whether one specific predictor contributes meaningfully. I expect this predictor to explain an additional 5% of variance (partial f² ≈ 0.053). ...

**Result: FAIL**
**Root Cause:** Close answer but outside strict tolerance

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 210 | 208 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| f2 | 0.053 | 0.053 |
| power | 0.9 | 0.9 |

### ✅ t2-linreg-006

**Question:** We're conducting a large epidemiological study with 15 risk factors as predictors. We expect only a small effect (R² around 5%) since these are observational data. What sample size do we need for 95% ...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 688 | 688 | ±1 | 0.00 |
| power | 0.95 | 0.95 | ±0.03 | 0.00 |

### ✅ t2-logreg-001

**Question:** I'm analyzing whether a binary exposure (present in 50% of patients) predicts disease. The outcome rate is 20% in unexposed patients, and I expect an odds ratio of 2.0 for exposed vs unexposed. How ma...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 344 | 347 | ±10 | 3.00 |
| odds_ratio | 2 | 2 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ❌ t2-logreg-002

**Question:** In our case-control study, I want to detect whether a continuous exposure is associated with disease. I expect an odds ratio of 1.5 per standard deviation increase in the exposure. The baseline diseas...

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 505 | 522 | ±10 | 17.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| odds_ratio | 1.5 | 1.5 |
| baseline_risk | 0.1 | 0.1 |
| power | 0.8 | 0.8 |

### ✅ t2-logreg-003

**Question:** I'm building a multivariable logistic regression to predict readmission risk with 5 covariates. My main predictor is a continuous biomarker (normally distributed). I expect an odds ratio of 1.8 per SD...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 196 | 204 | ±10 | 8.00 |
| odds_ratio | 1.8 | 1.8 | ±5 | 0.00 |
| baseline_risk | 0.15 | 0.15 | ±5 | 0.00 |
| r2_other | 0.1 | 0.1 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-logreg-004

**Question:** I'm studying a protective factor with an expected odds ratio of 0.6 (40% reduction in odds). The exposure is binary with 50% prevalence, and baseline disease rate in unexposed is 25%. What sample size...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 996 | 999 | ±15 | 3.00 |
| odds_ratio | 0.6 | 0.6 | ±5 | 0.00 |
| baseline_risk | 0.25 | 0.25 | ±5 | 0.00 |
| power | 0.9 | 0.9 | ±0.03 | 0.00 |

### ✅ t2-logreg-005

**Question:** We're studying a rare outcome (5% baseline risk) and a binary exposure that's present in only 30% of the population. We expect an OR of 2.5 for exposed vs unexposed. What total sample size is needed f...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 606 | 610 | ±15 | 4.00 |
| odds_ratio | 2.5 | 2.5 | ±5 | 0.00 |
| baseline_risk | 0.05 | 0.05 | ±5 | 0.00 |
| predictor_prevalence | 0.3 | 0.3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ❌ t2-logreg-006

**Question:** I'm testing for an interaction between two binary risk factors in a logistic regression. Each factor has 50% prevalence and they're independent. Baseline risk (neither factor present) is 20%, main eff...

**Result: FAIL**
**Root Cause:** Wrong statistical method for logistic regression

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 1330 | 319 | ±16 | 1011.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| baseline_risk | 0.2 | 0.2 |
| power | 0.8 | 0.8 |

### ✅ t2-mixed-001

**Question:** I'm planning a longitudinal study with 4 repeated measures per subject, comparing treatment vs control. I expect a medium effect size (d = 0.5) between groups, and the ICC for within-subject correlati...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 40 | 40 | ±2 | 0.00 |
| total_subjects | 80 | 80 | ±2 | 0.00 |
| measurements_per_subject | 4 | 4 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ❌ t2-mixed-002

**Question:** We're doing a simple pre-post study comparing treatment vs control, with measurements at baseline and 8 weeks. We expect a treatment effect of d = 0.4, and within-patient correlation is about ICC = 0....

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects_per_group | 63 | 80 | ±5 | 17.00 | value_incorrect |
| total_subjects | 126 | 160 | ±5 | 34.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| measurements_per_subject | 2 | 2 |
| power | 0.8 | 0.8 |

### ✅ t2-mixed-003

**Question:** We're running a clinical trial with monthly visits over 6 months to detect a treatment effect of d = 0.35. The within-patient correlation (compound symmetry) is about ICC = 0.4. How many subjects per ...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 86 | 87 | ±3 | 1.00 |
| total_subjects | 172 | 174 | ±3 | 2.00 |
| measurements_per_subject | 6 | 6 | ±5 | 0.00 |
| power | 0.9 | 0.9 | ±0.03 | 0.00 |

### ❌ t2-mixed-004

**Question:** Our trial has patients nested within 10 clinics per treatment arm. The treatment effect is d = 0.3 and the ICC between patients within clinics is 0.05. How many patients per clinic do we need for 80% ...

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| patients_per_cluster | 750 | 150 | ±50 | 600.00 | value_incorrect |
| total_patients | 15000 | 3000 | ±5 | 12000.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.8 | 0.8 |

### ✅ t2-mixed-005

**Question:** We have a three-level study design: 3 measurements within patients, 15 patients within sites, and 5 sites per treatment arm. The variance is partitioned as: site variance = 0.02, patient variance = 0....

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_sites_per_arm | 5 | 5 | ±5 | 0.00 |
| given_patients_per_site | 15 | 15 | ±5 | 0.00 |
| given_measurements_per_patient | 3 | 3 | ±5 | 0.00 |
| given_total_patients | 150 | 150 | ±5 | 0.00 |
| site_icc | 0.02 | 0.02 | ±5 | 0.00 |
| patient_icc | 0.5 | 0.5 | ±5 | 0.00 |
| power | 0.59 | 0.58 | ±0.08 | 0.01 |

### ❌ t2-mixed-006

**Question:** I'm analyzing a growth curve study comparing two groups over 8 time points (0-7). I expect the groups to differ in their slopes by 0.1 units per time point. The random intercept SD is 1.0, random slop...

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_subjects | 360 | 380 | ±18 | 20.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| subjects_per_group | 180 | 190 |
| time_points | 8 | 8 |
| power | 0.8 | 0.8 |

### ✅ t2-mixed-007

**Question:** I'm planning a 2-period AB/BA crossover trial. The within-subject correlation is 0.7, and the treatment effect is d = 0.6 (standardized by total SD). How many subjects do I need for 85% power at alpha...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects | 17 | 17 | ±1 | 0.00 |
| periods | 2 | 2 | ±5 | 0.00 |
| power | 0.85 | 0.85 | ±0.03 | 0.00 |

### ✅ t2-mixed-008

**Question:** I'm running a trial with 2 correlated outcomes (correlation = 0.6) measured at 3 time points. The treatment effect on the primary outcome is d = 0.4, and within-subject ICC is 0.5. I only need to powe...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 66 | 67 | ±3 | 1.00 |
| total_subjects | 132 | 134 | ±3 | 2.00 |
| outcomes | 2 | 2 | ±5 | 0.00 |
| correlation_outcomes | 0.6 | 0.6 | ±5 | 0.00 |
| time_points | 3 | 3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-poisson-001

**Question:** We're comparing event rates between treatment and control. The control group has about 2 events per person-year, and we expect the treatment to increase this by 50% (rate ratio = 1.5). With 1-year fol...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 40 | 40 | ±2 | 0.00 |
| total_subjects | 80 | 79 | ±2 | 1.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-poisson-002

**Question:** We're testing whether a treatment reduces infection rate. Control patients average 0.5 infections per month, and we hope to reduce this to 0.3 per month. With 6 months of follow-up, how many per group...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 27 | 27 | ±1 | 0.00 |
| total_subjects | 54 | 54 | ±1 | 0.00 |
| control_rate | 0.5 | 0.5 | ±5 | 0.00 |
| followup_months | 6 | 6 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-poisson-003

**Question:** Our outcome is count data with overdispersion (variance greater than mean). The control group averages 5 events, treatment group expected to average 4 events, with dispersion parameter k = 2. How many...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 229 | 230 | ±23 | 1.00 |
| total_subjects | 458 | 460 | ±23 | 2.00 |
| control_mean | 5 | 5 | ±5 | 0.00 |
| treatment_mean | 4 | 4 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-poisson-004

**Question:** We're analyzing count data where patients have variable follow-up time (mean 0.8 years, SD 0.3 years). The baseline event rate is 3 per year, and we want to detect a rate ratio of 1.4. How many subjec...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 50 | 50 | ±5 | 0.00 |
| total_subjects | 100 | 100 | ±5 | 0.00 |
| mean_exposure | 0.8 | 0.8 | ±5 | 0.00 |
| sd_exposure | 0.3 | 0.3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ❌ t2-poisson-005

**Question:** Our count outcome has 30% structural zeros (patients who can never experience the event). Among those who can have events, the control mean is 3 and treatment mean is 2. What sample size per group for...

**Result: FAIL**
**Root Cause:** Task requires Monte Carlo simulation

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects_per_group | 100 | 150 | ±15 | 50.00 | value_incorrect |
| total_subjects | 200 | 300 | ±15 | 100.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| zero_inflation | 0.3 | 0.3 |
| control_mean_nonzero | 3 | 3 |
| treatment_mean_nonzero | 2 | 2 |
| power | 0.8 | 0.8 |

### ✅ t2-poisson-006

**Question:** I'm studying a condition where the event rate increases by about 10% each year. At baseline (time 0), the rate is 1 event per person-year. I want to detect if a treatment reduces the rate ratio to 0.8...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_group | 103 | 103 | ±5 | 0.00 |
| total_subjects | 206 | 206 | ±5 | 0.00 |
| rate_increase_per_year | 0.1 | 0.1 | ±5 | 0.00 |
| study_years | 3 | 3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-poisson-007

**Question:** We have 20 clinics per arm with 25 subjects per clinic. The ICC is 0.03, baseline rate is 4 events per person-year, and we want to detect a rate ratio of 1.25. What power does this cluster design achi...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| given_clusters_per_arm | 20 | 20 | ±5 | 0.00 |
| given_subjects_per_cluster | 25 | 25 | ±5 | 0.00 |
| given_total_subjects | 1000 | 1000 | ±5 | 0.00 |
| control_rate | 4 | 4 | ±5 | 0.00 |
| power | 0.9999 | 0.99 | ±0.03 | 0.01 |

### ✅ t2-surv-001

**Question:** We're planning a survival trial where we expect the treatment to reduce the hazard by 30% (HR = 0.7). Control group median survival is 2 years. We'll have 3 years of accrual and 2 years of additional ...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_arm | 198 | 198 | ±5 | 0.00 |
| total_subjects | 396 | 396 | ±5 | 0.00 |
| control_median_survival | 2 | 2 | ±5 | 0.00 |
| accrual_years | 3 | 3 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-surv-002

**Question:** In our survival study, the control group has 50% 2-year survival and we expect HR = 0.65 for the treatment. With 2-year accrual and 1-year additional follow-up, how many patients per arm for 80% power...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_arm | 200 | 201 | ±5 | 1.00 |
| total_subjects | 400 | 402 | ±5 | 2.00 |
| control_2yr_survival | 0.5 | 0.5 | ±5 | 0.00 |
| accrual_years | 2 | 2 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-surv-003

**Question:** I'm analyzing whether a continuous biomarker predicts survival. I expect an HR of 1.3 per standard deviation increase in the biomarker. About 25% of patients will experience the event during the study...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 460 | 460 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t2-surv-004

**Question:** We're planning a survival trial expecting HR = 0.75. Control 1-year survival is 70%. We'll have 18 months of accrual and 12 months of follow-up, but expect 20% dropout. How many patients per arm do we...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| subjects_per_arm | 656 | 657 | ±10 | 1.00 |
| total_subjects | 1312 | 1314 | ±10 | 2.00 |
| control_1yr_survival | 0.7 | 0.7 | ±5 | 0.00 |
| dropout_rate | 0.2 | 0.2 | ±5 | 0.00 |
| accrual_months | 18 | 18 | ±5 | 0.00 |
| followup_months | 12 | 12 | ±5 | 0.00 |
| power | 0.85 | 0.85 | ±0.03 | 0.00 |

### ❌ t2-surv-005

**Question:** We're planning a survival study to detect HR = 0.70 (treatment benefit). Control median survival is 18 months and total study duration is 36 months. With 1:1 allocation, 80% power, and alpha = 0.05, w...

**Result: FAIL**
**Root Cause:** Survival analysis formula error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_subjects | 603 | 361 | ±10 | 242.00 | value_incorrect |
| subjects_per_arm | 302 | 181 | ±10 | 121.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| events_needed | 247 | 247 |
| power | 0.8 | 0.8 |

### ❌ t2-surv-006

**Question:** We're studying a condition where about 30% of control patients are long-term survivors (essentially cured). We expect the treatment to increase this cure fraction to 45%. Among those who aren't cured,...

**Result: FAIL**
**Root Cause:** Survival analysis formula error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_subjects | 280 | 300 | ±15 | 20.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| subjects_per_arm | 140 | 150 |
| power | 0.8 | 0.8 |

### ❌ t2-surv-007

**Question:** In our survival study, 15% of patients may experience a competing event (e.g., death from unrelated cause) that's independent of treatment. We want to detect a cause-specific HR = 0.7 for our primary ...

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects_per_arm | 485 | 474 | ±10 | 11.00 | value_incorrect |
| total_subjects | 970 | 948 | ±10 | 22.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| competing_event_rate | 0.15 | 0.15 |
| power | 0.8 | 0.8 |

### ❌ t2-surv-008

**Question:** We're conducting a stratified survival analysis across 3 strata with different baseline hazards, but the treatment HR = 0.75 is assumed constant across strata. Over the 2-year study period, we expect ...

**Result: FAIL**
**Root Cause:** Survival analysis formula error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| subjects_per_arm | 529 | 475 | ±10 | 54.00 | value_incorrect |
| total_subjects | 1058 | 950 | ±10 | 108.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| study_duration_years | 2 | 2 |
| power | 0.8 | 0.8 |

