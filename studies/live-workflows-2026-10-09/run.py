#!/usr/bin/env python3
"""Run small live-filesystem workflows under four execution boundaries."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'qualification'))
from bounded import run

# Exact application-visible outcomes, not merely 'anything different from Bash'.
# A blocked outcome also requires its witness and clean stderr, proving that the
# command reached the scenario rather than failing to start its sandbox.
CASES = [
    ('01-spool-pipeline', 'invoice 42\n', 'spool: unavailable\n', True,
     'Published queue file is private; producer waits for its removal.'),
    ('02-batch-export', 'north,10\nsouth,10\nwest,10\n', 'empty\nempty\nempty\n', False,
     'The stream announces new batches while the file still exposes the old batch.'),
    ('03-temporary-preview', '<h1>Preview</h1>\npreview: cleaned\n', 'preview: unavailable\npreview: cleaned\n', False,
     'Temporary output is created and removed before an end-of-command commit.'),
    ('04-log-monitor', 'worker: started\nmonitor: stopping build\n', 'worker: started\n', True,
     'The monitor cannot see the error that would make it stop the running job.'),
    ('05-release-healthcheck', 'healthcheck: v2\n', 'healthcheck: v1\n', False,
     'The smoke check reads the old release while deployment tests its private switch.'),
    ('06-shared-audit-log', 'worker\npeer\n', 'worker\n', False,
     'Committing a private whole-file result overwrites the peer append.'),
    ('07-cancel-worker', 'cancelled\n', 'processed: expensive-task\n', False,
     'A private control file masks the controller cancellation.'),
    ('08-queue-rename', 'queue: already claimed\n', 'queue: duplicate claim\n', False,
     'Moving a job in a private namespace does not remove it from the shared queue.'),
    ('09-directory-lock', 'deploy: busy\n', 'deploy: overlap\n', False,
     'A private mkdir does not exclude a peer mkdir.'),
    ('10-exclusive-claim', 'claim: already owned\n', 'claim: duplicate owner\n', False,
     'Noclobber checks different filesystem views, so both exclusive creates succeed.'),
    ('11-flock', 'lock: busy\n', 'lock: overlap\n', False,
     'Opening for write copies up the lock file; the locks refer to different inodes.'),
    ('12-fifo-stream', 'event: uploaded\n', 'fifo: unavailable\n', True,
     'A private FIFO cannot rendezvous with its outside reader.'),
    ('13-local-socket', 'reply: healthy\n', 'socket: unavailable\n', True,
     'The caller cannot reach a Unix socket created inside the private filesystem.'),
    ('14-delivery-receipt', 'consumer: invoice-42\nsender: delivered\n', 'consumer: invoice-42\nsender: retry\n', False,
     'Deleting the shared retry ticket does not delete the private ticket.'),
    ('15-sqlite-lock', 'database: writer blocked\n', 'database: concurrent writer\n', False,
     'Copy-up separates the database inode from the already-held SQLite writer lock.'),
    ('16-tee-stream', 'stream: record 42\njournal: verified\n', 'stream: record 42\n', True,
     'tee forwards the record but withholds its journal; the producer waits for acknowledgment.'),
]
MODES = ('native', 'observe', 'incr', 'sandbox')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(script, mode, directory, timeout):
    work = directory / 'work'
    cache = directory / 'cache'
    work.mkdir(parents=True)
    cache.mkdir()
    environment = dict(os.environ, DEMO=str(HERE), DEMO_MODE=mode,
                       DEMO_CACHE=str(cache), DEMO_INCR=str(ROOT / 'target/release/incr'),
                       DEMO_OBSERVE=str(ROOT.parent / 'observe/target/release/observe'),
                       DEMO_TRY=str(ROOT / 'src/scripts/try.sh'), LC_ALL='C')
    # Source strings and script paths both run with ordinary stdin/stdout/stderr.
    argv = ['bash', '-c', script] if isinstance(script, str) else ['bash', str(script)]
    return run(argv, cwd=work, env=environment, timeout=timeout, grace=.4)


def clean_work(directory):
    # All children have already been reaped. Refuse to remove a surviving mount.
    mounts = Path('/proc/self/mountinfo').read_text().splitlines()
    for line in mounts:
        mount = Path(re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), line.split()[4]))
        if mount == directory or directory in mount.parents:
            raise RuntimeError(f'refusing to delete a mounted workspace: {directory}')
    try:
        shutil.rmtree(directory)
    except PermissionError:
        # Only our uniquely allocated workspace; private namespace roots may be
        # read-only or owned by sandbox helpers. Never remove a shared /tmp tree.
        subprocess.run(['sudo', '-n', 'rm', '-rf', '--', str(directory)], check=True, timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', action='append', default=[], help='case number or name; repeatable')
    parser.add_argument('--mode', choices=('all', *MODES), default='all')
    parser.add_argument('--timeout', type=float, default=4, help='per invocation deadline (default: 4s)')
    parser.add_argument('--repeat', type=int, default=1, help='independent cold runs (default: 1)')
    parser.add_argument('--results', type=Path, help='new directory for raw records and summary')
    parser.add_argument('--keep-work', action='store_true', help='retain owned fixtures and caches')
    parser.add_argument('--explain', action='store_true', help='show source, outputs, and explanation for each example')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.timeout <= 0 or args.repeat < 1:
        parser.error('timeout and repeat must be positive')
    if args.list:
        for name, _, _, _, reason in CASES:
            print(f'{name:25} {reason}')
        return 0
    selected = [case for case in CASES if not args.case or any(
        case[0] == value or case[0].split('-')[0] == value.zfill(2) for value in args.case)]
    if not selected or any(not any(case[0] == value or case[0].split('-')[0] == value.zfill(2)
                                 for case in CASES) for value in args.case):
        parser.error('unknown case; use --list')
    modes = MODES if args.mode == 'all' else (args.mode,)
    required = ['bash', 'python3']
    if any(case[0].startswith('11-') for case in selected):
        required += ['flock']
    if any(case[0].startswith('13-') for case in selected):
        required += ['nc']
    if any(mode in modes for mode in ('incr', 'sandbox')):
        required += ['unshare', 'mergerfs', 'sudo', 'getfattr']
    if 'incr' in modes:
        required += ['strace']
    missing = [tool for tool in required if shutil.which(tool) is None]
    if missing:
        parser.error('missing prerequisites: ' + ', '.join(missing))
    binaries = [ROOT / 'target/release/incr', ROOT.parent / 'observe/target/release/observe']
    needed_binaries = ([binaries[0]] if any(mode in modes for mode in ('incr', 'observe')) else [])
    if 'observe' in modes:
        needed_binaries.append(binaries[1])
    for binary in needed_binaries:
        if not os.access(binary, os.X_OK):
            parser.error(f'build the Rust projects first; missing {binary}')
    if 'incr' in modes:
        subprocess.run(['sudo', '-n', 'true'], check=True, timeout=5)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    results = (args.results or HERE / 'results' / stamp).resolve()
    results.mkdir(parents=True, exist_ok=False)
    parent = HERE / '.work'
    parent.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='run-', dir=parent))
    runtime_files = [*needed_binaries, ROOT / 'src/scripts/try.sh', ROOT / 'qualification/bounded.py']
    source_files = [HERE / 'run.sh', HERE / 'run.py', HERE / 'backend.sh', HERE / 'lib.sh',
                    *sorted((HERE / 'cases').glob('*.sh'))]
    fingerprints = {str(p.relative_to(ROOT.parent)): sha256(p) for p in runtime_files}
    source_fingerprints = {str(p.relative_to(HERE)): sha256(p) for p in source_files}
    records = []
    started = time.monotonic()
    safe_to_clean = True
    passed = False
    try:
        # Sequential finite commands must work with every backend. Infrastructure
        # failure aborts the demonstration instead of counting as isolation evidence.
        for mode in modes:
            record = execute("source \"$DEMO/lib.sh\"; memo bash -eu -c 'echo control > output'; cat output",
                             mode, workspace / f'control-{mode}', max(10, args.timeout))
            (results / f'control-{mode}.json').write_text(json.dumps(record, indent=2) + '\n')
            if record['remaining_descendants']:
                safe_to_clean = False
            if (record['returncode'] != 0 or record['timeout'] or record['leaked_descendants']
                    or record['remaining_descendants'] or record['stdout'] != 'control\n'
                    or record['stderr']):
                raise RuntimeError(f'{mode} positive control failed; see {results}/control-{mode}.json')
        print('Cold runs; Observe uses live policy. Each memo call is the boundary.', flush=True)
        print(f'{"example":25} ' + ' '.join(f'{mode:13}' for mode in modes), flush=True)
        for repetition in range(args.repeat):
            for name, expected, isolated, blocked, reason in selected:
                row = []
                example_records = []
                if args.explain:
                    print(f'\n--- {name}: cases/{name}.sh ---\n' +
                          (HERE / 'cases' / f'{name}.sh').read_text(), flush=True)
                for mode in modes:
                    record = execute(HERE / 'cases' / f'{name}.sh', mode,
                                     workspace / f'{repetition}-{name}-{mode}', args.timeout)
                    private = mode in ('incr', 'sandbox')
                    want_block = private and blocked
                    want_stdout = isolated if private else expected
                    valid = (record['stdout'] == want_stdout and not record['stderr']
                             and record['timeout'] == want_block
                             and (want_block or record['returncode'] == 0)
                             and not record['remaining_descendants']
                             and not record['leaked_descendants'])
                    if record['remaining_descendants']:
                        safe_to_clean = False
                    label = ('BLOCKED' if want_block else 'DIFF') if private else 'OK'
                    if not valid:
                        label = 'UNEXPECTED'
                    record.update(case=name, mode=mode, repetition=repetition + 1,
                                  expected_stdout=want_stdout, expected_timeout=want_block,
                                  verified=valid, reason=reason)
                    records.append(record)
                    example_records.append(record)
                    (results / f'{repetition + 1}-{name}-{mode}.json').write_text(json.dumps(record, indent=2) + '\n')
                    row.append(label)
                print(f'{name:25} ' + ' '.join(f'{label:13}' for label in row), flush=True)
                if args.explain:
                    print(reason)
                    for record in example_records:
                        status = 'deadline reached' if record['timeout'] else f'exit {record["returncode"]}'
                        print(f'  {record["mode"]} ({status}):\n' +
                              ''.join('    ' + line + '\n' for line in record['stdout'].splitlines()), end='')
                        if record['stderr']:
                            print('  stderr: ' + record['stderr'])
                    sys.stdout.flush()
        passed = all(record['verified'] for record in records)
    except BaseException:
        # An interrupted/failed supervisor may not have returned its cleanup
        # status. Preserve the workspace rather than assuming it is safe to erase.
        safe_to_clean = False
        raise
    finally:
        inputs_unchanged = (
            fingerprints == {str(p.relative_to(ROOT.parent)): sha256(p) for p in runtime_files}
            and source_fingerprints == {str(p.relative_to(HERE)): sha256(p) for p in source_files})
        passed = passed and inputs_unchanged
        metadata = {
            'passed': passed, 'elapsed_sec': round(time.monotonic() - started, 3),
            'cold_runs': True, 'observe_effect_policy': 'live', 'cases': len(selected),
            'modes': modes, 'repeat': args.repeat, 'verified': sum(r['verified'] for r in records),
            'executions': len(records), 'results': str(results),
            'fingerprints': fingerprints, 'source_fingerprints': source_fingerprints,
            'inputs_unchanged': inputs_unchanged,
            'work_retained': str(workspace) if args.keep_work or not safe_to_clean else None,
        }
        (results / 'summary.json').write_text(json.dumps(metadata, indent=2) + '\n')
        if not args.keep_work and safe_to_clean:
            clean_work(workspace)
    print(f'\n{metadata["verified"]}/{len(records)} expected outcomes verified in {metadata["elapsed_sec"]:.1f}s.')
    print(f'Raw evidence: {results}')
    if not passed:
        print('UNEXPECTED is a failed check, not evidence for the isolation claim.', file=sys.stderr)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
