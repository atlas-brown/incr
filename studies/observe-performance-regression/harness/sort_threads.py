"""Serial native-sort thread-count experiments; no runtime shortcuts."""
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK, atomic_json, remove_owned, supervise, file_hash
from provenance import fingerprint, verify, validate_arguments
from study import lock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--mib', type=int, default=8)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--input',type=Path,help='Optional frozen local sort input, up to 1 GiB')
    parser.add_argument('--prototype', type=Path, help='Compare a diagnostic plain-sort prototype against native GNU sort')
    args = parser.parse_args()
    validate_arguments(parser, args)
    if args.prototype is not None and not args.prototype.is_file():
        parser.error('Prototype binary must exist')
    if args.input is not None and (not args.input.is_file() or args.input.stat().st_size > 1024**3):
        parser.error('Input must be an existing file no larger than 1 GiB')
    result = ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True, exist_ok=False)
    fingerprint(ROOT, result, Path(__file__))
    prototype = None
    prototype_hash = None
    if args.prototype is not None:
        prototype = result/'prototype'
        shutil.copy2(args.prototype, prototype)
        prototype_hash = file_hash(prototype)
        if args.prototype.with_suffix('.rs').is_file():
            shutil.copy2(args.prototype.with_suffix('.rs'), result/'prototype.rs')
        atomic_json(result/'prototype.json', {'source':str(args.prototype.resolve()),'sha256':prototype_hash})
    owned = Path(tempfile.mkdtemp(prefix='sort-threads-', dir=WORK))
    rows = []
    try:
        line = b'one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\nten\n'
        if args.input is None:
            (owned/'input').write_bytes((line * (args.mib*1024**2//len(line)+1))[:args.mib*1024**2])
        else:
            shutil.copyfile(args.input, owned/'input')
        input_hash=file_hash(owned/'input')
        atomic_json(result/'input.json',{'source':str(args.input.resolve()) if args.input else 'generated tokens','bytes':(owned/'input').stat().st_size,'sha256':input_hash})
        (owned/'invoke').write_text('exec "$@" < input\n')
        env = {key: os.environ[key] for key in ('HOME', 'USER', 'PATH') if key in os.environ}
        env.update(LC_ALL='C', LANG='C', TMPDIR=str(owned))
        worker = ('import json,resource,subprocess,sys,time;start=time.perf_counter();'
                  'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();'
                  'elapsed=time.perf_counter()-start;r=resource.getrusage(resource.RUSAGE_CHILDREN);'
                  'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":elapsed,"user_sec":r.ru_utime,"system_sec":r.ru_stime}));sys.exit(status)')
        reference = None
        for repetition in range(args.repetitions):
            counts = [None, 'prototype'] if prototype else [None, 1, 2, 4, 8]
            random.Random(repetition).shuffle(counts)
            if repetition == 0:
                counts.remove(None)
                counts.insert(0,None)
            for count in counts:
                capture = owned/'capture'
                if capture.exists(): remove_owned(capture)
                timing = owned/'timing.json'
                command = [str(prototype)] if count == 'prototype' else ['sort'] + ([] if count is None else [f'--parallel={count}'])
                row = supervise([sys.executable, '-c', worker, str(timing), 'bash', str(owned/'invoke'), *command],
                    cwd=owned, env=env, capture=capture, timeout=60, reserve=8*1024**3, budget=32*1024**3)
                actual = [row['returncode'], row['stdout_sha256'], row['stderr_sha256']]
                if reference is None: reference = actual
                row.update(threads=count, repetition=repetition, command_resources=json.loads(timing.read_text()),
                    valid=not row['failure'] and row['returncode']==0 and actual==reference)
                rows.append(row)
                atomic_json(result/'measurements.json', rows)
                print(count, row['command_resources'], row['valid'], flush=True)
        if file_hash(owned/'input') != input_hash:
            raise RuntimeError('Input changed during measurement')
        atomic_json(result/'summary.json', {'valid': all(row['valid'] for row in rows), 'samples':len(rows),
            'mib':args.mib, 'median_sec': {str(count):statistics.median(row['command_resources']['elapsed_sec']
                for row in rows if row['threads']==count) for count in ([None,'prototype'] if prototype else [None,1,2,4,8])}})
    finally:
        try:
            verify(ROOT, result, Path(__file__))
            if prototype and file_hash(prototype) != prototype_hash:
                atomic_json(result/'summary.json',{'valid':False,'error':'Prototype binary changed'})
                raise RuntimeError('Prototype binary changed during measurement')
        finally: remove_owned(owned)


if __name__ == '__main__':
    with lock(): main()
