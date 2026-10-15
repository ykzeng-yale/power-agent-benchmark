import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


old = module('old', ROOT/'runner/audited_benchmark.py')
new = module('new', ROOT/'runner/audited_benchmark_v2_0_1.py')
current = module('current', ROOT/'runner/audited_benchmark_v2_0_2.py')


class RawFirst(unittest.TestCase):
    def test_null_answer_across_terminal_statuses(self):
        oracle = json.loads((ROOT/'audited/oracles.json').read_text())['tasks'][0]
        for status in ['completed', 'needs_clarification', 'review_failed', 'budget_exhausted', 'provider_error']:
            result = new.score({'answer': None, 'results': [], 'status': status, 'success': status == 'completed'}, oracle)
            self.assertFalse(result['passed'])
            self.assertFalse(result['numeric_pass'])
            self.assertEqual(result, current.score({'answer': None, 'results': [], 'status': status, 'success': status == 'completed'}, oracle))

    def test_all_existing_judgments_unchanged(self):
        by_id = {o['id']: o for o in json.loads((ROOT/'audited/oracles.json').read_text())['tasks']}
        files = list((ROOT/'results/haiku-v2-20261001').glob('pa26*json'))
        self.assertEqual(len(files), 105)
        passed = 0
        for file in files:
            row = json.loads(file.read_text())
            before = old.score(row['record'], by_id[row['task_id']])
            after = new.score(row['record'], by_id[row['task_id']])
            self.assertEqual(before, after)
            self.assertEqual(before, current.score(row['record'], by_id[row['task_id']]))
            passed += before['passed']
        self.assertEqual(passed, 38)

    def test_raw_survives_scorer_exception(self):
        record = {'answer': None, 'status': 'budget_exhausted', 'success': False, 'results': []}
        job = {'task_id': 'fixture', 'mode': 'multi', 'repeat': 1}
        with tempfile.TemporaryDirectory() as folder:
            file = pathlib.Path(folder)/'fixture.json'

            def failing_scorer(received, oracle):
                saved = json.loads(file.read_text())
                self.assertTrue(saved['evaluation_pending'])
                self.assertEqual(saved['record'], received)
                raise RuntimeError('Deliberately failed scorer')

            result = new.persist_and_score(file, job, record, 1.0, {}, scorer=failing_scorer)
            self.assertEqual(json.loads(file.read_text())['record'], record)
            self.assertFalse(result['evaluation']['passed'])
            self.assertEqual(result['evaluation']['reason'], ['invalid_provider_schema'])

    def test_other_malformed_fields_fail_without_crash(self):
        oracle = json.loads((ROOT/'audited/oracles.json').read_text())['tasks'][0]
        for field, value in [('design', 'not-a-design'), ('executions', None), ('answer', []), ('results', None)]:
            record = {'status': 'completed', 'success': True, field: value}
            self.assertFalse(new.score(record, oracle)['passed'])


if __name__ == '__main__':
    unittest.main()
