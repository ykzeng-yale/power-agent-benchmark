# Predeclared separate scientific-figure review

Automatic primary scoring certifies that real execution produced a delivered parseable PNG/PDF and that the companion CSV contains the declared independently verified grid. It **does not certify that the visible figure draws those values**, nor infer scientific readability or source support from a file name, a hash, image headers or a model's claim.

Before empirical results exist, this rubric defines a separate manual scientific-content assessment. Reviewers receive a randomly relabelled image/PDF, the task's original scientific request, and the validated CSV, with mode/profile/repeat/status and model-review verdict withheld. All delivered figures are assessed, including numerically incorrect or incomplete attempts; missing files receive `not_delivered` and remain in the planned denominator. Primary automatic scores are never changed by this assessment.

For each figure, record pass/fail/unverifiable with a concrete observation on each item:

1. The plotted scientific quantity and horizontal variable match the requested sensitivity question; no continuous solution is mislabeled as an integer recommendation.
2. Every requested grid value and curve is represented. No supplied sensitivity scenario is omitted, duplicated or silently interpolated as a measured point.
3. Vertical and horizontal axes name the quantities and give the correct count/effect/probability units. Power is on the0–1 scale or explicitly labelled percent with a corresponding100-fold conversion.
4. The plotted positions agree with the validated CSV within the resolution of the rendering. A graph cannot pass merely because its title repeats the requested method.
5. Legends identify all multiple curves and their nuisance-parameter values; one-curve tasks need no unnecessary legend. The title/caption names the scientific design.
6. Target-power lines requested for t/ANOVA use the supplied target. Integer sample-size plots do not suggest a fractional participant recommendation.
7. The NIH MDE plot identifies the t-quantile approximation. It does not label MDE as achieved power or assert exact80%power certification.
8. Text, symbols, ticks, legends and curves are legible at normal document scale and are not clipped or obscured.

A scientific-figure pass requires all applicable items to pass. `Unverifiable` remains distinct from a scientific pass. At least one human assessment is required; if a second reviewer is available, preserve both ratings and disagreements, then a separate adjudication. Do not replace human assessment with an unvalidated language-model visual judge or infer independent errors from two calls to the same model.

Artifact SHA identifies the exact assessed bytes; canonical CSV SHA identifies the assessed data. The rating file records reviewer label, assessment date, artifact SHA, CSV SHA and the eight item-level ratings. Aggregate planned counts and coverage are reported separately from the automatic outcome and from numerical accuracy.
