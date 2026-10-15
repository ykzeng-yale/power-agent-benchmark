"""Controlled positive/negative tests. No model, network or R calls."""
import base64
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import run
import score

ORACLE = {'id': 'synthetic-test-only', 'metric': 'sample_size', 'unit': 'participants_per_group',
          'value': 64, 'absolute_tolerance': 0,
          'design': {'method': 'two_sample_t', 'alpha': .05, 'alternative': 'two_sided', 'allocation_ratio': 1}}

def evidence(id_, role, rows, round_=0, blind=False):
    code = 'synthetic fixture; not scientific execution'
    payload = {'results': copy.deepcopy(rows)}
    return {'id': id_, 'role': role, 'candidate_round': round_, 'success': True,
            'exitCode': 0, 'code': code, 'code_sha256': score.digest(code.encode()),
            'timedOut': False, 'outputLimit': False,
            'computed': payload, 'output': 'POWER_AGENT_RESULT=' + json.dumps(payload) + '\n',
            'worker_phase': 'blind_verification' if blind else 'verification' if role == 'reviewer' else 'solver'}

def valid(mode='single'):
    rows = [{'metric': 'sample_size', 'value': 64, 'unit': 'participants_per_arm'}]
    review = {'verdict': 'pass', 'checked_evidence_ids': ['e1'], 'independent_check_evidence_ids': ['e2'],
              'checks': [{'name': 'test-only', 'passed': True}], 'issues': []}
    vr = {'round': 0, 'review': review,
          'context_topology': 'fresh_review_conversation' if mode == 'multi' else 'shared_author_conversation',
          'blind_precheck': mode == 'multi', 'candidate_revealed': True,
          'precheck_evidence_ids': ['e2'] if mode == 'multi' else []}
    trace = [{'type': 'tool_result', 'tool': 'execute_r', 'result': {'evidence_id': 'e2', 'success': True}}]
    if mode == 'multi':
        trace.append({'type': 'candidate_revealed', 'candidate_round': 0, 'precheck_evidence_ids': ['e2']})
    return {'success': True, 'status': 'completed', 'scientificStatus': 'completed',
            'workflowMode': mode, 'verificationPolicy': 'required',
            'answer': {'results': rows, 'evidence_ids': ['e1']}, 'results': copy.deepcopy(rows),
            'design': {'method': 'two_sample_t', 'alpha': .05, 'alternative': 'two-sided',
                       'allocation_ratio': 1, 'sample_size_unit': 'participants_per_group'},
            'executions': [evidence('e1', 'coder', rows), evidence('e2', 'reviewer', rows, blind=mode == 'multi')],
            'verification': {'current_candidate_round': 0, 'rounds': [vr]}, 'review': review, 'trace': trace}

def replace_rows(r, rows):
    r['answer']['results'] = copy.deepcopy(rows)
    r['results'] = copy.deepcopy(rows)
    for e in r['executions']:
        e['computed'] = {'results': copy.deepcopy(rows)}
        e['output'] = 'POWER_AGENT_RESULT=' + json.dumps(e['computed']) + '\n'

class ScientificGateTests(unittest.TestCase):
    def check(self, r, expected=False, oracle=ORACLE, mode='single'):
        result = score.check_record(r, oracle, mode)
        self.assertEqual(result['strict_primary_contract_pass'], expected, result)
        return result

    def test_valid_single(self):
        self.check(valid(), True)

    def test_valid_multi(self):
        self.check(valid('multi'), True, mode='multi')

    def test_group_arm_alias(self):
        r = valid()
        replace_rows(r, [{'metric': 'sample_size', 'value': 64, 'unit': 'participants_per_group'}])
        self.check(r, True)

    def test_same_metric_per_arm_and_total_are_distinct(self):
        r = valid()
        replace_rows(r, [{'metric': 'sample_size', 'value': 64, 'unit': 'participants_per_arm'},
                         {'metric': 'sample_size', 'value': 128, 'unit': 'participants_total'}])
        self.check(r, True)

    def test_correct_numeric_wrong_unit(self):
        r = valid()
        replace_rows(r, [{'metric': 'sample_size', 'value': 64, 'unit': 'participants_total'}])
        result = self.check(r)
        self.assertTrue(result['primary_numeric_pass'])
        self.assertFalse(result['primary_unit_pass'])

    def test_annotated_design_unit_not_stripped(self):
        r = valid()
        r['design']['sample_size_unit'] = 'participants_per_group (equal allocation)'
        self.check(r)

    def test_wrong_minimum(self):
        r = valid()
        replace_rows(r, [{'metric': 'sample_size', 'value': 65, 'unit': 'participants_per_arm'}])
        self.check(r)

    def test_noninteger(self):
        r = valid()
        replace_rows(r, [{'metric': 'sample_size', 'value': 63.99, 'unit': 'participants_per_arm'}])
        self.check(r)

    def test_bool_not_numeric(self):
        r = valid()
        r['answer']['results'][0]['value'] = True
        self.check(r)

    def test_nonfinite_not_numeric(self):
        r = valid()
        r['answer']['results'][0]['value'] = float('nan')
        self.check(r)

    def test_wrong_design_parameters(self):
        for key, bad in [('method', 'paired_t'), ('alpha', .025), ('alternative', 'one-sided'), ('allocation_ratio', 2)]:
            with self.subTest(key=key):
                r = valid()
                r['design'][key] = bad
                self.check(r)

    def test_partial_correct_result_cannot_pass(self):
        for status in ['failed', 'review_failed', 'budget_exhausted', 'needs_clarification']:
            with self.subTest(status=status):
                r = valid()
                r.update(success=False, status=status, scientificStatus=status)
                self.assertTrue(self.check(r)['primary_numeric_pass'])

    def test_missing_r_evidence(self):
        r = valid()
        r['answer']['evidence_ids'] = []
        self.check(r)

    def test_failed_coder_with_correct_output(self):
        r = valid()
        r['executions'][0]['success'] = False
        self.check(r)

    def test_bad_code_hash(self):
        r = valid()
        r['executions'][0]['code_sha256'] = '0' * 64
        self.check(r)

    def test_computed_result_not_in_real_stdout(self):
        r = valid()
        r['executions'][0]['output'] = 'calculation done but no JSON\n'
        self.check(r)

    def test_stdout_computed_disagreement(self):
        r = valid()
        r['executions'][0]['output'] = 'POWER_AGENT_RESULT={"results":[{"metric":"sample_size","value":999,"unit":"participants_per_arm"}]}\n'
        self.check(r)

    def test_stale_candidate_evidence(self):
        r = valid()
        r['verification']['current_candidate_round'] = 1
        self.check(r)

    def test_current_candidate_cannot_reuse_old_review(self):
        r = valid()
        r['executions'][1]['candidate_round'] = -1
        self.check(r)

    def test_duplicate_execution_ids(self):
        r = valid()
        r['executions'].append(copy.deepcopy(r['executions'][0]))
        self.check(r)

    def test_missing_required_executed_review(self):
        r = valid()
        r['review']['independent_check_evidence_ids'] = []
        self.check(r)

    def test_optional_verification_cannot_pass(self):
        r = valid()
        r['verificationPolicy'] = 'optional'
        self.check(r)

    def test_review_does_not_cover_candidate(self):
        r = valid()
        r['review']['checked_evidence_ids'] = []
        self.check(r)

    def test_failed_or_major_review(self):
        for kind in ['check', 'major']:
            with self.subTest(kind=kind):
                r = valid()
                if kind == 'check':
                    r['review']['checks'][0]['passed'] = False
                else:
                    r['review']['issues'].append({'severity': 'major'})
                self.check(r)

    def test_multi_no_blind_precheck(self):
        r = valid('multi')
        r['executions'][1]['worker_phase'] = 'verification'
        self.check(r, mode='multi')

    def test_multi_reveal_before_precheck_return(self):
        r = valid('multi')
        r['trace'].reverse()
        self.check(r, mode='multi')

    def test_multi_cannot_claim_shared_context(self):
        r = valid('multi')
        r['verification']['rounds'][0]['context_topology'] = 'shared_author_conversation'
        self.check(r, mode='multi')

    def test_extra_ungrounded_result_fails(self):
        r = valid()
        r['answer']['results'].append({'metric': 'other', 'value': 100, 'unit': 'items'})
        r['results'] = r['answer']['results']
        self.check(r)

    def test_ancillary_current_file_only_execution_allowed(self):
        r = valid()
        e = evidence('e3', 'coder', [])
        e.update(computed=None, output='wrote optional table')
        r['executions'].append(e)
        r['answer']['evidence_ids'].append('e3')
        r['review']['checked_evidence_ids'].append('e3')
        self.check(r, True)

    def test_literal_serialization_roundoff_distinct_from_oracle_tolerance(self):
        o = copy.deepcopy(ORACLE)
        o.update(metric='power', unit='probability', value=.8000000000000001, absolute_tolerance=.0001)
        r = valid()
        replace_rows(r, [{'metric': 'power', 'value': .8, 'unit': 'probability'}])
        r['executions'][0]['computed']['results'][0]['value'] = .8000000000000001
        r['executions'][0]['output'] = 'POWER_AGENT_RESULT=' + json.dumps(r['executions'][0]['computed']) + '\n'
        self.check(r, True, o)
        r['answer']['results'][0]['value'] = .8002
        self.check(r, False, o)

    def test_omnibus_schema_mapping(self):
        o = copy.deepcopy(ORACLE)
        o['design']['alternative'] = 'omnibus'
        r = valid()
        r['design']['alternative'] = 'not-applicable'
        self.check(r, True, o)

    def test_duplicate_primary(self):
        r = valid()
        r['answer']['results'].append(copy.deepcopy(r['answer']['results'][0]))
        self.check(r)

    def test_malformed_nested_ids_are_failure_not_crash(self):
        r = valid()
        r['review']['independent_check_evidence_ids'] = [{}]
        self.check(r)

class ParserTests(unittest.TestCase):
    def test_marked_and_unmarked(self):
        p = {'results': [{'metric': 'x', 'value': .123, 'unit': 'probability'}]}
        for text in [json.dumps(p), 'POWER_AGENT_RESULT=' + json.dumps(p), '[1] ' + json.dumps(p)]:
            self.assertEqual(score.stdout_result(text), p)

    def test_session_info_trim_and_duplicate_json(self):
        p = {'results': [{'metric': 'x', 'value': 1, 'unit': 'items'}]}
        text = 'POWER_AGENT_RESULT=' + json.dumps(p) + '\nPOWER_AGENT_SESSION_INFO_BEGIN\n[1] "{not JSON}"\nPOWER_AGENT_SESSION_INFO_END\n'
        self.assertEqual(score.stdout_result(text), p)
        self.assertIsNone(score.stdout_result('POWER_AGENT_RESULT={"results":[],"results":[]}'))

    def test_ambiguous_or_nonfinite_or_bad_rows(self):
        good = 'POWER_AGENT_RESULT={"results":[{"metric":"x","value":1,"unit":"items"}]}'
        for s in [good + '\n' + good, good + '\n{}', good.replace('1,', 'NaN,'), good.replace('"unit":"items"', '"unit":"items","extra":1')]:
            self.assertIsNone(score.stdout_result(s))

class RawFirstRunnerTests(unittest.TestCase):
    def job(self):
        return {'job_id': 'synthetic__single__r1', 'task_id': 'synthetic', 'mode': 'single', 'repeat': 1}

    def execute_fake(self, directory, program, deadline=1000):
        fake = directory / 'fake.py'
        fake.write_text(program)
        request = {'query': 'synthetic test only', 'deadlineMs': deadline}
        return run.execute_job(self.job(), request, fake, sys.executable, directory / 'out', 'protocol-test',
                               {'fake.py': run.sha(fake)}, timeout_extra=.05), request

    def test_raw_saved_before_json_parser_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            original = run.strict_json
            def checking_parser(text):
                self.assertTrue((d / 'out/transports/synthetic__single__r1.transport.json').exists())
                return original(text)
            with mock.patch.object(run, 'strict_json', side_effect=checking_parser):
                row, request = self.execute_fake(d, 'print(\'{"success":false,"status":"failed"}\')\n')
            path = d / 'out/transports/synthetic__single__r1.transport.json'
            self.assertEqual(score.check_transport(row, path, 'protocol-test', hashlib.sha256(run.encoded(request)).hexdigest()), [])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            altered = copy.deepcopy(row)
            altered['record']['success'] = True
            self.assertIn('parsed_record_differs_from_captured_stdout', score.check_transport(altered, path, 'protocol-test', hashlib.sha256(run.encoded(request)).hexdigest()))

    def test_invalid_json_raw_retained(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            row, _ = self.execute_fake(d, 'print("invalid model stdout")\n')
            self.assertIsNone(row['record'])
            self.assertEqual(row['capture_error'], 'JSONDecodeError')
            raw = json.loads((d / 'out/transports/synthetic__single__r1.transport.json').read_text())
            self.assertEqual(base64.b64decode(raw['stdout_base64']), b'invalid model stdout\n')

    def test_timeout_record_retained(self):
        with tempfile.TemporaryDirectory() as t:
            row, _ = self.execute_fake(pathlib.Path(t), 'import time\ntime.sleep(5)\n', deadline=20)
            self.assertEqual(row['process_error'], 'process_deadline_exceeded')
            self.assertTrue(row['transport_captured'])

    def test_refuse_attempt_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            self.execute_fake(d, 'print("{}")\n')
            with self.assertRaisesRegex(RuntimeError, 'refuse_attempt_overwrite'):
                self.execute_fake(d, 'print("{}")\n')

    def test_runtime_drift_prevents_process_dispatch(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            fake = d / 'fake.py'
            fake.write_text('raise RuntimeError("should never execute")\n')
            row = run.execute_job(self.job(), {'query': 'test', 'deadlineMs': 100}, fake, sys.executable,
                                  d / 'out', 'p', {'fake.py': '0' * 64})
            self.assertFalse(row['dispatched'])
            self.assertTrue(row['runtime_changed'])

    def test_request_question_only_and_identical_except_mode(self):
        p = {'common': {'maxModelCalls': 96}}
        questions = [{'query': 'EXACT frozen query\n', 'output_contract': {'do_not_send': True}}]
        j = {'question_index': 0, 'mode': 'single', 'task_id': 'not_sent'}
        a = run.make_request(p, questions, j)
        b = run.make_request(p, questions, dict(j, mode='multi'))
        self.assertEqual(a['query'], questions[0]['query'])
        self.assertEqual(set(a), {'maxModelCalls', 'query', 'workflowMode'})
        a.pop('workflowMode')
        b.pop('workflowMode')
        self.assertEqual(a, b)

    def test_no_api_or_oracle_imports_in_runner(self):
        text = pathlib.Path(run.__file__).read_text()
        self.assertNotIn('import score', text)
        self.assertNotIn('oracles.json', text)
        self.assertNotIn('urllib', text)

    def test_all_planned_denominator_kept(self):
        rows = [{'task_id': 'x', 'repeat': 1, 'mode': mode, 'strict_pass': mode == 'single'} for mode in ['single', 'multi']]
        result = score.summarize(rows)
        self.assertEqual(result['single']['planned'], 1)
        self.assertEqual(result['multi']['planned'], 1)
        self.assertEqual(result['paired_attempts']['single_only'], 1)

if __name__ == '__main__':
    unittest.main()
