# Audited v2 methodology

Use [audited-methodology.md](audited-methodology.md) and the executable contracts in `audited/tasks.json`, `audited/reference-specifications.json` and `runner/audited_benchmark.py`. Historical v1 documentation is preserved under `historical/docs/`; its assertions about complete validation and rounding flexibility have been withdrawn.

Integer sample sizes must exactly match the independently inverted feasible design. Deterministic power uses absolute tolerance 0.0001. Status, schema, unit, method, alpha, sidedness, allocation and executed numerical evidence are mandatory gates. No LLM extraction or judge decides the primary endpoint. Corrections create a new frozen version; preserve original records and do not retune tolerances on failures.
