#!/usr/bin/env python3
"""Probe changed lock state with stable file contents and a retained cache.

This is a diagnostic audit, not a claim that arbitrary synchronization can be
memoized. Exit 1 reports any difference from the explicit native lock oracle.
"""
import argparse
import fcntl
import gzip
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('warm_audit', HERE / 'warm_audit.py')
warm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(warm)
study, ROOT = warm.study, warm.ROOT

FLOCK = ['bash', '-c', 'exec 9>>lock; if flock -n 9; then echo acquired; else echo busy; fi']
SQLITE = ['python3', '-c', '''import sqlite3
db = sqlite3.connect('jobs.db', timeout=0)
try:
    db.execute('begin immediate')
    db.rollback()
    print('acquired')
except sqlite3.OperationalError as error:
    if 'locked' not in str(error):
        raise
    print('busy')
finally:
    db.close()
''']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (HERE / '.work').mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='coordination-', dir=HERE / '.work'))
    fingerprints = {str(p): study.sha256(p) for p in (
        HERE / 'coordination_audit.py', HERE / 'warm_audit.py', HERE / 'run.py',
        ROOT / 'target/release/incr', ROOT.parent / 'observe/target/release/observe',
        ROOT / 'src/scripts/try.sh', ROOT / 'qualification/bounded.py')}
    records = []
    safe = False
    started = time.monotonic()
    try:
        for policy in ('live', 'final'):
            for execution in ('stream', 'batch'):
                for kind, command in (('flock', FLOCK), ('sqlite', SQLITE)):
                    for mode in ('native', 'incr', 'observe'):
                        root = workspace / f'{policy}-{execution}-{kind}-{mode}'
                        work, cache = root / 'work', root / 'cache'
                        work.mkdir(parents=True); cache.mkdir()
                        (work / 'lock').touch()
                        db = sqlite3.connect(work / 'jobs.db')
                        db.execute('create table jobs(name text)'); db.commit(); db.close()
                        # Python descriptors are non-inheritable. The supervisor
                        # closes unrelated FDs, so Incr does not take an FD fallback.
                        lock = None
                        env = warm.environment(mode, work, cache)
                        argv = command
                        if mode != 'native':
                            argv = [str(ROOT / 'target/release/incr'), '--cache', str(cache),
                                    '--try', str(ROOT / 'src/scripts/try.sh'), '--effect-policy', policy]
                            if execution == 'batch':
                                argv += ['-b']
                            if mode == 'observe':
                                argv += ['--observe', str(ROOT.parent / 'observe/target/release/observe')]
                            argv += ['--', *command]
                        try:
                            for phase, held in (('cold-free', False), ('warm-free', False),
                                                ('warm-held', True), ('warm-held-again', True),
                                                ('warm-released', False), ('cold-held', True),
                                                ('warm-free-after-held', False)):
                                if phase == 'cold-held':
                                    study.clean_work(cache)
                                    cache.mkdir()
                                lock = (work / 'lock').open('a')
                                db = sqlite3.connect(work / 'jobs.db')
                                # Hash BEFORE acquiring a POSIX record lock: closing any
                                # descriptor for that inode would release this process's locks.
                                target = work / ('lock' if kind == 'flock' else 'jobs.db')
                                before = {'sha256': study.sha256(target), 'inode': target.stat().st_ino,
                                          'mtime_ns': target.stat().st_mtime_ns}
                                if held:
                                    if kind == 'flock':
                                        fcntl.flock(lock, fcntl.LOCK_EX)
                                    else:
                                        db.execute('begin immediate')
                                metadata = warm.inventory(cache)
                                try:
                                    r = study.run(argv, cwd=work, env=env, timeout=5, grace=.4)
                                finally:
                                    if held:
                                        if kind == 'flock':
                                            fcntl.flock(lock, fcntl.LOCK_UN)
                                        else:
                                            db.rollback()
                                    lock.close(); db.close()
                                after = warm.inventory(cache)
                                want = 'busy\n' if held else 'acquired\n'
                                r.update(kind=kind, mode=mode, execution=execution, effect_policy=policy,
                                         phase=phase, expected_stdout=want, file_before=before,
                                         file_after={'sha256': study.sha256(target), 'inode': target.stat().st_ino,
                                                     'mtime_ns': target.stat().st_mtime_ns},
                                         cache_before=metadata, cache_after=after,
                                         retained_metadata=sum(after.get(k) == v for k,v in metadata.items()))
                                r['verified'] = warm.healthy(r) and (r['returncode'], r['stdout'], r['stderr']) == (0, want, '')
                                records.append(r)
                                name = f'{policy}-{execution}-{kind}-{mode}-{phase}.json.gz'
                                (output / name).write_bytes(gzip.compress(json.dumps(r,indent=2).encode(),mtime=0))
                                print(name, 'PASS' if r['verified'] else 'DIFF', repr(r['stdout']), flush=True)
                                if mode == 'native' and not r['verified']:
                                    raise RuntimeError('Native lock oracle failed; results cannot establish a backend difference')
                                if r['remaining_descendants']:
                                    raise RuntimeError('surviving descendants')
                        finally:
                            if lock is not None:
                                lock.close()
                            db.close()
        safe = True
    finally:
        unchanged = fingerprints == {name: study.sha256(Path(name)) for name in fingerprints}
        summary = dict(complete=safe, passed=safe and unchanged and all(r['verified'] for r in records),
                       executions=len(records), native_matches=sum(r['verified'] for r in records),
                       differences=[{k:r[k] for k in ('kind','mode','execution','effect_policy','phase','stdout','expected_stdout')}
                                    for r in records if not r['verified']],
                       elapsed_sec=round(time.monotonic()-started,3), fingerprints=fingerprints,
                       inputs_unchanged=unchanged, workspace_removed=safe)
        if safe:
            study.clean_work(workspace)
        (output / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
