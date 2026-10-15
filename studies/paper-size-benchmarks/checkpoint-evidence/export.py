"""Export completed qualification evidence without mixing binary cohorts.

Each bundle retains the original run's raw records, configuration, source
archives, validation manifests and timing files. No measurements are performed.
"""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[3]
DESTINATION = Path(__file__).resolve().parent
PAPER = ROOT / "studies/paper-size-benchmarks/results"
PROBES = ROOT / "studies/observe-performance-regression/results"
RUNS = [
    ("final-min", PAPER / "final-cleanup-min-01", "Final binary; minimum diagnostic, one repetition"),
    ("final-128", PROBES / "final-cleanup-128-01", "Final binary; larger verification, one repetition"),
    ("final-dpt", PROBES / "final-cleanup-dpt-archive-01", "Final binary; one-image archive diagnostic"),
    ("final-supplemental", PAPER / "final-cleanup-supplemental-min-01", "Final binary; supplemental minimum, two repetitions"),
    ("paired-8", PROBES / "content-inputs-8-01", "Pre-style binary; paired synthetic diagnostic, two repetitions"),
    ("paired-32", PROBES / "content-inputs-32-01", "Pre-style binary; paired synthetic diagnostic, two repetitions"),
    ("paired-128", PROBES / "content-inputs-128-01", "Pre-style binary; paired synthetic diagnostic, two repetitions"),
    ("dpt-ten-versions", PAPER / "content-inputs-dpt-min-01", "Pre-style binary; ten-version real-model minimum"),
    ("dpt-three-images", PROBES / "general-dpt-archive-content-three-01", "Pre-style binary; three-image archive diagnostic"),
    ("large-pipeline-profile", PROBES / "general-unannotated-profile-128-01", "Cache-30 attribution only; not primary performance samples"),
    ("archive-fault", PROBES / "general-archive-content-01", "Intentional fault probe: baseline stale output retained; not performance evidence"),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tree_digest(files):
    return digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode())


def main():
    records = []
    for label, source, scope in RUNS:
        summary = json.loads((source / "summary.json").read_text())
        assert summary.get("complete", summary.get("candidate_correct", False)), source
        if (source / "provenance-check.json").exists():
            assert json.loads((source / "provenance-check.json").read_text())["valid"], source
        files = sorted(p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        assert all(not p.is_symlink() for p in files)
        hashes = {str(p.relative_to(source)): digest(p.read_bytes()) for p in files}
        destination = DESTINATION / (label + ".tar.gz")
        if not destination.exists():
            with tarfile.open(destination, "w:gz", compresslevel=6) as archive:
                for path in files:
                    archive.add(path, arcname=str(path.relative_to(source)), recursive=False)
        with tarfile.open(destination, "r:gz") as archive:
            restored = {entry.name: digest(archive.extractfile(entry).read()) for entry in archive.getmembers()}
        assert restored == hashes, destination
        records.append({"label": label, "source": str(source.relative_to(ROOT)), "scope": scope,
                        "bundle": destination.name, "bundle_sha256": digest(destination.read_bytes()),
                        "content_tree_sha256": tree_digest(hashes), "files": len(files),
                        "payload_bytes": sum(p.stat().st_size for p in files)})
        (DESTINATION / (label + "-summary.json")).write_text(json.dumps(summary, indent=2) + "\n")
    (DESTINATION / "manifest.json").write_text(json.dumps({
        "scope": "Qualification and attribution evidence only; full-size evaluation remains pending.",
        "cohorts": "Do not pool timing samples from different binary hashes or diagnostic input sizes.",
        "tree_digest": "SHA256 of compact sorted JSON mapping relative filenames to content SHA256.",
        "runs": records,
    }, indent=2) + "\n")
    print(f"Exported and verified {len(records)} independent evidence bundles.")


if __name__ == "__main__":
    main()
