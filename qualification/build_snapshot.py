"""Freeze candidate executables and shell helpers for a qualification run."""
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def snapshot():
    sources = [(ROOT / 'incr.sh', Path('incr/incr.sh')),
               (ROOT / 'target/release/incr', Path('incr/target/release/incr')),
               (ROOT.parent / 'observe/target/release/observe', Path('observe/target/release/observe'))]
    sources.extend((p, Path('incr') / p.relative_to(ROOT))
                   for p in sorted((ROOT / 'src/scripts').rglob('*'))
                   if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'))
    digest = hashlib.sha256()
    for source, relative in sources:
        digest.update(str(relative).encode() + b'\0' + source.read_bytes())
    destination = ROOT / 'qualification/.work/builds' / digest.hexdigest()[:20]
    marker = destination / 'complete'
    if not marker.exists():
        for source, relative in sources:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        marker.write_text(digest.hexdigest() + '\n')
    return destination / 'incr'
