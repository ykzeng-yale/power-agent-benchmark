import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'runner'/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current = load('runner_203', 'audited_benchmark_v2_0_3.py')
historical = load('runner_202', 'audited_benchmark_v2_0_2.py')
OLD_CORE = ['scientific-harness-cli.js', 'scientific-harness.js',
            'scientific-r-executor.js', 'model-config.js', 'scientific-r-worker.py']


class GuardDependencyFreeze(unittest.TestCase):
    def test_guard_change_addition_and_removal_invalidate_fingerprint(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = pathlib.Path(temporary)
            for name in OLD_CORE:
                (folder/name).write_text('archived fixture '+name)
            cli = folder/OLD_CORE[0]
            guard = folder/'scientific-reference-guard.js'
            absent = current.source_hashes(cli)
            self.assertIn(str(guard), absent)
            self.assertIsNone(absent[str(guard)])
            guard.write_bytes(b'first guard bytes')
            frozen = current.source_hashes(cli)
            self.assertNotEqual(frozen, absent)
            self.assertEqual(frozen[str(guard)], hashlib.sha256(guard.read_bytes()).hexdigest())
            guard.write_bytes(b'first guard bytes!')
            self.assertNotEqual(current.source_hashes(cli), frozen)
            guard.unlink()
            self.assertEqual(current.source_hashes(cli), absent)
            self.assertNotEqual(current.source_hashes(cli), frozen)

    def test_old_guardless_five_file_manifest_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = pathlib.Path(temporary)
            for name in OLD_CORE:
                (folder/name).write_text('old release fixture '+name)
            cli = folder/OLD_CORE[0]
            historic = historical.source_hashes(cli)
            new = current.source_hashes(cli)
            expected = {str(folder/name): hashlib.sha256((folder/name).read_bytes()).hexdigest()
                        for name in OLD_CORE}
            self.assertEqual({k: historic[k] for k in expected}, expected)
            self.assertEqual({k: new[k] for k in expected}, expected)
            guard = folder/'scientific-reference-guard.js'
            self.assertNotIn(str(guard), historic)
            self.assertIsNone(new[str(guard)])
            guard.write_text('new post-study guard')
            self.assertEqual(historical.source_hashes(cli), historic)
            self.assertIsNotNone(current.source_hashes(cli)[str(guard)])


if __name__ == '__main__':
    unittest.main()
