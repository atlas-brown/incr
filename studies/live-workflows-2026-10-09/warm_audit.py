#!/usr/bin/env python3
"""Audit retained-cache live workflows and Bash-wrapper dependency changes.

Run serially after building both repositories. Every child has a process-tree
bound. Generated fixtures/caches are removed; compressed raw evidence is retained.
"""
import argparse
import gzip
import importlib.util
import json
import os
import shlex
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('live_study', HERE / 'run.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
ROOT = study.ROOT
MODES = ('native', 'incr', 'observe')

# These scripts run through incr.sh's Bash parser, not just a manually chosen
# memo boundary. References are actual native executions of the same source.
CONTROLS = {
    'pipeline': 'cat input | sort | tr a-z A-Z\n',
    'for-loop': 'for n in one two; do printf "%s:" "$n"; cat input; done\n',
    'while-read': 'cat input | while IFS= read -r line; do printf "[%s]\\n" "$line"; done\n',
    'substitution': 'value=$(sort input); printf "%s\\n" "$value"\n',
    'function': 'render() { cat "$1" | tr a-z A-Z; }; render input\n',
    'conditional': 'if grep -q alpha input; then echo first; else echo changed; fi\n',
    'streams-status': 'cat input; printf diagnostic >&2; exit 7\n',
    'file-output': 'cp input output; cat output\n',
    'missing-input': 'if test -f optional; then cat optional; else echo absent; fi\n',
    'symlink': 'cat link\n',
    'glob': 'printf "%s\\n" files/*.txt | sort\n',
    'environment': 'printenv AUDIT_VALUE | tr a-z A-Z\n',
}


def inventory(cache):
    return {str(p.relative_to(cache)): {'sha256': study.sha256(p),
                                      'mtime_ns': p.stat().st_mtime_ns}
            for p in sorted(cache.rglob('data.incr')) if p.is_file()}


def healthy(r):
    return not (r['timeout'] or r['leaked_descendants'] or r['remaining_descendants'])


def state(work, name):
    def read(path):
        p = work / path
        return p.read_text() if p.exists() else None
    if name.startswith('05-'):
        return {'release': os.readlink(work / 'current') if (work / 'current').is_symlink() else None}
    if name.startswith('06-'):
        return {'audit': read('audit.log')}
    if name.startswith('07-'):
        return {'state': read('job.state')}
    if name.startswith('08-'):
        return {'first': read('working/first'), 'second': read('working/second')}
    if name.startswith('09-'):
        return {'lock_exists': (work / 'deploy.lock').exists()}
    if name.startswith('14-'):
        return {'pending': read('pending')}
    if name.startswith('15-'):
        if not (work / 'jobs.db').is_file():
            return {'rows': None}
        with sqlite3.connect(work / 'jobs.db') as db:
            return {'rows': db.execute('select name from jobs order by name').fetchall()}
    return {}


def environment(mode, work, cache):
    env = dict(os.environ, LC_ALL='C', DEMO=str(HERE), DEMO_MODE=mode,
               DEMO_CACHE=str(cache), DEMO_INCR=str(ROOT / 'target/release/incr'),
               DEMO_OBSERVE=str(ROOT.parent / 'observe/target/release/observe'),
               DEMO_TRY=str(ROOT / 'src/scripts/try.sh'),
               INCR_CACHE_DIR=str(cache), INCR_SYS_PATH=str(ROOT / 'target/release/incr'),
               INCR_TRY_PATH=str(ROOT / 'src/scripts/try.sh'),
               INCR_OBSERVE='1' if mode == 'observe' else '0',
               INCR_OBSERVE_PATH=str(ROOT.parent / 'observe/target/release/observe'),
               INCR_PYTHON=str(ROOT / 'qualification/.venv/bin/python'),
               INCR_SHELL='/bin/bash')
    for key in ('BASH_ENV', 'ENV', 'INCR_ASSUME_TEXT'):
        env.pop(key, None)
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new evidence directory')
    parser.add_argument('--suite', choices=('all', 'live', 'wrapper', 'replay'), default='all')
    parser.add_argument('--timeout', type=float, default=4)
    parser.add_argument('--live-policy', choices=('live', 'final'), default='live',
                        help='final is an exploratory probe outside the live-workflow contract')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('timeout must be positive')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    parent = HERE / '.work'
    parent.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='warm-', dir=parent))
    tracked = [HERE / 'warm_audit.py', HERE / 'evidence/audit.json.gz', HERE / 'run.py', HERE / 'backend.sh', HERE / 'lib.sh',
               *sorted((HERE / 'cases').glob('*.sh')), ROOT / 'incr.sh',
               ROOT / 'src/scripts/insert.py', ROOT / 'src/scripts/try.sh',
               ROOT / 'qualification/bounded.py', ROOT / 'target/release/incr',
               ROOT.parent / 'observe/target/release/observe']
    fingerprints = {str(p): study.sha256(p) for p in tracked}
    records = []
    safe_to_clean = False
    started = time.monotonic()

    def execute(name, mode, phase, argv, work, cache, env, **extra):
        before = inventory(cache)
        r = study.run(argv, cwd=work, env=env, timeout=args.timeout, grace=.4)
        after = inventory(cache)
        r.update(suite=name, mode=mode, phase=phase, cache_before=before,
                 cache_after=after, retained_metadata=sum(after.get(k) == v for k, v in before.items()),
                 **extra)
        if r['remaining_descendants']:
            raise RuntimeError('Unreaped descendants; preserving workspace')
        return r

    def save(r):
        records.append(r)
        filename = f'{len(records):04}-{r["suite"]}-{r["mode"]}-{r["phase"]}.json.gz'
        (output / filename).write_bytes(gzip.compress(json.dumps(r, indent=2).encode(), mtime=0))
        print(f'{r["suite"]:30} {r["mode"]:7} {r["phase"]:14} '
              f'{"PASS" if r["verified"] else "FAIL"} entries={len(r["cache_after"])} '
              f'retained={r["retained_metadata"]}', flush=True)

    try:
        # Infrastructure failures cannot be accepted as expected isolation failures.
        for mode in MODES:
            root = workspace / f'control-{mode}'
            work, cache = root / 'work', root / 'cache'
            work.mkdir(parents=True); cache.mkdir()
            env = environment(mode, work, cache)
            r = execute('positive-control', mode, 'cold', ['bash', '-c',
                        'source "$DEMO/lib.sh"; memo bash -eu -c "echo control > output"; cat output'],
                        work, cache, env)
            r['verified'] = healthy(r) and (r['returncode'], r['stdout'], r['stderr']) == (0, 'control\n', '')
            save(r)
            if not r['verified']:
                raise RuntimeError(f'{mode} infrastructure control failed')

        if args.suite in ('all', 'live'):
            archive = json.loads(gzip.decompress((HERE / 'evidence/audit.json.gz').read_bytes()))
            delayed = {r['case']: r['script'] for r in archive['audit']['delayed_consumers']}
            for name, expected, isolated, blocked, reason in study.CASES:
                reference_states = {}
                for mode in MODES:
                    root = workspace / f'{name}-{mode}'
                    work, cache = root / 'work', root / 'cache'
                    root.mkdir(); cache.mkdir()
                    script = root / 'scenario.sh'
                    env = environment(mode, work, cache)
                    if args.live_policy == 'final':
                        helper = root / 'helper'
                        helper.mkdir()
                        (helper / 'lib.sh').write_bytes((HERE / 'lib.sh').read_bytes())
                        backend = helper / 'backend.sh'
                        backend.write_text((HERE / 'backend.sh').read_text().replace('--effect-policy live', '--effect-policy final'))
                        backend.chmod(0o755)
                        env['DEMO'] = str(helper)
                    for phase in ('cold', 'warm-1', 'warm-2', 'delayed-warm', 'warm-after-delay'):
                        if work.exists():
                            study.clean_work(work)
                        work.mkdir()
                        source = (delayed.get(name) if phase == 'delayed-warm' else None)
                        source = source or (HERE / 'cases' / f'{name}.sh').read_text()
                        script.write_text(source)
                        r = execute(name, mode, phase, ['bash', str(script)], work, cache, env,
                                    script=source, effect_policy=args.live_policy, reason=reason,
                                    delay_applied=phase == 'delayed-warm' and name in delayed)
                        private = mode == 'incr'
                        r['expected_stdout'] = isolated if private else expected
                        r['expected_timeout'] = private and blocked
                        r['filesystem'] = state(work, name)
                        if mode == 'native':
                            reference_states[phase] = r['filesystem']
                        r['matches_native_state'] = r['filesystem'] == reference_states[phase]
                        private_states = {
                            '05-release-healthcheck': {'release': 'v1'},
                            '06-shared-audit-log': {'audit': 'worker\n'},
                            '07-cancel-worker': {'state': 'running\n'},
                            '08-queue-rename': {'first': 'job\n', 'second': 'job\n'},
                            '09-directory-lock': {'lock_exists': False},
                            '14-delivery-receipt': {'pending': 'invoice-42\n'},
                            '15-sqlite-lock': {'rows': [('second',)]},
                        }
                        r['expected_filesystem'] = private_states.get(name, {}) if private else reference_states[phase]
                        r['verified'] = (r['stdout'] == r['expected_stdout'] and not r['stderr']
                                         and r['timeout'] == r['expected_timeout']
                                         and (r['expected_timeout'] or r['returncode'] == 0)
                                         and not r['leaked_descendants']
                                         and not r['remaining_descendants']
                                         and r['filesystem'] == r['expected_filesystem'])
                        save(r)

        if args.suite in ('all', 'wrapper'):
            for policy in ('live', 'final'):
                for name, body in CONTROLS.items():
                    references = {}
                    for mode in MODES:
                        root = workspace / f'wrapper-{policy}-{name}-{mode}'
                        work, cache = root / 'work', root / 'cache'
                        work.mkdir(parents=True); cache.mkdir()
                        script = root / 'program.sh'
                        script.write_text('#!/usr/bin/env bash\nset -o pipefail\n' + body)
                        (work / 'files').mkdir()
                        (work / 'first').write_text('first\n')
                        (work / 'second').write_text('second\n')
                        env = environment(mode, work, cache)
                        env['INCR_EFFECT_POLICY'] = policy
                        previous = None
                        for phase, version in (('cold', 'A'), ('warm-1', 'A'), ('warm-2', 'A'),
                                               ('changed', 'B'), ('changed-warm', 'B'), ('restored', 'A')):
                            if previous != version:
                                inp = work / 'input'
                                stamp = inp.stat() if inp.exists() else None
                                inp.write_text('alpha\nbeta\n' if version == 'A' else 'gamma\nzeta\n')
                                # Same-sized content with restored mtime tests more than timestamp keys.
                                if stamp:
                                    os.utime(inp, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                                (work / 'optional').unlink(missing_ok=True)
                                if version == 'B':
                                    (work / 'optional').write_text('appeared\n')
                                (work / 'link').unlink(missing_ok=True)
                                (work / 'link').symlink_to('first' if version == 'A' else 'second')
                                for f in (work / 'files').iterdir():
                                    f.unlink()
                                (work / 'files' / ('a.txt' if version == 'A' else 'b.txt')).touch()
                                previous = version
                            (work / 'output').unlink(missing_ok=True)
                            env['AUDIT_VALUE'] = version
                            argv = ['bash', str(script)] if mode == 'native' else [str(ROOT / 'incr.sh'), '-b', str(script)]
                            r = execute(f'wrapper-{policy}-{name}', mode, phase, argv, work, cache, env,
                                        script=script.read_text(), effect_policy=policy, fixture_version=version)
                            r['output_file'] = (work / 'output').read_text() if (work / 'output').exists() else None
                            signature = (r['returncode'], r['stdout'], r['stderr'], r['output_file'])
                            if mode == 'native':
                                references[phase] = signature
                            r['expected'] = references[phase]
                            r['verified'] = healthy(r) and signature == references[phase]
                            save(r)
        if args.suite in ('all', 'replay'):
            # Instrument the launcher before tracing starts, outside the command's
            # observed filesystem effects. Full tracing prevents the read-only
            # strace fast path from bypassing the sandbox launcher counter.
            # Batch hits do not launch a worker.
            for policy in ('live', 'final'):
                for command in ('cat', 'cp'):
                    for mode in ('incr', 'observe'):
                        root = workspace / f'replay-{policy}-{command}-{mode}'
                        work, cache = root / 'work', root / 'cache'
                        work.mkdir(parents=True); cache.mkdir()
                        launches = root / 'launches'
                        launcher = root / 'launcher.sh'
                        real = ROOT.parent / 'observe/target/release/observe' if mode == 'observe' else ROOT / 'src/scripts/try.sh'
                        guard = 'true' if mode == 'observe' else '[[ ${1:-} == -D ]]'
                        launcher.write_text('#!/bin/bash\nif ' + guard + '; then echo launch >> ' + shlex.quote(str(launches)) + '; fi\nexec ' + shlex.quote(str(real)) + ' "$@"\n')
                        launcher.chmod(0o755)
                        env = environment(mode, work, cache)
                        argv = [str(ROOT / 'target/release/incr'), '-b', '-f', '--effect-policy', policy,
                                '--cache', str(cache), '--try', str(launcher if mode == 'incr' else ROOT / 'src/scripts/try.sh')]
                        if mode == 'observe':
                            argv += ['--observe', str(launcher)]
                        argv += ['--', command, 'input'] + (['output'] if command == 'cp' else [])
                        previous = None
                        for phase, content in (('cold', 'first\n'), ('warm-1', 'first\n'), ('warm-2', 'first\n'),
                                               ('changed', 'other\n'), ('changed-warm', 'other\n'), ('restored', 'first\n')):
                            inp = work / 'input'
                            if previous != content:
                                stamp = inp.stat() if inp.exists() else None
                                inp.write_text(content)
                                if stamp:
                                    os.utime(inp, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                                previous = content
                            (work / 'output').unlink(missing_ok=True)
                            before = launches.read_text().count('launch') if launches.exists() else 0
                            r = execute(f'replay-{policy}-{command}', mode, phase, argv, work, cache, env, effect_policy=policy)
                            after = launches.read_text().count('launch') if launches.exists() else 0
                            r['worker_launches'] = after - before
                            r['confirmed_batch_hit'] = after == before and bool(r['cache_before']) and healthy(r)
                            actual = r['stdout'] if command == 'cat' else ((work / 'output').read_text() if (work / 'output').exists() else None)
                            r['verified'] = healthy(r) and r['returncode'] == 0 and not r['stderr'] and actual == content
                            if command == 'cat' and phase in ('warm-1', 'warm-2', 'changed-warm'):
                                r['verified'] = r['verified'] and r['confirmed_batch_hit']
                            save(r)
        safe_to_clean = True
    finally:
        unchanged = fingerprints == {str(p): study.sha256(p) for p in tracked}
        summary = dict(complete=safe_to_clean, passed=safe_to_clean and unchanged and all(r['verified'] for r in records),
                       live_policy=args.live_policy, executions=len(records), verified=sum(r['verified'] for r in records),
                       failures=[{k:r[k] for k in ('suite','mode','phase','stdout','stderr','returncode','timeout')}
                                 for r in records if not r['verified']],
                       elapsed_sec=round(time.monotonic()-started, 3), fingerprints=fingerprints,
                       inputs_unchanged=unchanged, retained_cache_is_not_proof_of_hit=True,
                       workspace_removed=safe_to_clean, workspace=str(workspace))
        if safe_to_clean:
            study.clean_work(workspace)
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'fingerprints'}, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
