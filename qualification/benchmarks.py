#!/usr/bin/env python3
"""Isolated minimum-input differential benchmark driver. No global cleanup."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile

from bounded import run
from build_snapshot import snapshot

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/benchmarks"
WORK = ROOT / "qualification/.work/benchmarks"
MAIN = ROOT.parent / "incr-main-qualification"
NAMES = ["beginner", "bio", "covid", "file-mod", "nginx-analysis", "nlp-ngrams",
         "nlp-uppercase", "poet", "spell", "unixfun", "weather", "word-freq", "dpt", "web-search"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical_file(path):
    data = path.read_bytes()
    # Encryption salts, tar timestamps and gzip timestamps are deliberately
    # nondeterministic. Compare decrypted/decompressed payloads, not ciphertext.
    if path.suffix == ".enc":
        data = subprocess.check_output(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                                        "-iter", "20000", "-k", "key", "-in", str(path)], timeout=10)
    if data.startswith(b"\x1f\x8b"):
        data = gzip.decompress(data)
    if ".tar" in path.name:
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            members = []
            for member in archive.getmembers():
                stream = archive.extractfile(member) if member.isfile() else None
                payload = stream.read() if stream else b""
                if member.name.endswith(".gz"):
                    payload = gzip.decompress(payload)
                members.append((member.name, member.mode, member.type.decode(), member.linkname, digest(payload)))
            return digest(json.dumps(sorted(members)).encode())
    return digest(data)


def manifest(directory):
    result = {}
    inodes = {}
    for path in sorted(directory.rglob("*")):
        rel = str(path.relative_to(directory))
        if rel.startswith("scripts/") or rel == "scripts":
            continue
        metadata = path.lstat()
        entry = {"mode": stat.S_IMODE(metadata.st_mode)}
        if path.is_symlink():
            entry.update(kind="symlink", target=os.readlink(path))
        elif path.is_dir():
            entry.update(kind="directory")
        elif path.is_file():
            inode = (metadata.st_dev, metadata.st_ino)
            entry.update(kind="file", content=canonical_file(path))
            if metadata.st_nlink > 1:
                entry["hardlink"] = inodes.setdefault(inode, rel)
        else:
            entry.update(kind="special")
        result[rel] = entry
    return result


def environment(name, directory):
    inp, out = directory / "inputs", directory / "outputs"
    env = dict(os.environ, LC_ALL="C", PYTHONDONTWRITEBYTECODE="1", RUN_SIZE="min",
               mode="qualification", MODE="qualification", BENCHMARK_DIR=str(directory),
               OUTPUT_DIR=str(out), OUT=str(out), TMPDIR=str(directory / "tmp"),
               OMP_NUM_THREADS="8" if name == "dpt" else "2", TF_NUM_INTRAOP_THREADS="2", TF_NUM_INTEROP_THREADS="2",
               MPLBACKEND="Agg", MPLCONFIGDIR=str(directory / "tmp/matplotlib"))
    venv = ROOT / "qualification/.venv/bin"
    env["PATH"] = str(ROOT / "qualification/.work/node-v22.20.0-linux-x64/bin") + os.pathsep + str(venv) + os.pathsep + env["PATH"]
    values = {
        "beginner": {"IN": inp / "nginx-logs_min/log0"},
        "bio": {"IN": inp / "bio-min", "IN_NAME": inp / "bio-min/input_min.txt"},
        "covid": {"INPUT": inp / "in_min.csv"},
        "file-mod": {"IN": inp / "songs.min"},
        "nginx-analysis": {"INPUT": inp / "nginx-logs_min"},
        "nlp-ngrams": {"IN": inp / "pg-min", "ENTRIES": "1"},
        "nlp-uppercase": {"IN": inp / "pg-min", "ENTRIES": "1"},
        "poet": {"IN": inp / "pg-min"}, "spell": {"IN": inp / "pg-min"},
        "unixfun": {"INPUT": inp / "4.min.txt"},
        "weather": {"INPUT": inp / "temperatures.min.txt", "input_file": inp / "temperatures.min.txt",
                    "statistics_dir": out / "statistics.min", "scripts_dir": directory / "scripts"},
        "web-search": {"IN": inp, "WIKI": inp / "articles_min", "INDEX_FILE": inp / "index_min.txt", "TEST_BASE": directory},
        "word-freq": {"INPUT": inp / "10M.txt"}, "dpt": {"IMG_DIR": inp / "dpt.min"},
    }
    env.update({k: str(v) for k, v in values[name].items()})
    return env


def prepare(name, results=None):
    fixture = WORK / name / "fixture"
    if fixture.exists():
        shutil.rmtree(fixture)
    shutil.copytree(SOURCE / name, fixture, ignore=shutil.ignore_patterns(
        "inputs", "outputs", "cache", "node_modules", "*.incr_orig", "incr_script_*", "__pycache__"))
    shutil.copytree(SOURCE / name / "inputs", fixture / "inputs", ignore=shutil.ignore_patterns("models", "*.zip", "*.tar.gz"))
    if name == "web-search":
        (fixture / "scripts/node_modules").symlink_to(SOURCE / name / "scripts/node_modules", target_is_directory=True)
    if name == "dpt":
        (fixture / "inputs/models").symlink_to(SOURCE / name / "inputs/models", target_is_directory=True)
    if name == "bio" and (fixture / "Gene_locs.txt").exists():
        shutil.copy2(fixture / "Gene_locs.txt", fixture / "scripts/Gene_locs.txt")
    (fixture / "outputs").mkdir()
    (fixture / "tmp").mkdir()
    if name == "weather":
        (fixture / "outputs/statistics.min").mkdir()
        weather = fixture / "inputs/tuft_weather.min.txt"
        rows = weather.read_text().splitlines()
        first = rows[0].split('\t')
        weather.write_text('\n'.join(row for row in rows
            if (row.split('\t')[2], row.split('\t')[5]) == (first[2], first[5])) + '\n')
    if name == "web-search":
        index = fixture / "inputs/index_min.txt"
        index.write_text(index.read_text().splitlines()[0] + '\nstop\n')
    if name in ("weather", "dpt"):
        # Matplotlib discovers fonts in process-dependent order. Treat its
        # generated library cache as a fixed setup input, shared by every mode.
        setup = run([str(ROOT / "qualification/.venv/bin/python"), "-c", "import matplotlib.font_manager"],
                    cwd=fixture, env=environment(name, fixture), timeout=10)
        if results is not None:
            (results / f"{name}.font-cache-setup.json").write_text(json.dumps(setup, indent=2) + "\n")
        if setup["returncode"] != 0 or setup["timeout"] or setup["leaked_descendants"] or setup["remaining_descendants"]:
            raise RuntimeError("Matplotlib fixture setup failed; see setup record")
    return fixture


def stderr_key(text, name):
    if name == "dpt":
        # Abseil prefixes contain wall-clock timestamps and process IDs.
        text = re.sub(r"(?m)^([IWEF]\d{4}) \d{2}:\d{2}:\d+\.\d+\s+\d+ ", r"\1 <time> <pid> ", text)
    if name == "file-mod":
        text = re.sub(r"0x[0-9a-f]+", "<address>", text)
        text = re.sub(r"(?:size|frame)=.*?(?:\r|\n|$)", "", text)
    return text


def restore_fixture(source, destination):
    """Restore effects while retaining unchanged inputs and their inode/ctime."""
    if source.is_symlink():
        if destination.is_symlink() and os.readlink(destination) == os.readlink(source):
            return
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink(missing_ok=True)
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        if destination.is_symlink() or destination.exists() and not destination.is_dir():
            destination.unlink()
        destination.mkdir(exist_ok=True)
        source_names = {p.name for p in source.iterdir()}
        for extra in destination.iterdir():
            if extra.name not in source_names:
                if extra.is_dir() and not extra.is_symlink():
                    shutil.rmtree(extra)
                else:
                    extra.unlink()
        for child in source.iterdir():
            restore_fixture(child, destination / child.name)
        old, new = source.stat(), destination.stat()
        if (old.st_mode, old.st_mtime_ns) != (new.st_mode, new.st_mtime_ns):
            shutil.copystat(source, destination)
    else:
        if destination.is_symlink() or destination.exists() and not destination.is_file():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        same = destination.is_file() and source.stat().st_size == destination.stat().st_size
        if same:
            import filecmp
            same = filecmp.cmp(source, destination, shallow=False)
            filecmp.clear_cache()
        if not same:
            shutil.copy2(source, destination)
        else:
            old, new = source.stat(), destination.stat()
            if (old.st_mode, old.st_mtime_ns) != (new.st_mode, new.st_mtime_ns):
                shutil.copystat(source, destination)


def execute(name, script, mode, repetition, phase, fixture, results, timeout=None):
    directory = WORK / name / "run"
    if phase == "warm" and directory.exists():
        restore_fixture(fixture, directory)
    else:
        if directory.exists():
            shutil.rmtree(directory)
        shutil.copytree(fixture, directory, symlinks=True)
    env = environment(name, directory)
    if name == "weather" and script.startswith("tuft-weather"):
        env["input_file"] = str(directory / "inputs/tuft_weather.min.txt")
        env["plot_dir"] = str(directory / "outputs/plots.min")
    cache = WORK / name / "caches" / script / mode / str(repetition)
    if phase == "cold" and cache.exists():
        shutil.rmtree(cache)
    env["INCR_TOP"] = str(CANDIDATE)
    env["INCR_SYS_PATH"] = str(CANDIDATE / "target/release/incr")
    env["INCR_TRY_PATH"] = str(CANDIDATE / "src/scripts/try.sh")
    env["INCR_OBSERVE_PATH"] = str(CANDIDATE.parent / "observe/target/release/observe")
    env["INCR_PYTHON"] = str(ROOT / "qualification/.venv/bin/python")
    env["INCR_CACHE_DIR"] = str(cache)
    env["INCR_OBSERVE"] = "1" if mode == "observe" else "0"
    if mode == "bash":
        command = ["bash", str(directory / "scripts" / script)]
    elif mode == "main":
        env["INCR_TOP"] = str(MAIN)
        env["INCR_SYS_PATH"] = str(MAIN / "target/release/incr")
        env["INCR_TRY_PATH"] = str(MAIN / "src/scripts/try.sh")
        command = ["bash", str(MAIN / "src/incr.sh"), str(directory / "scripts" / script)]
    else:
        command = ["bash", str(CANDIDATE / "incr.sh"), str(directory / "scripts" / script)]
    cache_before = {str(p.relative_to(cache)): p.stat().st_mtime_ns for p in cache.rglob("data.incr")}
    before = manifest(directory)
    record = run(command, cwd=directory, env=env, timeout=timeout or (900 if name == "dpt" else 300))
    record["candidate_snapshot"] = str(CANDIDATE)
    record["runtime_settings"] = {key: env[key] for key in
        ("LC_ALL", "RUN_SIZE", "OMP_NUM_THREADS", "TF_NUM_INTRAOP_THREADS", "TF_NUM_INTEROP_THREADS", "MPLBACKEND")}
    record["fixture_profile"] = "one city-year" if name == "weather" and script.startswith("tuft") else "one real HTML page plus stop sentinel" if name == "web-search" else "supplied --min"
    record.update(benchmark=name, script=script, mode=mode, repetition=repetition, phase=phase)
    try:
        if name == "dpt":
            database = directory / "outputs/db.qualification.txt"
            rows = database.read_text().splitlines()
            if not rows or any(re.match(r"^g: \S+", row) is None for row in rows):
                raise ValueError("DPT produced no valid classification records")
            if script == "dpt_5e.sh":
                plot = directory / "outputs/classifications.qualification.txt.png"
                if not plot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("DPT did not produce a PNG plot")
        after = manifest(directory)
        record["effects"] = {p: after.get(p) for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)}
        record["small_text_outputs"] = {p: (directory / p).read_text(errors="surrogateescape")
            for p in record["effects"] if p.startswith("outputs/") and Path(p).suffix in (".txt", ".csv")
            and (directory / p).is_file() and (directory / p).stat().st_size < 65536}
    except Exception as error:
        record["validation_error"] = str(error)
    cache_after = {str(p.relative_to(cache)): p.stat().st_mtime_ns for p in cache.rglob("data.incr")}
    record["cache_entries_retained"] = sum(cache_before.get(p) == m for p, m in cache_after.items())
    record["cache_entries_written"] = sum(cache_before.get(p) != m for p, m in cache_after.items())
    record["cache_bytes"] = sum(p.stat().st_size for p in cache.rglob("*") if p.is_file()) if cache.exists() else 0
    path = results / name / f"{script}.{mode}.{repetition}.{phase}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    global CANDIDATE
    CANDIDATE = snapshot()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default=",".join(NAMES))
    parser.add_argument("--scripts", default="")
    parser.add_argument("--modes", default="bash,main,try,observe")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--append", action="store_true", help="append new, disjoint cases to saved results")
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    summary_path = args.results / "summary.json"
    summary = json.loads(summary_path.read_text()) if args.append and summary_path.exists() else []
    existing_cases = {(r["benchmark"], r["script"]) for r in summary}
    for name in args.only.split(","):
        fixture = prepare(name, args.results)
        scripts = args.scripts.split(",") if args.scripts else [p.name for p in sorted((fixture / "scripts").glob("*.sh"))]
        scripts = [s for s in scripts if s != "dpt_reference.sh" and (name != "web-search" or s == "engine.sh")]
        for script in scripts:
            if (name, script) in existing_cases:
                parser.error(f"refusing to overwrite existing measurements: {name}/{script}")
            if not (fixture / "scripts" / script).is_file():
                parser.error(f"missing script: {name}/{script}")
            reference = None
            modes = args.modes.split(",")
            if modes[0] != "bash":
                parser.error("bash must be the first reference mode")
            for repetition in range(args.repetitions):
                order = modes if repetition == 0 else modes[repetition % len(modes):] + modes[:repetition % len(modes)]
                for mode in order:
                    for phase in ("cold", "warm"):
                        print(f"RUN {name}/{script} {mode} {repetition} {phase}", flush=True)
                        r = execute(name, script, mode, repetition, phase, fixture, args.results, args.timeout)
                        key = (r["returncode"], r["stdout_sha256"], stderr_key(r["stderr"], name), r.get("effects"))
                        if reference is None:
                            reference = key
                        valid = (key == reference and not r["timeout"] and not r["leaked_descendants"]
                                 and not r["remaining_descendants"] and "validation_error" not in r)
                        valid = valid and r["returncode"] == 0
                        valid = valid and not re.search(r"No such file or directory|Traceback \(most recent|command not found|\[E::|failed to open|Error:", r["stderr"], re.I)
                        summary.append({k: r[k] for k in ("benchmark", "script", "mode", "repetition", "phase", "elapsed_sec", "returncode", "timeout", "cache_bytes")})
                        summary[-1]["valid"] = valid
                        print(f"{'PASS' if valid else 'FAIL'} {r['elapsed_sec']:.3f}s rc={r['returncode']}", flush=True)
                        (args.results / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (args.results / "timings.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary)
    raise SystemExit(0 if all(r["valid"] for r in summary) else 1)


if __name__ == "__main__":
    main()
