#!/usr/bin/env python3
"""Bounded checks for try's standalone commit and temporary-file ownership."""
import json
import os
from pathlib import Path
import re
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get('INCR_QUALIFICATION_RESULTS', ROOT / 'qualification/.work/test-results')) / 'try-tests.json'
RECORDS = []


class TryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix='try-review-', dir=ROOT / 'qualification/.work')
        self.work = Path(self.fixture.name)
        self.sandbox = self.work / 'sandbox with spaces'
        self.upper = self.sandbox / 'upperdir'
        self.upper.mkdir(parents=True)
        self.temporary = self.work / 'temporary'
        self.temporary.mkdir()
        (self.sandbox / 'ignore').write_text('')

    def tearDown(self):
        self.fixture.cleanup()

    def invoke(self, *arguments, expected=0):
        result = run(['sh', str(ROOT / 'src/scripts/try.sh'), *map(str, arguments)],
                     cwd=self.work, env=dict(os.environ, TMPDIR=str(self.temporary)), timeout=3)
        RECORDS.append(result)
        self.assertFalse(result['timeout'], result)
        self.assertFalse(result['leaked_descendants'], result)
        self.assertFalse(result['remaining_descendants'], result)
        self.assertEqual(result['returncode'], expected, result)
        self.assertEqual(list(self.temporary.iterdir()), [])
        return result

    def overlay_file(self, path, contents):
        source = self.upper / str(path).lstrip('/')
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(contents)

    def test_commit_honors_saved_ignore_list(self):
        output = self.work / 'retained file'
        output.write_text('original')
        self.overlay_file(output, 'replacement')
        (self.sandbox / 'ignore').write_text(re.escape(str(output)) + '\n')
        self.invoke('commit', self.sandbox)
        self.assertEqual(output.read_text(), 'original')
        self.assertTrue((self.sandbox / 'ignore').is_file())

    def test_commit_propagates_failure(self):
        directory = self.work / 'readonly'
        directory.mkdir()
        self.overlay_file(directory / 'new-file', 'new')
        directory.chmod(0o500)
        try:
            self.invoke('commit', self.sandbox, expected=1)
        finally:
            directory.chmod(0o700)

    def test_commit_preserves_spaced_paths(self):
        output = self.work / 'output with spaces'
        self.overlay_file(output, 'contents')
        self.invoke('commit', self.sandbox)
        self.assertEqual(output.read_text(), 'contents')

    def test_incr_streaming_sandbox_commits_output(self):
        source = self.work / 'input'
        source.write_text('sandbox output')
        result = run([str(ROOT / 'target/release/incr'), '--try', str(ROOT / 'src/scripts/try.sh'),
                      '--cache', str(self.work / 'cache'), '--', 'sh', '-c',
                      'cat input > output; printf done'], cwd=self.work, stdin=b'', timeout=10)
        RECORDS.append(result)
        self.assertFalse(result['timeout'], result)
        self.assertFalse(result['leaked_descendants'], result)
        self.assertFalse(result['remaining_descendants'], result)
        self.assertEqual((result['returncode'], result['stdout'], result['stderr']), (0, 'done', ''), result)
        self.assertEqual((self.work / 'output').read_text(), 'sandbox output')
        self.assertFalse(list((self.work / 'cache').glob('sandbox_*')))

    def test_help_cleans_temporary_ignore(self):
        self.invoke('-h')


if __name__ == '__main__':
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    try:
        unittest.main()
    finally:
        RESULTS.write_text(
            json.dumps(RECORDS, indent=2) + '\n')
