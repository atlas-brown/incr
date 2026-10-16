"""Explicitly install the three real DPT models with recorded size/hash checks."""
import argparse
import shutil
import zipfile

from common import GIB, WORK, file_hash, remove_owned
from prepare import SOURCE, check_space, download
from study import lock

MODELS = {
    'model.h5': (7263856, '5f60011895c5f7ca2f2c15cfe1ba3173c3352161133be21f4d8a35e127190fa0'),
    'rdict.json': (7823, '8672144b5a859afb382bc0392c1969496d00cff978087375ddf46fecf7e8c847'),
    'sam_vit_h.pth': (2564550879, 'a7bf3b02f3ebf1267aba913ff637d9a2d5c33d3173bb679e46d9f338c26f262e'),
}


def validate(directory):
    for name, (size, digest) in MODELS.items():
        path = directory / name
        if path.stat().st_size != size or file_hash(path) != digest:
            raise RuntimeError('DPT model checksum/size mismatch: ' + str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    with lock():
        destination = SOURCE / 'dpt/inputs/models'
        if destination.exists():
            validate(destination)
            print('Existing real models verified.')
            return
        check_space(8 * GIB, 8 * GIB)
        archive = download('https://atlas.cs.brown.edu/data/models.zip',
                           WORK / 'downloads/models.zip', 8 * GIB, maximum=4 * GIB)
        pending = WORK / 'model-install'
        remove_owned(pending)
        pending.mkdir()
        with zipfile.ZipFile(archive) as source:
            for name, (size, _) in MODELS.items():
                matches = [m for m in source.infolist()
                           if m.filename.rsplit('/', 1)[-1] == name and not m.is_dir()]
                if len(matches) != 1 or matches[0].file_size != size:
                    raise RuntimeError('Unexpected DPT model archive entry: ' + name)
                # Fixed trusted output names; no archive paths are extracted.
                with source.open(matches[0]) as data, (pending / name).open('wb') as output:
                    shutil.copyfileobj(data, output, length=1024**2)
        validate(pending)
        destination.parent.mkdir(parents=True, exist_ok=True)
        pending.rename(destination)
        print('Installed and verified all three real DPT models.')


if __name__ == '__main__':
    main()
