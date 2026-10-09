#!/usr/bin/env python3
"""Prepare the pinned Bash build and minimal parser environment, when absent."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import urllib.request

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[1]
sys.path.insert(0, str(ROOT / "qualification"))
from bounded import run


def checked(command, timeout=180, cwd=ROOT):
    result = run([str(x) for x in command], timeout=timeout, cwd=cwd)
    print(result["stdout"], end="")
    print(result["stderr"], end="", file=sys.stderr)
    if result["returncode"] or result["timeout"] or result["remaining_descendants"]:
        raise RuntimeError(f"Prerequisite command failed: {command}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash-build", type=Path, default=ROOT / "qualification/.work/bash-src")
    parser.add_argument("--venv", type=Path, default=ROOT / "qualification/.venv")
    args = parser.parse_args()
    build = args.bash_build.resolve()
    if not (build / "bash").exists():
        if build.exists():
            raise RuntimeError(
                f"{build} exists without a Bash binary; preserve it and choose another --bash-build"
            )
        metadata = json.loads((STUDY / "corpus-provenance.json").read_text())
        payload = urllib.request.urlopen(metadata["url"], timeout=30).read()
        if hashlib.sha256(payload).hexdigest() != metadata["tarball_sha256"]:
            raise RuntimeError("Official Bash archive checksum mismatch")
        build.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="bash-setup-", dir=build.parent) as directory:
            archive = tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz")
            # Only the pinned, checksum-verified GNU release is extracted.
            archive.extractall(directory)
            source = Path(directory) / "bash-5.2.37"
            checked(["./configure", "--without-bash-malloc"], cwd=source)
            checked(["make", "-j4"], timeout=300, cwd=source)
            checked(["make", "recho", "zecho", "printenv", "xcase"], cwd=source)
            shutil.move(str(source), str(build))
    python = args.venv.absolute() / "bin/python"
    if not python.exists():
        checked([sys.executable, "-m", "venv", args.venv])
        checked(
            [python, "-m", "pip", "install", "libbash==0.1.14", "libdash==0.5.2", "shasta==0.5"],
            timeout=300,
        )
    checked([python, "-c", "import libbash, libdash, shasta"])
    checked([build / "bash", "--version"])
    print(f"Prerequisites ready: {build}; {python}")


if __name__ == "__main__":
    main()
