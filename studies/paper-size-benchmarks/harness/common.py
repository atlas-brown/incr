"""Owned workspaces, atomic evidence and bounded Linux process supervision."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import threading
import time

STUDY = Path(os.environ.get('INCR_BENCH_STUDY', str(Path(__file__).resolve().parents[1]))).resolve()
ROOT = STUDY.parents[1]
WORK = STUDY / '.work'
SCRATCH = WORK / 'runner'
GIB = 1024 ** 3


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.pending')
    with pending.open('w') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def mounts_under(path):
    prefix = str(Path(path).absolute()).rstrip('/')
    mounts = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        target = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), line.split()[4])
        if target == prefix or target.startswith(prefix + '/'):
            mounts.append(target)
    return sorted(set(mounts), key=len, reverse=True)


def remove_owned(path):
    """Never follow a root symlink or delete a mounted or non-study tree."""
    path = Path(path).absolute()
    if (path.name in ('.', '..') or path == WORK or not path.is_relative_to(WORK)
            or not path.parent.resolve().is_relative_to(WORK.resolve())):
        raise ValueError(f'Not a disposable study child: {path}')
    if path.is_symlink():
        path.unlink()
        return
    # A killed try process can leave mounts under its cache. Unmount only these.
    for mount in mounts_under(path):
        subprocess.run(['sudo', '-n', 'umount', mount], check=True, timeout=15,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if mounts_under(path):
        raise RuntimeError(f'Refusing deletion of mounted tree: {path}')
    if not path.exists():
        return
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    except PermissionError:
        # Fixed program, separately passed path. Recheck mounts inside root helper.
        program = ('import sys,shutil,pathlib; p=pathlib.Path(sys.argv[1]); '
                   'assert p.is_absolute() and not p.is_symlink(); '
                   'assert not any(l.split()[4]==str(p) or '
                   'l.split()[4].startswith(str(p)+"/") for l in '
                   'pathlib.Path("/proc/self/mountinfo").read_text().splitlines()); '
                   'shutil.rmtree(p)')
        subprocess.run(['sudo', '-n', 'python3', '-c', program, str(path)],
                       check=True, timeout=120)


def allocated_bytes(path):
    """Count allocated blocks once per inode; do not traverse symlinks/mounts."""
    seen, total = set(), 0
    mounted = set(mounts_under(path))
    for directory, names, files in os.walk(path, followlinks=False):
        names[:] = [n for n in names if str(Path(directory) / n) not in mounted]
        for name in [None, *files]:
            p = Path(directory) if name is None else Path(directory) / name
            try:
                st = p.lstat()
                key = st.st_dev, st.st_ino
                if key not in seen:
                    seen.add(key)
                    total += st.st_blocks * 512
            except (FileNotFoundError, PermissionError):
                pass
    return total


def children(pid):
    try:
        return [int(n) for n in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()]
    except OSError:
        return []


def descendants(pid):
    found, pending = set(), children(pid)
    while pending:
        child = pending.pop()
        if child not in found:
            found.add(child)
            pending.extend(children(child))
    return found


def process_state(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
    except OSError:
        return None


def reap():
    while True:
        try:
            if os.waitpid(-1, os.WNOHANG)[0] == 0:
                return
        except ChildProcessError:
            return


def signal_children(sig):
    # Child ownership excludes unrelated jobs even if a worker changed sessions.
    for pid in descendants(os.getpid()):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            subprocess.run(['sudo', '-n', 'kill', f'-{int(sig)}', '--', str(pid)],
                           timeout=5, check=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)


def supervise(argv, *, cwd, env, capture, timeout, reserve, budget, heartbeat=None):
    """Capture to disk, enforce time/free-space limits, adopt and reap children.

    Elapsed time ends when the invocation completes; validation/cleanup are outside
    timing. Surviving live children make the sample invalid. Reaping zombies alone
    is recorded separately and does not change program output or sample validity.
    """
    if children(os.getpid()):
        raise RuntimeError('Supervisor owns unrelated children')
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER')
    capture.mkdir(parents=True, exist_ok=True)
    out_path, err_path = capture / 'stdout', capture / 'stderr'
    # Inventory is setup work, not part of the measured program. Sample again
    # during long invocations and after completion for bounded disk accounting.
    peak_work = allocated_bytes(WORK)
    cache_directory = Path(env.get('INCR_CACHE_DIR', str(SCRATCH / 'cache')))
    peak_cache = allocated_bytes(cache_directory)
    peak_used = shutil.disk_usage(WORK).used
    started = time.monotonic()
    reason = None
    last_disk = 0
    last_beat = started
    finished = threading.Event()
    finish_time = []
    interrupted = None
    proc = None
    states = {}
    with out_path.open('wb') as out, err_path.open('wb') as err:
        try:
            proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=out, stderr=err, start_new_session=True)
            def wait_for_completion():
                proc.wait()
                finish_time.append(time.monotonic())
                finished.set()
            threading.Thread(target=wait_for_completion, daemon=True).start()
            while not finished.is_set():
                now = time.monotonic()
                if peak_work > budget:
                    reason = 'work-budget'
                    break
                if now - started >= timeout:
                    reason = 'timeout'
                    break
                if now - last_disk >= 1:
                    space = shutil.disk_usage(WORK)
                    peak_used = max(peak_used, space.used)
                    if space.free < reserve:
                        reason = 'disk-reserve'
                        break
                    last_disk = now
                if now - last_beat >= 10:
                    usage = allocated_bytes(WORK)
                    peak_work = max(peak_work, usage)
                    peak_cache = max(peak_cache, allocated_bytes(cache_directory))
                    if usage > budget:
                        reason = 'work-budget'
                        break
                    if heartbeat:
                        heartbeat({'pid': proc.pid, 'elapsed_sec': now - started,
                                   'free_bytes': shutil.disk_usage(WORK).free,
                                   'work_bytes': usage, 'peak_cache_bytes': peak_cache})
                    last_beat = now
                finished.wait(.05)
            elapsed = (finish_time[0] if finish_time else time.monotonic()) - started
        except BaseException as error:
            interrupted = error
            reason = 'interrupted'
            elapsed = time.monotonic() - started
        finally:
            if proc is not None:
                proc.poll()
                states = {str(p): process_state(p) for p in descendants(os.getpid())}
                # Natural termination may briefly race descendants exiting.
                if reason is None:
                    end = time.monotonic() + .5
                    while time.monotonic() < end and any(
                            process_state(p) not in (None, 'Z') for p in descendants(os.getpid())):
                        time.sleep(.02)
                    states = {str(p): process_state(p) for p in descendants(os.getpid())}
                live = [p for p, state in states.items() if state not in (None, 'Z')]
                if live and reason is None:
                    reason = 'surviving-descendants'
                if reason:
                    signal_children(signal.SIGTERM)
                    end = time.monotonic() + 2
                    while proc.poll() is None and time.monotonic() < end:
                        time.sleep(.02)
                    signal_children(signal.SIGKILL)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    signal_children(signal.SIGKILL)
                    proc.wait(timeout=5)
                end = time.monotonic() + 5
                while children(os.getpid()) and time.monotonic() < end:
                    reap()
                    if children(os.getpid()):
                        signal_children(signal.SIGKILL)
                        time.sleep(.02)
    peak_work = max(peak_work, allocated_bytes(WORK))
    peak_cache = max(peak_cache, allocated_bytes(cache_directory))
    record = {'argv': list(map(str, argv)), 'returncode': proc.returncode if proc else None,
              'elapsed_sec': elapsed, 'failure': reason, 'descendant_states': states,
              'remaining_descendants': children(os.getpid()), 'peak_work_bytes': peak_work,
              'peak_cache_bytes': peak_cache, 'peak_filesystem_used_bytes': peak_used,
              'stdout_sha256': file_hash(out_path), 'stderr_sha256': file_hash(err_path),
              'stdout_bytes': out_path.stat().st_size, 'stderr_bytes': err_path.stat().st_size}
    atomic_json(capture / 'supervisor.json', record)
    if interrupted:
        raise interrupted
    if record['remaining_descendants']:
        raise RuntimeError('Owned descendants survived SIGKILL; refusing next run')
    return record
