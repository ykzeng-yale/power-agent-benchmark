# Prospective numerical comparison, API 2.4.3

All 48 planned attempts were captured before releasing these questions and
references: 12 questions, two workflow modes, two repeats. The original question
bytes were frozen before independent R/SciPy reference computation. The methods
and source families were already developer-known. This is a **question-level
prospective partition**, not an unseen-method or contamination-free study.

| Outcome | Shared-conversation single | Fresh-review multi |
|---|---:|---:|
| Completed workflows | 24/24 | 24/24 |
| Specified primary numerical agreement | 24/24 | 24/24 |
| Correct primary count/probability units | 24/24 | 24/24 |
| Current executed required review | 24/24 | 24/24 |
| Strict primary contract | 23/24 | 23/24 |
| Median CLI seconds [Q1, Q3] | 46.19 [37.96, 66.39] | 46.21 [40.20, 73.62] |
| Model calls / R executions | 175 / 74 | 196 / 94 |
| Input / output tokens | 4,163,493 / 152,652 | 3,150,406 / 171,457 |

The strict failures are preserved: single repeated-measures interaction repeat2
and multi omnibus-regression repeat2 declared `two-sided` in design metadata
where the frozen contract expects omnibus/not-applicable. Their executed
upper-tail F calculations and primary values were correct. No post-outcome
alias expansion or replacement attempt was used. Of 24 matched task-repeat
pairs, 22 passed both modes, one passed single only, one passed multi only, and
none failed both. Repeats are clustered within 12 questions.

Each mode has tier denominators 4/6/8/6. Single strict successes are 4/6/7/6;
multi successes are 4/5/8/6. All tier primary numerical counts equal their
denominators. No broad superiority or robustness claim follows from this
small prescribed-method study.

Both modes used Sonnet 5.5 scientific roles, Haiku 5.5 advisory routing, the same
scientific role instructions and tools, required numerical review, and identical
96-call/48-R/1,200-second budgets with 300 seconds per R call. The unchanged
runtime supports two complete repair cycles, reserved in both modes; three
would silently clamp to two. All final candidates were round0, although local
coding or checking errors were recovered within initial phases. The multi
reviewer completed a candidate-withheld numerical precheck in all 24 attempts.
Withholding from messages does not certify filesystem isolation or independent
scientific assumptions. Local fresh R processes are not an OS sandbox.

The strict composite concerns the specified **primary quantity**, declared
design, recorded execution evidence and required review. It does not certify
every supplementary simulation or narrative claim. The non-Tier4 audit found
all 36 primary coder methods/inputs/units correct, with one substantive
unresolved supplementary failure: factorial single repeat1 correctly calculated
22 per cell and a correct analytic check, but its reviewer simulated
`lambda=(N-6)*f²` instead of the requested `lambda=N*f²`, then accepted that
simulation comparison without resolving the change. See
[non-Tier4 audit](ancillary/non-tier4-summary.json). Other bounded qualifications
include overlapping Monte Carlo streams, conservative literal-metadata guard
rejections, recovered invalid outputs and inaccurate supplementary explanations.

All 12 prediction attempts used the requested `pmsampsize` 1.1.3 families,
inputs, criterion maxima and participant units correctly. All four survival
attempts meet both risk-precision margins at the returned sample size; the
separate two-margin precision minimum and predecessor were checked. Four
ancillary audits are unqualified and eight retain narrative, rounding or
supplementary-check qualifications. See the separate [Tier4 audit](ancillary/tier4-summary.md).
Neither audit is a complete prose-validity certificate.

These questions do not require figures, source acquisition, Monte Carlo,
clarification or autonomous method selection. Their absence is not scored as
failure, and numerical success does not establish those capabilities. The
questions prescribe method conventions. Integer references are exact minima on
the stated feasible grid; power tolerance is 0.0001. See
[reference specifications](audited/reference-specifications.json).

The observed standard global token-price estimate is about $9.78 single and
$7.94 multi, excluding source tools, unobserved responses/retries and platform
charges. This is not an invoice. No cache tokens were recorded. The previous
API 2.4.2 capability cohort and its strict unit failures remain unchanged.

## Public evidence and restricted captures

`manifest.json` binds public bytes to original private identities. The published
protocol is an explicitly sanitized derivative: only two local executable path
values were redacted and JSON was reserialized. It is **not** a substitute for
the original frozen dispatch protocol. Its original and derivative hashes are
retained. The original preparation script and private README remain omitted,
with their adapter pins preserved in the protocol.

`runner/run.py`, `runner/score.py`, and `runner/test_adapter.py` are byte-identical
to the frozen programs. Full raw transports/provider transcripts/source bodies
remain restricted. Public per-attempt metadata, scores, primary values, design
fields and request identities support aggregate/reference reproduction, but
cannot independently rerun the restricted raw stdout/code-binding gates. Do
not treat a public hash or execution exit status as a scientific proof.

`audited/tasks.json` is the exact pre-dispatch metadata snapshot; its zero
under-test execution counts describe that historical freeze, not the final
state. Final outcomes are in `outcomes/`. Original private reference hashes and
the earlier question freeze remain in the protocol identity chain.

## Reproduce public checks

```sh
python3 validation/verify_public.py
python3 -m unittest discover -s runner -p test_adapter.py
python3 validation/independent.py reproduction-python.json
```

The last command requires SciPy 1.13.1 and refuses to overwrite an output. It
uses the original independent core implementation plus the same two explicit
Freedman/cluster expressions, with no R or model calls. The exact observed
pre-dispatch SciPy results are retained separately.

For R 4.4.2 with `jsonlite` 2.0.0, `pmsampsize` 1.1.3 and `pwr` 1.3.0, reproduce
in a **new scratch directory** containing a copy of `audited/`, then invoke
`Rscript validation/reference.R /absolute/path/to/scratch`. The historical
reference script writes scratch `audited/oracles.json`; never point it at the
frozen corpus. Numerical reference agreement is conditional on the stated
methods and does not establish finite-sample operating characteristics.
