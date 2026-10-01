import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mc', ROOT/'validation/monte_carlo.py')
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)


class Accounting(unittest.TestCase):
    def setUp(self):
        self.protocol = {'trials': 10000, 'seeds': [501], 'method': 'fixed_test',
                         'cases': [{'id': 'case', 'n_per_arm': 50}], 'calibration_standard_errors': 4}
        self.record = {'case_id': 'case', 'parameters': self.protocol['cases'][0],
                       'trials': 10000, 'seed': 501, 'method': 'fixed_test',
                       'rejections': 8000, 'nonrejections': 1900, 'failures': 100,
                       'estimate': .8, 'mcse': .004, 'wilson_95': mc.wilson(8000, 10000)}

    def test_failures_count_in_denominator(self):
        self.assertTrue(mc.validate_record(self.record, self.protocol, .8)['passed'])

    def test_success_conditioned_estimate_rejected(self):
        self.record['estimate'] = 8000/9900
        self.assertIn('estimate_mismatch', mc.validate_record(self.record, self.protocol, .8)['errors'])

    def test_missing_trials_rejected(self):
        self.record['nonrejections'] = 1800
        self.assertFalse(mc.validate_record(self.record, self.protocol, .8)['passed'])

    def test_changed_test_rejected(self):
        self.record['method'] = 'convenient_different_test'
        self.assertFalse(mc.validate_record(self.record, self.protocol, .8)['passed'])

    def test_undeclared_seed_rejected(self):
        self.record['seed'] = 502
        self.assertFalse(mc.validate_record(self.record, self.protocol, .8)['passed'])

    def test_different_dgp_rejected(self):
        self.record['parameters'] = {'id': 'case', 'n_per_arm': 100}
        self.assertFalse(mc.validate_record(self.record, self.protocol, .8)['passed'])

    def test_spurious_precision_rejected(self):
        self.record['mcse'] = 0
        self.assertFalse(mc.validate_record(self.record, self.protocol, .8)['passed'])

    def test_numerically_wrong_simulation_rejected(self):
        self.assertIn('analytic_calibration_mismatch', mc.validate_record(self.record, self.protocol, .7)['errors'])


if __name__ == '__main__':
    unittest.main()
