#!/usr/bin/env python3
"""Record source, binary, dependency and input fingerprints for reproduction."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys

from build_snapshot import snapshot

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True, timeout=10).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    data = dict(candidate_snapshot=str(snapshot()), platform=platform.platform(),
                python=sys.version, repositories={}, files={})
    for root in [ROOT, ROOT.parent / 'observe', ROOT.parent / 'incr-main-qualification']:
        names = set(git(root, 'ls-files').splitlines()) | set(git(root, 'ls-files', '--others', '--exclude-standard').splitlines())
        names = sorted(n for n in names if (n.startswith('src/') or n in ['incr.sh', 'Cargo.toml', 'Cargo.lock'])
                       and (root / n).is_file() and '__pycache__' not in n)
        digest = hashlib.sha256()
        for name in names:
            digest.update(name.encode() + b'\0' + (root / name).read_bytes())
        data['repositories'][root.name] = dict(head=git(root, 'rev-parse', 'HEAD'),
            branch=git(root, 'branch', '--show-current'), source_sha256=digest.hexdigest(),
            binary_sha256=sha(root / 'target/release' / ('observe' if root.name == 'observe' else 'incr')))
    for path in sorted((ROOT / 'evaluation/benchmarks').rglob('*')):
        if not path.is_file() or path.is_symlink() or 'node_modules' in path.parts or '__pycache__' in path.parts:
            continue
        if 'inputs' in path.parts or path.suffix in ['.sh', '.py', '.js', '.json']:
            data['files'][str(path.relative_to(ROOT))] = dict(bytes=path.stat().st_size, sha256=sha(path))
    (args.results / 'final-build.json').write_text(json.dumps(data, indent=2) + '\n')
    dependencies = subprocess.check_output([str(ROOT / 'qualification/.venv/bin/python'), '-m', 'pip', 'freeze'], text=True, timeout=30)
    (args.results / 'python-dependencies.txt').write_text(dependencies)
    print('Snapshot:', data['candidate_snapshot'])
    print('Fingerprinted benchmark files:', len(data['files']))


if __name__ == '__main__':
    main()
