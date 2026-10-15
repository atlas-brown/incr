"""Read only the fixed-format replay-barrier prefix of current cache metadata.

Diagnostic schema: Incr cache format 25, fixed-width little-endian bincode.
Never validates cache entries or changes their reuse decisions. Run only against
an Observe sequence, because the original baseline uses a different schema.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK, STUDY, atomic_json


def barrier_prefix(path):
    with path.open('rb') as stream:
        header = stream.read(12)
        if len(header) != 12: raise ValueError('incomplete metadata header')
        exit_code, count = struct.unpack('<iQ', header)
        if count > 128: raise ValueError('unexpected schema or barrier count')
        barriers = []
        for _ in range(count):
            size = stream.read(8)
            if len(size) != 8: raise ValueError('incomplete barrier length')
            length = struct.unpack('<Q', size)[0]
            if length > 4096: raise ValueError('unexpected barrier length')
            value = stream.read(length)
            if len(value) != length: raise ValueError('incomplete barrier')
            barriers.append(value.decode('utf-8'))
        return exit_code, barriers


def audit(run):
    run = Path(run).resolve()
    if not run.is_relative_to((STUDY/'results').resolve()):
        raise ValueError('Run must belong to this study')
    status = json.loads((run/'status.json').read_text())
    if status.get('mode') != 'observe' or status.get('state') != 'running':
        print('No live Observe sequence; no cache inspection performed')
        return
    setup=run/'sequences'/f"{status['benchmark']}.{status['mode']}.{status['repetition']}"/'setup.json'
    cache=Path(json.loads(setup.read_text())['environment']['INCR_CACHE_DIR'])
    rows = []
    for directory in sorted(cache.glob('batch_*')):
        path = directory/'data.incr'
        if not path.is_file() or path.is_symlink(): continue
        row = {'entry':directory.name}
        try:
            row['exit_code'], row['replay_barriers'] = barrier_prefix(path)
            info = directory/'debug_info.json'
            if info.is_file() and info.stat().st_size < 1024*1024:
                data = json.loads(info.read_text())
                row.update(command=data.get('name'), arguments=data.get('arguments'))
            from cache_metadata import directory_summary
            row.update(directory_summary(path))
        except (OSError, ValueError, struct.error) as error:
            row['diagnostic_error'] = str(error)
        rows.append(row)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    atomic_json(run/'cache-audits'/f'{stamp}.json', {'time':stamp,'status':status,'schema_compat':[25,26],'entries':rows,
        'scope':'Replay-barrier prefix only; not a full integrity/dependency validation'})
    print(json.dumps(rows, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    audit(parser.parse_args().run)


if __name__ == '__main__': main()
