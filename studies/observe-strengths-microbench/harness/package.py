"""Verify and compact one stopped measurement directory, retaining all raw evidence."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

KEEP = {
    "REPORT.md",
    "audit.json",
    "summary.json",
    "timings.csv",
    "configuration.json",
    "provenance.json",
    "status.json",
    "profile-audit.json",
    "phase-analysis.json",
}


def digest(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(1024**2), b""):
        value.update(block)
    return value.hexdigest()


def package(root):
    root = root.resolve()
    study = Path(__file__).resolve().parents[1]
    if root.parent != study / "measurements":
        raise RuntimeError("Only owned measurement directories can be packaged")
    lock = (study / ".work/lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status = json.loads((root / "status.json").read_text())
    if status["state"] not in ("complete", "failed", "interrupted"):
        raise RuntimeError("Refuse to package an active run")
    archive = root / "raw-evidence.tar.gz"
    if archive.exists():
        raise RuntimeError("Evidence is already packaged")
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if any(p.is_symlink() for p in files):
        raise RuntimeError("Unexpected link in measurement evidence")
    hashes = {}
    with tarfile.open(archive, "w:gz", compresslevel=6) as output:
        for p in files:
            name = str(p.relative_to(root))
            with p.open("rb") as source:
                hashes[name] = digest(source)
            output.add(p, arcname=name, recursive=False)
    restored = {}
    with tarfile.open(archive, "r:gz") as source:
        for member in source:
            if not member.isfile() or member.name in restored:
                raise RuntimeError("Unexpected archive member")
            with source.extractfile(member) as stream:
                restored[member.name] = digest(stream)
    if restored != hashes:
        raise RuntimeError("Evidence archive round-trip mismatch")
    with archive.open("rb") as source:
        archive_hash = digest(source)
    (root / "raw-catalog.json").write_text(
        json.dumps(
            {
                "verified_roundtrip": True,
                "archive_sha256": archive_hash,
                "members": hashes,
            },
            indent=2,
        )
        + "\n"
    )
    # Only verified generated copies are removed; direct comparison files remain.
    for p in list(root.iterdir()):
        if p.name in KEEP or p.name in ("raw-evidence.tar.gz", "raw-catalog.json"):
            continue
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    print(root.name, ":", len(hashes), "verified evidence files packaged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    package(parser.parse_args().run)
