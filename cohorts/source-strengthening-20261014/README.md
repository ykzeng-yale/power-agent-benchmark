# Source-strengthened development anchors

This version contains 14 developer-exposed questions: 11 textbook worked answers and 3 official `pmsampsize` code illustrations. It is a development and reproducibility corpus, not a held-out performance study. No new LLM evaluation was run on these questions during corpus preparation. Historical questions, taxonomy, experiments, failures, and scores remain unchanged.

| Tier | Subdomain | Cases | Source answers |
|---|---|---:|---|
| 1 | One-sample, independent, and paired t tests | 3 | 41 total; 42 per group; 21 pairs |
| 2 | Regression, one-way ANOVA, factorial ANOVA | 3 | 148 total; 52 per group; 26 per cell |
| 3 | Repeated measures and cluster-rate design | 3 | 18 per group; 26 total; 7 clusters per arm |
| 4 | Prediction development and advanced logistic inference | 5 | Three computed code illustrations; textbook logistic answers 51 and 188 total |

Only this new version extends Tier 4 to an explicit **advanced logistic coefficient-inference** subdomain alongside prediction-model development. The two logistic cases are not Riley development-sizing tasks. The cohort has three cases in each of Tiers 1–3 and five in Tier 4; it is not a balanced four-tier performance sample.

`public/questions.json` contains prompts and response contracts. `audited/` contains source metadata and public development oracles. An evaluator must keep oracle files out of an agent's task context. Because the development answers are public and several cases were previously evaluated, this corpus cannot establish contamination-free generalization. New prospective questions remain outside this repository and were not dispatched as part of this preparation.

The Verma questions use the verified chapter/illustration locators from the first edition of [Verma and Verma (2020)](https://link.springer.com/book/10.1007/978-981-15-5204-5). Precise printed-page ranges were not independently established and are omitted. Supplied OCR and selected result/option figures were inspected privately; copyrighted images, full OCR, and chapters are not distributed. The [Field Trials book](https://www.ncbi.nlm.nih.gov/books/NBK305517/) example is Chapter 5, Section 6.1; its official indexed section exposed the formula, inputs, and seven-cluster answer, while direct fetching encountered a recaptcha. This is not a new full-chapter reading certificate.

The three [CRAN manual](https://cran.r-project.org/web/packages/pmsampsize/pmsampsize.pdf) examples provide inputs and executable code, rather than printed numeric answers. Their `published_source_value` is **null**. Independent formulas and `pmsampsize` 1.1.3 agree on 662, 5143, and 918 participants. This agreement must not be described as three textbook answers.

The logistic cases retain G*Power 3.1.9.2's **Demidenko (2007) with variance correction** option, verified from the textbook's result and option figures. The [official manual](https://www.psychologie.hhu.de/fileadmin/redaktion/Fakultaeten/Mathematisch-Naturwissenschaftliche_Fakultaet/Psychologie/AAP/gpower/GPowerManual.pdf), Section 29.6.2, printed pages 72–73, equations 14–15, supplies the expected-information/normal-approximation convention. Gaussian-predictor correction `a=1` gives N=51; Bernoulli-predictor correction `a=0.85` gives N=188. Disabling correction gives 65 and 206, respectively. These negative option controls show why silently substituting another logistic power method does not reproduce the source answer. The approximation is not exact finite-sample logistic power.

Important conventions:

- Paired sample size counts independent participants, each contributing one pair. The difference SD uses both marginal SDs and their within-person correlation.
- Equal allocations are enforced on the feasible integer grid. The factorial answer is 26 per cell, hence 156 total; the source's displayed power at unrestricted N=155 is not the power at N=156.
- Repeated-measures cases specify compound symmetry, the requested between/within estimand, and sphericity. These assumptions are supplied inputs, not default advice for a new study.
- The cluster-rate example uses a between-cluster coefficient of variation, an additive one-cluster correction, and child-weeks of exposure. CV is not ICC and exposure is not participant count.
- Riley requirements are conditional deterministic planning results. Future realized event counts are random. Binary/survival anticipated adjusted R-squared is Cox–Snell; the apparent-adjusted difference criterion uses Nagelkerke scaling. Continuous intercept precision is evaluated subject to satisfying the other criteria; its reported fourth component is not an independently minimized unconstrained criterion.
- Logistic `R²` describes the tested predictor explained by other predictors. It is not outcome prediction-model R-squared. Bernoulli predictor prevalence is not marginal outcome prevalence.

## Reproduce the references

From this cohort directory, use R 4.4.2 with `jsonlite` 2.0.0, `pmsampsize` 1.1.3 and `pwr` 1.3.0; use Python with SciPy 1.13.1. Dependencies are installed separately. These scripts perform numerical reference calculations; they do not call a model or fit simulated datasets.

```sh
Rscript validation/reference.R . reproduction-output/r-reference.json
python validation/independent.py . reproduction-output/python-reference.json
python validation/verify.py reproduction-output/r-reference.json reproduction-output/python-reference.json
Rscript validation/logistic_option_controls.R reproduction-output/logistic-options-R.json
python validation/logistic_option_controls.py reproduction-output/logistic-options-python
```

Scripts refuse to overwrite existing reproduction outputs. The exact observed R/Python outputs used for this candidate are under `validation/`, with software versions and all 14 answers. The Python log retains low-design SciPy distribution warnings with machine paths redacted; each returned candidate is checked for finiteness, and all selected answers agree. The observed four logistic corrected/uncorrected control outputs are retained separately. No scorer or historical results were changed. A prospective comparison requires its own runtime, adapter, budgets, source-access policy, scorer, and question freeze before model execution.
