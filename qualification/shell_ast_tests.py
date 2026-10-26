#!/usr/bin/env python3
"""Small behavioral checks for shell parsing and incremental script generation."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(os.environ.get('INCR_QUALIFICATION_PYTHON', ROOT / 'qualification/.venv/bin/python'))
RESULTS = Path(os.environ.get('INCR_QUALIFICATION_RESULTS', ROOT / 'qualification/.work/test-results')) / 'shell-ast-tests.json'
RECORDS = []


class ShellAstTests(unittest.TestCase):
    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(prefix='shell-ast-', dir=ROOT / 'qualification/.work')
        self.work = Path(self.fixture.name)

    def tearDown(self):
        self.fixture.cleanup()

    def invoke(self, command, env=None):
        result = run([str(argument) for argument in command], cwd=self.work, timeout=3, env=env)
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

    def test_literal_commands_wrap_without_build_time_path_lookup(self):
        source = self.work / 'source.sh'
        source.write_text('go version\n')
        parser_env = os.environ.copy()
        parser_env.update({'PATH': '/usr/bin:/bin', 'INCR_SHELL': '/bin/bash'})
        for parser_flags in ([], ['--bash']):
            transformed = self.invoke([
                PYTHON, ROOT / 'src/scripts/insert.py', *parser_flags,
                '--sys-path', '/usr/bin/env', '--cache-path', '', source,
            ], env=parser_env)
            self.assertIn('/usr/bin/env go version', transformed)

    def test_shell_functions_and_aliases_remain_native(self):
        cases = (
            ('rev() { printf function; }\nrev\n', []),
            ("alias rev='printf alias'\nrev\n", []),
            ('rev() { printf function; }\nrev\n', ['--bash']),
        )
        for script, parser_flags in cases:
            source = self.work / 'shell-binding.sh'
            source.write_text(script)
            transformed = self.invoke([
                PYTHON, ROOT / 'src/scripts/insert.py', *parser_flags,
                '--sys-path', '/usr/bin/env', '--cache-path', '', source,
            ])
            self.assertNotIn('/usr/bin/env', transformed)
            output = self.work / 'shell-binding-transformed.sh'
            output.write_text(transformed)
            self.invoke(['sh' if not parser_flags else 'bash', '-n', output])

    def test_dynamic_shell_bindings_keep_the_script_untransformed(self):
        cases = (
            ('. ./functions.sh\ngo version\n', []),
            ('source ./functions.sh\ngo version\n', ['--bash']),
            ('eval "go() { :; }"\ngo version\n', ['--bash']),
        )
        for script, parser_flags in cases:
            source = self.work / 'dynamic-bindings.sh'
            source.write_text(script)
            transformed = self.invoke([
                PYTHON, ROOT / 'src/scripts/insert.py', *parser_flags,
                '--sys-path', '/usr/bin/env', '--cache-path', '', source,
            ])
            self.assertEqual(transformed, script)

    def test_dash_transform_descends_through_installer_loop(self):
        source = self.work / 'source.sh'
        source.write_text("""if [ "$RUN_STAGES" = "yes" ]; then
    set -eux
    for stage in /work/stages/*; do
        if [ -f "$stage/install.sh" ]; then
            chmod +x "$stage/install.sh"
            bash "$stage/install.sh"
        fi
    done
fi
""")
        transformed = self.invoke([PYTHON, ROOT / 'src/scripts/insert.py',
                                   '--sys-path', '/usr/bin/env', '--cache-path', '', source])
        self.assertEqual(transformed.count('/usr/bin/env'), 1, transformed)
        self.assertIn('/usr/bin/env bash', transformed)
        output = self.work / 'transformed.sh'
        output.write_text(transformed)
        self.invoke(['bash', '-n', output])

    def test_recursive_instrumentation_of_static_executed_script(self):
        rootfs = self.work / 'rootfs'
        (rootfs / 'bin').mkdir(parents=True)
        (rootfs / 'usr/bin').mkdir(parents=True)
        (rootfs / 'work').mkdir()
        shell = rootfs / 'bin/sh'
        shell.write_bytes(Path('/bin/sh').read_bytes())
        shell.chmod(0o755)
        rev = rootfs / 'usr/bin/rev'
        rev.write_bytes(Path('/usr/bin/rev').read_bytes())
        rev.chmod(0o755)

        installer = rootfs / 'work/install.sh'
        installer.write_text(
            '#!/bin/sh\nprintf "%s:%s:" "$0" "$1"\nprintf abc | rev\n'
        )
        installer.chmod(0o755)
        run_body = self.work / 'run.sh'
        run_body.write_text('./install.sh arg-one\n')
        incr = self.work / 'fake-incr'
        incr.write_text("""#!/bin/sh
echo incr >> "$INCR_LOG"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --try|--cache|--observe) shift 2 ;;
        *) break ;;
    esac
done
exec "$@"
""")
        incr.chmod(0o755)
        recursive = self.work / 'recursive'
        transformed = self.invoke([
            PYTHON, ROOT / 'src/scripts/insert.py',
            '--sys-path', incr, '--cache-path', '',
            '--rootfs', rootfs, '--cwd', '/work',
            '--target-path', '/bin:/usr/bin',
            '--recursive-dir', recursive, '--recursive-dest', recursive,
            run_body,
        ])
        self.assertEqual(len(list(recursive.glob('*.sh'))), 1)
        child_script = next(recursive.glob('*.sh')).read_text()
        self.assertIn(str(incr), child_script)

        transformed_run = self.work / 'transformed-run.sh'
        transformed_run.write_text(transformed)
        log = self.work / 'incr.log'
        result = run(
            ['/bin/sh', transformed_run],
            cwd=self.work,
            env={**os.environ, 'INCR_LOG': str(log)},
            timeout=3,
        )
        self.assertEqual(
            (result['returncode'], result['stdout']),
            (0, './install.sh:arg-one:cba'),
        )
        self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_recursive_instrumentation_skips_dynamic_script_path(self):
        rootfs = self.work / 'rootfs'
        rootfs.mkdir()
        source = self.work / 'run.sh'
        source.write_text('./"$INSTALLER"\n')
        recursive = self.work / 'recursive'
        transformed = self.invoke([
            PYTHON, ROOT / 'src/scripts/insert.py',
            '--sys-path', '/usr/bin/env', '--cache-path', '',
            '--rootfs', rootfs, '--cwd', '/work',
            '--target-path', '/bin:/usr/bin',
            '--recursive-dir', recursive,
            source,
        ])
        self.assertNotIn('/usr/bin/env', transformed)
        self.assertFalse(recursive.exists())

    def test_recursive_instrumentation_resolves_script_path_in_literal_glob_loop(self):
        rootfs = self.work / 'rootfs'
        (rootfs / 'bin').mkdir(parents=True)
        (rootfs / 'work/stages/alpha').mkdir(parents=True)
        (rootfs / 'work/stages/beta').mkdir(parents=True)
        (rootfs / 'usr/bin').mkdir(parents=True)
        bash = rootfs / 'bin/bash'
        bash.write_bytes(Path('/bin/bash').read_bytes())
        bash.chmod(0o755)
        (rootfs / 'usr/bin/rev').touch()
        (rootfs / 'usr/bin/rev').chmod(0o755)
        for stage in ('alpha', 'beta'):
            installer = rootfs / f'work/stages/{stage}/install.sh'
            installer.write_text(
                f"#!/bin/bash\nprintf '%s:%s' {stage} \"$1\" | rev\n"
            )
            installer.chmod(0o755)

        source = self.work / 'run.sh'
        source.write_text(
            'for stage in /work/stages/*; do\n'
            '    bash "$stage/install.sh"\n'
            'done\n'
        )
        recursive = self.work / 'recursive'
        transformed = self.invoke([
            PYTHON, ROOT / 'src/scripts/insert.py',
            '--sys-path', '/usr/bin/env', '--cache-path', '',
            '--rootfs', rootfs, '--cwd', '/work',
            '--target-path', '/bin:/usr/bin',
            '--recursive-dir', recursive, '--recursive-dest', recursive.resolve(),
            source,
        ])
        sidecars = list(recursive.glob('*.sh'))
        dispatcher = next(recursive.glob('*-dispatch'))
        self.assertEqual(len(sidecars), 2)
        for stage in ('alpha', 'beta'):
            sidecar = next(
                path for path in sidecars
                if f"printf '%s:%s' {stage}" in path.read_text()
            )
            self.assertIn('/usr/bin/env', sidecar.read_text())
            self.assertIn(f'/work/stages/{stage}/install.sh', dispatcher.read_text())
            self.assertIn(str(recursive), transformed)
        output = self.work / 'transformed-loop.sh'
        output.write_text(transformed)
        self.invoke(['sh', '-n', output])

        self.assertEqual(
            self.invoke([dispatcher, '/work/stages/alpha/install.sh', 'hello']),
            'olleh:ahpla',
        )

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
