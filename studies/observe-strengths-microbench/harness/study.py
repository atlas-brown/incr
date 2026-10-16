#!/usr/bin/env python3
"""Serial paired shell microbenchmarks; setup, compilation and validation untimed."""

import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tarfile
import time

from workloads import SCENARIOS, PHASES, setup, edit, program

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[1]
BASELINE = ROOT.parent / "incr-main-qualification"
WORK = STUDY / ".work"
PYTHON = ROOT / "qualification/.venv/bin/python"
sys.path.insert(0, str(ROOT / "qualification"))
from bounded import run

os.environ["INCR_BENCH_STUDY"] = str(STUDY)
sys.path.insert(0, str(ROOT / "studies/paper-size-benchmarks/harness"))
from common import supervise, remove_owned


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024**2), b""):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".pending")
    pending.write_text(json.dumps(value, indent=2) + "\n")
    pending.replace(path)


def inventory(root):
    result = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            result[rel] = {"link": os.readlink(p)}
        elif p.is_file():
            result[rel] = {
                "sha256": sha(p),
                "mode": p.stat().st_mode & 0o7777,
                "bytes": p.stat().st_size,
            }
        elif p.is_dir():
            result[rel] = {"directory": True, "mode": p.stat().st_mode & 0o7777}
    return result


def allocated(root):
    return sum(p.lstat().st_blocks * 512 for p in root.rglob("*") if not p.is_symlink())


def summarize(destination):
    rows = [
        json.loads(p.read_text()) for p in destination.glob("samples/*/*/*/*/*.json")
    ]
    output = []
    for scenario in SCENARIOS:
        for scale in ("small", "medium", "large"):
            bymode = {}
            for mode in ("bash", "original", "observe", "sandbox"):
                selected = [
                    x
                    for x in rows
                    if (x["scenario"], x["scale"], x["mode"]) == (scenario, scale, mode)
                ]
                episodes = []
                for rep in sorted({x["repetition"] for x in selected}):
                    seq = [x for x in selected if x["repetition"] == rep]
                    if len(seq) == len(PHASES) and all(x["valid"] for x in seq):
                        episodes.append(
                            {
                                "repetition": rep,
                                "total_sec": sum(x["elapsed_sec"] for x in seq),
                                "edited_sec": sum(
                                    x["elapsed_sec"]
                                    for x in seq
                                    if x["phase"] not in ("cold", "unchanged")
                                ),
                                "cold_sec": next(
                                    x["elapsed_sec"]
                                    for x in seq
                                    if x["phase"] == "cold"
                                ),
                                "unchanged_sec": next(
                                    x["elapsed_sec"]
                                    for x in seq
                                    if x["phase"] == "unchanged"
                                ),
                            }
                        )
                if episodes:
                    bymode[mode] = {
                        "complete_repetitions": len(episodes),
                        "episodes": episodes,
                        **{
                            k: statistics.median(x[k] for x in episodes)
                            for k in (
                                "total_sec",
                                "edited_sec",
                                "cold_sec",
                                "unchanged_sec",
                            )
                        },
                    }
            if bymode:
                output.append({"scenario": scenario, "scale": scale, "modes": bymode})
    save(
        destination / "summary.json",
        {
            "recorded": len(rows),
            "valid": sum(x["valid"] for x in rows),
            "comparisons": output,
        },
    )
    if rows:
        keys = [
            "scenario",
            "scale",
            "repetition",
            "mode",
            "phase",
            "count",
            "rows_per_file",
            "elapsed_sec",
            "valid",
            "returncode",
            "cache_bytes",
            "cache_entries",
            "stdout_sha256",
            "stderr_sha256",
        ]
        with (destination / "timings.csv").open("w", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=keys, extrasaction="ignore", lineterminator="\n"
            )
            w.writeheader()
            w.writerows(rows)
    return rows


def freeze(destination):
    build = WORK / "build"
    build.mkdir(exist_ok=False)
    provenance = {
        "repositories": {},
        "binaries": {},
        "annotations": False,
        "transformer": "shared current Python transformer, Bash then dash selected by complete static coverage; transformation untimed",
        "effect_policy": "final",
        "directory_access_assumption": True,
        "content_validated_inputs": False,
    }
    for name, repo, binary in [
        ("original", BASELINE, "incr"),
        ("observe", ROOT.parent / "observe", "observe"),
        ("candidate", ROOT, "incr"),
    ]:
        target = build / name
        target.mkdir()
        shutil.copy2(repo / "target/release" / binary, target / binary)
        provenance["repositories"][name] = {
            "head": subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip(),
            "diff": subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(repo),
                    "diff",
                    "HEAD",
                    "--",
                    "src",
                    "Cargo.toml",
                    "Cargo.lock",
                ],
                text=True,
            ),
        }
        provenance["binaries"][name] = {
            "path": str(target / binary),
            "sha256": sha(target / binary),
        }
        with tarfile.open(destination / (name + "-sources.tar.gz"), "w:gz") as archive:
            for part in ["src", "Cargo.toml", "Cargo.lock"]:
                archive.add(
                    repo / part,
                    arcname=part,
                    filter=lambda x: None if "__pycache__" in x.name else x,
                )
    shutil.copy2(BASELINE / "src/scripts/try.sh", build / "original/try.sh")
    subprocess.run(
        [
            "cc",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(ROOT / "studies/paper-size-benchmarks/harness/fdguard.c"),
            "-o",
            str(build / "fdguard"),
        ],
        check=True,
    )
    shutil.copytree(
        ROOT / "src/scripts",
        build / "scripts",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy2(STUDY / "PLAN.md", destination / "PLAN.md")
    shutil.copytree(STUDY / "scenarios", destination / "scenarios")
    shutil.copytree(
        STUDY / "harness",
        destination / "harness",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shared = destination / "shared-helpers"
    shared.mkdir()
    for source in [
        ROOT / "qualification/bounded.py",
        ROOT / "studies/paper-size-benchmarks/harness/common.py",
        ROOT / "studies/paper-size-benchmarks/harness/fdguard.c",
    ]:
        shutil.copy2(source, shared / source.name)
    provenance["launcher_sha256"] = sha(build / "fdguard")
    provenance["shared_helpers"] = {p.name: sha(p) for p in shared.iterdir()}
    provenance["host"] = {
        "uname": list(os.uname()),
        "cpuinfo": Path("/proc/cpuinfo").read_text(),
        "meminfo": Path("/proc/meminfo").read_text(),
    }
    save(destination / "provenance.json", provenance)
    return build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scales", default="small,medium,large")
    parser.add_argument("--only", default=",".join(SCENARIOS))
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--counts", default="4,24,128")
    parser.add_argument("--rows", default="16,128,1024")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Enable current-engine phase profiles outside final measurements",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Also compare current Incr without Observe",
    )
    args = parser.parse_args()
    if not args.run_id.replace("-", "").replace("_", "").isalnum():
        parser.error("Use a simple run ID")
    scales = args.scales.split(",")
    names = args.only.split(",")
    if not set(scales) <= {"small", "medium", "large"} or not set(names) <= set(
        SCENARIOS
    ):
        parser.error("Unknown scale/scenario")
    counts = dict(zip(("small", "medium", "large"), map(int, args.counts.split(","))))
    sizes = dict(zip(("small", "medium", "large"), map(int, args.rows.split(","))))
    if (
        len(counts) != 3
        or len(sizes) != 3
        or min(counts.values()) < 1
        or min(sizes.values()) < 1
        or args.repetitions < 1
    ):
        parser.error("Three positive counts/row sizes and repetitions required")
    WORK.mkdir(exist_ok=True)
    lock = (WORK / "lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    destination = STUDY / "measurements" / args.run_id
    destination.mkdir(parents=True, exist_ok=False)
    build = WORK / "build"
    if build.exists():
        remove_owned(build)
    build = freeze(destination)
    save(destination / "configuration.json", vars(args))
    env = dict(
        os.environ,
        PATH=str(PYTHON.parent) + ":/usr/bin:/bin",
        LC_ALL="C",
        LANG="C",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONHASHSEED="42",
        INCR_EFFECT_POLICY="final",
        INCR_ASSUME_DIRECTORY_ACCESS="true",
    )
    for key in list(env):
        if key.startswith("INCR_") and key not in (
            "INCR_EFFECT_POLICY",
            "INCR_ASSUME_DIRECTORY_ACCESS",
        ):
            del env[key]
    fixture = WORK / "fixture"
    cache = WORK / "cache"
    os.umask(0o022)
    try:
        for scenario in names:
            for scale in scales:
                count = counts[scale]
                rowcount = sizes[scale]
                if scenario == "dummy-loop":
                    count = {"small": 4, "medium": 64, "large": 256}[scale]
                if scenario == "dummy-straightline":
                    count = min(128, count)
                if scenario == "staged-artifacts":
                    count = {"small": 4, "medium": 16, "large": 64}[scale]
                for rep in range(args.repetitions):
                    references = {}
                    modes = ["bash"] + (
                        ["original", "observe"]
                        if rep % 2 == 0
                        else ["observe", "original"]
                    )
                    if args.sandbox:
                        modes.append("sandbox")
                    for mode in modes:
                        for path in [fixture, cache]:
                            if path.exists():
                                remove_owned(path)
                        fixture.mkdir()
                        cache.mkdir()
                        setup(fixture, count, rowcount)
                        for phase in PHASES:
                            if shutil.disk_usage(WORK).free < 8 * 1024**3:
                                raise RuntimeError("Disk reserve exhausted")
                            edit(fixture, scenario, phase, count, rowcount)
                            source = fixture / "workload.sh"
                            source.write_text(
                                program(scenario, phase, destination / "scenarios")
                            )
                            executable = WORK / "compiled.sh"
                            transform = None
                            if mode == "bash":
                                executable = source
                            else:
                                engine = (
                                    build / "original/incr"
                                    if mode == "original"
                                    else build / "candidate/incr"
                                )
                                required = "\n".join(
                                    source.read_text().splitlines()[1:]
                                ).count("/usr/bin/")
                                for frontend in ("bash", "dash"):
                                    argv = [
                                        str(PYTHON),
                                        str(build / "scripts/insert.py"),
                                    ]
                                    if frontend == "bash":
                                        argv += ["--bash"]
                                    argv += [
                                        "--sys-path",
                                        str(engine),
                                        "--try-path",
                                        str(
                                            build / "original/try.sh"
                                            if mode == "original"
                                            else build / "scripts/try.sh"
                                        ),
                                        "--cache-path",
                                        str(cache),
                                    ]
                                    if mode == "observe":
                                        argv += [
                                            "--observe-path",
                                            str(build / "observe/observe"),
                                        ]
                                    argv += [str(source)]
                                    transform = run(
                                        argv, timeout=30, env=env, cwd=fixture
                                    )
                                    if (
                                        not transform["returncode"]
                                        and not transform["stderr"]
                                        and transform["stdout"].count(str(engine))
                                        == required
                                    ):
                                        break
                                else:
                                    raise RuntimeError(
                                        "No supported frontend completely instruments "
                                        + scenario
                                    )
                                executable.write_text(transform["stdout"])
                            target = (
                                destination
                                / "samples"
                                / scenario
                                / scale
                                / str(rep)
                                / mode
                            )
                            target.mkdir(parents=True, exist_ok=True)
                            save(
                                target / (phase + "-transform.receipt"),
                                {
                                    "source_sha256": sha(source),
                                    "compiled_sha256": sha(executable),
                                    "instrumented": mode != "bash"
                                    and scenario != "builtin-control",
                                    "frontend": frontend
                                    if mode != "bash"
                                    else "native",
                                    "static_commands": source.read_text()
                                    .split("\n", 1)[1]
                                    .count("/usr/bin/"),
                                    "wrapped_commands": transform["stdout"].count(
                                        str(engine)
                                    )
                                    if mode != "bash"
                                    else 0,
                                },
                            )
                            profile = WORK / "profile"
                            if profile.exists():
                                remove_owned(profile)
                            measurement_env = dict(env)
                            if args.diagnostic and mode in ("observe", "sandbox"):
                                profile.mkdir()
                                measurement_env["INCR_PROFILE_DIR"] = str(profile)
                            before = {
                                k: v
                                for k, v in inventory(fixture).items()
                                if k != "outputs" and not k.startswith("outputs/")
                            }
                            entries_before = {
                                str(p.relative_to(cache)): p.stat().st_mtime_ns
                                for p in cache.rglob("data.incr")
                            }
                            state = {
                                "state": "running",
                                "scenario": scenario,
                                "scale": scale,
                                "repetition": rep,
                                "mode": mode,
                                "phase": phase,
                                "started": time.time(),
                                "pid": os.getpid(),
                            }
                            save(destination / "status.json", state)
                            print(
                                "RUN",
                                scenario,
                                scale,
                                rep,
                                mode,
                                phase,
                                count,
                                flush=True,
                            )
                            resource = target / (phase + ".resources")
                            capture = target / (phase + "-capture")
                            result = supervise(
                                [
                                    "/usr/bin/time",
                                    "-f",
                                    "%U %S %M %I %O %w %c",
                                    "-o",
                                    str(resource),
                                    str(build / "fdguard"),
                                    "/bin/bash",
                                    str(executable),
                                ],
                                timeout=args.timeout,
                                cwd=fixture,
                                env=measurement_env,
                                capture=capture,
                                reserve=8 * 1024**3,
                                budget=8 * 1024**3,
                            )
                            result["stdout"] = (capture / "stdout").read_text(
                                errors="replace"
                            )
                            result["stderr"] = (capture / "stderr").read_text(
                                errors="replace"
                            )
                            result["timeout"] = result["failure"] == "timeout"
                            result["leaked_descendants"] = (
                                result["failure"] == "surviving-descendants"
                            )
                            if args.diagnostic and mode in ("observe", "sandbox"):
                                profiles = list(profile.glob("*.json"))
                                if not profiles and scenario != "builtin-control":
                                    raise RuntimeError(
                                        "No current executor profiles: possible native bypass"
                                    )
                                shutil.move(str(profile), target / (phase + "-profile"))
                            after = {
                                k: v
                                for k, v in inventory(fixture).items()
                                if k != "outputs" and not k.startswith("outputs/")
                            }
                            output = inventory(fixture / "outputs")
                            entries_after = {
                                str(p.relative_to(cache)): p.stat().st_mtime_ns
                                for p in cache.rglob("data.incr")
                            }
                            cache_activity = {
                                "before": len(entries_before),
                                "after": len(entries_after),
                                "new": len(
                                    entries_after.keys() - entries_before.keys()
                                ),
                                "rewritten": sum(
                                    k in entries_before and entries_before[k] != v
                                    for k, v in entries_after.items()
                                ),
                                "retained": sum(
                                    k in entries_before and entries_before[k] == v
                                    for k, v in entries_after.items()
                                ),
                            }
                            observed = {
                                k: result[k]
                                for k in (
                                    "stdout_sha256",
                                    "stderr_sha256",
                                    "returncode",
                                )
                            }
                            observed["outputs"] = output
                            if mode == "bash":
                                references[phase] = observed
                            valid = (
                                observed == references[phase]
                                and before == after
                                and result["returncode"] == 0
                                and not result["timeout"]
                                and not result["leaked_descendants"]
                                and not result["remaining_descendants"]
                            )
                            result.update(
                                scenario=scenario,
                                scale=scale,
                                repetition=rep,
                                mode=mode,
                                phase=phase,
                                count=count,
                                rows_per_file=rowcount,
                                valid=valid,
                                outputs=output,
                                inputs_unchanged=before == after,
                                reference=references[phase],
                                cache_bytes=allocated(cache),
                                cache_entries=sum(1 for p in cache.rglob("data.incr")),
                                resource_raw=resource.read_text(),
                                cache_activity=cache_activity,
                            )
                            save(target / (phase + ".json"), result)
                            print(
                                "PASS" if valid else "FAIL",
                                round(result["elapsed_sec"], 4),
                                flush=True,
                            )
                            if not valid:
                                raise RuntimeError(
                                    "Native validation failed: " + str(target / phase)
                                )
                        summarize(destination)
        rows = summarize(destination)
        expected = (
            len(names)
            * len(scales)
            * args.repetitions
            * (4 if args.sandbox else 3)
            * len(PHASES)
        )
        if len(rows) != expected or not all(x["valid"] for x in rows):
            raise RuntimeError("Incomplete final matrix")
        save(
            destination / "status.json",
            {
                "state": "complete",
                "recorded": len(rows),
                "valid": len(rows),
                "expected": expected,
                "finished": time.time(),
            },
        )
    except BaseException as error:
        save(
            destination / "status.json",
            {"state": "failed", "error": repr(error), "finished": time.time()},
        )
        summarize(destination)
        raise
    finally:
        for path in [fixture, cache]:
            if path.exists():
                remove_owned(path)
        lock.close()


if __name__ == "__main__":
    main()
