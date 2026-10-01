import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('current_runner', ROOT/'runner/audited_benchmark_v2_0_2.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class VersionChangeCapture(unittest.TestCase):
    def test_every_version_change_is_persisted_without_provider_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = pathlib.Path(temporary)/'study'
            calls = []
            def hashes(_):
                calls.append(True)
                return {'fixture': 'initial' if len(calls) == 1 else 'changed'}
            argv = ['runner', '--cli', '/nonexistent/never-called.js', '--out', str(destination),
                    '--split', 'pilot', '--repeats', '1', '--modes', 'single', '--workers', '1']
            with mock.patch.object(sys, 'argv', argv), mock.patch.object(runner, 'source_hashes', hashes), \
                 mock.patch.object(runner.subprocess, 'run') as provider, contextlib.redirect_stdout(io.StringIO()):
                runner.main()
            provider.assert_not_called()
            protocol = json.loads((destination/'protocol.json').read_text())
            result = json.loads((destination/'results.json').read_text())
            self.assertEqual(len(list(destination.glob('pa26*json'))), len(protocol['jobs']))
            self.assertEqual(result['recorded_attempts'], len(protocol['jobs']))
            self.assertTrue(all(r['record']['status'] == 'version_changed' and not r['evaluation']['passed']
                                for r in result['records']))


if __name__ == '__main__':
    unittest.main()
