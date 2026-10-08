#!/usr/bin/env python3
"""Small behavioral checks for shell parsing and incremental script generation."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / 'qualification/.venv/bin/python'
RESULTS = Path(os.environ.get('INCR_QUALIFICATION_RESULTS', ROOT / 'qualification/.work/test-results')) / 'shell-ast-tests.json'
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

    def test_prefix_arguments_preserve_shell_metacharacters(self):
        wrapper = self.work / "wrapper space'quote$()"
        wrapper.write_text("#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n")
        wrapper.chmod(0o755)
        source = self.work / "source.sh"
        source.write_text("rev\n")
        values = ["try space'quote", "cache\nline$HOME", 'observe"quote\\slash']
        for parser_flags in [[], ['--bash']]:
            transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py', *parser_flags,
                                       '--sys-path', wrapper, '--try-path', values[0],
                                       '--cache-path', values[1], '--observe-path', values[2], source])
            output = self.work / 'transformed.sh'
            output.write_text(transformed)
            actual = json.loads(self.invoke(['bash', output]))
            self.assertEqual(actual, ['--try', values[0], '--cache', values[1],
                                      '--observe', values[2], 'rev'])

    def test_execute_preserved_source(self):
        source = self.work / 'source.sh'
        source.write_text('printf executed # LINENO\n')
        output = self.work / 'preserved.sh'
        result = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py', '--bash',
                              '--execute', '--output', output, source])
        self.assertEqual(result, 'executed')
        self.assertEqual(output.read_bytes(), source.read_bytes())

    def test_quoted_and_multiple_alias_bindings_remain_native(self):
        source = self.work / 'aliases.sh'
        for command in ['alias', "'alias'", 'builtin alias', 'command alias']:
            source.write_text("shopt -s expand_aliases\n" + command + " 'rev=printf alias' 'sort=printf second'\nrev\nsort\n")
            transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py', '--bash',
                                       '--sys-path', '/usr/bin/env', '--cache-path', '', source])
            output = self.work / 'transformed.sh'
            output.write_text(transformed)
            self.assertEqual(self.invoke(['bash', output]), self.invoke(['bash', source]))

    def test_expanded_alias_bindings_preserve_source(self):
        for binding in ['name=rev; alias "$name=printf dynamic"',
                        'binding="rev=printf dynamic"; alias "$binding"']:
            source = self.work / 'aliases.sh'
            source.write_text('shopt -s expand_aliases\n' + binding + '\nrev\n')
            transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py', '--bash',
                                       '--sys-path', '/usr/bin/env', '--cache-path', '', source])
            self.assertEqual(transformed, source.read_text())
            self.assertEqual(self.invoke(['bash', source]), 'dynamic')

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
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    unittest.main()
