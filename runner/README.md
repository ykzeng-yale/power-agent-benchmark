# Audited v2 runner

The standard-library Python runner sends answer-free fully specified questions, preserves every planned attempt and uses locked numeric and structural gates. It never sends oracle answers or reference code to a model.

```sh
python3 runner/audited_benchmark_v2_0_3.py --cli /absolute/path/scientific-harness-cli.js --split all --repeats 3 --workers 3 --out results/a-fresh-run
```

For an HTTP provider, replace `--cli` with `--endpoint https://HOST/api/scientific-analysis`. The provider returns `scientificStatus`, `success`, structured `results`, `design`, code-hashed `executions` and token `usage`. `--freeze-only` saves a protocol without model calls. Existing protocols cannot be overwritten. `run-benchmark.js` forwards arguments to this runner; legacy `--tier` options are rejected.

The 20-task core plans 120 attempts with three repeats and both conditions. All provider, budget, clarification, review and schema failures count. Each attempt has its own raw JSON; `protocol.json` records hashes and randomized order; `results.json` includes descriptive rates, latency and a paired source-family bootstrap. See [methodology](../docs/audited-methodology.md). Historical SSE/LLM-judge runner documentation is archived under `historical/runner/`.

Future CLI runs use runner 2.0.3, which fingerprints the six runtime dependencies, including `scientific-reference-guard.js` when present. Its explicit null entry means that an archived release had no guard at freeze time; later guard addition, removal or byte changes invalidate the fingerprint. The old five-file protocols accurately describe their pre-guard releases and remain unchanged. Numerical scoring and oracle tolerances are unchanged. An HTTP endpoint does not expose its source files to this local fingerprint; retain its exact deployment-image manifest separately.
