"""Policy propagation and cross-study exclusion, without benchmark workloads."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import common
import study
from test_cohort_report import CohortReportTests
from cohort_report import combine


class LiveTests(unittest.TestCase):
    def test_environment_explicit_policy_overrides_parent(self):
        with patch.dict(os.environ, {'INCR_EFFECT_POLICY': 'final'}):
            value = study.environment('word-freq', 'min', Path('/fixture'), Path('/build'), 'live')
        self.assertEqual(value['INCR_EFFECT_POLICY'], 'live')

    def test_global_lock_excludes_other_studies_and_delegates(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(common, 'ROOT', Path(tmp)):
            with common.measurement_lock() as lock:
                program = ('import common; from pathlib import Path; '
                           f'common.ROOT=Path({tmp!r}); common.measurement_lock()')
                env = dict(os.environ)
                env.pop('INCR_BENCH_LOCK_FD', None)
                other = subprocess.run([sys.executable, '-c', program], env=env, capture_output=True)
                self.assertNotEqual(other.returncode, 0)
                env['INCR_BENCH_LOCK_FD'] = str(lock.fileno())
                delegated = subprocess.run([sys.executable, '-c', program], env=env,
                                           pass_fds=(lock.fileno(),), capture_output=True)
                self.assertEqual(delegated.returncode, 0, delegated.stderr)


class LiveCohortTests(CohortReportTests):
    def test_mixed_policies_rejected(self):
        a, b = self.fixture('final', 1), self.fixture('live', 2)
        for root, policy in ((a, 'final'), (b, 'live')):
            self.mutate(root/'configuration.json', lambda d: d.update(effect_policy=policy))
            for row in (root/'sequences').glob('*/*.json'):
                self.mutate(row, lambda d: d.update(effect_policy=policy))
        with self.assertRaisesRegex(ValueError, 'Fingerprint mismatch'):
            combine([a, b])


if __name__ == '__main__':
    unittest.main()
