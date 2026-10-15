"""Exercise changed stdin and warm replay for a pure command, with exact outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'studies/paper-size-benchmarks/harness'))
from common import WORK, atomic_json, file_hash, remove_owned, supervise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--mib', type=int, default=8)
    args = parser.parse_args()
    from provenance import validate_arguments
    validate_arguments(parser, args)
    result = ROOT / 'studies/observe-performance-regression/results' / args.id
    result.mkdir(parents=True, exist_ok=False)
    from provenance import fingerprint
    fingerprint(ROOT, result, Path(__file__))
    owned = Path(tempfile.mkdtemp(prefix='perf-candidates-', dir=WORK))
    fixture = owned / 'fixture'
    fixture.mkdir()
    invoke = fixture / 'invoke'
    invoke.write_text('exec "$@" < input\n')
    modes = {'original': ROOT.parent / 'incr-main-qualification', 'current-try': ROOT, 'observe': ROOT}
    rows = []
    env = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME', 'PATH') if key in os.environ}
    env.update(LC_ALL='C', INCR_EFFECT_POLICY='final')
    worker = ('import json,subprocess,sys,time;start=time.perf_counter();'
              'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();'
              'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":time.perf_counter()-start}));sys.exit(status)')
    try:
        for mode, top in modes.items():
            cache = owned / 'cache'
            if cache.exists(): remove_owned(cache)
            cache.mkdir()
            for iteration in range(12):
                variant = iteration if iteration < 8 else 0
                line = f'variant {variant} hello world\n'.encode()
                data = (line * (args.mib*1024**2//len(line)+1))[:args.mib*1024**2]
                (fixture / 'input').write_bytes(data)
                expected = hashlib.sha256(data.upper()).hexdigest()
                argv = [str(top / 'target/release/incr'), '--cache', str(cache), '--try', str(top/'src/scripts/try.sh')]
                if mode == 'observe': argv += ['--observe', str(ROOT.parent/'observe/target/release/observe')]
                argv += ['--', 'tr', 'a-z', 'A-Z']
                capture = owned / 'capture'
                if capture.exists(): remove_owned(capture)
                timing = owned / 'timing.json'
                row = supervise([sys.executable,'-c',worker,str(timing),'bash',str(invoke),*argv],
                                cwd=fixture,env=env,capture=capture,timeout=20,reserve=8*1024**3,budget=32*1024**3)
                row.update(mode=mode,iteration=iteration,variant=variant,
                           command_elapsed_sec=json.loads(timing.read_text())['elapsed_sec'],
                           valid=not row['failure'] and row['returncode']==0 and row['stdout_sha256']==expected)
                rows.append(row)
                atomic_json(result/'measurements.json',rows)
                print(mode,iteration,round(row['command_elapsed_sec'],5),row['valid'],flush=True)
        atomic_json(result/'summary.json',{'valid':all(row['valid'] for row in rows),'samples':len(rows),'mib':args.mib})
    finally:
        try:
            from provenance import verify
            verify(ROOT, result, Path(__file__))
        finally:
            remove_owned(owned)


if __name__ == '__main__':
    from study import lock
    with lock():
        main()
