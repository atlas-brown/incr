"""Preparation for non-paper workloads, using their supplied full-data recipes."""
from pathlib import Path, PurePosixPath
import gzip
import shutil
import subprocess
import sys
import tarfile

from common import GIB, WORK, file_hash


def prepare_inputs(name, profile, inputs, reserve, provenance):
    from prepare import SOURCE, BASE, check_space, download, extract_regular, member_path

    provenance['supplemental_preparation_code_sha256'] = file_hash(Path(__file__))
    if profile not in ('min', 'full'):
        raise ValueError('Supplemental workloads use min or full profiles')
    if name == 'weather-tufte':
        source = SOURCE / 'weather'
        target = inputs / 'tuft-weather.txt'
        if profile == 'min':
            original = source / 'min_inputs/tuft_weather.min.txt.gz'
            with gzip.open(original, 'rt') as stream:
                first = stream.readline().split('\t')
            with gzip.open(original, 'rt') as stream, target.open('w') as output:
                for row in stream:
                    fields = row.rstrip('\n').split('\t')
                    if (fields[2], fields[5]) == (first[2], first[5]):
                        output.write(row)
            provenance['recipes'].append({'source': str(original), 'sha256': file_hash(original),
                'selection': 'First city and first year; complete daily records',
                'city': first[5], 'year': first[2]})
        else:
            generator = source / 'scripts/generate_input.py'
            check_space(reserve, 32 * 1024**2)
            subprocess.run([sys.executable, str(generator), str(target), '--size', 'full'],
                           check=True, timeout=120)
            provenance['recipes'].append({'generator': str(generator), 'sha256': file_hash(generator),
                'arguments': ['--size', 'full'], 'seed': 42, 'python': sys.version,
                'scope': 'Supplied full recipe: all 27 cities, 30*365 days'})
        return
    if name != 'web-search':
        raise ValueError(name)
    source = SOURCE / name / 'min_inputs'
    articles = inputs / 'articles'
    index = inputs / 'index.txt'
    if profile == 'min':
        original = source / 'index_min.txt'
        first = original.read_text().splitlines()[0]
        relative = PurePosixPath(first)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe article name')
        destination = articles / str(relative)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source / 'articles_min' / str(relative), destination)
        shutil.copy2(source / 'stopwords.txt', inputs / 'stopwords.txt')
        index.write_text(first + '\nstop\n')
        provenance['recipes'].append({'source': str(original), 'sha256': file_hash(original),
            'selection': 'First real article plus supplied engine stop sentinel', 'article': first})
    else:
        downloads = WORK / 'downloads'
        url = BASE + 'wikipedia/wikipedia10g.tar.gz'
        archive_path = download(url, downloads / 'supplemental-wikipedia10g.tar.gz', reserve,
                                maximum=6*GIB)
        index_path = download(BASE + 'wikipedia/index10g.txt', downloads / 'supplemental-index10g.txt',
                              reserve, maximum=128*1024**2)
        stopwords = download(BASE + 'web-index/stopwords.txt', downloads / 'supplemental-stopwords.txt',
                             reserve, maximum=1024**2)
        seen, total = set(), 0
        with tarfile.open(archive_path, 'r|gz') as archive:
            for member in archive:
                path = member_path(member.name)
                if member.isdir():
                    continue
                if not member.isfile() or not path.parts or path.parts[0] != 'articles10g':
                    raise ValueError(f'Unexpected corpus member: {member.name}')
                relative = PurePosixPath(*path.parts[1:])
                if not relative.parts or relative in seen:
                    raise ValueError(f'Duplicate/empty article path: {member.name}')
                seen.add(relative)
                total += member.size
                if total > 12*GIB or len(seen) > 2_000_000:
                    raise ValueError('Full Wikipedia corpus exceeds preparation budget')
                extract_regular(archive, member, articles / str(relative), reserve)
        shutil.copy2(index_path, index)
        shutil.copy2(stopwords, inputs / 'stopwords.txt')
        provenance['recipes'].append({'url': url, 'archive_sha256': file_hash(archive_path),
            'index_url': BASE + 'wikipedia/index10g.txt', 'index_sha256': file_hash(index_path),
            'stopwords_url': BASE + 'web-index/stopwords.txt', 'articles': len(seen),
            'extracted_bytes': total, 'selection': 'Entire supplied full offline corpus and index'})
        from common import remove_owned
        remove_owned(archive_path)
    required = 0
    with index.open() as stream:
        for row in stream:
            name = row.rstrip('\r\n')
            if name == 'stop':
                break
            path = PurePosixPath(name)
            if not name or path.is_absolute() or '..' in path.parts or not (articles / str(path)).is_file():
                raise ValueError(f'Index names an unavailable/unsafe article: {name!r}')
            required += 1
    if not required:
        raise ValueError('Empty article index')
    provenance['indexed_articles'] = required
    if not (inputs / 'stopwords.txt').stat().st_size:
        raise ValueError('Empty stopword list')


def independent_checks(fixture, name, script):
    """Reject vacuous oracle agreement and malformed workload artifacts."""
    problems = []
    if name == 'weather-tufte':
        locations = set()
        with (fixture / 'inputs/tuft-weather.txt').open() as stream:
            for row in stream:
                fields = row.rstrip('\n').split('\t')
                locations.add((fields[5], fields[2]))
        for city in sorted({city for city, year in locations}):
            safe = city.translate(str.maketrans(' /', '__'))
            directory = fixture / 'outputs/plots/tmp' / safe
            for filename in ('formatted.txt', 'processed.txt') if script != 'tuft-weather-1.sh' else ('formatted.txt',):
                path = directory / filename
                if not path.is_file() or not path.stat().st_size:
                    problems.append(f'Missing/empty Tufte output: {safe}/{filename}')
        if script == 'tuft-weather-3.sh':
            from PIL import Image
            for city, year in sorted(locations):
                safe = city.translate(str.maketrans(' /', '__'))
                path = fixture / 'outputs/plots' / safe / f'{year}.png'
                try:
                    with Image.open(path) as picture:
                        if picture.format != 'PNG':
                            raise ValueError('Expected PNG')
                        picture.verify()
                except (OSError, ValueError):
                    problems.append(f'Missing/invalid city-year plot: {city}/{year}')
        return problems
    if name != 'web-search':
        return problems
    outputs = fixture / 'outputs'
    try:
        visited = set((outputs / 'visited.txt').read_text().splitlines())
        required = set()
        with (fixture / 'inputs/index.txt').open() as stream:
            for row in stream:
                article = row.rstrip('\r\n')
                if article == 'stop':
                    break
                required.add(article.removeprefix('./'))
        if not required or not required <= visited:
            problems.append('Article index was not fully visited')
        for article in visited:
            path = PurePosixPath(article)
            if path.is_absolute() or '..' in path.parts or not (fixture / 'inputs/articles' / str(path)).is_file():
                problems.append(f'Visited unavailable article: {article}')
        previous, count = None, 0
        with (outputs / 'global-index.txt').open('rb') as stream:
            for raw in stream:
                if previous is not None and raw < previous:
                    raise ValueError('Index is not C-locale sorted')
                previous = raw
                term, postings = raw.decode().rstrip('\n').split('|')
                tokens = postings.split()
                if not term.strip() or not tokens or len(tokens) % 2:
                    raise ValueError('Malformed index row')
                for url, frequency in zip(tokens[::2], tokens[1::2]):
                    if url not in visited or int(frequency) <= 0:
                        raise ValueError('Invalid index posting')
                count += 1
        if not count:
            problems.append('Empty search index')
    except (OSError, ValueError, UnicodeError) as error:
        problems.append(f'Invalid search artifacts: {error}')
    return problems
