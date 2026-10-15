"""Explicit, bounded dataset preparation; never call legacy install/clean scripts."""
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import time
import urllib.request
import zipfile

from common import GIB, ROOT, STUDY, WORK, atomic_json, file_hash, remove_owned

SOURCE = ROOT / 'evaluation/benchmarks'
BASE = 'https://atlas.cs.brown.edu/data/'


class LimitedHTTP:
    """Bound reads even while gzip/tar skip unselected members."""
    def __init__(self, response, maximum, deadline=1800):
        self.response = response
        self.maximum = maximum
        self.deadline = time.monotonic() + deadline
        self.total = 0

    def read(self, size=-1):
        if time.monotonic() > self.deadline:
            raise TimeoutError('Preparation stream deadline exceeded')
        if size < 0:
            raise ValueError('Unbounded preparation read')
        block = self.response.read(size)
        self.total += len(block)
        if self.total > self.maximum:
            raise ValueError('Preparation stream exceeds byte limit')
        return block


def check_space(reserve, expected=0):
    free = shutil.disk_usage(WORK).free
    if free < reserve + expected:
        raise RuntimeError(f'Insufficient disk: {free} free, {reserve + expected} required')


def download(url, target, reserve, maximum=GIB, retries=3):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    meta = target.with_suffix(target.suffix + '.json')
    if target.is_file() and meta.is_file():
        saved = json.loads(meta.read_text())
        if saved['url'] == url and saved['sha256'] == file_hash(target):
            return target
    pending = target.with_suffix(target.suffix + '.part')
    for attempt in range(retries):
        try:
            digest, total, started = hashlib.sha256(), 0, time.monotonic()
            with urllib.request.urlopen(url, timeout=30) as response, pending.open('wb') as out:
                declared = response.headers.get('Content-Length')
                if declared and int(declared) > maximum:
                    raise ValueError(f'Download exceeds declared budget: {url}')
                for block in iter(lambda: response.read(1024 * 1024), b''):
                    total += len(block)
                    if total > maximum or time.monotonic() - started > 1800:
                        raise ValueError(f'Download limit exceeded: {url}')
                    check_space(reserve, len(block))
                    out.write(block)
                    digest.update(block)
                if declared and total != int(declared):
                    raise IOError('Truncated HTTP response')
                out.flush()
                os.fsync(out.fileno())
            if total == 0:
                raise ValueError('Empty download')
            pending.replace(target)
            atomic_json(meta, {'url': url, 'bytes': total, 'sha256': digest.hexdigest(),
                               'download_sec': time.monotonic() - started})
            return target
        except (OSError, TimeoutError):
            pending.unlink(missing_ok=True)
            if attempt + 1 == retries:
                raise
            time.sleep(attempt + 1)
        except BaseException:
            pending.unlink(missing_ok=True)
            raise


def member_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'Unsafe archive member: {name}')
    return path


def extract_regular(archive, member, target, reserve):
    if not member.isfile():
        raise ValueError('Selected archive member is not regular')
    member_path(member.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    check_space(reserve, member.size)
    with archive.extractfile(member) as inp, target.open('wb') as out:
        shutil.copyfileobj(inp, out, 1024 * 1024)
    if target.stat().st_size != member.size:
        raise IOError('Truncated archive member')


def book_prefix(url, directory, count, reserve):
    """Reconstruct a count-based corpus without storing the enormous full archive.

    Archive order and all selected names/hashes are recorded. This is explicitly
    reconstructed data, not a claim that missing historical input hashes match.
    A partial network stream is intentional once the requested corpus is complete.
    """
    selected, seen, total = [], set(), 0
    started = time.monotonic()
    with urllib.request.urlopen(url, timeout=30) as response:
        with tarfile.open(fileobj=LimitedHTTP(response, 20 * GIB), mode='r|gz') as archive:
            for member in archive:
                if time.monotonic() - started > 1800:
                    raise TimeoutError('Corpus preparation deadline exceeded')
                member_path(member.name)
                if not member.isfile() or not member.name.endswith('.txt'):
                    continue
                name = PurePosixPath(member.name).name
                if name in seen:
                    raise ValueError(f'Duplicate book basename: {name}')
                seen.add(name)
                total += member.size
                if total > 5 * GIB:
                    raise ValueError('Selected corpus exceeds disk budget')
                extract_regular(archive, member, directory / name, reserve)
                selected.append(member.name)
                if len(selected) == count:
                    break
    if len(selected) != count:
        raise ValueError(f'Corpus has only {len(selected)} of {count} required books')
    return {'url': url, 'selection': 'first regular .txt members in archive order',
            'members': selected, 'bytes': total}


def prepare(name, profile, reserve):
    WORK.mkdir(exist_ok=True)
    target = WORK / 'data' / profile / name
    marker = target / 'prepared.json'
    if marker.is_file():
        saved = json.loads(marker.read_text())
        for entry in saved['files']:
            if file_hash(target / entry['path']) != entry['sha256']:
                raise RuntimeError(f'Prepared input changed: {entry["path"]}')
        return target
    remove_owned(target)
    target.mkdir(parents=True)
    inputs = target / 'inputs'
    inputs.mkdir()
    provenance = {'name': name, 'profile': profile, 'version': 1, 'recipes': []}
    src = SOURCE / name
    try:
        if profile == 'min':
            if name == 'file-mod':
                songs = inputs / 'songs'
                shutil.copytree(src / 'inputs/songs.min', songs)
            elif name == 'word-freq':
                shutil.copy2(src / 'inputs/10M.txt', inputs / 'text.txt')
            elif name in ('nlp-ngrams', 'nlp-uppercase', 'poet', 'spell'):
                shutil.copytree(src / 'min_inputs/pg-min', inputs / 'books')
            elif name in ('beginner', 'nginx-analysis'):
                shutil.copytree(src / 'min_inputs/nginx-logs', inputs / 'logs')
            elif name == 'covid':
                shutil.copy2(src / 'inputs/in_min.csv', inputs / 'covid.csv')
            elif name == 'weather':
                shutil.copy2(src / 'min_inputs/temperatures.min.txt', inputs / 'temperatures.txt')
            elif name == 'unixfun':
                shutil.copy2(src / 'min_inputs/4.txt', inputs / 'chess.txt')
            elif name == 'bio':
                shutil.copytree(src / 'inputs/bio-min', inputs / 'bio')
            elif name == 'dpt':
                shutil.copytree(src / 'inputs/dpt.min/dpt.ref', inputs / 'dpt.ref')
            else:
                raise ValueError(name)
        elif profile == 'paper':
            downloads = WORK / 'downloads'
            if name == 'file-mod':
                path = download(BASE + 'llm/playlist_small.tar.gz', downloads / 'music.tar.gz', reserve)
                with tarfile.open(path) as archive:
                    members = [m for m in archive if m.isfile() and m.name.endswith('.mp3')]
                    groups = sorted({str(PurePosixPath(m.name).parent) for m in members})[:2]
                    selected = [m for g in groups for m in sorted(members, key=lambda m: m.name)
                                if str(PurePosixPath(m.name).parent) == g]
                    selected = [m for g in groups for m in [m for m in selected
                                if str(PurePosixPath(m.name).parent) == g][:10]]
                    if len(selected) != 20:
                        raise ValueError('Music recipe requires two groups of ten MP3s')
                    for m in selected:
                        extract_regular(archive, m, inputs / 'songs' / Path(m.name).parent.name / Path(m.name).name, reserve)
                    provenance['recipes'].append({'members': [m.name for m in selected], 'url': BASE + 'llm/playlist_small.tar.gz'})
                remove_owned(path)
            elif name == 'word-freq':
                path = download(BASE + 'dummy/1M.txt', downloads / 'word-base.txt', reserve)
                # Preserve historical newline + dos2unix recipe and 30 repetitions.
                data = path.read_bytes().replace(b'\r\n', b'\n') + b'\n'
                with (inputs / 'text.txt').open('wb') as out:
                    for _ in range(30):
                        out.write(data)
                provenance['recipes'].append({'url': BASE + 'dummy/1M.txt', 'repetitions': 30, 'newline_added': True})
            elif name in ('nlp-ngrams', 'nlp-uppercase', 'poet', 'spell'):
                path = download(BASE + 'nlp/pg-small.tar.gz', downloads / 'pg-small.tar.gz', reserve)
                books = inputs / 'books'
                books.mkdir()
                limit = {'nlp-ngrams': 100, 'nlp-uppercase': 200,
                         'poet': 200, 'spell': 500}[name] * 1024 ** 2
                merged = name in ('nlp-ngrams', 'nlp-uppercase')
                with tarfile.open(path, 'r:gz') as archive:
                    members = []
                    seen = set()
                    for member in archive.getmembers():
                        member_path(member.name)
                        if not member.isfile() or not member.name.endswith('.txt'):
                            continue
                        basename = PurePosixPath(member.name).name
                        if basename in seen:
                            raise ValueError(f'Duplicate book basename: {basename}')
                        seen.add(basename)
                        members.append(member)
                    chosen, total = [], 0
                    for member in sorted(members, key=lambda m: PurePosixPath(m.name).name):
                        if merged and total >= limit:
                            break
                        if not merged and total + member.size > limit:
                            continue
                        chosen.append(member)
                        total += member.size
                    if not chosen or (merged and total < limit):
                        raise ValueError('Insufficient historical small-corpus input')
                    check_space(reserve, total)
                    # Extract in physical archive order so gzip never repeatedly
                    # rewinds for lexically sorted filenames.
                    staging = target / 'book-selection' if merged else books
                    staging.mkdir(exist_ok=True)
                    selected_names = {member.name for member in chosen}
                    for member in members:
                        if member.name in selected_names:
                            extract_regular(archive, member, staging / PurePosixPath(member.name).name, reserve)
                    if merged:
                        check_space(reserve, total)
                        with (books / 'book.txt').open('wb') as output:
                            for member in chosen:
                                with (staging / PurePosixPath(member.name).name).open('rb') as inp:
                                    shutil.copyfileobj(inp, output, 1024 * 1024)
                        if (books / 'book.txt').stat().st_size != total:
                            raise IOError('Merged corpus length mismatch')
                        remove_owned(staging)
                provenance['recipes'].append({
                    'url': BASE + 'nlp/pg-small.tar.gz', 'archive_sha256': file_hash(path),
                    'basis': 'historical small fetch recipe; paper counts are contextual',
                    'selection': 'lexical whole-book prefix through limit' if merged else 'lexical greedy whole books within cap',
                    'limit_bytes': limit, 'bytes': total,
                    'members': [member.name for member in chosen]})
            elif name in ('beginner', 'nginx-analysis'):
                path = download(BASE + 'nginx.zip', downloads / 'nginx.zip', reserve)
                logs = inputs / 'logs'
                logs.mkdir()
                with zipfile.ZipFile(path) as archive:
                    members = sorted(n for n in archive.namelist() if not n.endswith('/')
                                     and PurePosixPath(n).parts[0] == 'nginx-logs')
                    if not members or not any(PurePosixPath(n).name == 'log0' for n in members):
                        raise ValueError('Nginx archive does not contain the expected log directory')
                    with (logs / 'log0').open('wb') as out:
                        for n in members:
                            member_path(n)
                            with archive.open(n) as inp:
                                shutil.copyfileobj(inp, out, 1024 * 1024)
                initial = (logs / 'log0').stat().st_size
                # Match the recorded run recipes; paper table sizes may be stale.
                doublings = 3 if name == 'beginner' else 2
                for _ in range(doublings):
                    p = logs / 'log0'
                    size = p.stat().st_size
                    with p.open('rb') as inp, p.open('ab') as out:
                        remaining = size
                        while remaining:
                            block = inp.read(min(1024 * 1024, remaining))
                            if not block:
                                raise IOError('Log source was truncated during preparation')
                            out.write(block)
                            remaining -= len(block)
                provenance['recipes'].append({'url': BASE + 'nginx.zip', 'members': members,
                    'base_bytes': initial, 'doublings': doublings,
                    'profile_basis': 'historical small-input preparation recipe'})
            elif name == 'unixfun':
                path = download(BASE + 'unix50/small/4_30M.txt', downloads / 'chess-base.txt', reserve)
                repetitions = (1024 ** 3) // path.stat().st_size
                with (inputs / 'chess.txt').open('wb') as out:
                    for _ in range(repetitions):
                        with path.open('rb') as inp:
                            shutil.copyfileobj(inp, out, 1024 * 1024)
                provenance['recipes'].append({'url': BASE + 'unix50/small/4_30M.txt', 'repetitions': repetitions})
            elif name == 'covid':
                # Do not materialize the multi-GB source before taking 5M rows.
                with urllib.request.urlopen(BASE + 'covid-mts/in_small.csv.gz', timeout=30) as response:
                    with gzip.GzipFile(fileobj=LimitedHTTP(response, 2 * GIB)) as inp, (inputs / 'covid.csv').open('wb') as out:
                        count = 0
                        while True:
                            row = inp.readline(1024 * 1024)
                            if not row:
                                break
                            if not row.endswith(b'\n'):
                                raise ValueError('COVID row is unterminated or exceeds 1 MiB')
                            if count % 16384 == 0:
                                check_space(reserve)
                            out.write(row)
                            count += 1
                            if count == 5_000_000:
                                break
                if count != 5_000_000:
                    raise ValueError('COVID data has fewer than 5M rows')
                provenance['recipes'].append({'url': BASE + 'covid-mts/in_small.csv.gz', 'rows': count})
            elif name == 'weather':
                path = download(BASE + 'max-temp/temperatures.small.tar.gz', downloads / 'weather.tar.gz', reserve)
                with tarfile.open(path) as archive:
                    m = next(m for m in archive if m.isfile() and m.name.endswith('temperatures.small.txt'))
                    extract_regular(archive, m, inputs / 'temperatures.txt', reserve)
                provenance['recipes'].append({'url': BASE + 'max-temp/temperatures.small.tar.gz', 'member': m.name})
                remove_owned(path)
            elif name == 'bio':
                bio = inputs / 'bio'
                bio.mkdir()
                shutil.copy2(STUDY / 'reference/bio-historical-samples.txt', bio / 'input.txt')
                for row in (bio / 'input.txt').read_text().splitlines():
                    sample = row.split()[1]
                    download(BASE + f'bio/medium/{sample}.bam', bio / f'{sample}.bam', reserve)
                provenance['recipes'].append({'sample_list': 'reference/bio-historical-samples.txt', 'tier': 'medium', 'samples': 3})
            elif name == 'dpt':
                path = download('https://atlas-group.cs.brown.edu/data/dpt/dpt.zip', inputs / 'images.zip', reserve)
                provenance['recipes'].append({'url': 'https://atlas-group.cs.brown.edu/data/dpt/dpt.zip',
                    'timed_fetch': 'local HTTP fixture mirror; same wget/unzip commands, pinned bytes'})
            else:
                raise ValueError(name)
        else:
            raise ValueError(profile)
        # Models are reused after hashing, never downloaded twice or copied per mode.
        if name == 'dpt':
            models = SOURCE / 'dpt/inputs/models'
            for required in ('sam_vit_h.pth', 'model.h5', 'rdict.json'):
                if not (models / required).is_file():
                    raise RuntimeError(f'DPT prerequisite missing: {required}')
            provenance['models'] = [{'path': str(p), 'sha256': file_hash(p), 'bytes': p.stat().st_size}
                                    for p in sorted(models.iterdir()) if p.is_file()]
        files = [p for p in sorted(inputs.rglob('*')) if p.is_file()]
        if not files or any(p.stat().st_size == 0 for p in files):
            raise ValueError('Empty prepared input')
        provenance['files'] = [{'path': str(p.relative_to(target)), 'bytes': p.stat().st_size,
                                'sha256': file_hash(p)} for p in files]
        provenance['input_bytes'] = sum(p.stat().st_size for p in files)
        provenance['preparation_code_sha256'] = file_hash(Path(__file__))
        atomic_json(marker, provenance)
        return target
    except BaseException:
        # No marker means a partial corpus can never be used by a runner.
        raise
