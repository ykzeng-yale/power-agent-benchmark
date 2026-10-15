#!/usr/bin/env python3
"""Verify public identities, exact requests and aggregates, not restricted gates."""
import collections
import hashlib
import json
import math
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads((ROOT / p).read_text())

def q(values, p):
    x = sorted(values)
    at = (len(x) - 1) * p
    i = int(at)
    return x[i] + (at - i) * (x[min(i + 1, len(x) - 1)] - x[i])

def main():
    manifest = load('manifest.json')
    assert all(sha(ROOT / name) == value for name, value in manifest['files'].items())
    p = load('protocol-public.json')
    assert sha(ROOT / 'public/questions-only.json') == p['question_payload_sha256']
    assert sha(ROOT / 'audited/oracles.json') == p['private_reference_sha256']
    assert sha(ROOT / 'audited/tasks.json') == p['original_task_sha256']
    assert sha(ROOT / 'audited/reference-specifications.json') == p['original_specification_sha256']
    questions = load('public/questions-only.json')
    requests = {r['job_id']: r['request_sha256'] for r in load('public/request-identities.json')['requests']}
    scores = load('outcomes/scored-results.json')['scores']
    rows = load('outcomes/attempt-summaries.json')['records']
    aggregate = load('outcomes/aggregate-results.json')
    assert len(scores) == len(rows) == len(requests) == len(p['jobs']) == 48
    assert {r['job_id'] for r in scores} == {r['job_id'] for r in rows} == set(requests)
    for job in p['jobs']:
        request = dict(p['common'], query=questions[job['question_index']]['query'], workflowMode=job['mode'])
        actual = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        assert actual == requests[job['job_id']]
    oracles = {r['id']: r for r in load('audited/oracles.json')['tasks']}
    for s in scores:
        o = oracles[s['task_id']]
        returned = s['primary_returned']
        numeric = type(returned.get('value')) in (int, float) and math.isfinite(returned['value'])
        numeric = numeric and abs(returned['value'] - o['value']) <= o['absolute_tolerance']
        assert bool(numeric) == s['primary_numeric_pass']
    for mode in ['single', 'multi']:
        ss = [s for s in scores if s['mode'] == mode]
        rr = [r for r in rows if r['mode'] == mode]
        a = aggregate['modes'][mode]
        assert a['planned_attempts'] == len(ss) == 24
        for key in ['strict_pass', 'completed', 'primary_numeric_pass', 'primary_unit_pass', 'design_pass',
                    'current_execution_pass', 'required_review_pass', 'transport_pass', 'runtime_contract_pass']:
            assert a[key] == sum(s[key] is True for s in ss)
        times = [r['duration_seconds'] for r in rr]
        assert a['duration_seconds']['median'] == statistics.median(times)
        assert a['duration_seconds']['q25'] == q(times, .25)
        assert a['duration_seconds']['q75'] == q(times, .75)
        assert a['logical_model_calls'] == sum(r['budget_used']['model_calls'] for r in rr)
        assert a['R_executions'] == sum(len(r['R_evidence']) for r in rr)
        for k in ['input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens']:
            assert a['usage'][k] == sum(r['usage'][k] for r in rr)
        for tier in [1, 2, 3, 4]:
            t = [s for s in ss if s['tier'] == tier]
            assert aggregate['tiers'][mode][str(tier)] == {'planned': len(t), 'primary_numeric': sum(s['primary_numeric_pass'] for s in t), 'strict': sum(s['strict_pass'] for s in t)}
    pairs = collections.defaultdict(dict)
    for s in scores:
        pairs[(s['task_id'], s['repeat'])][s['mode']] = s['strict_pass']
    counts = dict.fromkeys(['both_pass', 'single_only', 'multi_only', 'both_fail'], 0)
    for pair in pairs.values():
        k = 'both_pass' if pair['single'] and pair['multi'] else 'single_only' if pair['single'] else 'multi_only' if pair['multi'] else 'both_fail'
        counts[k] += 1
    assert counts == aggregate['paired']
    print('PASS: public file identities,48exactrequest identities,primary numeric comparison,mode/tier aggregates,elapsed quartiles,tokens,R/modelcounts andpaired outcomes.')
    print('Restricted raw stdout/code/review binding gates were not re-executed from this public derivative.')

if __name__ == '__main__':
    main()
