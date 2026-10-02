# Post hoc contract sensitivity and audits

This folder is a separately versioned engineering analysis performed **after inspection of the frozen 64-attempt outcomes**. It is not preregistration, an unseen holdout, new model testing, or a replacement accuracy estimate. The original questions, scientific oracles, 19 frozen evaluator files, provider records and primary scores remain unchanged.

The original strict calculation outcome was 0/12 in each of four conditions. Each condition also had 4/4 appropriate clarification responses, so the original 4/16 overall positive count must not be called numerical accuracy. Completed numerical agreement was 5/12 for single shared, 2/12 for multi shared, 3/12 for single expanded and 5/12 for multi expanded. Partial numeric agreement and all planned failures remain separately reported.

## Four engineering contrasts

The script loads the exact frozen scorer into fresh in-memory namespaces. It records every code substitution and changes only these contract conditions, separately and jointly:

1. Require an actual successful provider search receipt before the named-document read, without requiring the search result itself to return that same document URL. The matching document read, stored content SHA, date/scope and actual citation remain required. Empty search results are an attempted search, not document discovery.
2. Permit additional successful current-round reviewer executions without JSON numeric output, provided at least one cited current reviewer execution has structured numeric output. Missing, failed, wrong-role and stale review references remain invalid.
3. Permit other PNG/PDF basenames: public questions specified `sensitivity.csv` but did not specify image basenames. Exact execution snapshots, actual cited current producers, bytes/size/SHA, MIME/parser checks and the independently verified companion CSV grid remain required. This does not certify visible plot-data agreement or readability.
4. Match the existing runtime's numeric serialization grounding tolerance, `abs(computed - submitted) <= 1e-9 * max(1, abs(computed))`, with exact metric/unit strings. Scientific oracle tolerances, units, design requirements and completed status are unchanged. One completed continuous-event row differed by approximately `9.95e-14`.

| Diagnostic calculation positives | Single shared | Multi shared | Single expanded | Multi expanded |
|---|---:|---:|---:|---:|
| Original frozen | 0/12 | 0/12 | 0/12 | 0/12 |
| Search chain only | 0/12 | 0/12 | 1/12 | 0/12 |
| Review IDs only | 0/12 | 0/12 | 0/12 | 0/12 |
| Figure basename only | 0/12 | 0/12 | 0/12 | 0/12 |
| Grounding precision only | 0/12 | 0/12 | 0/12 | 0/12 |
| Combined four | 4/12 | 1/12 | 3/12 | 4/12 |

These contrasts explain measurement and contract sensitivity. They do not justify replacing the original primary result, selecting better responses, relaxing scientific mathematics, or concluding that one architecture is superior. All 64 attempts and both repeats remain included. The combined diagnostic preserved 2,304 numerical, design, completion, clarification and budget invariants across the six variants.

## Reproduction with authorized originals

The published script is byte-identical to the executed version: SHA-256 `dff349caf07535f2bf94535b870d9ec4f4cc26f7878905375eb97e8062c52556`. Its historical local defaults are retained for byte identity; always provide explicit paths in another clone. Run from the benchmark repository root:

```sh
python3 analysis/workflow-capabilities-20261002-posthoc/posthoc-contract-sensitivity.py \
  --repo "$PWD" \
  --run '/ABSOLUTE/verified-original-wc64' \
  --out '/ABSOLUTE/new-posthoc-output'
```

The output directory must be fresh. The script refuses to overwrite or resume existing derived results, records its SHA and input hashes before applying that version's transformations, then hashes the final outputs. It never invokes a model or source provider. Python 3.9 or later and `pdfinfo` are needed for the frozen offline evaluator.

Original provider responses include long extracted source text and remain restricted. Public redacted response derivatives omit that text and tool transcripts, and therefore are **not sufficient to fully rescore the original source/trace-dependent criteria**. Authorized original access is needed for this command; a redacted derivative is not the original raw record. The original identity audit records 132 retained objects, 64 stdout/stderr transports and no capture losses or undispatched attempts. Its hash manifests link original objects without publishing their content.

## Local contract fixtures

```sh
python3 analysis/workflow-capabilities-20261002-posthoc/test-posthoc-contract-sensitivity.py
```

The public test infers this repository from its location. Set `POWER_AGENT_BENCHMARK_REPO` only if the frozen cohort is in another clone. Tests use actual local R numeric/CSV/PNG fixtures and explicitly injected source/extra-review metadata; they require `Rscript` with `jsonlite`. They are not empirical provider receipts or model responses. Negative cases preserve rejection of bad scientific quantities/units, hashes and claims, missing citations, stale/failed/wrong-role IDs, incorrect companion grids, absent numeric verification, runtime drift and budget violations.

The public test has a different SHA from the original local test because its repository-path selection is portable. Its separately recorded execution receipt identifies the actual published test bytes; it does not reuse the earlier test's identity.

## Included audits and figure qualification

`publication-source-links.json` distinguishes byte-identical copied results from explicit projections. `posthoc-output-sha256.json` retains the executed version's original output hashes. `main-study-final-audit.json` records 607 passing original-identity, capture, budget and frozen-score reproduction checks. `main-workflow-failure-audit.json` records actual phase/review/source/artifact failures and measurement mismatches.

`figure-ai-only-condition-summary.json` is an aggregate-only projection of a sealed AI inspection. It contains no private case map, case IDs or figure bytes. It is supplemental AI assistance, not human judgment, and does not fulfill the frozen rubric's requirement for a human scientific-figure assessment. Automatic file parsing and correct companion CSV values likewise do not establish visible chart fidelity. Neither assessment changes the primary scores.
