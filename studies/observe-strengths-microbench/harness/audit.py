"""Independently audit complete paired measurements and write readable comparisons."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import tarfile
import tempfile
from pathlib import PurePosixPath

from workloads import SCENARIOS, PHASES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root):
    config = json.loads((root / "configuration.json").read_text())
    status = json.loads((root / "status.json").read_text())
    if status["state"] != "complete":
        raise RuntimeError("Run is not complete")
    provenance = json.loads((root / "provenance.json").read_text())
    if provenance["annotations"] or config["diagnostic"]:
        raise RuntimeError("Final audit requires unannotated, unprofiled measurements")
    modes = (
        ("bash", "original", "observe", "sandbox")
        if config["sandbox"]
        else ("bash", "original", "observe")
    )
    expected = {
        (s, z, r, m, p)
        for s in config["only"].split(",")
        for z in config["scales"].split(",")
        for r in range(config["repetitions"])
        for m in modes
        for p in PHASES
    }
    samples = {}
    instrumentation_warnings = []
    for path in root.glob("samples/*/*/*/*/*.json"):
        value = json.loads(path.read_text())
        key = tuple(
            value[k] for k in ("scenario", "scale", "repetition", "mode", "phase")
        )
        if key in samples or key not in expected:
            raise RuntimeError("Duplicate or unexpected measurement: " + str(path))
        if (
            not value["valid"]
            or value["returncode"] != 0
            or value["failure"]
            or value["remaining_descendants"]
            or not value["inputs_unchanged"]
            or not math.isfinite(value["elapsed_sec"])
            or value["elapsed_sec"] <= 0
        ):
            raise RuntimeError("Invalid sample: " + str(path))
        if (
            value["mode"] != "bash"
            and value["scenario"] != "builtin-control"
            and value["phase"] == "cold"
            and value["cache_entries"] < 1
        ):
            instrumentation_warnings.append(str(path.relative_to(root)))
        capture = path.parent / (value["phase"] + "-capture")
        for stream in ("stdout", "stderr"):
            if digest(capture / stream) != value[stream + "_sha256"]:
                raise RuntimeError("Capture changed: " + str(path))
        samples[key] = value
    if set(samples) != expected:
        raise RuntimeError(f"Coverage mismatch: {len(samples)}/{len(expected)}")
    for key, value in samples.items():
        reference = samples[key[:3] + ("bash", key[-1])]
        for field in ("stdout_sha256", "stderr_sha256", "returncode", "outputs"):
            if value[field] != reference[field]:
                raise RuntimeError("Native reference mismatch: " + str(key))
    comparisons = []
    lines = [
        "# Synthetic strengths results",
        "",
        "Median complete development episode seconds (six phases), with three independent paired repetitions. "
        "Cold, unchanged and edited phases are also retained separately. This is a deliberately synthetic strengths study, not a representative application sample.",
        "",
        "| Scenario | Scale | Bash | Original Incr | Observe | Original / Observe |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for scenario in config["only"].split(","):
        for scale in config["scales"].split(","):
            record = {"scenario": scenario, "scale": scale, "modes": {}}
            for mode in modes:
                episodes = []
                for rep in range(config["repetitions"]):
                    seq = {p: samples[scenario, scale, rep, mode, p] for p in PHASES}
                    episodes.append(
                        {
                            "repetition": rep,
                            "total_sec": sum(x["elapsed_sec"] for x in seq.values()),
                            "cold_sec": seq["cold"]["elapsed_sec"],
                            "unchanged_sec": seq["unchanged"]["elapsed_sec"],
                            "edited_sec": sum(
                                seq[p]["elapsed_sec"] for p in PHASES[2:]
                            ),
                        }
                    )
                record["modes"][mode] = {"episodes": episodes}
                for field in ("total_sec", "cold_sec", "unchanged_sec", "edited_sec"):
                    values = [e[field] for e in episodes]
                    record["modes"][mode][field] = {
                        "median": statistics.median(values),
                        "min": min(values),
                        "max": max(values),
                        "samples": values,
                    }
            medians = {m: record["modes"][m]["total_sec"]["median"] for m in modes}
            record["paired_total_speedups"] = [
                record["modes"]["original"]["episodes"][i]["total_sec"]
                / record["modes"]["observe"]["episodes"][i]["total_sec"]
                for i in range(config["repetitions"])
            ]
            lines.append(
                f"| {scenario} | {scale} | {medians['bash']:.3f} | {medians['original']:.3f} | {medians['observe']:.3f} | {medians['original'] / medians['observe']:.2f}× |"
            )
            comparisons.append(record)
    lines += [
        "",
        "All samples passed native stdout/stderr/status and filesystem validation. "
        "Ratios of medians and individual paired ratios are descriptive; three repetitions do not establish significance for small differences. "
        "Bash-only loops and CPU-heavy work are controls. Dummy commands are explicit overhead stresses. "
        "An episode advantage does not imply every unchanged or edited phase wins.",
        "",
        "Resource fields are GNU time user seconds, system seconds, maximum-process RSS KiB, filesystem input/output blocks, voluntary and involuntary context switches. "
        "Cache activity witnesses count new/rewritten/retained metadata entries, not exact logical hit rates.",
    ]
    report = {
        "valid": not instrumentation_warnings,
        "output_validation_passed": True,
        "instrumentation_warnings": instrumentation_warnings,
        "expected": len(expected),
        "verified": len(samples),
        "repetitions": config["repetitions"],
        "comparisons": comparisons,
    }
    (root / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    if instrumentation_warnings:
        lines[1:1] = ["", "**Performance qualification pending:** zero cache entries in some cold engine samples. All raw-output, native-reference and coverage checks passed, but the instrumentation gate did not. Inspect audit.json; do not certify these timings as fully audited speedups."]
    (root / "REPORT.md").write_text("\n".join(lines) + "\n")
    if instrumentation_warnings:
        raise RuntimeError(f"Output validation passed; {len(instrumentation_warnings)} cold samples require instrumentation review")
    print(json.dumps({"verified": len(samples), "valid": True}))


def audit_saved(root):
    archive = root / "raw-evidence.tar.gz"
    if not archive.exists():
        return audit(root)
    catalog = json.loads((root / "raw-catalog.json").read_text())
    if digest(archive) != catalog["archive_sha256"]:
        raise RuntimeError("Evidence archive changed")
    with tempfile.TemporaryDirectory(prefix="microbench-audit-") as directory:
        target = Path(directory)
        restored = {}
        with tarfile.open(archive, "r:gz") as source:
            for member in source:
                name = PurePosixPath(member.name)
                if (
                    not member.isfile()
                    or name.is_absolute()
                    or ".." in name.parts
                    or member.name in restored
                ):
                    raise RuntimeError("Unsafe or duplicate archive member")
                path = target / member.name
                path.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as data, path.open("wb") as output:
                    import shutil

                    shutil.copyfileobj(data, output)
                restored[member.name] = digest(path)
        if restored != catalog["members"]:
            raise RuntimeError("Archive member mismatch")
        audit(target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    if args.require_full:
        config = json.loads((args.run / "configuration.json").read_text())
        if (
            set(config["only"].split(",")) != set(SCENARIOS)
            or set(config["scales"].split(",")) != {"small", "medium", "large"}
            or config["repetitions"] != 3
            or config["diagnostic"]
            or config["sandbox"]
        ):
            raise RuntimeError(
                "Final report requires all scenarios/scales, three repetitions and unprofiled three-mode execution"
            )
    audit_saved(args.run)
