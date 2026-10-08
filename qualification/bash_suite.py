#!/usr/bin/env python3
"""Bounded Bash differential suite in a private mount namespace and private /tmp."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil

from bounded import run
from build_snapshot import snapshot

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'qualification/.work/bash-src'
WORK = ROOT / 'qualification/.work/bash-suite'
MAIN = ROOT.parent / 'incr-main-qualification'
CURATED = '''dollars execscript func getopts ifs input-test invert more-exp nquote ifs-posix
posix2 posixpat precedence quote read rhs-exp strip tilde dynvar iquote type comsub-eof comsub-posix'''.split()


def normalized(text):
    # Private transformed paths are source-location diagnostics, not outputs.
    text = re.sub(r'\S+/incr-script\.[A-Za-z0-9]+/script/([^\s:]+)(?=:(?: eval:)? line)', r'./\1', text)
    text = re.sub(r': line \d+:', ': line <line>:', text)
    text = re.sub(r'\S+/target/release/incr --try \S+ --cache \S+ (?:--observe \S+ )?', '', text)
    text = re.sub(r'cannot set terminal process group \(\d+\)', 'cannot set terminal process group (<pid>)', text)
    # The script interpreter emits an extra startup warning for absent locales;
    # retain the corresponding warning from the actual test shell.
    text = re.sub(r'(?m)^/bin/bash: warning: setlocale:.*\n', '', text)
    return text


def main():
    candidate = snapshot()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--cases')
    parser.add_argument('--modes', default='bash,main,observe')
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'evaluation/bash-ts/tests'
    cases = args.cases.split(',') if args.cases else (sorted(p.name[4:] for p in source.glob('run-*')
                if p.name not in ('run-all', 'run-minimal')) if args.all else CURATED)
    helpers = WORK / 'helpers'
    helpers.mkdir(exist_ok=True)
    diff = helpers / 'diff'
    diff.write_text('''#!/usr/bin/python3
import os, pathlib, shutil, sys
capture = pathlib.Path('/tmp/diff-captures')
capture.mkdir(exist_ok=True)
files = [pathlib.Path(a) for a in sys.argv[1:] if not a.startswith('-') and pathlib.Path(a).is_file()]
if len(files) >= 2:
    destination = capture / str(len(list(capture.glob('*.left'))))
    shutil.copyfile(files[-2], str(destination) + '.left')
    shutil.copyfile(files[-1], str(destination) + '.right')
os.execv('/usr/bin/diff', ['diff', *sys.argv[1:]])
''')
    diff.chmod(0o755)
    summary = []
    for case in cases:
        baseline = None
        baseline_leaks = False
        for mode in args.modes.split(','):
            print(f'RUN bash/{case} {mode}', flush=True)
            fixture = WORK / 'run'
            if fixture.exists():
                shutil.rmtree(fixture)
            shutil.copytree(source, fixture / 'tests', symlinks=True)
            (fixture / 'tmp').mkdir()
            (fixture / 'cache').mkdir()
            wrapper = WORK / 'bash'
            target = BUILD / 'bash' if mode == 'bash' else (MAIN / 'src/incr.sh' if mode == 'main' else candidate / 'incr.sh')
            # A real binary matters: execscript deliberately sources THIS_SH
            # and expects Bash to reject it as a binary, not execute a wrapper.
            launcher = WORK / 'launcher.c'
            target_literal = json.dumps(str(target))
            launcher.write_text('#include <unistd.h>\n#include <stdlib.h>\n#include <stdio.h>\n'
                + 'int main(int n,char **v){char **a=calloc(n+2,sizeof(char*));'
                + 'if(!a)return 125; a[0]=v[0];int j=1;'
                + ('setenv("INCR_ARGV0",v[0],1);' if mode == 'observe' else '')
                + ('a[j++]="-b";' if mode != 'bash' else '')
                + 'for(int i=1;i<n;i++)a[j++]=v[i];execv(' + target_literal + ',a);'
                + 'perror("execv");return 126;}\n')
            built = run(['cc', '-O2', '-o', str(wrapper), str(launcher)], timeout=30)
            if built['returncode'] != 0 or built['timeout']:
                raise RuntimeError(built)
            env = {k: os.environ[k] for k in ('HOME', 'USER', 'LOGNAME', 'TERM') if k in os.environ}
            env.update(PATH=f'{helpers}:{BUILD}:/usr/local/bin:/usr/bin:/bin', LC_ALL='C',
                       THIS_SH=str(wrapper), BUILD_DIR=str(BUILD), TMPDIR='/tmp', BASH_TSTOUT='/tmp/tstout',
                       INCR_CACHE_DIR=str(fixture / 'cache'), INCR_SHELL=str(BUILD / 'bash'),
                       INCR_PYTHON=str(ROOT / 'qualification/.venv/bin/python'),
                       INCR_TOP=str(MAIN if mode == 'main' else candidate), INCR_OBSERVE='1' if mode == 'observe' else '0',
                       INCR_SYS_PATH=str((MAIN if mode == 'main' else candidate) / 'target/release/incr'), INCR_TRY_PATH=str((MAIN if mode == 'main' else candidate) / 'src/scripts/try.sh'),
                       INCR_OBSERVE_PATH=str(candidate.parent / 'observe/target/release/observe'))
            # mount changes are confined to this command's namespace. No host /tmp cleanup.
            command = ['sudo', '-n', 'unshare', '-m', '--', 'bash', '-c',
                       'mount --make-rprivate / && mount --bind "$1" /tmp && shift && exec "$@"',
                       'private-tmp', str(fixture / 'tmp'), 'setpriv', '--reuid', str(os.getuid()),
                       '--regid', str(os.getgid()), '--init-groups', 'env', '-i',
                       *[f'{k}={v}' for k, v in env.items()], str(BUILD / 'bash'), f'run-{case}']
            result = run(command, cwd=fixture / 'tests', timeout=args.timeout)
            captures = sorted((fixture / 'tmp/diff-captures').glob('*.left'), key=lambda p: int(p.stem))
            result['test_outputs'] = [p.read_text(errors='surrogateescape') for p in captures]
            # Compare actual test output, not diff hunk line numbers. The run-*
            # driver may return 1 merely because the vendored .right differs.
            key = ([normalized(t) for t in result['test_outputs']], normalized(result['stderr'])) if captures else (
                result['returncode'], normalized(result['stdout']), normalized(result['stderr']))
            if mode == 'bash':
                baseline = key
                baseline_leaks = result["leaked_descendants"]
            valid = baseline is not None and key == baseline and not any(result[k] for k in
                           ('timeout', 'remaining_descendants'))
            valid = valid and (not result['leaked_descendants'] or baseline_leaks)
            result["candidate_snapshot"] = str(candidate)
            result.update(case=case, mode=mode, matches_bash=valid)
            (args.results / f'{case}.{mode}.json').write_text(json.dumps(result, indent=2) + '\n')
            summary.append({k: result[k] for k in ('case', 'mode', 'returncode', 'elapsed_sec', 'timeout', 'matches_bash')})
            (args.results / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
            print(f'{"PASS" if valid else "FAIL"} {result["elapsed_sec"]:.3f}s rc={result["returncode"]}', flush=True)
    return int(any(not r['matches_bash'] for r in summary))


if __name__ == '__main__':
    raise SystemExit(main())
