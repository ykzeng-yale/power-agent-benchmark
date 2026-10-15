#!/usr/bin/env python3
"""Numerical-only prospective scorer v1. No provider calls or source discovery.

Scientific oracles are read only in this offline program. Runtime stdout is not
trusted merely because a JSON field claims execution: code digests, captured
stdout, current candidate IDs, and executed required reviews are checked.
These checks establish recorded provenance, not formula correctness or an OS
sandbox. The independent reference establishes the specified primary quantity.
"""
import argparse
import base64
import hashlib
import json
import math
import pathlib
import re
import statistics

VERSION = 'prospective-numerical-score1-api2.4.3'

def digest(b):
    return hashlib.sha256(b).hexdigest()

def strict_json(text):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('duplicate_json_key')
            out[k] = v
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))

def obj(x):
    return x if isinstance(x, dict) else {}

def arr(x):
    return x if isinstance(x, list) else []

def finite(x):
    return type(x) in (int, float) and math.isfinite(x)

def token(x):
    return str(x).strip().lower().replace('-', '_').replace(' ', '_')

def unit(x):
    # Predeclared synonyms; no annotation stripping or count conversion.
    return {'participants_per_group': 'participants_per_arm'}.get(token(x), token(x))

def alternative(x):
    # Runtime design schema expresses omnibus tests as not-applicable sidedness.
    return {'omnibus': 'not_applicable', 'two_tailed': 'two_sided',
            'one_tailed': 'one_sided'}.get(token(x), token(x))

def json_blocks(text):
    """Independent port of the frozen host's balanced-container extraction."""
    lines = []
    for line in text.split('\n'):
        if re.fullmatch(r'[ \t]*(?:\[,\d+\][ \t]*)+', line) or re.fullmatch(r'[ \t]*\[\d+,\][ \t]*', line):
            lines.append('')
        else:
            lines.append(re.sub(r'^[ \t]*\[(?:\d+|\d+,)\][ \t]+', '', line))
    text = '\n'.join(lines)
    blocks = []
    start = 0
    outside_quote = outside_escape = False
    while start < len(text):
        char = text[start]
        if outside_quote:
            if outside_escape:
                outside_escape = False
            elif char == '\\':
                outside_escape = True
            elif char == '"':
                outside_quote = False
            start += 1
            continue
        if char == '"':
            outside_quote = True
            start += 1
            continue
        if char not in '{[':
            start += 1
            continue
        stack, quoted, escaped, end = [], False, False, start
        while end < len(text):
            c = text[end]
            if quoted:
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '"':
                    quoted = False
            elif c == '"':
                quoted = True
            elif c in '{[':
                stack.append(c)
            elif c in '}]':
                opening = stack.pop() if stack else None
                if opening != ('{' if c == '}' else '[') or not stack:
                    end += 1
                    break
            end += 1
        blocks.append(text[start:end].strip())
        start = end
    return blocks

def stdout_result(output):
    text = str(output or '').replace('\r\n', '\n')
    start = text.rfind('\nPOWER_AGENT_SESSION_INFO_BEGIN\n')
    if start != -1 and re.search(r'\nPOWER_AGENT_SESSION_INFO_END\s*$', text):
        text = text[:start]
    markers = [line for line in text.split('\n') if line.startswith('POWER_AGENT_RESULT=')]
    unmarked = json_blocks('\n'.join(line for line in text.split('\n') if not line.startswith('POWER_AGENT_RESULT=')))
    if len(markers) > 1 or (markers and unmarked):
        return None
    candidates = [markers[0][len('POWER_AGENT_RESULT='):]] if markers else unmarked
    if len(candidates) != 1:
        return None
    try:
        value = strict_json(candidates[0])
        rows = obj(value).get('results')
        if not isinstance(rows, list) or not rows:
            return None
        identities = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'metric', 'value', 'unit'}:
                return None
            if not all(isinstance(row[k], str) and row[k].strip() for k in ['metric', 'unit']) or not finite(row['value']):
                return None
            identities.append((row['metric'], row['unit']))
        if len(set(identities)) != len(identities):
            return None
        return value
    except (ValueError, TypeError):
        return None

def execution_valid(e, numerical=False):
    if not isinstance(e, dict) or e.get('success') is not True or e.get('exitCode') != 0:
        return False
    if e.get('timedOut') is True or e.get('outputLimit') is True:
        return False
    if not isinstance(e.get('code'), str) or digest(e['code'].encode()) != e.get('code_sha256'):
        return False
    parsed = stdout_result(e.get('output'))
    if numerical:
        return isinstance(parsed, dict) and parsed == e.get('computed')
    # Successful file-only evidence is valid for inspection, but cannot support a
    # numerical row. A claimed computed result must still match stdout.
    return e.get('computed') is None or (isinstance(parsed, dict) and parsed == e.get('computed'))

def linked(row, executions):
    return any(any(isinstance(v, dict) and v.get('metric') == row.get('metric')
                   and v.get('unit') == row.get('unit') and finite(v.get('value'))
                   and finite(row.get('value'))
                   and abs(v['value'] - row['value']) <= 1e-9 * max(1, abs(v['value']))
                   for v in arr(obj(e.get('computed')).get('results')))
               for e in executions if execution_valid(e, True))

def _check_record(record, oracle, mode):
    r = obj(record)
    errors = []
    completed = r.get('success') is True and r.get('status') == 'completed' and r.get('scientificStatus') == 'completed'
    if not completed:
        errors.append('workflow_not_completed')
    answer = obj(r.get('answer'))
    rows = arr(answer.get('results'))
    metric_matches = [v for v in rows if isinstance(v, dict) and v.get('metric') == oracle['metric']]
    matches = [v for v in metric_matches if unit(v.get('unit')) == unit(oracle['unit'])]
    # Metric+unit is the primary identity. A separate same-metric total count is
    # legitimate. One wrong-unit row can show numerical agreement diagnostically,
    # but cannot pass the unit/strict gate.
    primary = matches[0] if len(matches) == 1 else metric_matches[0] if not matches and len(metric_matches) == 1 else {}
    numerical = bool(primary) and finite(primary.get('value'))
    v = primary.get('value')
    if numerical and oracle['metric'] == 'sample_size':
        numerical = v >= 1 and v == int(v)
    if numerical and oracle['metric'] == 'power':
        numerical = 0 <= v <= 1
    numerical = bool(numerical and abs(v - oracle['value']) <= oracle['absolute_tolerance'])
    if not numerical:
        errors.append('primary_numeric_mismatch_or_missing_or_noninteger')
    units_ok = len(matches) == 1 and unit(primary.get('unit')) == unit(oracle['unit'])
    if not units_ok:
        errors.append('primary_unit_mismatch')
    design = obj(r.get('design'))
    design_errors = []
    for key, want in oracle['design'].items():
        if want is None:
            continue
        got = design.get(key)
        ok = (finite(got) and abs(got - want) <= 1e-12) if finite(want) else (
            alternative(got) == alternative(want) if key == 'alternative' else token(got) == token(want))
        if not ok:
            design_errors.append('design_mismatch:' + key)
    if oracle['metric'] == 'sample_size' and unit(design.get('sample_size_unit')) != unit(oracle['unit']):
        design_errors.append('design_mismatch:sample_size_unit')
    errors += design_errors
    evidence_errors = []
    es = arr(r.get('executions'))
    ids_all = [e.get('id') for e in es if isinstance(e, dict)]
    if any(not isinstance(x, str) for x in ids_all) or len(ids_all) != len(set(ids_all)):
        evidence_errors.append('execution_ids_not_unique_strings')
    round_ = obj(r.get('verification')).get('current_candidate_round')
    if type(round_) is not int or round_ < 0:
        evidence_errors.append('missing_current_candidate_round')
    declared = arr(answer.get('evidence_ids'))
    current = [e for e in es if isinstance(e, dict) and e.get('role') == 'coder'
               and e.get('candidate_round') == round_ and execution_valid(e)]
    accepted = [e for e in current if e.get('id') in declared]
    if (not declared or any(not isinstance(x, str) for x in declared)
            or len(set(declared)) != len(declared)
            or set(declared) != {e.get('id') for e in accepted}):
        evidence_errors.append('answer_evidence_not_all_current_valid_unique')
    if not primary or not linked(primary, accepted):
        evidence_errors.append('primary_not_linked_to_actual_current_coder_stdout')
    # Check every additional submitted row too: a correct primary value cannot
    # hide an invented ancillary numerical result.
    if any(not isinstance(row, dict) or not linked(row, accepted) for row in rows):
        evidence_errors.append('answer_row_missing_actual_execution_link')
    if r.get('results') != rows:
        evidence_errors.append('top_level_results_not_current_answer')
    errors += evidence_errors
    review_errors = []
    review = obj(r.get('review'))
    vids = arr(review.get('independent_check_evidence_ids'))
    checks = [e for e in es if isinstance(e, dict) and e.get('role') == 'reviewer'
              and e.get('candidate_round') == round_ and e.get('id') in vids and execution_valid(e)]
    if (r.get('verificationPolicy') != 'required' or review.get('verdict') != 'pass'
            or not vids or len(vids) != len(set(vids))
            or set(vids) != {e.get('id') for e in checks}
            or not any(execution_valid(e, True) for e in checks)):
        review_errors.append('required_current_executed_review_missing')
    inspected = arr(review.get('checked_evidence_ids'))
    if not set(declared) <= set(inspected) or len(inspected) != len(set(inspected)):
        review_errors.append('review_does_not_cover_current_answer')
    if any(len([e for e in es if isinstance(e, dict) and e.get('id') == id_
                and e.get('role') == 'coder' and e.get('candidate_round') == round_]) != 1 for id_ in inspected):
        review_errors.append('review_inspected_stale_or_missing_evidence')
    if (not arr(review.get('checks')) or any(obj(c).get('passed') is not True for c in arr(review.get('checks')))
            or any(obj(i).get('severity') in ['major', 'critical'] for i in arr(review.get('issues')))):
        review_errors.append('review_contains_failed_or_major_checks')
    rounds = [v for v in arr(obj(r.get('verification')).get('rounds')) if obj(v).get('round') == round_]
    if len(rounds) != 1 or obj(rounds[0]).get('review') != review:
        review_errors.append('current_review_not_bound_to_verification_round')
    topology_ok = r.get('workflowMode') == mode
    vr = obj(rounds[0]) if len(rounds) == 1 else {}
    if mode == 'multi':
        pre_ids = arr(vr.get('precheck_evidence_ids'))
        pre = [e for e in es if isinstance(e, dict) and e.get('role') == 'reviewer'
               and e.get('candidate_round') == round_ and e.get('id') in pre_ids
               and str(e.get('worker_phase', '')).startswith('blind_') and execution_valid(e, True)]
        revealed = [t for t in arr(r.get('trace')) if obj(t).get('type') == 'candidate_revealed'
                    and obj(t).get('candidate_round') == round_]
        trace = arr(r.get('trace'))
        reveal_index = trace.index(revealed[0]) if len(revealed) == 1 else -1
        prior_returns = {obj(t.get('result')).get('evidence_id') for t in trace[:reveal_index]
                         if obj(t).get('type') == 'tool_result' and obj(t).get('tool') == 'execute_r'
                         and obj(t.get('result')).get('success') is True}
        topology_ok = bool(topology_ok and vr.get('context_topology') == 'fresh_review_conversation'
                           and vr.get('blind_precheck') is True and vr.get('candidate_revealed') is True
                           and pre_ids and len(pre_ids) == len(set(pre_ids))
                           and set(pre_ids) == {e.get('id') for e in pre}
                           and len(revealed) == 1 and set(arr(revealed[0].get('precheck_evidence_ids'))) == set(pre_ids)
                           and set(pre_ids) <= prior_returns)
    else:
        topology_ok = bool(topology_ok and vr.get('context_topology') == 'shared_author_conversation'
                           and vr.get('blind_precheck') is False)
    if not topology_ok:
        review_errors.append('requested_context_topology_not_recorded')
    errors += review_errors
    return {'strict_primary_contract_pass': not errors, 'completed': completed,
            'primary_numeric_pass': numerical, 'primary_unit_pass': units_ok,
            'design_pass': not design_errors, 'current_execution_pass': not evidence_errors,
            'required_review_pass': not review_errors, 'context_topology_pass': topology_ok,
            'primary_returned': primary or None, 'errors': sorted(set(errors))}

def check_record(record, oracle, mode):
    try:
        return _check_record(record, oracle, mode)
    except (ValueError, TypeError, KeyError, OverflowError):
        # Malformed model/capture records are planned failures, never dropped
        # observations or an evaluator crash that suppresses the denominator.
        return {'strict_primary_contract_pass': False, 'completed': False,
                'primary_numeric_pass': False, 'primary_unit_pass': False,
                'design_pass': False, 'current_execution_pass': False,
                'required_review_pass': False, 'context_topology_pass': False,
                'primary_returned': None, 'errors': ['malformed_record_schema']}

def check_runtime(record, protocol, mode):
    r = obj(record)
    errors = []
    c = protocol['common']
    if r.get('harnessVersion') != protocol['harness_version']:
        errors.append('runtime_version_mismatch')
    if r.get('role_models') != c['roleModels']:
        errors.append('requested_role_models_mismatch')
    models = obj(r.get('actual_role_models'))
    for role, expected in c['roleModels'].items():
        got = models.get(role)
        # The router is advisory and may return unavailable before a valid
        # response receipt. Scientific roles must have actual model receipts.
        if role == 'router' and got == []:
            continue
        if not isinstance(got, list) or not got or set(got) != {expected}:
            errors.append('actual_role_model_mismatch:' + role)
    budget = obj(r.get('budget'))
    for key in ['maxModelCalls', 'maxExecutions', 'maxSearches', 'maxSourceReads', 'maxSourceChars', 'deadlineMs', 'maxRExecutionMs']:
        if obj(budget.get('global')).get(key) != c[key]:
            errors.append('global_budget_mismatch:' + key)
    if budget.get('profile') != c['budgetProfile']:
        errors.append('phase_profile_mismatch')
    if budget.get('planned_repair_allowance') != c['maxRepairs']:
        errors.append('effective_repair_allowance_not_two')
    used = obj(budget.get('used'))
    for key, ceiling in [('model_calls', c['maxModelCalls']), ('executions', c['maxExecutions'])]:
        if type(used.get(key)) is not int or not 0 <= used[key] <= ceiling:
            errors.append('budget_use_invalid:' + key)
    for key in ['execute_r', 'search_sources', 'read_source']:
        if obj(r.get('capabilities')).get(key) is not True:
            errors.append('required_available_tool_missing:' + key)
    if obj(r.get('referenceAudit')).get('status') == 'failed':
        errors.append('deterministic_reference_audit_failed')
    return errors

def check_transport(row, raw_path, protocol_sha, request_sha):
    errors = []
    if row.get('dispatched') is not True or row.get('transport_captured') is not True:
        return ['not_dispatched_or_not_captured']
    try:
        b = raw_path.read_bytes()
        if digest(b) != row.get('transport_sha256'):
            errors.append('transport_file_hash_mismatch')
        t = strict_json(b)
        for k in ['job_id', 'task_id', 'mode', 'repeat']:
            if t.get(k) != row.get(k):
                errors.append('transport_job_mismatch:' + k)
        if t.get('protocol_sha256') != protocol_sha or row.get('protocol_sha256') != protocol_sha:
            errors.append('transport_protocol_mismatch')
        if t.get('request_sha256') != request_sha:
            errors.append('transport_request_mismatch')
        stdout = base64.b64decode(t['stdout_base64'], validate=True)
        stderr = base64.b64decode(t['stderr_base64'], validate=True)
        if digest(stdout) != t.get('stdout_sha256') or digest(stderr) != t.get('stderr_sha256'):
            errors.append('transport_captured_bytes_hash_mismatch')
        if strict_json(stdout) != row.get('record'):
            errors.append('parsed_record_differs_from_captured_stdout')
        if t.get('exit_code') != 0 or row.get('exit_code') != 0 or t.get('runner_failure') or row.get('process_error') or row.get('capture_error'):
            errors.append('transport_or_process_failed')
        if row.get('runtime_changed'):
            errors.append('runtime_changed_during_attempt')
    except (OSError, ValueError, TypeError, KeyError):
        errors.append('transport_unreadable_or_malformed')
    return sorted(set(errors))

def summarize(scores):
    summary = {}
    for mode in ['single', 'multi']:
        rows = [r for r in scores if r['mode'] == mode]
        keys = ['strict_pass', 'completed', 'primary_numeric_pass', 'primary_unit_pass', 'design_pass', 'current_execution_pass', 'required_review_pass']
        summary[mode] = {'planned': len(rows), **{k: sum(r.get(k) is True for r in rows) for k in keys},
                         'median_captured_duration_seconds': statistics.median([r['duration_seconds'] for r in rows if finite(r.get('duration_seconds'))]) if any(finite(r.get('duration_seconds')) for r in rows) else None}
    pairs = {}
    for r in scores:
        pairs.setdefault((r['task_id'], r['repeat']), {})[r['mode']] = r['strict_pass']
    summary['paired_attempts'] = {'both_pass': 0, 'single_only': 0, 'multi_only': 0, 'both_fail': 0}
    for p in pairs.values():
        name = 'both_pass' if p.get('single') and p.get('multi') else 'single_only' if p.get('single') else 'multi_only' if p.get('multi') else 'both_fail'
        summary['paired_attempts'][name] += 1
    summary['inference_scope'] = 'Two repeats per task/topology are repeated attempts, not 48 independent scientific designs. Report task-level outcomes, tier denominators, paired discordances, token use and failures; no broad superiority claim.'
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocol', type=pathlib.Path, required=True)
    ap.add_argument('--records', type=pathlib.Path, required=True)
    ap.add_argument('--oracles', type=pathlib.Path, required=True)
    ap.add_argument('--questions', type=pathlib.Path, required=True)
    ap.add_argument('--out', type=pathlib.Path, required=True)
    a = ap.parse_args()
    protocol = strict_json(a.protocol.read_bytes())
    if digest(a.oracles.read_bytes()) != protocol['private_reference_sha256']:
        raise ValueError('private_reference_drift')
    oracles = {o['id']: o for o in strict_json(a.oracles.read_bytes())['tasks']}
    questions = strict_json(a.questions.read_bytes())
    if digest(a.questions.read_bytes()) != protocol['question_payload_sha256']:
        raise ValueError('question_drift')
    raw = strict_json(a.records.read_bytes())
    protocol_sha = digest(a.protocol.read_bytes())
    if raw.get('protocol_sha256') != protocol_sha:
        raise ValueError('aggregate_protocol_drift')
    actual = arr(raw.get('records'))
    ids = [r.get('job_id') for r in actual]
    if len(ids) != len(set(ids)) or any(j not in {v['job_id'] for v in protocol['jobs']} for j in ids):
        raise ValueError('duplicate_or_unplanned_record')
    scores = []
    for job in protocol['jobs']:
        row = next((r for r in actual if r.get('job_id') == job['job_id']), dict(job, dispatched=False))
        # Reconstruct exactly the public request, without importing the runner.
        request = dict(protocol['common'], query=questions[job['question_index']]['query'], workflowMode=job['mode'])
        request_sha = digest(json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
        errors = check_transport(row, a.records.parent / 'transports' / (job['job_id'] + '.transport.json'), protocol_sha, request_sha)
        result = check_record(row.get('record'), oracles[job['task_id']], job['mode'])
        try:
            runtime_errors = check_runtime(row.get('record'), protocol, job['mode'])
        except (ValueError, TypeError, KeyError):
            runtime_errors = ['malformed_runtime_metadata']
        scores.append(dict(job, **result, transport_pass=not errors, runtime_contract_pass=not runtime_errors,
                           strict_pass=result['strict_primary_contract_pass'] and not errors and not runtime_errors,
                           transport_errors=errors, runtime_contract_errors=runtime_errors, duration_seconds=row.get('duration_seconds'),
                           status=obj(row.get('record')).get('scientificStatus'), usage=obj(row.get('record')).get('usage'),
                           effective_repair_allowance=obj(obj(row.get('record')).get('budget')).get('planned_repair_allowance')))
    out = {'scorer_version': VERSION, 'protocol_sha256': protocol_sha,
           'records_sha256': digest(a.records.read_bytes()), 'planned_attempts': len(protocol['jobs']),
           'summary': summarize(scores), 'scores': scores}
    if a.out.exists():
        raise ValueError('refuse_score_overwrite')
    a.out.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    a.out.chmod(0o600)
    print(json.dumps(out['summary'], indent=2))

if __name__ == '__main__':
    main()
