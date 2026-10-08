#!/usr/bin/env python3
"""Bounded, tiny streaming-effects probes; compare correctness and actual cache reuse."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
WORKER = '''import os, pathlib, sys, time
first = sys.stdin.buffer.readline()
p = pathlib.Path('data/output')
p.write_bytes(b'partial')
if sys.argv[1] == 'rename':
    pathlib.Path('data/transient').write_bytes(b'temporary')
    pathlib.Path('data/transient').unlink()
if sys.argv[1] == 'tree':
    os.mkdir('data/source')
    os.mkdir('data/source/nested')
    pathlib.Path('data/source/nested/file').write_bytes(b'tree')
    os.symlink('file', 'data/source/nested/link')
rest = sys.stdin.buffer.read()
time.sleep(0.3)
result = first + rest
if sys.argv[1] == 'tree':
    os.rename('data/source', 'data/destination')
if sys.argv[1] == 'rename':
    pathlib.Path('data/replacement').write_bytes(result)
    os.replace('data/replacement', p)
else:
    p.write_bytes(result)
sys.stdout.buffer.write(result)
'''
PRODUCER = '''import pathlib, sys, time
sys.stdout.buffer.write(b'first\\n'); sys.stdout.buffer.flush()
deadline = time.monotonic() + 2
p = pathlib.Path('data/output')
while not p.exists() or p.read_bytes() != b'partial':
    if time.monotonic() > deadline:
        raise SystemExit('writer did not expose its live effect')
    time.sleep(0.001)
sys.stdout.buffer.write(sys.argv[1].encode() + b'\\n')
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--expect-hit', action='store_true')
    parser.add_argument('--policy', choices=['live', 'final'])
    args = parser.parse_args()
    args.results.parent.mkdir(parents=True, exist_ok=True)
    work_root = ROOT / 'qualification/.work'
    work_root.mkdir(exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix='effect-probe-', dir=work_root) as temp:
        work = Path(temp)
        (work / 'data').mkdir()
        (work / 'worker.py').write_text(WORKER)
        (work / 'producer.py').write_text(PRODUCER)
        for scenario in ['overwrite', 'rename', 'tree']:
            cache = work / ('cache-' + scenario)
            command = [str(ROOT / 'target/release/incr'), '--cache', str(cache),
                       '--try', str(ROOT / 'src/scripts/try.sh'),
                       '--observe', str(ROOT.parent / 'observe/target/release/observe')]
            if args.policy:
                command += ['--effect-policy', args.policy]
            command += ['--', sys.executable, str(work / 'worker.py'), scenario]
            previous = {}
            for phase, suffix in [('cold', 'second'), ('warm', 'second'), ('changed', 'third'), ('older-candidate', 'second')]:
                pipeline = shlex.join([sys.executable, str(work / 'producer.py'), suffix]) + ' | ' + shlex.join(command)
                expected = 'first\n' + suffix + '\n'
                for output in (work / 'data').iterdir():
                    if output.is_dir() and not output.is_symlink():
                        shutil.rmtree(output)
                    else:
                        output.unlink()
                result = run(['bash', '-o', 'pipefail', '-c', pipeline], cwd=work,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), timeout=4)
                valid = (result['returncode'] == 0 and not result['timeout']
                         and not result['leaked_descendants'] and not result['remaining_descendants']
                         and result['stdout'] == expected and result['stderr'] == ''
                         and (work / 'data/output').read_bytes() == expected.encode()
                         and not (work / 'data/transient').exists() and not (work / 'data/replacement').exists())
                if scenario == 'tree':
                    valid = valid and (work / 'data/destination/nested/file').read_bytes() == b'tree'
                    valid = valid and os.readlink(work / 'data/destination/nested/link') == 'file'
                    valid = valid and not (work / 'data/source').exists()
                entries = {str(p.relative_to(cache)): p.stat().st_mtime_ns for p in cache.glob('batch_*/data.incr')}
                retained = bool(previous.get(suffix)) and all(entries.get(name) == stamp for name, stamp in previous[suffix].items())
                result.update(scenario=scenario, phase=phase, valid=valid,
                              cache_metadata_retained=retained, entries=len(entries))
                records.append(result)
                args.results.write_text(json.dumps(records, indent=2) + '\n')
                print(scenario, phase, 'valid=' + str(valid), 'cache_retained=' + str(retained),
                      f"seconds={result['elapsed_sec']:.3f}", flush=True)
                if not valid or (args.expect_hit and phase in ['warm', 'older-candidate'] and not retained):
                    raise SystemExit(1)
                if suffix not in previous:
                    previous[suffix] = entries.copy()


if __name__ == '__main__':
    main()
