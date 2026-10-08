#!/usr/bin/env python3
"""Linux serial process-tree supervisor; no pipe-drain or orphan waits can hang.

Run this as a dedicated process: it adopts and reaps all orphan descendants.
Results include timeout/descendant leakage even when the immediate command exits 0.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time


def children(pid):
    try:
        return [int(p) for p in Path(f"/proc/{pid}/task/{pid}/children").read_text().split()]
    except OSError:
        return []


def descendants(pid):
    result, pending = [], children(pid)
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(children(child))
    return list(reversed(result))


def signal_owned(sig):
    for pid in descendants(os.getpid()):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            # Some owned sandbox helpers run through noninteractive sudo.
            subprocess.run(["sudo", "-n", "kill", f"-{sig.value}", "--", str(pid)],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=2, check=False)


def reap(exclude=None):
    for child in children(os.getpid()):
        if child == exclude:
            continue
        try:
            os.waitpid(child, os.WNOHANG)
        except ChildProcessError:
            pass


def run(argv, *, timeout=30, cwd=None, env=None, stdin=b"", grace=5):
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "cannot become child subreaper")
    if children(os.getpid()):
        raise RuntimeError("bounded runner must not own unrelated child processes")
    started = time.monotonic()
    timed_out = leaked = False
    diagnostics = []
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        inp.write(stdin)
        inp.seek(0)
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=inp, stdout=out,
                                stderr=err, start_new_session=True)
        finished = threading.Event()
        finish_time = []

        def wait_child():
            proc.wait()
            finish_time.append(time.monotonic())
            finished.set()

        threading.Thread(target=wait_child, daemon=True).start()
        heartbeat = started + 30
        try:
            while not finished.is_set():
                now = time.monotonic()
                if now >= started + timeout:
                    timed_out = True
                    break
                if now >= heartbeat:
                    print(f"[bounded] running {now-started:.0f}s: {argv[0]}", flush=True)
                    heartbeat = now + 30
                finished.wait(min(.1, max(0, started + timeout - now)))
            elapsed = (finish_time[0] if finish_time else time.monotonic()) - started
            leaked = finished.is_set() and bool(children(os.getpid()))
        finally:
            if timed_out or leaked or proc.poll() is None:
                for pid in descendants(os.getpid()):
                    try:
                        diagnostics.append({"pid": pid, "status": Path(f"/proc/{pid}/status").read_text(),
                                            "wait": Path(f"/proc/{pid}/wchan").read_text()})
                    except OSError:
                        pass
                signal_owned(signal.SIGTERM)
                end = time.monotonic() + grace
                while time.monotonic() < end and children(os.getpid()):
                    proc.poll()
                    reap(exclude=proc.pid)
                    time.sleep(.02)
                end = time.monotonic() + 2
                while children(os.getpid()) and time.monotonic() < end:
                    signal_owned(signal.SIGKILL)
                    proc.poll()
                    reap(exclude=proc.pid)
                    time.sleep(.02)
            proc.poll()
            reap(exclude=proc.pid)
        out.seek(0)
        err.seek(0)
        stdout, stderr = out.read(), err.read()
        return {"argv": argv, "returncode": proc.returncode, "elapsed_sec": elapsed,
                "timeout": timed_out, "leaked_descendants": leaked,
                "remaining_descendants": children(os.getpid()), "diagnostics": diagnostics,
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("command is required")
    result = run(command, timeout=args.timeout)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("returncode", "elapsed_sec", "timeout", "leaked_descendants", "remaining_descendants")}))
    raise SystemExit(1 if result["timeout"] or result["leaked_descendants"] or result["remaining_descendants"] else result["returncode"])


if __name__ == "__main__":
    main()
