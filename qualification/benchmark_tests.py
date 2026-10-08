#!/usr/bin/env python3
"""Small independent checks for repaired benchmark components."""
import os
from pathlib import Path
import shlex
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_complete_ngrams(self):
        scripts = ROOT / 'evaluation/benchmarks/web-search/scripts/c'
        with tempfile.TemporaryDirectory(dir=ROOT / 'qualification/.work') as work:
            command = 'bash ' + shlex.quote(str(scripts / 'combine.sh'))
            command += ' | bash ' + shlex.quote(str(scripts / 'invert.sh')) + ' https://example.test/page'
            result = run(['bash', '-o', 'pipefail', '-c', command], cwd=work,
                         stdin=b'alpha\nbeta\ngamma\n', timeout=5)
            self.assertEqual(result['returncode'], 0, result)
            self.assertFalse(result['leaked_descendants'], result)
            expected = {f'{term} | 1 | https://example.test/page' for term in
                        ['alpha', 'beta', 'gamma', 'alpha beta', 'beta gamma', 'alpha beta gamma']}
            self.assertEqual(set(result['stdout'].splitlines()), expected)
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_dpt_plot_record_format(self):
        scripts = ROOT / 'evaluation/benchmarks/dpt/scripts'
        with tempfile.TemporaryDirectory(dir=ROOT / 'qualification/.work') as work:
            record = Path(work) / 'classifications.txt'
            record.write_text('g: A c: 0.95 example.jpg\ng: B c: 0.8 example.jpg\n')
            env = dict(os.environ, MPLBACKEND='Agg', MPLCONFIGDIR=str(Path(work) / 'mpl'),
                       PYTHONDONTWRITEBYTECODE='1')
            for number in range(1, 4):
                result = run([str(ROOT / 'qualification/.venv/bin/python'),
                              str(scripts / f'plot_{number}.py'), str(record)],
                             cwd=work, env=env, timeout=10)
                self.assertEqual(result['returncode'], 0, result)
                self.assertFalse(result['timeout'], result)
            self.assertTrue(Path(str(record) + '.png').read_bytes().startswith(b'\x89PNG'))


if __name__ == '__main__':
    unittest.main()
