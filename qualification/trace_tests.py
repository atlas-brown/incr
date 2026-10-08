#!/usr/bin/env python3
"""Bounded native comparisons and cache-hit checks for the strace backend."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get('INCR_QUALIFICATION_RESULTS', ROOT / 'qualification/.work/test-results')) / 'trace-tests.json'
RECORDS = []


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix='trace-test-', dir=ROOT / 'qualification/.work')
        self.directory = Path(self.fixture.name)
        self.work = self.directory / 'work'
        self.cache = self.directory / 'cache'
        self.work.mkdir()
        self.cache.mkdir()

    def tearDown(self):
        self.fixture.cleanup()

    def invoke(self, arguments):
        native = run(arguments, cwd=self.work, timeout=3)
        command = [str(ROOT / 'target/release/incr'), '-b', '--cache', str(self.cache),
                   '--try', str(ROOT / 'src/scripts/try.sh'), '--', *arguments]
        observed = run(command, cwd=self.work, timeout=5)
        RECORDS.append(observed)
        RESULTS.write_text(json.dumps(RECORDS, indent=2) + '\n')
        self.assertFalse(observed['timeout'], observed)
        self.assertFalse(observed['leaked_descendants'], observed)
        self.assertFalse(observed['remaining_descendants'], observed)
        self.assertEqual(tuple(native[key] for key in ['stdout', 'stderr', 'returncode']),
                         tuple(observed[key] for key in ['stdout', 'stderr', 'returncode']))
        return observed

    def entries(self):
        return {path: path.stat().st_mtime_ns for path in self.cache.glob('batch_*/data.incr')}

    def test_special_path_reuse_and_invalidation(self):
        source = self.work / 'café, quote" and parenthesis)=name'
        source.write_text('original')
        command = ['cat', source.name]
        self.invoke(command)
        previous = self.entries()
        self.assertTrue(previous)
        self.invoke(command)
        self.assertEqual(previous, self.entries(), 'warm invocation did not reuse its cache')
        source.write_text('changed')
        self.assertEqual(self.invoke(command)['stdout'], 'changed')
        self.assertNotEqual(previous, self.entries())

    def test_same_mtime_content_change_invalidates(self):
        source = self.work / 'input'
        source.write_text('original')
        stamp = source.stat()
        command = ['cat', source.name]
        self.invoke(command)
        previous = self.entries()
        source.write_text('modified')
        os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        self.assertEqual(self.invoke(command)['stdout'], 'modified')
        self.assertNotEqual(previous, self.entries())

    def test_long_negative_path_dependency(self):
        source = self.work / ('absent-' + 'x' * 160)
        command = ['cat', source.name]
        self.invoke(command)
        previous = self.entries()
        self.invoke(command)
        self.assertEqual(previous, self.entries(), 'negative lookup was not reused')
        source.write_text('now present')
        self.assertEqual(self.invoke(command)['stdout'], 'now present')


if __name__ == '__main__':
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    unittest.main()
