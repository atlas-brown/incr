"""Run the full unannotated reproduction serially on a pushed checkpoint.

Run from a fresh committed study containing both manifests and the reviewed
reference patch. Reuse the committed paper-study harness through its existing
INCR_BENCH_STUDY override; each measurement run freezes that harness itself.
An ignored results/checkpoint.json supplied after both clean pushes pins
repository heads, runtime binaries and baseline.
The caller reviews qualification and targeted evidence before supplying pins.
Use --check for a preflight that never prepares inputs or runs measurements.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    study = Path(__file__).resolve().parent
    root = study.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='Verify checkpoint without preparing or measuring')
    parser.add_argument('--checkpoint', type=Path,
                        default=study / 'results/checkpoint.json')
    args = parser.parse_args()
    old_study = root / 'studies/paper-size-benchmarks'
    harness = old_study / 'harness'
    require(study != old_study and study.parent == root / 'studies',
            'Install in a separate fresh study under the Incr studies directory')
    require((harness / 'study.py').is_file(), 'Shared study harness is missing')
    os.environ['INCR_BENCH_STUDY'] = str(study)
    sys.path.insert(0, str(harness))
    from common import GIB, WORK, allocated_bytes, atomic_json, file_hash

    pin = json.loads(args.checkpoint.read_text())
    state = study / 'results/controller.json'

    def record(stage, **fields):
        from datetime import datetime, timezone
        atomic_json(state, {'stage': stage,
                            'updated': datetime.now(timezone.utc).isoformat(),
                            'pid': os.getpid(), **fields})

    def command(argv, suite='paper'):
        return subprocess.run(argv, cwd=root, check=True,
                              env=dict(os.environ, INCR_BENCH_SUITE=suite))

    def verify_checkpoint():
        require(set(pin['gate_receipts']) == {'qualification-and-targeted-review', 'evidence-catalog'},
                'Qualification and evidence receipts must be pinned')
        for receipt in pin['gate_receipts'].values():
            path = (root / receipt['path']).resolve()
            require(path.is_relative_to(root) and file_hash(path) == receipt['sha256'],
                    'Checkpoint gate evidence changed: ' + str(path))
        for name, expected in pin['repositories'].items():
            repo = root if name == 'incr' else root.parent / 'observe'
            head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
            require(head == expected['head'], f'Checkpoint changed: {repo}')
            dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=all'], text=True)
            require(not dirty, f'Checkpoint is not clean: {repo}')
            upstream = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '@{upstream}'], text=True).strip()
            require(upstream == head, f'Checkpoint is not the pushed upstream: {repo}')
            require(file_hash(repo / 'target/release' / name) == expected['binary_sha256'],
                    f'Runtime binary changed: {repo}')
        baseline = root.parent / 'incr-main-qualification'
        require(subprocess.check_output(['git', '-C', str(baseline), 'rev-parse', 'HEAD'], text=True).strip()
                == pin['baseline_head'], 'Original baseline revision changed')
        require(file_hash(baseline / 'target/release/incr') == pin['baseline_binary_sha256'],
                'Original baseline binary changed')
        patch = subprocess.check_output(['git', '-C', str(baseline), 'diff', 'HEAD', '--', 'src', 'Cargo.toml', 'Cargo.lock'])
        require(patch == (study / 'reference/original-minimal-fixes.patch').read_bytes(),
                'Original baseline patch changed')

    def monitor(run):
        command([sys.executable, str(harness / 'monitor.py'), str(run)])
        report = json.loads((run / 'monitor.json').read_text())
        require(report['health'] == 'ok', f'Evidence audit failed: {run}')

    def retarget_monitor(run):
        target = Path.home() / '.config/systemd/user/incr-bench-monitor.service.d/trusted-cache-target.conf'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('[Service]\nExecStart=\nExecStart=/usr/bin/python3 '
                          + str(harness / 'monitor.py') + ' ' + str(run) + '\n')
        command(['systemctl', '--user', 'daemon-reload'])
        command(['systemctl', '--user', 'start', 'incr-bench-monitor.timer'])

    old_work = old_study / '.work'
    old_lock = (old_work / 'study.lock').open('a+')
    fcntl.flock(old_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        service_pid = subprocess.check_output(
            ['systemctl', '--user', 'show', 'incr-bench-study.service',
             '-p', 'MainPID', '--value'], text=True).strip()
        if not args.check:
            require(service_pid == str(os.getpid()),
                    'Launch the controller as the persistent incr-bench-study.service')
        require(set(pin['repositories']) == {'incr', 'observe'},
                'Both implementation repositories must be pinned')
        require(not WORK.exists(), 'Reproduction requires a completely fresh workspace')
        require(pin['targeted_review_passed'] and pin['qualification_passed'], 'Checkpoint gates have not passed')
        verify_checkpoint()
        linger = subprocess.check_output(['loginctl', 'show-user', str(os.getuid()), '-p', 'Linger', '--value'], text=True).strip()
        require(linger == 'yes', 'User services must survive logout')
        if args.check:
            record('preflight-complete', measurements_launched=False)
            print('Checkpoint verified; no preparation or measurements launched.', flush=True)
            return
        command(['systemctl', '--user', 'stop', 'incr-bench-monitor.timer'])
        for suite, profile, run_name, expected in [
                ('paper', 'paper', 'historical-01', 828),
                ('supplemental', 'full', 'supplemental-01', 45)]:
            verify_checkpoint()
            manifest_name = 'manifest.json' if suite == 'paper' else 'supplemental-manifest.json'
            manifest = json.loads((study / manifest_name).read_text())
            families = ','.join(b['name'] for b in manifest['benchmarks'])
            require(sum(len(b['scripts']) for b in manifest['benchmarks']) * 9 == expected,
                    f'Unexpected workload scope: {suite}')
            record('preparing', suite=suite, profile=profile)
            command([sys.executable, str(harness / 'study.py'), 'prepare',
                     '--profile', profile, '--only', families,
                     '--result', str(study / 'results' / (run_name + '-preparation'))], suite)
            # Preparation is outside timings. Reserve room for the independent fixture
            # copy; the supervisor additionally enforces actual runtime/cache budgets.
            import shutil
            data_bytes = allocated_bytes(WORK / 'data' / profile)
            require(shutil.disk_usage(WORK).free >= 8 * GIB + data_bytes,
                    'Prepared inputs leave insufficient space for fixtures and reserve')
            require(allocated_bytes(WORK) + data_bytes <= 32 * GIB,
                    'Prepared inputs and independent fixtures exceed workspace budget')
            verify_checkpoint()
            run = study / 'results' / run_name
            record('measuring', suite=suite, run=str(run), expected_invocations=expected)
            argv = [sys.executable, str(harness / 'study.py'), 'run',
                    '--profile', profile, '--only', families, '--run-id', run_name,
                    '--repetitions', '3', '--modes', 'bash,original,observe',
                    '--native-transform', '--assume-directory-access',
                    '--content-validated-inputs', '--release-inputs']
            child = subprocess.Popen(argv, cwd=root, env=dict(os.environ, INCR_BENCH_SUITE=suite))
            deadline = time.monotonic() + 600
            while not (run / 'status.json').is_file():
                require(child.poll() is None, f'Worker exited before measurements: {suite}')
                require(time.monotonic() < deadline, 'Worker startup deadline exceeded')
                time.sleep(2)
            retarget_monitor(run)
            require(child.wait() == 0, f'Benchmark worker failed: {run}')
            command(['systemctl', '--user', 'stop', 'incr-bench-monitor.timer'])
            summary = json.loads((run / 'summary.json').read_text())
            require(summary['complete'] and summary['invocations'] == expected
                    and summary['valid_invocations'] == expected and not summary['failed_sequences'],
                    f'Incomplete or invalid workload: {run}')
            monitor(run)
            command([sys.executable, str(harness / 'cohort_report.py'), str(run),
                     '--output', str(study / 'results' / (run_name + '-paired-report.json'))])
            verify_checkpoint()
        record('complete', historical_invocations=828, supplemental_invocations=45)
    except BaseException as error:
        record('failed', error=repr(error))
        raise
    finally:
        old_lock.close()


if __name__ == '__main__':
    main()
