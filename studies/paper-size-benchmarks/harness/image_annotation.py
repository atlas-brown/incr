"""Explicit opt-in live API workload preparation and limited output validation."""
from pathlib import PurePosixPath
import shutil
import zipfile

from common import WORK, file_hash


def prepare_inputs(profile, inputs, reserve, provenance):
    from prepare import SOURCE, download, check_space
    images = inputs / 'images'
    images.mkdir()
    if profile == 'min':
        for path in sorted((SOURCE / 'image-annotation/min_inputs').glob('*.jpg')):
            shutil.copy2(path, images / path.name)
        provenance['recipes'].append({'selection': 'all five versioned minimum images'})
    elif profile == 'paper':
        url = 'https://atlas.cs.brown.edu/data/small/jpg.zip'
        archive = download(url, WORK / 'downloads/image-small.zip', reserve)
        with zipfile.ZipFile(archive) as source:
            members = sorted(m for m in source.namelist() if m.lower().endswith('.jpg'))[:10]
            if len(members) != 10:
                raise ValueError('Image paper recipe requires ten JPEGs')
            for member in members:
                name = PurePosixPath(member).name
                target = images / name
                if target.exists():
                    raise ValueError('Duplicate image basename')
                info = source.getinfo(member)
                if info.file_size > 64 * 1024**2:
                    raise ValueError('Image exceeds preparation limit')
                check_space(reserve, info.file_size)
                with source.open(member) as inp, target.open('wb') as out:
                    shutil.copyfileobj(inp, out)
        provenance['recipes'].append({'url': url, 'members': members,
                                      'selection': 'ten lexically first JPEG members; historical small recipe'})
    else:
        raise ValueError('Image annotation supports min or paper')


def comparison_payload(outputs):
    # Preserve the exact manifest in evidence; compare only source payloads.
    # Fresh model calls can change generated titles and accumulate extra names.
    return sorted({entry['content'] for entry in outputs.values()
                   if entry['kind'] == 'file'})


def independent_checks(fixture, record, stderr):
    problems = []
    expected = {file_hash(p) for p in (fixture / 'inputs/images').glob('*.jpg')}
    files = list((fixture / 'outputs').rglob('*'))
    if not expected:
        problems.append('no input images')
    if any(p.is_symlink() or not p.is_file() or p.suffix != '.jpg' for p in files):
        problems.append('unexpected image output type or extension')
    actual = {file_hash(p) for p in files if p.is_file() and not p.is_symlink()}
    if actual != expected:
        problems.append('output image contents do not preserve every input')
    if any(p.name in ('.jpg', '.study.jpg') for p in files):
        problems.append('empty model-generated title')
    if stderr['bytes'] or record['stdout_bytes']:
        problems.append('unexpected API/client diagnostic or shell output')
    return problems
