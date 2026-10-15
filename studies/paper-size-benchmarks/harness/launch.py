"""Explicitly launch one prepared evaluation as a persistent systemd user job."""
import argparse
import os
import pwd
from pathlib import Path
import subprocess
import sys
import shutil

from common import STUDY, WORK
from study import selected, lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('min', 'paper'), required=True)
    parser.add_argument('--stage', choices=('run', 'prepare'), default='run')
    parser.add_argument('--only', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--native-transform', action='store_true')
    parser.add_argument('--assume-directory-access', action='store_true')
    parser.add_argument('--continue-on-failure', action='store_true')
    parser.add_argument('--release-inputs', action='store_true')
    args = parser.parse_args()
    if args.stage == 'prepare' and (args.native_transform or args.assume_directory_access):
        parser.error('Runtime options apply only to measurements')
    if args.repetitions < 1 or not args.run_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.run_id):
        parser.error('Use positive repetitions and a simple, unique run ID')
    if (STUDY / 'results' / args.run_id).exists():
        parser.error('Run ID already exists; use run --resume or a new ID')
    # Check before launch; the worker takes the same lock for its entire run.
    with lock():
        for benchmark in selected(args.only):
            if args.stage == 'run' and not (WORK / 'data' / args.profile / benchmark['name'] / 'prepared.json').is_file():
                parser.error(f'Prepare {benchmark["name"]} explicitly first')
    active = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'incr-bench-study.service'], timeout=10)
    if active.returncode == 0:
        parser.error('Study service is already active; inspect it before launching another')
    # Linger keeps the user service alive when the chat/SSH window closes.
    subprocess.run(['sudo', '-n', 'loginctl', 'enable-linger', pwd.getpwuid(os.getuid()).pw_name], check=True, timeout=10)
    logs = STUDY / 'results/logs'
    logs.mkdir(parents=True, exist_ok=True)
    logfile = logs / f'{args.run_id}.log'
    subprocess.run(['systemctl', '--user', 'reset-failed', 'incr-bench-study.service'],
                   check=False, timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    command = [sys.executable, str(STUDY / 'harness/study.py'), 'run', '--profile', args.profile,
               '--only', args.only, '--run-id', args.run_id, '--repetitions', str(args.repetitions)]
    if args.native_transform:
        command.append('--native-transform')
    if args.assume_directory_access:
        command.append('--assume-directory-access')
    if args.continue_on_failure:
        command.append('--continue-on-failure')
    if args.release_inputs:
        command.append('--release-inputs')
    if args.stage == 'prepare':
        command = [sys.executable, str(STUDY / 'harness/study.py'), 'prepare', '--profile', args.profile,
                   '--only', args.only, '--result', str(STUDY / 'results' / args.run_id)]
    job = WORK / 'jobs' / args.run_id
    shutil.copytree(STUDY / 'harness', job / 'harness', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    command[1] = str(job / 'harness/study.py')
    subprocess.run(['systemd-run', '--user', '--unit=incr-bench-study', '--collect',
                    '--property=KillMode=control-group', '--property=TimeoutStopSec=20',
                    '--property=Restart=no', f'--property=WorkingDirectory={STUDY}',
                    f'--setenv=INCR_BENCH_STUDY={STUDY}',
                    f'--setenv=PATH={os.environ.get("PATH", os.defpath)}',
                    f'--property=StandardOutput=append:{logfile}',
                    f'--property=StandardError=append:{logfile}', '--', *command],
                   check=True, timeout=15)
    print(f'Launched incr-bench-study.service\nLog: {logfile}\nResults: {STUDY / "results" / args.run_id}')


if __name__ == '__main__':
    main()
