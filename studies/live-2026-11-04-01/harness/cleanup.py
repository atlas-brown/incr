"""Explicit, locked cleanup of disposable study state; preserve result evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
import re
import shutil

from common import WORK, SCRATCH, STUDY, allocated_bytes, atomic_json, mounts_under, remove_owned
from study import lock


def plan(include_inputs=False, builds=()):
    # Recovery snapshots describe an incomplete rollback: removing their fixture
    # would lose the opportunity to inspect/repair it, even if caches are tiny.
    for cache in (WORK/'cache', SCRATCH/'cache'):
        if (cache.parent.resolve().is_relative_to(WORK.resolve())
                and not cache.is_symlink() and list(cache.glob('*.recovery'))):
            raise RuntimeError(f'Recovery requires inspection; preserving state under {cache}')
    paths = [SCRATCH, WORK/'fixture', WORK/'cache', WORK/'capture', WORK/'validation-capture']
    if include_inputs:
        paths += [WORK/'data/paper', WORK/'downloads']
    for name in builds:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name):
            raise ValueError(f'Use an explicit simple build ID: {name!r}')
        paths.append(WORK/'builds'/name)
    records = []
    for path in dict.fromkeys(paths):
        if not path.parent.resolve().is_relative_to(WORK.resolve()):
            raise ValueError(f'Cleanup parent escapes study workspace: {path}')
        records.append({'path': str(path), 'exists': path.exists() or path.is_symlink(),
                        'allocated_bytes': path.lstat().st_blocks*512 if path.is_symlink() else allocated_bytes(path),
                        'mounts': mounts_under(path)})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Delete the listed owned state; default only prints the plan')
    parser.add_argument('--include-inputs', action='store_true', help='Also remove historical-size prepared inputs and downloads')
    parser.add_argument('--build', action='append', default=[], help='Explicit obsolete frozen build ID; repeat as needed')
    args = parser.parse_args()
    with lock():
        records = plan(args.include_inputs, args.build)
        print(json.dumps({'apply': args.apply, 'paths': records}, indent=2), flush=True)
        if not args.apply:
            return
        # Keep a durable list before deletion, including partial-failure evidence.
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        destination = STUDY/'results/maintenance'/f'cleanup-{stamp}-{os.getpid()}.json'
        evidence = {'state': 'running', 'paths': records, 'removed': [],
                    'free_before': shutil.disk_usage(WORK).free}
        atomic_json(destination, evidence)
        try:
            for record in records:
                remove_owned(record['path'])
                evidence['removed'].append(record['path'])
                atomic_json(destination, evidence)
            evidence['state'] = 'complete'
        except BaseException as error:
            evidence.update(state='error', error=repr(error))
            raise
        finally:
            evidence['free_after'] = shutil.disk_usage(WORK).free
            atomic_json(destination, evidence)
        print(f'Cleanup evidence: {destination}')


if __name__ == '__main__':
    main()
