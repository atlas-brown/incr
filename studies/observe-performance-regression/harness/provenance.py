"""Record and recheck all runtime sources, binaries and measurement code."""
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone


def inventory(directory):
    from common import file_hash
    return {str(path.relative_to(directory)): file_hash(path)
            for path in sorted(directory.rglob('*'))
            if path.is_file() and '__pycache__' not in path.parts}


def snapshot(root, driver, repositories):
    from common import file_hash
    data = {'platform': platform.platform(), 'driver_sha256': file_hash(driver),
            'probe_sources': inventory(root/'studies/observe-performance-regression/harness'),
            'supervisor_sources': inventory(root/'studies/paper-size-benchmarks/harness'),
            'repositories': {}}
    for repo in repositories:
        binary = repo/'target/release'/('observe' if repo.name.startswith('observe') else 'incr')
        patch = subprocess.check_output(['git','-C',str(repo),'diff','HEAD','--','src','Cargo.toml','Cargo.lock'])
        data['repositories'][str(repo)] = {
            'revision': subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
            'patch_sha256': hashlib.sha256(patch).hexdigest(),
            'sources': inventory(repo/'src'), 'binary_sha256': file_hash(binary),
            'entrypoints': {path.name: file_hash(path) for path in sorted(repo.glob('*.sh'))},
            'cargo': {name: file_hash(repo/name) for name in ('Cargo.toml','Cargo.lock') if (repo/name).exists()}}
    return data


def fingerprint(root, result, driver, extra_repositories=()):
    from common import atomic_json
    repositories = [root, root.parent/'observe', root.parent/'incr-main-qualification', *extra_repositories]
    data = snapshot(root, driver, repositories)
    data['time'] = datetime.now(timezone.utc).isoformat()
    atomic_json(result/'provenance.json', data)
    for index, repo in enumerate(repositories):
        patch = subprocess.check_output(['git','-C',str(repo),'diff','HEAD','--','src','Cargo.toml','Cargo.lock'])
        (result/f'source-{index}.patch').write_bytes(patch)
        # git diff omits new source files; retain their bytes as well as hashes.
        untracked = subprocess.check_output(['git', '-C', str(repo), 'ls-files',
            '--others', '--exclude-standard', '-z', '--', 'src'])
        for raw_path in untracked.split(b'\0'):
            if not raw_path:
                continue
            relative = Path(raw_path.decode('utf-8', errors='surrogateescape'))
            if '__pycache__' in relative.parts or not (repo/relative).is_file():
                continue
            destination = result/f'source-{index}-new'/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo/relative, destination)


def verify(root, result, driver):
    from common import atomic_json
    original = json.loads((result/'provenance.json').read_text())
    original.pop('time')
    current = snapshot(root, driver, [Path(path) for path in original['repositories']])
    valid = original == current
    atomic_json(result/'provenance-check.json', {'valid': valid, 'time': datetime.now(timezone.utc).isoformat()})
    if not valid:
        summary = result/'summary.json'
        if summary.exists():
            data = json.loads(summary.read_text())
            data.update(valid=False, provenance_failure='Code or binary changed during measurement')
            atomic_json(summary, data)
        raise RuntimeError('Code or binary changed during measurement; results invalidated')


def validate_arguments(parser, arguments):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', arguments.id):
        parser.error('Use a simple result ID containing letters, digits, dots, dashes or underscores')
    for name in ('runs', 'repetitions'):
        if hasattr(arguments, name) and getattr(arguments, name) < 1:
            parser.error(f'{name} must be positive')
    if hasattr(arguments, 'mib') and not 1 <= arguments.mib <= 1024:
        parser.error('Small probes support input sizes from 1 to 1024 MiB')
