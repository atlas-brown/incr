"""Paired transformer startup measurements, with identical generated output."""
import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK, atomic_json, file_hash, remove_owned, supervise
from provenance import fingerprint, verify, validate_arguments
from study import lock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--repetitions', type=int, default=12)
    parser.add_argument('--reference-scripts', type=Path, required=True)
    parser.add_argument('--bash', action='store_true')
    args = parser.parse_args()
    validate_arguments(parser, args)
    names = ('insert.py', 'shell_ast.py')
    if not all((args.reference_scripts/name).is_file() for name in names):
        parser.error('Reference directory must contain insert.py and shell_ast.py')
    result = ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True, exist_ok=False)
    fingerprint(ROOT, result, Path(__file__))
    snapshots = {}
    for mode, source in [('before', args.reference_scripts), ('after', ROOT/'src/scripts')]:
        destination = result/mode
        destination.mkdir()
        for name in names:
            shutil.copy2(source/name, destination/name)
            snapshots[f'{mode}/{name}'] = file_hash(destination/name)
    atomic_json(result/'helpers.json', snapshots)
    owned = Path(tempfile.mkdtemp(prefix='startup-probe-', dir=WORK))
    rows = []
    try:
        env = {key: os.environ[key] for key in ('HOME', 'USER', 'PATH') if key in os.environ}
        env.update(PYTHONPATH=str(ROOT/'src/scripts'), LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
        worker = ('import json,subprocess,sys,time;start=time.perf_counter();'
                  'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();'
                  'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":time.perf_counter()-start}));sys.exit(status)')
        reference = None
        for repetition in range(args.repetitions):
            for mode in (('before', 'after') if repetition % 2 == 0 else ('after', 'before')):
                capture = owned/'capture'
                if capture.exists(): remove_owned(capture)
                timing = owned/'timing.json'
                command = [str(ROOT/'qualification/.venv/bin/python'), str(result/mode/'insert.py'),
                           str(ROOT/'evaluation/benchmarks/word-freq/scripts/wf.sh'),
                           '--sys-path', str(ROOT/'target/release/incr'),
                           '--observe-path', str(ROOT.parent/'observe/target/release/observe')]
                if args.bash: command.append('--bash')
                row = supervise([sys.executable, '-c', worker, str(timing), *command], cwd=ROOT,
                    env=env, capture=capture, timeout=10, reserve=8*1024**3, budget=32*1024**3)
                actual = [row['returncode'], row['stdout_sha256'], row['stderr_sha256']]
                if reference is None: reference = actual
                row.update(mode=mode, repetition=repetition,
                    command_elapsed_sec=json.loads(timing.read_text())['elapsed_sec'],
                    valid=not row['failure'] and row['returncode']==0 and actual==reference)
                rows.append(row)
                atomic_json(result/'measurements.json', rows)
        if any(file_hash(result/path)!=digest for path, digest in snapshots.items()):
            raise RuntimeError('Copied helpers changed during measurement')
        atomic_json(result/'summary.json', {'valid':all(row['valid'] for row in rows),
            'samples':len(rows), 'bash':args.bash, 'median_sec':{
                mode:statistics.median(row['command_elapsed_sec'] for row in rows if row['mode']==mode)
                for mode in ('before','after')}})
    finally:
        try: verify(ROOT, result, Path(__file__))
        finally: remove_owned(owned)


if __name__ == '__main__':
    with lock(): main()
