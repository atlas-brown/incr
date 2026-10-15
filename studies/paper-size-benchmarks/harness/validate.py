"""Streaming application-output comparison and independent workload checks."""
import gzip
import hashlib
import io
from pathlib import Path
import re
import stat
import subprocess
import tarfile

from common import file_hash


def hash_stream(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def decoded_file(path):
    """Remove archive timestamps/salts, retaining names, modes and payloads."""
    path = Path(path)
    proc = None
    raw = path.open('rb')
    try:
        if path.name.endswith('.enc'):
            proc = subprocess.Popen(['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2',
                '-iter', '20000', '-k', 'key', '-in', str(path)], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            raw.close()
            raw = proc.stdout
        stream = io.BufferedReader(raw) if not isinstance(raw, io.BufferedReader) else raw
        if stream.peek(2)[:2] == b'\x1f\x8b':
            stream = gzip.GzipFile(fileobj=stream)
        if '.tar' in path.name:
            members = []
            with tarfile.open(fileobj=stream, mode='r|') as archive:
                for member in archive:
                    data = archive.extractfile(member) if member.isfile() else None
                    if data is not None and member.name.endswith('.gz'):
                        data = gzip.GzipFile(fileobj=data)
                    digest = hash_stream(data) if data else None
                    members.append([member.name, member.mode, member.type.decode(), member.linkname, digest])
            # Drain decrypt output before wait, even if tar stopped at end markers.
            for _ in iter(lambda: stream.read(1024 * 1024), b''):
                pass
            result = sorted(members)
        else:
            result = hash_stream(stream)
        if proc is not None:
            error = proc.stderr.read(65536)
            if proc.wait(timeout=10) != 0:
                raise ValueError(f'Cannot decode encrypted output: {error!r}')
        return result
    finally:
        raw.close()
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


def bam_hash(path):
    """Compare alignment payloads; retain header semantics excluding @PG provenance."""
    digest = hashlib.sha256()
    with subprocess.Popen(['samtools', 'view', '-h', str(path)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as proc:
        for row in proc.stdout:
            if not row.startswith(b'@PG\t'):
                digest.update(row)
        error = proc.stderr.read(65536)
        if proc.wait(timeout=30) != 0:
            raise ValueError(f'Invalid BAM output: {error!r}')
    return digest.hexdigest()


def normalized_stderr(path, name):
    digest, sample, total, sample_bytes, errors = hashlib.sha256(), [], 0, 0, []
    # FFmpeg emits progress separated by CR, not LF; bounded read avoids huge rows.
    with Path(path).open('rb') as stream:
        pending = b''
        for block in iter(lambda: stream.read(65536), b''):
            pending += block
            lines = re.split(rb'[\r\n]', pending)
            pending = lines.pop()
            if len(pending) > 4 * 1024 * 1024:
                raise ValueError('Unreasonably long stderr record')
            for row in lines:
                row = normalize_row(row, name)
                if row is None:
                    continue
                digest.update(row + b'\n')
                total += len(row)
                if re.search(rb'No such file or directory|Traceback \(most recent|command not found|\[E::|failed to open|Error:|\bERROR\s+[45]\d\d:', row, re.I):
                    errors.append(row[:1024].decode(errors='replace'))
                if sample_bytes < 65536:
                    sample.append(row)
                    sample_bytes += len(row)
        if pending:
            row = normalize_row(pending, name)
            if row is not None:
                digest.update(row + b'\n')
                total += len(row)
                sample.append(row[:65536])
                if re.search(rb'No such file or directory|Traceback \(most recent|command not found|\[E::|failed to open|Error:|\bERROR\s+[45]\d\d:', row, re.I):
                    errors.append(row[:1024].decode(errors='replace'))
    return {'sha256': digest.hexdigest(), 'sample': b'\n'.join(sample).decode(errors='replace'),
            'bytes': total, 'errors': errors[:100]}


def normalize_row(row, name):
    if name == 'file-mod':
        if re.match(rb'^(?:size|frame)=', row.strip()):
            return None
        row = re.sub(rb'0x[0-9a-fA-F]+', b'<address>', row)
    if name == 'dpt':
        # Wget's clock/rate/ETA are transport provenance; keep URL, HTTP status,
        # filename, progress offset/percentage and exact saved-byte counts.
        row = re.sub(rb'^--\d{4}-\d\d-\d\d \d\d:\d\d:\d\d--', b'--<time>--', row)
        progress = re.fullmatch(rb'(\s*\d+K[ .]*\d+%)\s+[0-9.]+[KMGT]?(?:=\S+|\s+\S+)\s*', row)
        if progress:
            row = progress[1] + b' <rate> <duration>'
        row = re.sub(rb'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d \([0-9.]+ [KMGT]?B/s\)( - .+ saved \[\d+/\d+\])$',
                     rb'<time> (<rate>)\1', row)
        row = re.sub(rb'^([IWEF]\d{4}) \d\d:\d\d:\d+\.\d+\s+\d+ ', rb'\1 <time> <pid> ', row)
        row = re.sub(rb'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+:', b'<time>:', row)
    return row


def manifest(fixture, name):
    result, identities = {}, {}
    # Captures, caches and interpreter/generated helpers are outside outputs.
    # Private TMPDIR is measured and cleaned separately, never an application output.
    paths = list((fixture / 'outputs').rglob('*'))
    if name == 'dpt':
        paths += list((fixture / 'inputs/dpt').rglob('*'))
    # Include unexpected application directories and dangling links too. Merely
    # scanning root files would miss extra effects such as scratch/result.txt.
    infrastructure = {'outputs', 'inputs', 'scripts', 'tmp', 'config', 'Gene_locs.txt'}
    for path in fixture.iterdir():
        if path.name not in infrastructure:
            paths.append(path)
            if path.is_dir() and not path.is_symlink():
                paths.extend(path.rglob('*'))
    for path in sorted(paths):
        rel = str(path.relative_to(fixture))
        metadata = path.lstat()
        entry = {'mode': stat.S_IMODE(metadata.st_mode)}
        if stat.S_ISLNK(metadata.st_mode):
            entry.update(kind='symlink', target=str(path.readlink()))
        elif stat.S_ISDIR(metadata.st_mode):
            entry.update(kind='directory')
        elif stat.S_ISREG(metadata.st_mode):
            key = metadata.st_dev, metadata.st_ino
            content = (decoded_file(path) if name == 'file-mod' else
                       bam_hash(path) if path.suffix == '.bam' else file_hash(path))
            entry.update(kind='file', content=content)
            if metadata.st_nlink > 1:
                entry['hardlink'] = identities.setdefault(key, rel)
        else:
            entry.update(kind='special')
        result[rel] = entry
    return result


def independent_checks(fixture, name, script, record, stderr):
    problems = []
    if record['failure']:
        problems.append(record['failure'])
    if record['returncode'] != 0:
        problems.append(f'nonzero status {record["returncode"]}')
    if stderr.get('errors'):
        problems.append('unexpected error diagnostic')
    outputs = fixture / 'outputs'
    if name in ('web-search', 'weather-tufte'):
        from supplemental import independent_checks as supplemental_checks
        problems.extend(supplemental_checks(fixture, name, script))
    if name in ('word-freq', 'covid', 'beginner', 'nginx-analysis', 'unixfun', 'spell'):
        if record['stdout_bytes'] == 0:
            # Some filtered tiny examples legitimately have no matches.
            if name in ('word-freq', 'covid', 'spell'):
                problems.append('empty primary output')
    if name in ('nlp-ngrams', 'nlp-uppercase') and not any(p.is_file() for p in outputs.rglob('*')):
        problems.append('no NLP output files')
    if name in ('nlp-ngrams', 'nlp-uppercase'):
        book = sorted((fixture / 'inputs/books').iterdir())[0].name
        expected = {
            'ngrams-1.sh': f'4_3_unigrams/{book}.input.unigrams.study.out',
            'ngrams-2.sh': f'4_3/{book}.input.bigrams.study.out',
            'ngrams-3.sh': f'8.2_2/{book}.study.out',
            'uppercase_by_token.sh': f'6_1_1/{book}.study.out',
            'uppercase_by_type.sh': f'6_1_2/{book}.study.out'}[script]
        if not (outputs / expected).is_file():
            problems.append(f'missing version-specific NLP output: {expected}')
    if name == 'weather':
        required = ['max.txt'] + (['min.txt'] if script != 'temp-analytics-1.sh' else [])
        if script == 'temp-analytics-3.sh':
            required.append('average.txt')
        for filename in required:
            try:
                float((outputs / 'statistics' / filename).read_text().strip())
            except (OSError, ValueError):
                problems.append(f'invalid weather output {filename}')
    if name == 'file-mod':
        songs = list((fixture / 'inputs/songs').rglob('*.mp3'))
        wavs = list(outputs.glob('*.wav'))
        if len(wavs) != len(songs) or not songs:
            problems.append('missing WAV outputs')
        if script != 'file-mod-1.sh' and not list(outputs.glob('*.tar*')):
            problems.append('missing archive output')
    if name == 'bio':
        bams = list(outputs.glob('*.bam'))
        if not bams:
            problems.append('missing BAM output')
        for bam in bams:
            checked = subprocess.run(['samtools', 'quickcheck', str(bam)], capture_output=True, timeout=30)
            if checked.returncode or not bam.with_suffix(bam.suffix + '.bai').is_file():
                problems.append(f'invalid/unindexed BAM: {bam.name}')
        if script == 'bio-6.sh':
            plot = outputs / 'reads_per_sample.png'
            if not plot.is_file() or plot.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                problems.append('missing bio coverage plot')
            else:
                from PIL import Image
                with Image.open(plot) as image:
                    image.verify()
    if name == 'dpt':
        database = outputs / 'db.study.txt'
        try:
            rows = database.read_text().splitlines()
            if not rows or any(not row.startswith('g: ') for row in rows):
                problems.append('invalid/empty DPT classification database')
        except OSError:
            problems.append('missing DPT database')
        if script in ('dpt_5c.sh', 'dpt_5d.sh', 'dpt_5e.sh'):
            classification = outputs / 'classifications.study.txt'
            try:
                if not re.search(r'g:\s*\S+\s+c:\s*[0-9.eE+-]+\s+\S+', classification.read_text()):
                    problems.append('invalid formatted plotting records')
            except OSError:
                problems.append('missing formatted plotting records')
        # plot_1 and plot_2 are intentionally partial development versions.
        if script == 'dpt_5e.sh':
            image = outputs / 'classifications.study.txt.png'
            if not image.is_file() or image.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                problems.append('missing DPT plot')
            else:
                from PIL import Image
                with Image.open(image) as picture:
                    picture.verify()
    return problems


def compare(reference, observed):
    keys = ('returncode', 'stdout_sha256', 'normalized_stderr_sha256', 'outputs')
    return [f'{key} mismatch' for key in keys if reference[key] != observed[key]]
