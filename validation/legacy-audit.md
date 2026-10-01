# Legacy 106-task audit

Every legacy task is excluded from the new primary suite until source/design verification. Executable reproduction alone does not establish scientific validity.

| ID | Execution | Stored → recomputed | Status | Findings |
|---|---|---|---|---|
| t1-ttest-001 | executed | 64 → 64 | numeric_reproduced_source_unverified |  |
| t1-ttest-002 | executed | 86 → 86 | numeric_reproduced_source_unverified |  |
| t1-ttest-003 | executed | 139 → 139 | numeric_reproduced_source_unverified |  |
| t1-ttest-004 | executed | 69 → 69 | quarantine | Reference rounds 8/12 to .667 before solving; clean task must use exact supplied means and SD. |
| t1-ttest-005 | executed | 164 → 164 | numeric_reproduced_source_unverified |  |
| t1-ttest-006 | executed | 102 → 102 | numeric_reproduced_source_unverified |  |
| t1-paired-001 | executed | 34 → 34 | numeric_reproduced_source_unverified |  |
| t1-paired-002 | executed | 32 → 32 | numeric_reproduced_source_unverified |  |
| t1-paired-003 | executed | 38 → 38 | numeric_reproduced_source_unverified |  |
| t1-paired-004 | executed | 289 → 289 | numeric_reproduced_source_unverified |  |
| t1-anova-001 | executed | 53 → 53 | numeric_reproduced_source_unverified |  |
| t1-anova-002 | executed | 32 → 32 | numeric_reproduced_source_unverified |  |
| t1-anova-003 | executed | 78 → 78 | numeric_reproduced_source_unverified |  |
| t1-anova-004 | executed | 35 → 35 | quarantine | Reference rounds f to .312 before solving although prompt group means imply sqrt(mean squared deviation)/20; integer may change. |
| t1-anova-005 | executed | 29 → 29 | numeric_reproduced_source_unverified |  |
| t1-prop-001 | executed | 97 → 97 | numeric_reproduced_source_unverified |  |
| t1-prop-002 | executed | 292 → 292 | numeric_reproduced_source_unverified |  |
| t1-prop-003 | executed | 582 → 582 | numeric_reproduced_source_unverified |  |
| t1-prop-004 | executed | 133 → 133 | numeric_reproduced_source_unverified |  |
| t1-prop-005 | executed | 477 → 477 | numeric_reproduced_source_unverified |  |
| t1-chi-001 | executed | 88 → 88 | numeric_reproduced_source_unverified |  |
| t1-chi-002 | executed | 155 → 155 | numeric_reproduced_source_unverified |  |
| t1-chi-003 | executed | 152 → 152 | numeric_reproduced_source_unverified |  |
| t1-chi-004 | executed | 654 → 654 | numeric_reproduced_source_unverified |  |
| t1-chi-005 | executed | 110 → 110 | numeric_reproduced_source_unverified |  |
| t1-corr-001 | executed | 85 → 85 | numeric_reproduced_source_unverified |  |
| t1-corr-002 | executed | 164 → 164 | numeric_reproduced_source_unverified |  |
| t1-corr-003 | executed | 346 → 346 | numeric_reproduced_source_unverified |  |
| t1-corr-004 | executed | 62 → 62 | numeric_reproduced_source_unverified |  |
| t1-corr-005 | executed | 221 → 221 | numeric_reproduced_source_unverified |  |
| t2-linreg-001 | executed | 122 → 122 | numeric_reproduced_source_unverified |  |
| t2-linreg-002 | executed | 62 → 62 | numeric_reproduced_source_unverified |  |
| t2-linreg-003 | executed | 85 → 85 | numeric_reproduced_source_unverified |  |
| t2-linreg-004 | executed | 174 → 174 | numeric_reproduced_source_unverified |  |
| t2-linreg-005 | executed | 208 → 208 | numeric_reproduced_source_unverified |  |
| t2-linreg-006 | executed | 688 → 688 | numeric_reproduced_source_unverified |  |
| t2-logreg-001 | executed | 347 → 349 | quarantine | Supplied executable reference does not reproduce stored primary answer under installed R packages. |
| t2-logreg-002 | executed | 522 → 519 | quarantine | Supplied executable reference does not reproduce stored primary answer under installed R packages. |
| t2-logreg-003 | executed | 204 → 204 | numeric_reproduced_source_unverified |  |
| t2-logreg-004 | executed | 999 → 1007 | quarantine | Supplied executable reference does not reproduce stored primary answer under installed R packages. |
| t2-logreg-005 | executed | 610 → 614 | quarantine | Supplied executable reference does not reproduce stored primary answer under installed R packages. |
| t2-logreg-006 | executed | 319 → 370 | quarantine | Interaction reference substitutes two risks into a main-effect logistic formula. Earlier local simulation report recommends 1350, current ground truth 319 and reference comment 370; cannot certify interaction power. Supplied executable reference does not reproduce stored primary answer under installed R packages. |
| t2-mixed-001 | no_executable_calculation | 40 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-mixed-002 | no_executable_calculation | 80 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-mixed-003 | no_executable_calculation | 87 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-mixed-004 | no_executable_calculation | 150 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-mixed-005 | no_executable_calculation | 0.58 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-mixed-006 | no_executable_calculation | 190 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-mixed-007 | executed | 17 → 17 | numeric_reproduced_source_unverified |  |
| t2-mixed-008 | no_executable_calculation | 67 → — | quarantine | Reference reduces a multivariate model to one averaged outcome without specifying estimand or multivariate test; conflicts with earlier local simulation report 140/group. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-001 | no_executable_calculation | 198 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-002 | no_executable_calculation | 201 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-003 | no_executable_calculation | 460 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-004 | no_executable_calculation | 657 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-005 | no_executable_calculation | 45 → — | quarantine | Two-arm Schoenfeld reference omits 1/[allocation*(1-allocation)] = 4. Its 62 events are a continuous-predictor calculation, not a two-arm log-rank design. Accrual is also unspecified. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-006 | no_executable_calculation | 150 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-007 | no_executable_calculation | 474 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-surv-008 | no_executable_calculation | 475 → — | quarantine | Strata weights and stratum event distributions unspecified; control risk substituted for pooled event probability. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-poisson-001 | executed | 40 → 40 | numeric_reproduced_source_unverified |  |
| t2-poisson-002 | executed | 27 → 27 | numeric_reproduced_source_unverified |  |
| t2-poisson-003 | no_executable_calculation | 230 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-poisson-004 | no_executable_calculation | 50 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-poisson-005 | no_executable_calculation | 150 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-poisson-006 | no_executable_calculation | 103 → — | quarantine | 10% yearly increase is encoded as linear 1+0.1t, whereas multiplicative annual growth gives a different integrated rate; prompt must specify rate function. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t2-poisson-007 | no_executable_calculation | 0.99 → — | quarantine | Wald reference double-counts baseline rate: sqrt(effective events) and inverse rate variance are both used. Exact clustered count model/test also unspecified. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cluster-001 | no_executable_calculation | 7 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cluster-002 | no_executable_calculation | 0.35 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cluster-003 | no_executable_calculation | 0.94 → — | quarantine | Variable-cluster design effect incorrectly multiplies the equal-size DE by (1+CV²); standard approximation is 1+[((1+CV²)m)-1]ICC. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cluster-004 | no_executable_calculation | 48 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cluster-005 | no_executable_calculation | 7 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cross-001 | no_executable_calculation | 21 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cross-002 | executed | 119 → 119 | numeric_reproduced_source_unverified |  |
| t3-cross-003 | no_executable_calculation | 42 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-cross-004 | no_executable_calculation | 76 → — | quarantine | Prompt says bioequivalence but provides no equivalence margins. A superiority paired t test cannot answer this question. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-fact-001 | no_executable_calculation | 50 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-fact-002 | no_executable_calculation | 350 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-fact-003 | no_executable_calculation | 22 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-fact-004 | no_executable_calculation | 0.93 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-001 | no_executable_calculation | 50 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-002 | no_executable_calculation | 58 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-003 | no_executable_calculation | 0.32 → — | quarantine | Reference explicitly averages powers from z, likelihood-ratio and Kenward–Roger tests (36.5%, 30%, 26%). These are different procedures, not one ground truth. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-004 | no_executable_calculation | 0.6 → — | quarantine | Reference gives different test-specific powers (63%,57%,54%) and uses their midpoint. Test and randomization level must be fixed. Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-005 | no_executable_calculation | 0.58 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-006 | no_executable_calculation | 55 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t3-simr-007 | no_executable_calculation | 0.82 → — | quarantine | Reference contains no executable power/sample-size calculation; library imports and prose are not validation. |
| t4-binary-001 | executed | 662 → 662 | numeric_reproduced_source_unverified |  |
| t4-binary-002 | executed | 870 → 870 | numeric_reproduced_source_unverified |  |
| t4-binary-003 | executed | 1679 → 1679 | numeric_reproduced_source_unverified |  |
| t4-binary-004 | executed | 2977 → 2977 | numeric_reproduced_source_unverified |  |
| t4-binary-005 | executed | 1214 → 1214 | numeric_reproduced_source_unverified |  |
| t4-surv-001 | executed | 5143 → 5143 | numeric_reproduced_source_unverified |  |
| t4-surv-002 | executed | 185 → 185 | numeric_reproduced_source_unverified |  |
| t4-surv-003 | executed | 659 → 659 | numeric_reproduced_source_unverified |  |
| t4-surv-004 | executed | 449 → 449 | numeric_reproduced_source_unverified |  |
| t4-surv-005 | executed | 597 → 597 | numeric_reproduced_source_unverified |  |
| t4-cont-001 | executed | 918 → 918 | numeric_reproduced_source_unverified |  |
| t4-cont-002 | executed | 239 → 239 | numeric_reproduced_source_unverified |  |
| t4-cont-003 | executed | 1508 → 1508 | numeric_reproduced_source_unverified |  |
| t4-cont-004 | executed | 580 → 580 | numeric_reproduced_source_unverified |  |
| t4-valid-001 | executed | 1832 → 1832 | numeric_reproduced_source_unverified |  |
| t4-valid-002 | executed | 1183 → 1183 | numeric_reproduced_source_unverified |  |
| t4-valid-003 | executed | 1674 → 1674 | numeric_reproduced_source_unverified |  |
| t4-valid-004 | executed | 3733 → 3733 | numeric_reproduced_source_unverified |  |
| t4-valid-005 | executed | 814 → 814 | numeric_reproduced_source_unverified |  |
| t4-valid-006 | executed | 3461 → 3461 | numeric_reproduced_source_unverified |  |
| t4-valid-007 | executed | 1100 → 1095 | quarantine | Supplied executable reference does not reproduce stored primary answer under installed R packages. |
