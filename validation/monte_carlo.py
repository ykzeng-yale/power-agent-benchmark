#!/usr/bin/env python3
"""Validate all-trial Monte Carlo accounting against a predeclared analytic target."""
import hashlib
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def wilson(k, n, z=1.959963984540054):
    p = k/n
    denominator = 1+z*z/n
    center = (p+z*z/(2*n))/denominator
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return [center-half, center+half]


def validate_record(record, protocol, analytic_power):
    """Failures stay in the denominator; success-conditioned power is rejected."""
    errors = []
    b = protocol['trials']
    counts = [record.get(k) for k in ['rejections', 'nonrejections', 'failures']]
    if any(type(k) is not int or k < 0 for k in counts) or sum(counts) != b:
        return {'passed': False, 'errors': ['invalid_all_trials_accounting']}
    k = counts[0]
    if record.get('trials') != b:
        errors.append('trials_mismatch')
    if record.get('seed') not in protocol['seeds']:
        errors.append('undeclared_seed')
    if record.get('method') != protocol['method']:
        errors.append('different_test')
    cases = {c['id']: c for c in protocol['cases']}
    if record.get('case_id') not in cases or record.get('parameters') != cases[record.get('case_id')]:
        errors.append('different_dgp')
    estimate = k/b
    mcse = math.sqrt(estimate*(1-estimate)/b)
    for field, wanted in [('estimate', estimate), ('mcse', mcse)]:
        got = record.get(field)
        if type(got) not in [int, float] or not math.isfinite(got) or abs(got-wanted) > 1e-12:
            errors.append(field+'_mismatch')
    interval = record.get('wilson_95')
    if not isinstance(interval, list) or len(interval) != 2 or any(abs(a-bb) > 1e-12 for a, bb in zip(interval, wilson(k, b))):
        errors.append('interval_mismatch')
    bound = protocol['calibration_standard_errors']*math.sqrt(analytic_power*(1-analytic_power)/b)
    if abs(estimate-analytic_power) > bound:
        errors.append('analytic_calibration_mismatch')
    return {'passed': not errors, 'errors': errors, 'analytic_power': analytic_power,
            'all_trials_estimate': estimate, 'mcse': mcse, 'calibration_bound': bound}


def main():
    from scipy.stats import nct, t
    protocol_path = ROOT/'validation/monte-carlo-protocol.json'
    protocol = json.loads(protocol_path.read_text())
    if hashlib.sha256((ROOT/'validation/monte_carlo.R').read_bytes()).hexdigest() != protocol['r_source_sha256']:
        raise ValueError('Monte Carlo source changed after protocol freeze')
    rows = json.loads((ROOT/'validation/monte-carlo-results.json').read_text())['records']
    expected = {(c['id'], seed) for c in protocol['cases'] for seed in protocol['seeds']}
    if {(r['case_id'], r['seed']) for r in rows} != expected or len(rows) != len(expected):
        raise ValueError('Missing or duplicated planned simulation')
    validated = []
    for r in rows:
        p = r['parameters']
        df = 2*p['n_per_arm']-2
        nc = p['mean_difference']*math.sqrt(p['n_per_arm']/(2*(p['tau']**2+p['sigma']**2/p['measurements'])))
        critical = t.isf(p['alpha']/2, df)
        exact = float(nct.sf(critical, df, nc)+nct.cdf(-critical, df, nc))
        out = validate_record(r, protocol, exact)
        out.update(case_id=r['case_id'], seed=r['seed'], R_scipy_difference=abs(exact-r['analytic_power']), failures=r['failures'])
        validated.append(out)
    result = {'kind': 'Constructed reference Monte Carlo calibration; not an LLM benchmark result',
              'planned_simulations': len(expected), 'recorded_simulations': len(rows),
              'all_validated': all(v['passed'] for v in validated), 'records': validated}
    (ROOT/'validation/monte-carlo-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    assert result['all_validated']


if __name__ == '__main__':
    main()
