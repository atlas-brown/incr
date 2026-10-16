"""Export independent result directories after all measurements and monitors stop.

Raw workload payloads above 16 MiB stay on disk with
size/SHA256 receipts; measurement metadata, logs and source/provenance stay in
portable archives. No source evidence is removed or rewritten and no timings
from different runs are combined.
"""
import argparse
from contextlib import contextmanager
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    'paper': ROOT / 'studies/paper-size-benchmarks/results',
    'probes': ROOT / 'studies/observe-performance-regression/results',
    'bash': ROOT / 'studies/bash-parity-audit-2026-10-08/results',
    'qualification': ROOT / 'qualification/results',
}
METADATA = {'.json', '.jsonl', '.csv', '.log', '.patch', '.md', '.py', '.sh', '.c', '.rs', '.toml'}
RAW_LIMIT = 16 * 1024**2
ARCHIVE_LIMIT = 80 * 1024**2


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(1024**2), b''):
        value.update(block)
    return value.hexdigest()


@contextmanager
def reader(path):
    """Read owned result files without changing root-created capture permissions."""
    try:
        stream = path.open('rb')
    except PermissionError:
        child = subprocess.Popen(['sudo', '-n', 'cat', '--', str(path)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            yield child.stdout
            child.stdout.close()
            error = child.stderr.read().decode(errors='replace')
            require(child.wait(timeout=30) == 0,
                    'Privileged evidence read failed: ' + str(path) + ': ' + error)
        finally:
            child.stdout.close()
            child.stderr.close()
            if child.poll() is None:
                child.kill()
                child.wait(timeout=10)
    else:
        with stream:
            yield stream


def file_hash(path):
    with reader(path) as stream:
        return digest(stream)


def save(path, value):
    pending = path.with_suffix(path.suffix + '.pending')
    pending.write_text(json.dumps(value, indent=2) + '\n')
    pending.replace(path)


def identity(path):
    info = path.lstat()
    return info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns


def files_under(path):
    def fail(error):
        raise error

    for directory, names, files in os.walk(path, followlinks=False, onerror=fail):
        names.sort()
        files.sort()
        for name in names[:]:
            entry = Path(directory) / name
            if name == '__pycache__':
                names.remove(name)
            elif entry.is_symlink():
                names.remove(name)
                yield entry
        for name in files:
            if not name.endswith('.pyc'):
                yield Path(directory) / name


def declared_metadata(source):
    output = {}
    selections = {
        'summary.json': ('complete', 'invocations', 'expected_invocations', 'valid_invocations', 'failed_sequences', 'scope'),
        'configuration.json': ('suite', 'profile', 'only', 'repetitions', 'modes', 'annotations', 'native_transform', 'assume_directory_access', 'content_validated_inputs'),
        'status.json': ('state', 'phase', 'error'),
    }
    for name, keys in selections.items():
        path = source / name
        if path.is_file():
            try:
                value = json.loads(path.read_text())
                output[name] = {key: value[key] for key in keys if key in value}
            except (ValueError, TypeError):
                output[name] = {'unparsed': True}
    path = source / 'frozen-build.json'
    if path.is_file():
        value = json.loads(path.read_text())
        output['frozen-build.json'] = {
            'revisions': value.get('revisions'),
            'binary_hashes': {k: v for k, v in value.get('sha256', {}).items()
                             if k.endswith('/target/release/incr') or k.endswith('/target/release/observe')},
        }
    return output


def portable_parts(archive_path):
    """Split only generated archives; verify concatenated bytes before removal."""
    total_bytes = archive_path.stat().st_size
    total_hash = file_hash(archive_path)
    if total_bytes <= ARCHIVE_LIMIT:
        return total_bytes, total_hash, [
            {'name': archive_path.name, 'bytes': total_bytes, 'sha256': total_hash}]
    parts = []
    with archive_path.open('rb') as source:
        for index in range((total_bytes + ARCHIVE_LIMIT - 1) // ARCHIVE_LIMIT):
            data = source.read(ARCHIVE_LIMIT)
            part = archive_path.with_name(archive_path.name + f'.part-{index:03d}')
            part.write_bytes(data)
            parts.append({'name': part.name, 'bytes': len(data),
                          'sha256': hashlib.sha256(data).hexdigest()})
        require(not source.read(1), 'Archive grew while splitting')
    restored = hashlib.sha256()
    for info in parts:
        part = archive_path.parent / info['name']
        require(part.stat().st_size == info['bytes']
                and file_hash(part) == info['sha256'], 'Archive part mismatch')
        with part.open('rb') as stream:
            for block in iter(lambda: stream.read(1024**2), b''):
                restored.update(block)
    require(sum(p['bytes'] for p in parts) == total_bytes
            and restored.hexdigest() == total_hash, 'Split archive mismatch')
    archive_path.unlink()  # Verified generated derivative; source evidence stays.
    return total_bytes, total_hash, parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--namespaces', default='paper,probes,bash',
                        help='Comma-separated evidence roots, including qualification')
    args = parser.parse_args()
    namespaces = args.namespaces.split(',')
    require(len(namespaces) == len(set(namespaces))
            and set(namespaces) <= set(SOURCES), 'Unknown or duplicate evidence root')
    destination = args.destination.resolve()
    require(destination.is_relative_to(ROOT), 'Destination must be inside Incr')
    require(not any(destination.is_relative_to(p.resolve()) for p in SOURCES.values()), 'Destination overlaps source evidence')
    for unit in ('incr-bench-study.service', 'incr-bench-monitor.timer', 'incr-bench-monitor.service', 'incr-memory-qualification-01.service'):
        active = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', unit], timeout=10)
        require(active.returncode != 0, 'Stop and audit the live unit before archiving: ' + unit)
    lock = (SOURCES['paper'].parent / '.work/study.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    destination.mkdir(parents=True, exist_ok=False)
    report = {
        'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'namespaces': namespaces,
        'scope': 'Independent archives of all existing result groups in the selected roots, including failed/incomplete attempts; declared statuses are not substituted for final validation. No cross-revision timing pooling.',
        'bulk_policy': 'All measurement/provenance/log metadata is archived. Other regular payloads above16MiB remain at their original on-disk paths with size and SHA256 receipts; no source evidence is deleted.',
        'excluded_generated_files': ['__pycache__ directories', '*.pyc'],
        'archive_parts': 'Each portable part is at most80MiB. Concatenate parts in listed order before extraction; the combined SHA256 and every extracted member were verified.',
        'state': 'running', 'groups': [],
    }
    save(destination / 'catalog.json', report)
    try:
        for namespace in namespaces:
            source = SOURCES[namespace]
            require(source.is_dir(), 'Missing evidence root: ' + str(source))
            directories = sorted(p for p in source.iterdir() if p.is_dir() and not p.is_symlink() and p.name != '__pycache__')
            groups = [(p.name, p, list(files_under(p))) for p in directories]
            direct = sorted(p for p in source.iterdir() if p.is_file() or p.is_symlink())
            if direct:
                groups.append(('_root_files', source, direct))
            for name, origin, paths in groups:
                label = namespace + '--' + name
                catalog = {}
                originals = {}
                for path in sorted(paths):
                    relative = str(path.relative_to(origin))
                    before = identity(path)
                    if stat.S_ISLNK(before[2]):
                        catalog[relative] = {'kind': 'symlink', 'target': os.readlink(path), 'included': False,
                                             'reason': 'Link metadata retained here without dereferencing external state'}
                        continue
                    require(stat.S_ISREG(before[2]), 'Unexpected special evidence file: ' + str(path))
                    sha256 = file_hash(path)
                    require(identity(path) == before, 'Evidence changed while hashing: ' + str(path))
                    included = before[3] <= RAW_LIMIT or path.suffix in METADATA
                    catalog[relative] = {'kind': 'file', 'bytes': before[3], 'sha256': sha256, 'included': included}
                    if not included:
                        catalog[relative]['reason'] = 'Large raw workload payload retained at original source path'
                    else:
                        originals[relative] = (path, before)
                archive_path = destination / (label + '.tar.gz')
                with tarfile.open(archive_path, 'w:gz', compresslevel=6, dereference=True) as archive:
                    for relative, (path, before) in sorted(originals.items()):
                        require(identity(path) == before, 'Evidence changed before archiving: ' + str(path))
                        info = archive.gettarinfo(path, arcname=relative)
                        require(info.isfile(), 'Evidence changed file type: ' + str(path))
                        with reader(path) as stream:
                            archive.addfile(info, stream)
                        require(identity(path) == before, 'Evidence changed during archiving: ' + str(path))
                restored = {}
                with tarfile.open(archive_path, 'r:gz') as archive:
                    for member in archive:
                        require(member.isfile() and member.name not in restored, 'Invalid archive member')
                        with archive.extractfile(member) as stream:
                            restored[member.name] = digest(stream)
                expected = {name: catalog[name]['sha256'] for name in originals}
                require(restored == expected, 'Archive round-trip mismatch: ' + label)
                bundle_bytes, bundle_hash, parts = portable_parts(archive_path)
                save(destination / (label + '.files.json'), catalog)
                row = {'label': label, 'source': str(origin.relative_to(ROOT)), 'bundle': archive_path.name,
                       'bundle_sha256': bundle_hash, 'bundle_bytes': bundle_bytes, 'parts': parts,
                       'file_catalog': label + '.files.json', 'archived_files': len(originals),
                       'retained_bulk_files': sum(not x['included'] for x in catalog.values()),
                       'declared_metadata': declared_metadata(origin)}
                report['groups'].append(row)
                save(destination / 'catalog.json', report)
                print(label, len(originals), 'archived files;', row['retained_bulk_files'], 'bulk/link receipts', flush=True)
        report['state'] = 'complete'
    except BaseException as error:
        report.update(state='failed', error=repr(error))
        raise
    finally:
        save(destination / 'catalog.json', report)
        lock.close()


if __name__ == '__main__':
    main()
