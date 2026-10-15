# Judge-free primary evaluation

The primary scorer is `score` in `runner/audited_benchmark.py`. It evaluates the structured record against a private scorer-side numeric specification and requires status, schema, units, scientific design and successful code-hashed R evidence. Integer sample size tolerance is zero; deterministic power tolerance is 0.0001 absolute. Every planned attempt counts.

The v1 JavaScript evaluators are deliberately quarantined and throw an error if run. Their original source files remain under `historical/evaluator/*.disabled` for audit. They must not be used to support current performance claims. A model reviewer inside the workflow is not the scientific evaluation oracle. See [methodology](../docs/audited-methodology.md).
