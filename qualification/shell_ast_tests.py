#!/usr/bin/env python3
"""Small behavioral checks for shell parsing and incremental script generation."""
import json
from pathlib import Path
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / 'qualification/.venv/bin/python'
RESULTS = ROOT / 'qualification/results/effect-replay/shell-ast-tests.json'
RECORDS = []


class ShellAstTests(unittest.TestCase):
    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix='shell-ast-', dir=ROOT / 'qualification/.work')
        self.work = Path(self.fixture.name)

    def tearDown(self):
        self.fixture.cleanup()

    def invoke(self, command):
        result = run([str(argument) for argument in command], cwd=self.work, timeout=3)
        RECORDS.append(result)
        RESULTS.write_text(json.dumps(RECORDS, indent=2) + '\n')
        self.assertFalse(result['timeout'], result)
        self.assertFalse(result['leaked_descendants'], result)
        self.assertFalse(result['remaining_descendants'], result)
        self.assertEqual((result['returncode'], result['stderr']), (0, ''), result)
        return result['stdout']

    def test_incremental_pipeline_and_loop_outputs(self):
        source = self.work / 'source.sh'
        source.write_text('printf first\nprintf abc | rev\n'
                          'for value in one two; do printf "<%s>" "$value"; printf "!"; done\n')
        destination = self.work / 'generated'
        self.invoke([PYTHON, ROOT / 'src/scripts/incrementize.py', source, destination])
        outputs = [self.invoke(['bash', script]) for script in sorted(destination.iterdir())]
        self.assertEqual(outputs, ['first', 'firstabc', 'firstcba',
                                   'firstcba<one><two>', 'firstcba<one>!<two>!'])

    def test_dash_transform_preserves_pipeline_and_loop_output(self):
        source = self.work / 'source.sh'
        source.write_text('printf abc | rev\n'
                          'for value in ab cd; do printf "%s" "$value" | rev; done\n')
        transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py',
                                   '--sys-path', '/usr/bin/env', '--cache-path', '', source])
        self.assertEqual(transformed.count('/usr/bin/env'), 2)
        output = self.work / 'transformed.sh'
        output.write_text(transformed)
        self.assertEqual(self.invoke(['bash', output]), 'cbabadc')

    def test_bash_nested_control_flow_and_functions(self):
        source = self.work / 'control.sh'
        source.write_text("""rev() { printf function; }
if [[ yes == yes ]]; then printf abc | /usr/bin/rev; else false; fi
for value in one; do case "$value" in one) printf def | /usr/bin/rev;; esac; done
count=0
until [[ $count == 1 ]]; do printf ghi | /usr/bin/rev; count=1; done
( printf jkl | /usr/bin/rev )
rev
""")
        transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py', '--bash',
                                   '--sys-path', '/usr/bin/env', '--cache-path', '', source])
        self.assertEqual(transformed.count('/usr/bin/env'), 4)
        output = self.work / 'transformed.sh'
        output.write_text(transformed)
        self.assertEqual(self.invoke(['bash', output]), self.invoke(['bash', source]))

    def test_dash_identity_does_not_insert_incr(self):
        source = self.work / 'source.sh'
        source.write_text('printf abc | rev\n')
        transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py', '--identity',
                                   '--sys-path', '/bin/false', source])
        self.assertNotIn('/bin/false', transformed)
        output = self.work / 'identity.sh'
        output.write_text(transformed)
        self.assertEqual(self.invoke(['bash', output]), 'cba')


if __name__ == '__main__':
    unittest.main()
