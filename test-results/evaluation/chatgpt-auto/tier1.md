# Tier 1 — Basic Comparisons (t-tests, ANOVA, proportions, chi-square, correlation)

## Results: 17/30 PASS (56.7%)

| Task ID | Result | Extracted Value | Ground Truth | Tolerance | Diff | Root Cause |
|---------|--------|-----------------|--------------|-----------|------|------------|
| t1-anova-001 | **PASS** | sample_size_per_group=53 | 53 | ±5 | 0.0 | — |
| t1-anova-002 | **PASS** | sample_size_per_group=32 | 32 | ±5 | 0.0 | — |
| t1-anova-003 | **FAIL** | sample_size_per_group=390 | 78 | ±5 | 312.0 | Wrong formula or major computation error |
| t1-anova-004 | **FAIL** | sample_size_per_group=103 | 35 | ±5 | 68.0 | Wrong formula or major computation error |
| t1-anova-005 | **PASS** | sample_size_per_group=29 | 29 | ±5 | 0.0 | — |
| t1-chi-001 | **PASS** | total_sample_size=88 | 88 | ±1 | 0.0 | — |
| t1-chi-002 | **PASS** | total_sample_size=155 | 155 | ±1 | 0.0 | — |
| t1-chi-003 | **PASS** | total_sample_size=152 | 152 | ±1 | 0.0 | — |
| t1-chi-004 | **FAIL** | total_sample_size=680 | 654 | ±1 | 26.0 | Wrong formula or major computation error |
| t1-chi-005 | **PASS** | total_sample_size=110 | 110 | ±1 | 0.0 | — |
| t1-corr-001 | **PASS** | sample_size=85 | 85 | ±1 | 0.0 | — |
| t1-corr-002 | **PASS** | sample_size=165 | 164 | ±1 | 1.0 | — |
| t1-corr-003 | **PASS** | sample_size=347 | 346 | ±1 | 1.0 | — |
| t1-corr-004 | **PASS** | sample_size=63 | 62 | ±1 | 1.0 | — |
| t1-corr-005 | **PASS** | sample_size=222 | 221 | ±1 | 1.0 | — |
| t1-paired-001 | **PASS** | sample_size=34 | 34 | ±1 | 0.0 | — |
| t1-paired-002 | **FAIL** | sample_size=30 | 32 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t1-paired-003 | **FAIL** | sample_size=36 | 38 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t1-paired-004 | **FAIL** | sample_size=286 | 289 | ±1 | 3.0 | Z-approximation instead of exact t-distribution |
| t1-prop-001 | **PASS** | sample_size_per_group=97 | 97 | ±5 | 0.0 | — |
| t1-prop-002 | **PASS** | sample_size_per_group=293 | 292 | ±5 | 1.0 | — |
| t1-prop-003 | **PASS** | sample_size_per_group=582 | 582 | ±5 | 0.0 | — |
| t1-prop-004 | **FAIL** | sample_size_per_group=140 | 133 | ±5 | 7.0 | Close answer but outside strict tolerance |
| t1-prop-005 | **PASS** | sample_size_per_group=473 | 477 | ±5 | 4.0 | — |
| t1-ttest-001 | **FAIL** | total_sample_size=126 | 128 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t1-ttest-002 | **FAIL** | total_sample_size=170 | 172 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t1-ttest-003 | **FAIL** | total_sample_size=276 | 278 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t1-ttest-004 | **FAIL** | total_sample_size=134 | 138 | ±1 | 4.0 | Z-approximation instead of exact t-distribution |
| t1-ttest-005 | **FAIL** | total_sample_size=326 | 328 | ±1 | 2.0 | Z-approximation instead of exact t-distribution |
| t1-ttest-006 | **FAIL** | total_sample_size=198 | 204 | ±1 | 6.0 | Z-approximation instead of exact t-distribution |

---

## Detailed Per-Task Judgments

### ✅ t1-anova-001

**Question:** We're comparing 3 treatment groups for pain relief and expect a medium effect size (Cohen's f = 0.25). How many subjects per group for 80% power at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 53 | 53 | ±5 | 0.00 |
| total_sample_size | 159 | 159 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |
| groups | 3 | 3 | ±5 | 0.00 |

### ✅ t1-anova-002

**Question:** We're testing 4 different dosage levels of a medication and expect to see an effect size of f = 0.30 between groups. How many patients per dosage group for 80% power at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 32 | 32 | ±5 | 0.00 |
| total_sample_size | 128 | 128 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |
| groups | 4 | 4 | ±5 | 0.00 |

### ❌ t1-anova-003

**Question:** We're comparing 5 different exercise interventions for VO2max improvement. We expect a small-medium effect (f = 0.20). How many subjects per group for 90% power at alpha = 0.05?

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size_per_group | 390 | 78 | ±5 | 312.00 | value_incorrect |
| total_sample_size | 1950 | 390 | ±1 | 1560.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.9 | 0.9 |
| groups | 5 | 5 |

### ❌ t1-anova-004

**Question:** We're comparing three different diets for LDL cholesterol reduction. Based on the literature, we expect reductions of about 10, 20, and 25 mg/dL for the three diets, with a common SD of 20 mg/dL. How ...

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size_per_group | 103 | 35 | ±5 | 68.00 | value_incorrect |
| total_sample_size | 309 | 105 | ±2 | 204.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.8 | 0.8 |
| groups | 3 | 3 |

### ✅ t1-anova-005

**Question:** We're conducting a large multi-center trial across 6 treatment centers and expect a large effect (f = 0.40). Due to regulatory requirements, we need 95% power at a stringent alpha = 0.01. How many sub...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 29 | 29 | ±5 | 0.00 |
| total_sample_size | 174 | 174 | ±1 | 0.00 |
| power | 0.95 | 0.95 | ±0.03 | 0.00 |
| groups | 6 | 6 | ±5 | 0.00 |

### ✅ t1-chi-001

**Question:** I'm testing independence in a 2×2 table and want 80% power to detect a medium effect (w = 0.3) at alpha = 0.05. What total sample size do I need?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 88 | 88 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |
| df | 1 | 1 | ±5 | 0.00 |

### ✅ t1-chi-002

**Question:** I'm analyzing a 3×2 contingency table (3 treatment groups, 2 outcome categories) and want to detect an effect size of w = 0.25 with 80% power at alpha = 0.05. What total N is needed?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 155 | 155 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |
| df | 2 | 2 | ±5 | 0.00 |

### ✅ t1-chi-003

**Question:** I'm testing association in a 3×4 contingency table. I want to detect an effect size of w = 0.3 with 80% power at alpha = 0.05. What total sample size do I need?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 152 | 152 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |
| df | 6 | 6 | ±5 | 0.00 |

### ❌ t1-chi-004

**Question:** We're analyzing genotype-phenotype association in a 4×4 table and need to detect a small effect (w = 0.2) with 90% power at a stringent alpha = 0.01. What total sample size?

**Result: FAIL**
**Root Cause:** Wrong formula or major computation error

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 680 | 654 | ±1 | 26.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.9 | 0.9 |
| df | 9 | 9 |

### ✅ t1-chi-005

**Question:** I'm running a goodness-of-fit test with 5 categories, comparing observed vs expected distributions. I want to detect an effect size w = 0.35 with 85% power at alpha = 0.05. What sample size?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| total_sample_size | 110 | 110 | ±1 | 0.00 |
| power | 0.85 | 0.85 | ±0.03 | 0.00 |
| df | 4 | 4 | ±5 | 0.00 |

### ✅ t1-corr-001

**Question:** I want to investigate whether BMI is correlated with blood pressure in our patient population. Based on the literature, I expect a moderate correlation of about r = 0.3. How many patients do I need fo...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 85 | 85 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t1-corr-002

**Question:** We're studying whether age is correlated with cognitive decline scores. We expect a modest correlation of r = 0.25. How many participants for 90% power at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 165 | 164 | ±1 | 1.00 |
| power | 0.9 | 0.9 | ±0.03 | 0.00 |

### ✅ t1-corr-003

**Question:** I'm investigating whether a novel biomarker correlates with patient outcomes. The expected correlation is small (r = 0.15), but clinically meaningful. How many patients do I need for 80% power at alph...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 347 | 346 | ±1 | 1.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t1-corr-004

**Question:** We expect a strong correlation (r = 0.5) between exercise frequency and VO2max. We want high confidence - 95% power with alpha = 0.01. What sample size do we need?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 63 | 62 | ±1 | 1.00 |
| power | 0.95 | 0.95 | ±0.03 | 0.00 |

### ✅ t1-corr-005

**Question:** I hypothesize that medication adherence is positively correlated with health outcomes (r = 0.2). Since I'm predicting a positive direction, I'll use a one-sided test at alpha = 0.025. How many patient...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 222 | 221 | ±1 | 1.00 |
| power | 0.85 | 0.85 | ±0.03 | 0.00 |

### ✅ t1-paired-001

**Question:** I'm measuring patients' depression scores before and after 8 weeks of treatment. Expected improvement is 5 points with SD of changes = 10 (d = 0.5). With 80% power and alpha = 0.05, how many patients ...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size | 34 | 34 | ±1 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ❌ t1-paired-002

**Question:** I'm running a weight loss intervention and will measure participants before and after. We expect about 3 kg average loss with individual variation (SD of the changes) around 5 kg. How many participant...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 30 | 32 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.9 | 0.9 |

### ❌ t1-paired-003

**Question:** We're doing a crossover bioequivalence study comparing two drug formulations. The expected difference in AUC between formulations is 50 units, with within-subject SD of 100. How many subjects do we ne...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 36 | 38 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.85 | 0.85 |

### ❌ t1-paired-004

**Question:** In our bioequivalence crossover study, we need to be able to detect even small differences (d = 0.25) with high confidence - 95% power at the stricter alpha = 0.01. How many subjects?

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size | 286 | 289 | ±1 | 3.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.95 | 0.95 |

### ✅ t1-prop-001

**Question:** We're testing a new treatment where we expect the response rate to improve from 40% (control) to 60% (treatment). How many patients per group for 80% power at alpha = 0.05 (two-sided)?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 97 | 97 | ±5 | 0.00 |
| total_sample_size | 194 | 194 | ±5 | 0.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t1-prop-002

**Question:** Our current drug has a 30% adverse event rate. We're hoping a new formulation will reduce this to 20%. How many patients per arm do we need to detect this difference with 80% power at alpha = 0.05?

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 293 | 292 | ±5 | 1.00 |
| total_sample_size | 586 | 584 | ±5 | 2.00 |
| power | 0.8 | 0.8 | ±0.03 | 0.00 |

### ✅ t1-prop-003

**Question:** We're planning a vaccine efficacy trial. The placebo group is expected to have a 10% infection rate, and we hope the vaccine reduces this to 5%. Since we're testing efficacy (one-sided), we'll use alp...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 582 | 582 | ±5 | 0.00 |
| total_sample_size | 1164 | 1164 | ±10 | 0.00 |
| power | 0.9 | 0.9 | ±0.03 | 0.00 |

### ❌ t1-prop-004

**Question:** We're comparing a new surgical technique to the standard approach. The standard technique has about 85% success rate, and we expect the new technique to achieve 95%. How many patients per group for 80...

**Result: FAIL**
**Root Cause:** Close answer but outside strict tolerance

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| sample_size_per_group | 140 | 133 | ±5 | 7.00 | value_incorrect |
| total_sample_size | 280 | 266 | ±5 | 14.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| power | 0.8 | 0.8 |

### ✅ t1-prop-005

**Question:** We're planning a non-inferiority trial for a new treatment. The standard treatment has about 70% response rate, and we expect the new treatment to be similar. We need to rule out that the new treatmen...

**Result: PASS**

| Field | Extracted | Ground Truth | Tolerance | Diff |
|-------|-----------|--------------|-----------|------|
| sample_size_per_group | 473 | 477 | ±5 | 4.00 |
| total_sample_size | 946 | 954 | ±10 | 8.00 |
| power | 0.9 | 0.9 | ±0.03 | 0.00 |

### ❌ t1-ttest-001

**Question:** I want to compare mean blood pressure between treatment and control groups. I expect a medium effect size (Cohen's d = 0.5), want 80% power at alpha = 0.05 using a two-sided test. How many participant...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 126 | 128 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| sample_size_per_group | 63 | 64 |
| power | 0.8 | 0.8 |

### ❌ t1-ttest-002

**Question:** Testing if a new drug reduces cholesterol. Expected reduction is 15 mg/dL with SD of 30 mg/dL in both groups. I need 90% power with two-sided alpha = 0.05. What sample size per group?

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 170 | 172 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| sample_size_per_group | 85 | 86 |
| power | 0.9 | 0.9 |

### ❌ t1-ttest-003

**Question:** I'm comparing pain scores between a new treatment and standard care. Based on prior studies, we expect only a small improvement (d = 0.3), but we believe the new treatment will be better, so we're usi...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 276 | 278 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| sample_size_per_group | 138 | 139 |
| power | 0.8 | 0.8 |

### ❌ t1-ttest-004

**Question:** We're running a trial comparing CBT therapy to a waitlist control for anxiety. Based on pilot data, we expect an 8-point difference on the anxiety scale, with a pooled SD of about 12 points. We want t...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 134 | 138 | ±1 | 4.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| sample_size_per_group | 67 | 69 |
| power | 0.9 | 0.9 |

### ❌ t1-ttest-005

**Question:** We're planning an RCT to see if continuous glucose monitors improve HbA1c compared to standard monitoring. We expect a 0.4% difference with SD of 1.0%. Since we're testing superiority (one-sided), we'...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 326 | 328 | ±1 | 2.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| sample_size_per_group | 163 | 164 |
| power | 0.95 | 0.95 |

### ❌ t1-ttest-006

**Question:** A pharmaceutical company needs to detect a large effect (d = 0.8) in a confirmatory phase III trial. They require 99% power with alpha = 0.001 (two-sided) for regulatory purposes. What's the sample si...

**Result: FAIL**
**Root Cause:** Z-approximation instead of exact t-distribution

**Failed Fields:**

| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |
|-------|-----------|--------------|-----------|------|--------|
| total_sample_size | 198 | 204 | ±1 | 6.00 | value_incorrect |

**Passed Fields:**

| Field | Extracted | Ground Truth |
|-------|-----------|-------------|
| sample_size_per_group | 99 | 102 |
| power | 0.99 | 0.99 |

