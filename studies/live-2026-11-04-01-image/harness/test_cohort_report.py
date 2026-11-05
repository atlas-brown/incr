"""Synthetic evidence fixtures for paired reporting; these are not benchmark data."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cohort_report import combine


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + '\n')


class CohortReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, name='one', repetitions=3, modes=None):
        run = self.root / name
        modes = modes or ['bash', 'original', 'observe']
        manifest = {'benchmarks': [{'name': 'example', 'scripts': ['cold.sh', 'edited.sh']}]}
        save(run / 'manifest.json', manifest)
        manifest_hash = hashlib.sha256((run / 'manifest.json').read_bytes()).hexdigest()
        save(run / 'configuration.json', dict(suite='paper', profile='paper', only='example',
            modes=modes, repetitions=repetitions, manifest_sha256=manifest_hash,
            native_transform=True, assume_directory_access=True,
            content_validated_inputs=True, annotations=False, harness_sha256='harness'))
        save(run / 'frozen-build.json', {'revisions': {'incr': 'commit'},
            'sha256': {'candidate/incr': 'binary'}})
        save(run / 'environment.json', dict(source_fingerprints={'source': 'hash'},
            original_baseline_patch='patch', packages=['package'], tool_versions=['tool'],
            dictionary_sha256='dictionary'))
        save(run / 'inputs/example.json', {'input_bytes': 100, 'sha256': 'input'})
        count = repetitions * 6
        save(run / 'summary.json', dict(complete=True, failed_sequences=[],
            invocations=count, expected_invocations=count, valid_invocations=count))
        save(run / 'status.json', {'state': 'complete'})
        save(run / 'monitor.json', dict(health='ok', run_state='complete', failed_samples=[],
            monitor_issues=[], recorded=count, valid=count))
        validation = dict(returncode=0, stdout_sha256='stdout',
            normalized_stderr_sha256='stderr', outputs={'output': {'content': 'hash'}})
        for repetition in range(repetitions):
            for index, script in enumerate(['cold.sh', 'edited.sh']):
                save(run / f'references/example/{repetition}.{script}.json', validation)
                for mode in modes:
                    seconds = {'bash': 10, 'original': 5, 'observe': 2}[mode] * (index + 1)
                    save(run / f'sequences/example.{mode}.{repetition}/{index:02}.{script}.json',
                        dict(benchmark='example', script=script, mode=mode, repetition=repetition,
                             index=index, valid=True, failure=None, remaining_descendants=[],
                             returncode=0, elapsed_sec=seconds, validation=validation))
        return run

    def mutate(self, path, function):
        data = json.loads(path.read_text())
        function(data)
        save(path, data)

    def test_exact_paired_totals_and_ratios(self):
        result = combine([self.fixture()])
        self.assertEqual(result['paired_repetitions'], 3)
        family = result['families'][0]
        self.assertEqual(family['seconds']['observe']['samples'], [6, 6, 6])
        self.assertEqual(family['paired_speedup']['bash_over_observe']['mean'], 5)
        self.assertEqual(family['paired_speedup']['original_over_observe']['mean'], 2.5)
        self.assertEqual(result['edited_families'][0]['seconds']['observe']['mean'], 4)
        self.assertTrue(result['versions'][0]['cold'])
        self.assertFalse(result['versions'][1]['cold'])

    def test_separate_runs_and_reversed_mode_order(self):
        result = combine([self.fixture('one', 1),
            self.fixture('two', 2, ['bash', 'observe', 'original'])])
        self.assertEqual(result['paired_repetitions'], 3)

    def test_fingerprint_changes_rejected(self):
        for filename, key in [('configuration.json', 'annotations'),
                              ('frozen-build.json', 'sha256'),
                              ('inputs/example.json', 'sha256')]:
            with self.subTest(filename=filename):
                a = self.fixture('a-' + key, 1)
                b = self.fixture('b-' + key, 2)
                self.mutate(b / filename, lambda data: data.update({key: 'changed'}))
                with self.assertRaisesRegex(ValueError, 'Fingerprint mismatch'):
                    combine([a, b])

    def test_invalid_evidence_rejected(self):
        mutations = [
            ('summary.json', lambda d: d.update(complete=False)),
            ('status.json', lambda d: d.update(state='running')),
            ('monitor.json', lambda d: d.update(recorded=2)),
            ('monitor.json', lambda d: d.update(monitor_issues=['bad'])),
            ('sequences/example.observe.0/00.cold.sh.json', lambda d: d.update(valid=False)),
            ('sequences/example.observe.0/00.cold.sh.json', lambda d: d.update(returncode=1)),
            ('sequences/example.observe.0/00.cold.sh.json', lambda d: d.update(remaining_descendants=[1])),
            ('sequences/example.observe.0/00.cold.sh.json', lambda d: d['validation'].update(stdout_sha256='bad')),
            ('sequences/example.observe.0/00.cold.sh.json', lambda d: d.update(elapsed_sec=0)),
            ('sequences/example.observe.0/00.cold.sh.json', lambda d: d.update(elapsed_sec=float('nan'))),
        ]
        for index, (filename, mutate) in enumerate(mutations):
            with self.subTest(filename=filename, index=index):
                run = self.fixture(str(index))
                self.mutate(run / filename, mutate)
                with self.assertRaises(ValueError):
                    combine([run])

    def test_missing_rows_manifest_changes_and_too_few_repetitions_rejected(self):
        run = self.fixture('missing')
        (run / 'sequences/example.observe.0/00.cold.sh.json').unlink()
        with self.assertRaises(ValueError):
            combine([run])
        run = self.fixture('manifest')
        self.mutate(run / 'manifest.json', lambda d: d.update(extra='changed'))
        with self.assertRaisesRegex(ValueError, 'Manifest hash mismatch'):
            combine([run])
        with self.assertRaisesRegex(ValueError, 'At least three'):
            combine([self.fixture('too-few', 2)])

    def test_checks_remain_enabled_under_python_optimization(self):
        run = self.fixture()
        self.mutate(run / 'sequences/example.observe.0/00.cold.sh.json',
                    lambda d: d.update(elapsed_sec=-1))
        command = [sys.executable, '-O', str(Path(__file__).with_name('cohort_report.py')),
                   str(run), '--output', str(self.root / 'report.json')]
        result = subprocess.run(command, capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'report.json').exists())
