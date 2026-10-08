#!/usr/bin/env python3
"""Behavioral qualification of enabled chunk optimizations, with bounded commands."""
import hashlib
import json
import os
from pathlib import Path
import random
import shlex
import sys
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get('INCR_QUALIFICATION_RESULTS', ROOT / 'qualification/.work/test-results')) / 'chunk-tests.json'
RECORDS = []


class ChunkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = random.Random(53).randbytes(17 * 1024 * 1024)

    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix='chunk-test-', dir=ROOT / 'qualification/.work')
        self.work = Path(self.fixture.name)
        self.cache = self.work / 'cache'

    def tearDown(self):
        self.fixture.cleanup()

    def command(self, arguments, compressed=False, assume_text=False):
        return [str(ROOT / 'target/release/incr'), '-a', *(['-z'] if compressed else []),
                *(['--assume-text'] if assume_text else []),
                '--cache', str(self.cache), '--observe', str(ROOT.parent / 'observe/target/release/observe'),
                '--', *arguments]

    def invoke(self, arguments, compressed=False, payload=None, assume_text=False):
        payload = self.payload if payload is None else payload
        result = run(self.command(arguments, compressed, assume_text), stdin=payload, cwd=self.work,
                     env=dict(os.environ, LC_ALL='C', PWD=str(self.work)), timeout=8)
        result.pop('stdout')
        RECORDS.append(result)
        RESULTS.write_text(json.dumps(RECORDS, indent=2) + '\n')
        self.assertFalse(result['timeout'], result)
        self.assertFalse(result['leaked_descendants'], result)
        self.assertFalse(result['remaining_descendants'], result)
        self.assertEqual((result['returncode'], result['stderr']), (0, ''), result)
        expected = payload.translate(bytes.maketrans(b'a', b'b')) if arguments[0] == 'tr' else payload
        if arguments[0] == 'rev':
            expected = b'\n'.join(line[::-1] for line in payload.split(b'\n'))
        self.assertEqual(result['stdout_sha256'], hashlib.sha256(expected).hexdigest())

    def check_reuse_and_corruption(self, arguments, compressed, payload=None, assume_text=False):
        self.invoke(arguments, compressed, payload, assume_text)
        before = {path: path.stat().st_mtime_ns for path in self.cache.glob('batch_*/data.incr')}
        self.assertGreaterEqual(len(before), 2, 'input did not exercise multiple chunks')
        self.invoke(arguments, compressed, payload, assume_text)
        self.assertEqual(before, {path: path.stat().st_mtime_ns
                                  for path in self.cache.glob('batch_*/data.incr')})
        damaged = next(iter(before))
        (damaged.parent / 'stdout.incr').write_bytes(b'corrupt cache')
        self.invoke(arguments, compressed, payload, assume_text)
        self.assertNotEqual(before[damaged], damaged.stat().st_mtime_ns)

    def test_cat(self):
        self.check_reuse_and_corruption(['cat'], False)

    def test_compressed_cat(self):
        self.check_reuse_and_corruption(['cat'], True)

    def test_translation(self):
        self.check_reuse_and_corruption(['tr', 'a', 'b'], False)

    def test_compressed_translation(self):
        self.check_reuse_and_corruption(['tr', 'a', 'b'], True)

    def test_text_line_reversal(self):
        table = bytes(10 if byte == 10 else 32 + byte % 95 for byte in range(256))
        self.check_reuse_and_corruption(['rev'], True, self.payload.translate(table), True)

    def test_invalid_text_without_assumption(self):
        environment = dict(os.environ, LC_ALL='C', PWD=str(self.work))
        baseline = run(['rev'], stdin=b'a\xffb\n', env=environment, timeout=2)
        candidate = run(self.command(['rev']), stdin=b'a\xffb\n', env=environment, timeout=2)
        self.assertFalse(candidate['timeout'])
        self.assertFalse(candidate['leaked_descendants'])
        self.assertEqual(tuple(candidate[key] for key in ['returncode', 'stdout', 'stderr']),
                         tuple(baseline[key] for key in ['returncode', 'stdout', 'stderr']))

    def test_cache_reuse_with_fragmented_producer(self):
        payload_file = self.work / 'input'
        payload_file.write_bytes(self.payload)
        self.invoke(['cat'])
        before = {path: path.stat().st_mtime_ns for path in self.cache.glob('batch_*/data.incr')}
        producer = ('import os,sys; data=open(sys.argv[1], "rb").read(); '
                    '[os.write(1, data[offset:offset+7777]) for offset in range(0,len(data),7777)]')
        pipeline = (shlex.join([sys.executable, '-c', producer, str(payload_file)])
                    + ' | ' + shlex.join(self.command(['cat'])))
        result = run(['bash', '-o', 'pipefail', '-c', pipeline], cwd=self.work,
                     env=dict(os.environ, LC_ALL='C', PWD=str(self.work)), timeout=5)
        result.pop('stdout')
        RECORDS.append(result)
        RESULTS.write_text(json.dumps(RECORDS, indent=2) + '\n')
        self.assertFalse(result['timeout'], result)
        self.assertFalse(result['leaked_descendants'], result)
        self.assertFalse(result['remaining_descendants'], result)
        self.assertEqual((result['returncode'], result['stderr']), (0, ''), result)
        self.assertEqual(result['stdout_sha256'], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(before, {path: path.stat().st_mtime_ns
                                  for path in self.cache.glob('batch_*/data.incr')})

    def test_empty_and_unterminated_input(self):
        for payload in [b'', b'no newline']:
            self.invoke(['cat'], payload=payload)
            self.invoke(['cat'], payload=payload)

    def test_infinite_producer_early_consumer(self):
        pipeline = 'yes x | ' + shlex.join(self.command(['cat'])) + ' | head -c 1'
        result = run(['bash', '-o', 'pipefail', '-c', pipeline], cwd=self.work, timeout=5)
        RECORDS.append(result)
        RESULTS.write_text(json.dumps(RECORDS, indent=2) + '\n')
        self.assertFalse(result['timeout'], result)
        self.assertFalse(result['leaked_descendants'], result)
        self.assertFalse(result['remaining_descendants'], result)
        self.assertEqual((result['returncode'], result['stdout'], result['stderr']), (141, 'x', ''), result)


if __name__ == '__main__':
    (ROOT / 'qualification/.work').mkdir(exist_ok=True)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    unittest.main()
