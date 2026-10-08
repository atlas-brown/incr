#!/usr/bin/env python3
"""Cancel a timing-dependent temporary write while preserving final outputs."""
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
WORKER = '''import os,pathlib,select,sys,time
first = os.read(0, 1)
extra = pathlib.Path('data/extra')
changed = not select.select([0], [], [], 0)[0]
if changed:
    original = extra.read_bytes()
    metadata = extra.stat()
    extra.chmod(0o600)
    extra.write_bytes(b'partial')
rest = bytearray()
while True:
    chunk = os.read(0, 4096)
    if not chunk: break
    rest.extend(chunk)
time.sleep(.3)
if changed:
    extra.write_bytes(original)
    extra.chmod(metadata.st_mode & 0o777)
    os.utime(extra, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
result = first + rest
pathlib.Path('data/output').write_bytes(result)
sys.stdout.buffer.write(result)
'''
PRODUCER = '''import pathlib,sys,time
sys.stdout.buffer.write(b'A'); sys.stdout.buffer.flush()
deadline = time.monotonic() + 2
while pathlib.Path('data/extra').read_bytes() != b'partial':
    if time.monotonic() > deadline: raise SystemExit('temporary write did not occur')
    time.sleep(.001)
sys.stdout.buffer.write(b'B')
'''


def main():
    records = []
    result_path = ROOT / 'qualification/results/effect-replay/speculative-restore.json'
    with tempfile.TemporaryDirectory(prefix='restore-probe-', dir=ROOT / 'qualification/.work') as temporary:
        work = Path(temporary)
        (work / 'data').mkdir()
        extra = work / 'data/extra'
        extra.write_bytes(b'original contents')
        extra.chmod(0o640)
        original_mtime = extra.stat().st_mtime_ns
        (work / 'worker.py').write_text(WORKER)
        (work / 'producer.py').write_text(PRODUCER)
        cache = work / 'cache'
        command = [str(ROOT / 'target/release/incr'), '--cache', str(cache),
                   '--observe', str(ROOT.parent / 'observe/target/release/observe'),
                   '--effect-policy', 'final', '--', sys.executable, str(work / 'worker.py')]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        previous = None
        for phase in ['cold', 'warm', 'warm-again']:
            output = work / 'data/output'
            output.unlink(missing_ok=True)
            if phase == 'cold':
                result = run(command, stdin=b'AB', cwd=work, env=environment, timeout=4)
            else:
                pipeline = shlex.join([sys.executable, str(work / 'producer.py')]) + ' | ' + shlex.join(command)
                result = run(['bash', '-o', 'pipefail', '-c', pipeline], cwd=work, env=environment, timeout=4)
            entries = {str(path): path.stat().st_mtime_ns for path in cache.glob('batch_*/data.incr')}
            valid = (result['returncode'] == 0 and result['stdout'] == 'AB' and result['stderr'] == ''
                     and not result['timeout'] and not result['leaked_descendants']
                     and not result['remaining_descendants'] and output.read_bytes() == b'AB'
                     and extra.read_bytes() == b'original contents' and extra.stat().st_mode & 0o777 == 0o640
                     and extra.stat().st_mtime_ns == original_mtime
                     and not list(cache.glob('*.snapshot')) and not list(cache.glob('*.gate')))
            reused = previous is not None and entries == previous and bool(entries)
            result.update(phase=phase, valid=valid, cache_reused=reused)
            records.append(result)
            result_path.write_text(json.dumps(records, indent=2) + '\n')
            print(phase, 'valid=' + str(valid), 'cache_reused=' + str(reused), flush=True)
            if not valid or (phase != 'cold' and not reused):
                return 1
            previous = entries
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
