#!/usr/bin/env python3
"""Deterministic post-capture summaries; no new scores or provider calls."""
import collections
import hashlib
import json
import pathlib
import statistics

HERE = pathlib.Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def quantile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (index - low) * (values[high] - values[low])

def main():
    protocol_path = HERE / 'protocol.json'
    record_path = HERE / 'results/records.json'
    score_path = HERE / 'scored-results.json'
    protocol = json.loads(protocol_path.read_text())
    captured = json.loads(record_path.read_text())
    scored = json.loads(score_path.read_text())
    assert scored['protocol_sha256'] == captured['protocol_sha256'] == sha(protocol_path)
    assert scored['records_sha256'] == sha(record_path)
    jobs = {j['job_id']: j for j in protocol['jobs']}
    scores = scored['scores']
    records = captured['records']
    assert len(jobs) == len(scores) == len(records) == 48
    assert set(jobs) == {s['job_id'] for s in scores} == {r['job_id'] for r in records}
    modes = {}
    gate_names = ['completed', 'primary_numeric_pass', 'primary_unit_pass', 'design_pass',
                  'current_execution_pass', 'required_review_pass', 'context_topology_pass',
                  'transport_pass', 'runtime_contract_pass', 'strict_pass']
    for mode in ['single', 'multi']:
        ss = [s for s in scores if s['mode'] == mode]
        rr = [r for r in records if r['mode'] == mode]
        bodies = [r.get('record') or {} for r in rr]
        durations = [r['duration_seconds'] for r in rr if isinstance(r.get('duration_seconds'), (int, float))]
        es = [e for r in bodies for e in r.get('executions', [])]
        calls = [t for r in bodies for t in r.get('trace', []) if t.get('type') == 'model_call']
        usage = {k: sum((r.get('usage') or {}).get(k, 0) for r in bodies)
                 for k in ['input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens']}
        role_cost = collections.defaultdict(float)
        for call in calls:
            u = call.get('usage') or {}
            router = call.get('role') == 'router'
            # First-party standard global uncached estimate. No cache tokens in
            # old forecast; report actual cache categories separately. Source
            # charges and missing response usage cannot be inferred here.
            price_input, price_output = (.1, .5) if router else (2, 10)
            prompt = sum(u.get(k, 0) for k in ['input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'])
            if router and prompt > 100000:
                price_input, price_output = .5, 2.5
            role_cost[call.get('role')] += (u.get('input_tokens', 0) * price_input
                                           + u.get('output_tokens', 0) * price_output) / 1e6
        error_counts = collections.Counter(error for s in ss for field in ['errors', 'transport_errors', 'runtime_contract_errors'] for error in s[field])
        modes[mode] = {'planned_attempts': len(ss), **{k: sum(s[k] is True for s in ss) for k in gate_names},
                       'duration_seconds': {'median': statistics.median(durations), 'q25': quantile(durations, .25),
                                            'q75': quantile(durations, .75), 'minimum': min(durations), 'maximum': max(durations)},
                       'logical_model_calls': sum((r.get('budget') or {}).get('used', {}).get('model_calls', 0) for r in bodies),
                       'recorded_model_responses': len(calls), 'R_executions': len(es),
                       'R_successful_exit': sum(e.get('success') is True for e in es),
                       'R_failed_exit_or_guard': sum(e.get('success') is not True for e in es),
                       'R_success_without_valid_numerical_payload': sum(e.get('success') is True and e.get('computed') is None for e in es),
                       'effective_repair_allowance_counts': dict(collections.Counter(str((r.get('budget') or {}).get('planned_repair_allowance')) for r in bodies)),
                       'final_candidate_round_counts': dict(collections.Counter(str((r.get('verification') or {}).get('current_candidate_round')) for r in bodies)),
                       'actual_role_models': {role: sorted({model for r in bodies for model in (r.get('actual_role_models') or {}).get(role, [])})
                                              for role in ['router', 'planner', 'coder', 'reviewer']},
                       'usage': usage, 'standard_token_estimate_usd_excluding_cache': sum(role_cost.values()),
                       'standard_token_estimate_by_role_usd': dict(role_cost), 'failure_gate_counts': dict(error_counts),
                       'failed_job_ids': [s['job_id'] for s in ss if not s['strict_pass']]}
    questions = []
    for id_ in dict.fromkeys(j['task_id'] for j in protocol['jobs']):
        ss = [s for s in scores if s['task_id'] == id_]
        questions.append({'task_id': id_, 'tier': ss[0]['tier'],
                          **{mode: {'attempts': 2, 'completed': sum(s['completed'] for s in ss if s['mode'] == mode),
                                    'primary_numeric': sum(s['primary_numeric_pass'] for s in ss if s['mode'] == mode),
                                    'strict_primary_contract': sum(s['strict_pass'] for s in ss if s['mode'] == mode)}
                             for mode in ['single', 'multi']}})
    tiers = {mode: {str(tier): {'planned': sum(s['tier'] == tier and s['mode'] == mode for s in scores),
                               'primary_numeric': sum(s['tier'] == tier and s['mode'] == mode and s['primary_numeric_pass'] for s in scores),
                               'strict': sum(s['tier'] == tier and s['mode'] == mode and s['strict_pass'] for s in scores)}
                    for tier in [1, 2, 3, 4]} for mode in ['single', 'multi']}
    output = {'protocol_sha256': sha(protocol_path), 'records_sha256': sha(record_path), 'scored_results_sha256': sha(score_path),
              'analysis_source_sha256': sha(pathlib.Path(__file__)), 'planned_attempts': 48,
              'modes': modes, 'tiers': tiers, 'questions': questions,
              'paired': scored['summary']['paired_attempts'],
              'duration_definition': 'End-to-end CLI captured duration; quartiles use linear interpolation at index(n-1)q.',
              'cost_qualification': 'Observed-response standard global token-price estimate only, not invoice. Actual cache counts retained but excluded from estimate; source tools, unobserved responses/retries and platform charges excluded. Official pricing source https://platform.claude.com/docs/en/about-claude/pricing read2026-10-15.',
              'scope': 'Primary quantity/declared design/evidence/review contract only. Ancillary scientific claims audited separately; repeats are clustered within12questions. No new scoring/gate or hypothesis added by this summary.'}
    out = HERE / 'aggregate-results-private.json'
    if out.exists():
        raise ValueError('refuse_summary_overwrite')
    out.write_text(json.dumps(output, indent=2) + '\n')
    out.chmod(0o600)
    print(json.dumps({'modes': modes, 'tiers': tiers, 'paired': output['paired']}, indent=2))

if __name__ == '__main__':
    main()
