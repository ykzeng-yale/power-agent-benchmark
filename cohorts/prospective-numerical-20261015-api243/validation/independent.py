#!/usr/bin/env python3
"""Post-publication reproduction of the frozen independent reference methods."""
import importlib.util
import json
import math
import pathlib
import sys

import scipy
from scipy.stats import norm

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location('original_independent_core', HERE / 'independent-core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def calculate(s):
    p = s['parameters']
    if s['method'] == 'logrank_freedman':
        return math.ceil(((p['HR'] + 1) / (p['HR'] - 1)) ** 2
                         * (norm.ppf(.975) + norm.ppf(p['power'])) ** 2 / (p['pE'] + p['pC']))
    if s['method'] == 'cluster_rate_cv':
        return math.ceil(1 + (norm.ppf(.975) + norm.ppf(p['power'])) ** 2
                         * ((p['r1'] + p['r2']) / p['exposure']
                            + p['cv'] ** 2 * (p['r1'] ** 2 + p['r2'] ** 2)) / (p['r1'] - p['r2']) ** 2)
    return core.calculate(s)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Supply a new output JSON path. No provider/model calls are made.')
    out = pathlib.Path(sys.argv[1])
    if out.exists():
        raise ValueError('Refuse reference output overwrite')
    specs = json.loads((ROOT / 'audited/reference-specifications.json').read_text())
    by_id = {o['id']: o for o in json.loads((ROOT / 'audited/oracles.json').read_text())['tasks']}
    rows = []
    for s in specs:
        value = float(calculate(s))
        expected = by_id[s['id']]['value']
        difference = abs(value - expected)
        rows.append({'id': s['id'], 'scipy_value': value, 'R_value': expected,
                     'absolute_difference': difference,
                     'verified': math.isfinite(value) and difference < 1e-8})
    result = {'scope': 'Reproduction after public release, not a new model experiment or a replacement oracle.',
              'scipy_version': scipy.__version__, 'all_verified': all(r['verified'] for r in rows), 'tasks': rows}
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'references': len(rows), 'verified': sum(r['verified'] for r in rows), 'scipy': scipy.__version__}))
    assert result['all_verified']
