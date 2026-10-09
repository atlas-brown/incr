#!/usr/bin/env python3
"""Run all upstream Bash groups cold/warm against native Bash and Incr Observe."""
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[1]
sys.path.insert(0, str(ROOT / "qualification"))
from bounded import run
from build_snapshot import snapshot
from compare import compare, line_counts

LOCALES = (
    ("zh_HK.big5hkscs", "zh_HK", "BIG5-HKSCS"),
    ("fr_FR.ISO8859-1", "fr_FR", "ISO-8859-1"),
    ("ja_JP.SJIS", "ja_JP", "SHIFT_JIS"),
    ("zh_TW.BIG5", "zh_TW", "BIG5"),
    ("de_DE.UTF-8", "de_DE", "UTF-8"),
)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2) + "\n"
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(text.encode(), mtime=0))
    else:
        path.write_text(text)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    return {
        str(p.relative_to(directory)): {
            "sha256": sha(p),
            "size": p.stat().st_size,
            "mtime_ns": p.stat().st_mtime_ns,
        }
        for p in sorted(directory.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def log(output, message):
    print(message, flush=True)
    with (output / "progress.md").open("a") as stream:
        stream.write(f"- {message}\n")


def checked(command, output, name, timeout=60, cwd=ROOT):
    result = run([str(x) for x in command], timeout=timeout, cwd=cwd)
    write_json(output / "setup" / f"{name}.json.gz", result)
    if result["returncode"] or result["timeout"] or result["remaining_descendants"]:
        raise RuntimeError(f"{name} failed; see setup/{name}.json.gz")
    return result


def prepare(args, work, output):
    build = args.bash_build.resolve()
    python = args.python.absolute()
    required = [
        build / "bash",
        build / "recho",
        build / "zecho",
        build / "printenv",
        build / "xcase",
        python,
    ]
    if any(not p.is_file() for p in required):
        raise RuntimeError(
            "Missing Bash build/helpers or parser Python. See README setup instructions."
        )
    checked(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            STUDY / "harness",
            "-p",
            "test_*.py",
            "-v",
        ],
        output,
        "harness-tests",
    )
    checked([python, "-c", "import libbash, libdash, shasta"], output, "parser-imports")
    for name, repo in [("incr", ROOT), ("observe", ROOT.parent / "observe")]:
        checked(["cargo", "build", "--release", "--locked"], output, f"build-{name}", 180, repo)
    candidate = snapshot()
    help_result = checked(
        ["env", "-u", "INCR_EFFECT_POLICY", candidate / "target/release/incr", "--help"],
        output,
        "default-policy",
    )
    if "[default: final]" not in help_result["stdout"]:
        raise RuntimeError("This study requires final as the binary's default effect policy")
    provenance = json.loads((STUDY / "corpus-provenance.json").read_text())
    mismatches = [
        r["path"]
        for r in provenance["files"]
        if not (build / "tests" / r["path"]).is_file()
        or sha(build / "tests" / r["path"]) != r["sha256"]
    ]
    if mismatches:
        raise RuntimeError(f"Bash test source differs from verified official release: {mismatches}")
    locales = work / "locales"
    shutil.copytree("/usr/lib/locale", locales)
    for name, source, encoding in LOCALES:
        result = run(
            ["localedef", "--no-archive", "-c", "-i", source, "-f", encoding, str(locales / name)],
            timeout=15,
        )
        write_json(output / "setup" / f"locale-{name}.json.gz", result)
        # localedef returns 1 for the known SHIFT_JIS ASCII-compatibility warning.
        expected_warning = (
            name == "ja_JP.SJIS"
            and result["returncode"] == 1
            and "not ASCII compatible" in result["stderr"]
        )
        if (
            result["timeout"]
            or result["remaining_descendants"]
            or not (locales / name / "LC_CTYPE").is_file()
            or (result["returncode"] and not expected_warning)
        ):
            raise RuntimeError(f"Locale setup failed: {name}")
    helpers = work / "helpers"
    helpers.mkdir()
    shutil.copy2(STUDY / "harness/capture_diff.py", helpers / "diff")
    (helpers / "diff").chmod(0o755)
    launcher = work / "bash"
    compile_launcher(launcher, work / "invocations.jsonl", build / "bash", False, output)
    checked(["sudo", "-n", "unshare", "-m", "--", "true"], output, "namespace-check")
    revisions = {}
    for name, repo in [("incr", ROOT), ("observe", ROOT.parent / "observe")]:
        revisions[name] = checked(
            ["git", "rev-parse", "HEAD"], output, f"revision-{name}", cwd=repo
        )["stdout"].strip()
    write_json(
        output / "provenance.json",
        {
            "revisions": revisions,
            "candidate_snapshot": str(candidate),
            "bash_build": str(build),
            "source_tarball_sha256": provenance["tarball_sha256"],
            "source_files_verified": len(provenance["files"]),
            "binaries": {
                str(p): sha(p)
                for p in [
                    build / "bash",
                    candidate / "target/release/incr",
                    candidate.parent / "observe/target/release/observe",
                    launcher,
                ]
            },
            "terminal": True,
            "policy": "final",
            "policy_selection": "binary default; INCR_EFFECT_POLICY unset",
            "runtime_sources": {
                str(p.relative_to(ROOT)): sha(p)
                for p in [ROOT / "src/main.rs", ROOT / "incr.sh", ROOT / "src/scripts/insert.py"]
            },
            "case_order": args.cases,
        },
    )
    return candidate, locales, helpers, launcher


def compile_launcher(launcher, log_path, target, observe, output):
    checked(
        [
            "cc",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-O2",
            "-DSTUDY_TARGET=" + json.dumps(str(target)),
            "-DSTUDY_LOG=" + json.dumps(str(log_path)),
            "-DSTUDY_OBSERVE=" + str(int(observe)),
            "-o",
            launcher,
            STUDY / "harness/launcher.c",
        ],
        output,
        "launcher-observe" if observe else "launcher-bash",
    )


def execute(args, work, output, candidate, locales, helpers, launcher, case, mode, phase):
    fixture = work / "run"
    if phase == "cold":
        compile_launcher(
            launcher,
            work / "invocations.jsonl",
            args.bash_build / "bash" if mode == "bash" else candidate / "incr.sh",
            mode == "observe",
            output,
        )
        if fixture.exists():
            shutil.rmtree(fixture)
        shutil.copytree(args.bash_build / "tests", fixture / "tests", symlinks=True)
        (fixture / "tmp").mkdir()
        (fixture / "cache").mkdir()
    capture_dir = fixture / "tmp/diff-captures"
    if capture_dir.exists():
        shutil.rmtree(capture_dir)
    invocation_log = work / "invocations.jsonl"
    invocation_log.write_text("")
    before = inventory(fixture / "cache")
    build = args.bash_build.resolve()
    env = {k: os.environ[k] for k in ("HOME", "USER", "LOGNAME") if k in os.environ}
    env.update(
        TERM="dumb",
        LC_ALL="C",
        PATH=f"{helpers}:{args.python.parent}:{build}:/usr/local/bin:/usr/bin:/bin",
        THIS_SH=str(launcher),
        BUILD_DIR=str(build),
        TMPDIR="/tmp",
        BASH_TSTOUT="/tmp/tstout",
        INCR_CACHE_DIR=str(fixture / "cache"),
        INCR_SHELL=str(build / "bash"),
        INCR_PYTHON=str(args.python.absolute()),
        INCR_TOP=str(candidate),
        INCR_OBSERVE="1" if mode == "observe" else "0",
        INCR_SYS_PATH=str(candidate / "target/release/incr"),
        INCR_TRY_PATH=str(candidate / "src/scripts/try.sh"),
        INCR_OBSERVE_PATH=str(candidate.parent / "observe/target/release/observe"),
    )
    command = [sys.executable, str(STUDY / "harness/terminal.py")]
    if case == "read":
        command.append("--stdin")
    command += [
        "sudo",
        "-n",
        "unshare",
        "-m",
        "--",
        "bash",
        "-c",
        'mount --make-rprivate / && mount --bind "$1" /tmp && '
        'mount --bind "$2" /usr/lib/locale && shift 2 && exec "$@"',
        "study",
        str(fixture / "tmp"),
        str(locales),
        "setpriv",
        "--reuid",
        str(os.getuid()),
        "--regid",
        str(os.getgid()),
        "--init-groups",
        "env",
        "-i",
        *[f"{key}={value}" for key, value in env.items()],
        str(build / "bash"),
        f"run-{case}",
    ]
    deadline = max(args.timeout, 120 if case == "jobs" else 60 if case == "exportfunc" else 0)
    result = run(command, timeout=deadline, cwd=fixture / "tests")
    after = inventory(fixture / "cache")
    result.update(
        case=case,
        mode=mode,
        phase=phase,
        deadline_sec=deadline,
        captures=[json.loads(p.read_text()) for p in sorted(capture_dir.glob("*.json"))],
        invocations=[json.loads(line) for line in invocation_log.read_text().splitlines()],
        cache_before=before,
        cache_after=after,
        cache_entries=sum(p.endswith("/data.incr") for p in after),
        retained_metadata=sum(
            p.endswith("/data.incr") and after.get(p) == value for p, value in before.items()
        ),
    )
    write_json(output / "records" / f"{case}.{mode}.{phase}.json.gz", result)
    log(
        output,
        f'{case}/{mode}/{phase}: status={result["returncode"]}, {result["elapsed_sec"]:.2f}s, '
        f'timeout={result["timeout"]}, captures={len(result["captures"])}, '
        f'entries={result["cache_entries"]}, retained metadata={result["retained_metadata"]}, '
        f'survivors={result["remaining_descendants"]}',
    )
    return result


def summarize_case(output, case, results):
    rows = []
    for phase in ("cold", "warm"):
        reference, candidate = results["bash", phase], results["observe", phase]
        row, diffs = compare(reference, candidate)
        row.update(
            reference_seconds=reference["elapsed_sec"],
            observe_seconds=candidate["elapsed_sec"],
            cache_entries=candidate["cache_entries"],
            retained_metadata=candidate["retained_metadata"],
            native_expected=[
                line_counts(c["expected"], c["actual"]) for c in reference["captures"]
            ],
            baseline_cleanup=reference["leaked_descendants"],
            observe_cleanup=candidate["leaked_descendants"],
        )
        for kind, text in diffs.items():
            if text:
                path = output / "diffs" / f"{case}.{phase}.{kind}.diff"
                path.parent.mkdir(exist_ok=True)
                path.write_text(text, errors="backslashreplace")
        rows.append(row)
    for mode in ("bash", "observe"):
        stable, diffs = compare(results[mode, "cold"], results[mode, "warm"])
        rows[1][f"{mode}_cold_warm_output_match"] = stable["output_match"]
        if diffs["normalized"]:
            path = output / "diffs" / f"{case}.{mode}.cold-warm.diff"
            path.parent.mkdir(exist_ok=True)
            path.write_text(diffs["normalized"], errors="backslashreplace")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", help="Comma-separated groups; default: all standard run-all groups"
    )
    parser.add_argument("--output", type=Path, default=STUDY / "results/latest")
    parser.add_argument("--bash-build", type=Path, default=ROOT / "qualification/.work/bash-src")
    parser.add_argument("--python", type=Path, default=ROOT / "qualification/.venv/bin/python")
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--total-timeout", type=float, default=1800)
    parser.add_argument(
        "--skip-regressions",
        action="store_true",
        help="Only Bash comparisons, for focused investigation",
    )
    args = parser.parse_args()
    args.bash_build = args.bash_build.resolve()
    # Keep the venv path: resolving its interpreter symlink would lose its environment.
    args.python = args.python.absolute()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(
            "Output directory must be empty; select a new --output to preserve prior evidence."
        )
    output.mkdir(parents=True, exist_ok=True)
    available = sorted(
        p.name[4:]
        for p in (args.bash_build / "tests").glob("run-*")
        if p.name not in ("run-all", "run-minimal", "run-gprof")
    )
    cases = args.cases.split(",") if args.cases else available
    if not cases or len(set(cases)) != len(cases) or set(cases) - set(available):
        parser.error("No cases, duplicate cases, or unknown case names")
    args.cases = cases
    started = time.monotonic()
    rows, regression_results = [], {}
    try:
        with tempfile.TemporaryDirectory(prefix=".run-", dir=STUDY) as directory:
            work = Path(directory)
            candidate, locales, helpers, launcher = prepare(args, work, output)
            for case in cases:
                if time.monotonic() - started >= args.total_timeout:
                    raise TimeoutError("Overall study deadline exceeded")
                results = {}
                for mode in ("bash", "observe"):
                    for phase in ("cold", "warm"):
                        record = execute(
                            args,
                            work,
                            output,
                            candidate,
                            locales,
                            helpers,
                            launcher,
                            case,
                            mode,
                            phase,
                        )
                        results[mode, phase] = record
                        if record["timeout"] or record["remaining_descendants"]:
                            raise RuntimeError(
                                f"{case}/{mode}/{phase} lifecycle failure; stopped incrementally"
                            )
                rows.extend(summarize_case(output, case, results))
                write_json(output / "case-results.json", rows)
                log(output, f'{case}: cold={rows[-2]["match"]}, warm={rows[-1]["match"]}')
            if not args.skip_regressions:
                for policy in ("live", "final"):
                    regression_results[policy] = checked(
                        [
                            sys.executable,
                            ROOT / "qualification/regressions.py",
                            "--effect-policy",
                            policy,
                            "-v",
                        ],
                        output,
                        f"regressions-{policy}",
                        60,
                    )
            summary = {
                "complete": len(rows) == 2 * len(cases),
                "groups": len(cases),
                "cold_matches": sum(r["match"] for r in rows if r["phase"] == "cold"),
                "warm_matches": sum(r["match"] for r in rows if r["phase"] == "warm"),
                "failures": [f'{r["case"]}/{r["phase"]}' for r in rows if not r["match"]],
                "elapsed_sec": time.monotonic() - started,
                "regressions": {
                    p: {"returncode": r["returncode"], "elapsed_sec": r["elapsed_sec"]}
                    for p, r in regression_results.items()
                },
                "scratch_cleaned": True,
            }
        write_json(output / "summary.json", summary)
        columns = [
            "case",
            "phase",
            "match",
            "exact",
            "reference_status",
            "candidate_status",
            "reference_seconds",
            "observe_seconds",
            "cache_entries",
            "retained_metadata",
            "baseline_cleanup",
            "observe_cleanup",
        ]
        with (output / "case-results.csv").open("w") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        log(output, json.dumps(summary))
        return int(bool(summary["failures"]))
    except Exception as error:
        write_json(
            output / "error.json", {"error": str(error), "elapsed_sec": time.monotonic() - started}
        )
        log(output, f"ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
