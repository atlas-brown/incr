"""Validation runs in a separately supervised process, including decoders."""
import argparse
import json
from pathlib import Path

from common import atomic_json, file_hash
from validate import independent_checks, manifest, normalized_stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fixture', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('name')
    parser.add_argument('script')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    record = json.loads((args.capture / 'supervisor.json').read_text())
    stderr = normalized_stderr(args.capture / 'stderr', args.name)
    result = {'returncode': record['returncode'], 'stdout_sha256': record['stdout_sha256'],
              'normalized_stderr_sha256': stderr['sha256'], 'stderr_sample': stderr['sample'],
              'outputs': manifest(args.fixture, args.name),
              'problems': independent_checks(args.fixture, args.name, args.script, record, stderr)}
    if args.name == 'image-annotation':
        from image_annotation import comparison_payload
        result['comparison_policy'] = 'image-content-preservation; generated titles are nondeterministic'
        result['comparison_outputs'] = comparison_payload(result['outputs'])
    # Tracee writes outside outputs cannot be silently discarded. Immutable
    # input/source inventories are checked by the driver around each sequence.
    atomic_json(args.output, result)


if __name__ == '__main__':
    main()
