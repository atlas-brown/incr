use anyhow::Result;
use nix::libc;
use nix::sys::ptrace;
use nix::sys::signal::{Signal, raise};
use nix::sys::wait::{WaitPidFlag, WaitStatus, waitpid};
use nix::unistd::{ForkResult, Pid, execvp, fork};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::ffi::CString;
use std::fs;
use std::io::{self, Read};
use std::os::unix::fs::MetadataExt;
use std::os::unix::io::AsRawFd;
use std::path::{Path, PathBuf};

type FileId = (u64, u64); // (st_dev, st_ino)

const PRE_WRITE_NONEXISTENT: &str = "<nonexistent>";
const PRE_WRITE_UNREADABLE: &str = "<unreadable>";

// ---- FIX: close_range syscall number (x86_64 Linux) ----
#[allow(dead_code)]
#[cfg(target_arch = "x86_64")]
const SYS_CLOSE_RANGE: i64 = 436; // Linux x86_64 close_range

// ---------------- Demo main (replace with your argv wiring) ----------------
fn main() -> Result<()> {
    // Example: touch newfile.txt
    let argv = vec![CString::new("touch")?, CString::new("newfile.txt")?];

    match unsafe { fork()? } {
        ForkResult::Child => {
            ptrace::traceme()?;
            raise(Signal::SIGSTOP)?; // allow parent to set ptrace options
            execvp(&argv[0], &argv)?;
            unreachable!()
        }
        ForkResult::Parent { child } => {
            run_tracer(child);
        }
    }

    Ok(())
}

// ---------------- Tracer core ----------------
pub(crate) fn run_tracer(init: Pid) -> Result<(HashSet<String>, HashMap<String, String>)> {
    eprintln!("waiting for initial stop");
    wait_for_initial_stop(init)?;
    eprintln!("after wait for initial stop");

    let opts = ptrace::Options::PTRACE_O_TRACESYSGOOD
        | ptrace::Options::PTRACE_O_TRACEFORK
        | ptrace::Options::PTRACE_O_TRACEVFORK
        | ptrace::Options::PTRACE_O_TRACECLONE
        | ptrace::Options::PTRACE_O_TRACEEXEC
        | ptrace::Options::PTRACE_O_EXITKILL;

    eprintln!("before set options");
    ptrace::seize(init, opts)?;
    eprintln!("after set options");

    // Bookkeeping
    let mut live: HashSet<Pid> = HashSet::from([init]);
    let mut in_syscall: HashSet<Pid> = HashSet::new();
    let mut last_enter: HashMap<Pid, SysEnter> = HashMap::new();

    // fd -> pretty path (symlink target)
    let mut fd_cache: HashMap<(Pid, i32), String> = HashMap::new();

    // Pre-write hashing memo by (dev, ino)
    let mut prehashed: HashSet<FileId> = HashSet::new();

    // Final results
    let mut read_paths: HashSet<String> = HashSet::new();
    // path -> pre-write hash (or marker)
    let mut write_paths: HashMap<String, String> = HashMap::new();

    eprintln!("before initial resume");
    ptrace::syscall(init, None)?; // initial resume
    eprintln!("after initial resume");

    loop {
        match waitpid(None, None)? {
            // fork/vfork/clone/exec notifications
            WaitStatus::PtraceEvent(pid, _sig, evt) => {
                if evt == libc::PTRACE_EVENT_FORK
                    || evt == libc::PTRACE_EVENT_VFORK
                    || evt == libc::PTRACE_EVENT_CLONE
                {
                    let child = Pid::from_raw(ptrace::getevent(pid)? as i32);
                    live.insert(child);
                    // Best-effort: set options on the new child and get it going
                    let _ = ptrace::setoptions(child, opts);
                    let _ = ptrace::syscall(child, None);
                }

                if evt == libc::PTRACE_EVENT_EXEC {
                    // Count the executed binary as a read dependency
                    let exe = format!("/proc/{}/exe", pid);
                    if let Ok(tgt) = fs::read_link(&exe) {
                        read_paths.insert(tgt.to_string_lossy().into_owned());
                    }
                }

                let _ = ptrace::syscall(pid, None);
            }

            // clean syscall-stop abstraction
            WaitStatus::PtraceSyscall(pid) => {
                if !in_syscall.contains(&pid) {
                    // ---------------- ENTRY ----------------
                    if let Ok(regs) = ptrace::getregs(pid) {
                        let se = SysEnter::from_regs(&regs);

                        // Pre-write hashing & read/write set collection on ENTRY
                        handle_pre_write_and_read_sets_entry(
                            pid,
                            &se,
                            &mut fd_cache,
                            &mut prehashed,
                            &mut read_paths,
                            &mut write_paths,
                        );

                        last_enter.insert(pid, se);
                    }
                    in_syscall.insert(pid);
                } else {
                    // ---------------- EXIT ----------------
                    if let Ok(regs) = ptrace::getregs(pid) {
                        if let Some(ent) = last_enter.get(&pid) {
                            handle_exit_updates(
                                pid,
                                ent,
                                regs.rax as i64,
                                &mut fd_cache,
                                &mut read_paths,
                                &mut write_paths,
                                &mut prehashed,
                            );
                            // fd may be closed -> drop cache
                            if ent.nr == libc::SYS_close as i64 {
                                let fd = ent.a[0] as i32;
                                fd_cache.remove(&(pid, fd));
                            }
                        }
                    }
                    in_syscall.remove(&pid);
                }
                let _ = ptrace::syscall(pid, None);
            }

            // pass other signals through
            WaitStatus::Stopped(pid, sig) => {
                // ---- avoid reinjecting SIGTRAP / SIGSTOP by default ----
                let deliver = match sig {
                    Signal::SIGTRAP => None,
                    Signal::SIGSTOP => None,
                    _ => Some(sig),
                };
                let _ = ptrace::syscall(pid, deliver);
            }

            // process exit
            WaitStatus::Exited(pid, _) | WaitStatus::Signaled(pid, _, _) => {
                live.remove(&pid);
                in_syscall.remove(&pid);
                last_enter.remove(&pid);
                fd_cache.retain(|(p, _), _| *p != pid);
                if live.is_empty() {
                    break;
                }
            }

            _ => {}
        }
    }

    Ok((read_paths, write_paths))
}

fn wait_for_initial_stop(pid: Pid) -> Result<()> {
    loop {
        match waitpid(Some(pid), Some(WaitPidFlag::WSTOPPED))? {
            WaitStatus::Stopped(_, _) => return Ok(()),
            _ => continue,
        }
    }
}

// ---------------- Entry/Exit handlers ----------------

fn handle_pre_write_and_read_sets_entry(
    pid: Pid,
    se: &SysEnter,
    fd_cache: &mut HashMap<(Pid, i32), String>,
    prehashed: &mut HashSet<FileId>,
    read_paths: &mut HashSet<String>,
    write_paths: &mut HashMap<String, String>,
) {
    let nr = se.nr;

    // ---------- FD-based READ syscalls (files or directories) ----------
    if is_fd_read_syscall(nr) {
        let fd = se.a[0] as i32;
        if let Some(path) = realpath_of_fd(pid, fd, fd_cache) {
            let proc_fd_path = format!("/proc/{}/fd/{}", pid, fd);
            if is_readable_node_proc_path(&proc_fd_path) {
                read_paths.insert(path);
            }
        }
    }

    // ---------- FD-based metadata reads (fstat) ----------
    if is_fd_metadata_read_syscall(nr) {
        let fd = se.a[0] as i32;
        if let Some(path) = realpath_of_fd(pid, fd, fd_cache) {
            let proc_fd_path = format!("/proc/{}/fd/{}", pid, fd);
            if is_readable_node_proc_path(&proc_fd_path) {
                read_paths.insert(path);
            }
        }
    }

    // ---------- Memory-mapped READs ----------
    if nr == libc::SYS_mmap as i64 {
        let prot = se.a[2] as i32;
        let fd = se.a[4] as i32;
        if fd >= 0 && (prot & libc::PROT_READ) != 0 {
            let proc_fd_path = format!("/proc/{}/fd/{}", pid, fd);
            if let Some(path) = realpath_of_fd(pid, fd, fd_cache) {
                if is_regular_file_proc_path(&proc_fd_path) {
                    read_paths.insert(path);
                }
            }
        }
    }

    // ---------- FD-based WRITE syscalls (pre-hash) ----------
    if is_fd_write_syscall(nr) {
        let fd = se.a[0] as i32;
        let proc_fd_path = format!("/proc/{}/fd/{}", pid, fd);
        if let (Some(path), Some(fid)) = (realpath_of_fd(pid, fd, fd_cache), file_id_from_proc_fd(pid, fd)) {
            if is_regular_file_proc_path(&proc_fd_path) {
                if !prehashed.contains(&fid) {
                    let hash = hash_via_proc_fd(pid, fd)
                        .ok()
                        .unwrap_or_else(|| PRE_WRITE_UNREADABLE.to_string());
                    write_paths.entry(path.clone()).or_insert(hash);
                    prehashed.insert(fid);
                } else {
                    write_paths
                        .entry(path)
                        .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
                }
            }
        }
    }

    // ---------- PATH-based syscalls ----------
    match nr {
        // open-like
        x if x == libc::SYS_open as i64 => {
            let path = read_cstr(pid, se.a[0] as u64).unwrap_or_default();
            let flags = se.a[1];
            // prehash when O_TRUNC is requested
            maybe_prehash_truncating_open(pid, None, &path, flags, None, prehashed, write_paths);
            handle_open_like_path(pid, None, &path, flags, None, prehashed, read_paths, write_paths);
        }
        x if x == libc::SYS_openat as i64 => {
            let dirfd = se.a[0] as i32;
            let path = read_cstr(pid, se.a[1] as u64).unwrap_or_default();
            let flags = se.a[2];
            // prehash when O_TRUNC is requested
            maybe_prehash_truncating_open(pid, Some(dirfd), &path, flags, None, prehashed, write_paths);
            handle_open_like_path(
                pid,
                Some(dirfd),
                &path,
                flags,
                None,
                prehashed,
                read_paths,
                write_paths,
            );
        }
        x if x == libc::SYS_openat2 as i64 => {
            let dirfd = se.a[0] as i32;
            let path = read_cstr(pid, se.a[1] as u64).unwrap_or_default();
            let howptr = se.a[2];
            let flags_opt = read_open_how_flags(pid, howptr);
            // prehash when O_TRUNC is requested
            maybe_prehash_truncating_open(pid, Some(dirfd), &path, 0, flags_opt, prehashed, write_paths);
            handle_open_like_path(
                pid,
                Some(dirfd),
                &path,
                0,
                flags_opt,
                prehashed,
                read_paths,
                write_paths,
            );
        }
        x if x == libc::SYS_creat as i64 => {
            let path = read_cstr(pid, se.a[0] as u64).unwrap_or_default();
            let flags = (libc::O_WRONLY | libc::O_CREAT | libc::O_TRUNC) as u64;
            // prehash when O_TRUNC is requested
            maybe_prehash_truncating_open(pid, None, &path, flags, None, prehashed, write_paths);
            handle_open_like_path(pid, None, &path, flags, None, prehashed, read_paths, write_paths);
        }

        // truncate(path) prehash
        x if x == libc::SYS_truncate as i64 => {
            let path = read_cstr(pid, se.a[0] as u64).unwrap_or_default();
            if let Some(host_path) = host_openable_path_for_tracee(pid, None, &path) {
                let proc_ok = is_regular_file_proc_path(&host_path);
                if let (true, Some(real_path), Some(fid)) = (
                    proc_ok,
                    real_fs_path_from_host_openable(&host_path),
                    file_id_from_host_path(&host_path),
                ) {
                    if !prehashed.contains(&fid) {
                        let hash = hash_via_host_path(&host_path)
                            .ok()
                            .unwrap_or_else(|| PRE_WRITE_UNREADABLE.to_string());
                        write_paths.entry(real_path.clone()).or_insert(hash);
                        prehashed.insert(fid);
                    } else {
                        write_paths
                            .entry(real_path)
                            .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
                    }
                }
            }
        }

        // ---------- PATH-based metadata reads ----------
        x if x == libc::SYS_newfstatat as i64 => {
            let dirfd = se.a[0] as i32;
            let path = read_cstr(pid, se.a[1] as u64).unwrap_or_default();
            if let Some(host_path) = host_openable_path_for_tracee(pid, Some(dirfd), &path) {
                if is_readable_node_proc_path(&host_path) {
                    if let Some(real) = real_fs_path_from_host_openable(&host_path) {
                        read_paths.insert(real);
                    }
                }
            }
        }
        x if x == libc::SYS_statx as i64 => {
            let dirfd = se.a[0] as i32;
            let path = read_cstr(pid, se.a[1] as u64).unwrap_or_default();
            if let Some(host_path) = host_openable_path_for_tracee(pid, Some(dirfd), &path) {
                if is_readable_node_proc_path(&host_path) {
                    if let Some(real) = real_fs_path_from_host_openable(&host_path) {
                        read_paths.insert(real);
                    }
                }
            }
        }
        x if x == libc::SYS_access as i64 => {
            let path = read_cstr(pid, se.a[0] as u64).unwrap_or_default();
            if let Some(host_path) = host_openable_path_for_tracee(pid, None, &path) {
                if is_readable_node_proc_path(&host_path) {
                    if let Some(real) = real_fs_path_from_host_openable(&host_path) {
                        read_paths.insert(real);
                    }
                }
            }
        }
        x if x == libc::SYS_faccessat as i64 => {
            let dirfd = se.a[0] as i32;
            let path = read_cstr(pid, se.a[1] as u64).unwrap_or_default();
            if let Some(host_path) = host_openable_path_for_tracee(pid, Some(dirfd), &path) {
                if is_readable_node_proc_path(&host_path) {
                    if let Some(real) = real_fs_path_from_host_openable(&host_path) {
                        read_paths.insert(real);
                    }
                }
            }
        }

        _ => {}
    }

    // ---------- Cross-FD ops ----------
    if nr == libc::SYS_sendfile as i64 {
        let in_fd = se.a[1] as i32;
        let out_fd = se.a[0] as i32;

        // read side
        let in_proc = format!("/proc/{}/fd/{}", pid, in_fd);
        if let Some(p) = realpath_of_fd(pid, in_fd, fd_cache) {
            if is_readable_node_proc_path(&in_proc) {
                read_paths.insert(p);
            }
        }
        // write side
        let out_proc = format!("/proc/{}/fd/{}", pid, out_fd);
        if let (Some(p), Some(fid)) = (
            realpath_of_fd(pid, out_fd, fd_cache),
            file_id_from_proc_fd(pid, out_fd),
        ) {
            if is_regular_file_proc_path(&out_proc) {
                if !prehashed.contains(&fid) {
                    let hash = hash_via_proc_fd(pid, out_fd)
                        .ok()
                        .unwrap_or_else(|| PRE_WRITE_UNREADABLE.to_string());
                    write_paths.entry(p.clone()).or_insert(hash);
                    prehashed.insert(fid);
                } else {
                    write_paths
                        .entry(p)
                        .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
                }
            }
        }
    }

    if nr == libc::SYS_copy_file_range as i64 {
        let in_fd = se.a[0] as i32;
        let out_fd = se.a[2] as i32;

        let in_proc = format!("/proc/{}/fd/{}", pid, in_fd);
        if let Some(p) = realpath_of_fd(pid, in_fd, fd_cache) {
            if is_readable_node_proc_path(&in_proc) {
                read_paths.insert(p);
            }
        }

        let out_proc = format!("/proc/{}/fd/{}", pid, out_fd);
        if let (Some(p), Some(fid)) = (
            realpath_of_fd(pid, out_fd, fd_cache),
            file_id_from_proc_fd(pid, out_fd),
        ) {
            if is_regular_file_proc_path(&out_proc) {
                if !prehashed.contains(&fid) {
                    let hash = hash_via_proc_fd(pid, out_fd)
                        .ok()
                        .unwrap_or_else(|| PRE_WRITE_UNREADABLE.to_string());
                    write_paths.entry(p.clone()).or_insert(hash);
                    prehashed.insert(fid);
                } else {
                    write_paths
                        .entry(p)
                        .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
                }
            }
        }
    }
}

fn handle_exit_updates(
    pid: Pid,
    ent: &SysEnter,
    ret: i64,
    fd_cache: &mut HashMap<(Pid, i32), String>,
    _read_paths: &mut HashSet<String>,
    write_paths: &mut HashMap<String, String>,
    prehashed: &mut HashSet<FileId>,
) {
    // Handle close_range cache invalidation first (best-effort)
    #[allow(non_upper_case_globals)]
    {
        #[cfg(target_arch = "x86_64")]
        if ent.nr == SYS_CLOSE_RANGE && ret == 0 {
            let first = ent.a[0] as i32;
            let last = ent.a[1] as i32; // may be ~0u to mean "max"
            fd_cache.retain(|(p, fd), _| {
                if *p != pid {
                    return true;
                }
                if last == !0 {
                    return *fd < first;
                }
                *fd < first || *fd > last
            });
        }
    }

    // treat rename*/link*/unlink* as writes (overapprox) and drop FD cache for pid
    if ret >= 0 {
        match ent.nr {
            x if x == libc::SYS_rename as i64 => {
                // args: oldpath, newpath
                let newp = read_cstr(pid, ent.a[1]).unwrap_or_default();
                mark_path_like_write(pid, None, &newp, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            x if x == libc::SYS_renameat as i64 => {
                // args: olddirfd, oldpath, newdirfd, newpath
                let newdirfd = ent.a[2] as i32;
                let newp = read_cstr(pid, ent.a[3]).unwrap_or_default();
                mark_path_like_write(pid, Some(newdirfd), &newp, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            x if x == libc::SYS_renameat2 as i64 => {
                let newdirfd = ent.a[2] as i32;
                let newp = read_cstr(pid, ent.a[3]).unwrap_or_default();
                mark_path_like_write(pid, Some(newdirfd), &newp, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            x if x == libc::SYS_link as i64 => {
                // args: oldpath, newpath
                let newp = read_cstr(pid, ent.a[1]).unwrap_or_default();
                mark_path_like_write(pid, None, &newp, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            x if x == libc::SYS_linkat as i64 => {
                // args: olddirfd, oldpath, newdirfd, newpath, flags
                let newdirfd = ent.a[2] as i32;
                let newp = read_cstr(pid, ent.a[3]).unwrap_or_default();
                mark_path_like_write(pid, Some(newdirfd), &newp, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            x if x == libc::SYS_unlink as i64 => {
                let up = read_cstr(pid, ent.a[0]).unwrap_or_default();
                // Overapprox: mark the parent dir of `up` as written by marking `up` itself
                mark_path_like_write(pid, None, &up, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            x if x == libc::SYS_unlinkat as i64 => {
                let dirfd = ent.a[0] as i32;
                let up = read_cstr(pid, ent.a[1]).unwrap_or_default();
                mark_path_like_write(pid, Some(dirfd), &up, write_paths);
                fd_cache.retain(|(p, _), _| *p != pid);
            }
            _ => {}
        }
    }

    // For the rest, we only act on successful open-ish syscalls.
    if ret < 0 {
        return;
    }

    let nr = ent.nr;
    let is_open_ret = nr == libc::SYS_open as i64
        || nr == libc::SYS_openat as i64
        || nr == libc::SYS_openat2 as i64
        || nr == libc::SYS_creat as i64;

    if !is_open_ret {
        return;
    }

    let fd = ret as i32;
    if let Some(p) = realpath_of_fd(pid, fd, fd_cache) {
        let proc_fd_path = format!("/proc/{}/fd/{}", pid, fd);
        if !is_readable_node_proc_path(&proc_fd_path) {
            return;
        }

        // derive flags and write intent
        let (flags, flags_openat2) = match nr {
            x if x == libc::SYS_open as i64 => (ent.a[1], None),
            x if x == libc::SYS_openat as i64 => (ent.a[2], None),
            x if x == libc::SYS_openat2 as i64 => (0, read_open_how_flags(pid, ent.a[2])),
            x if x == libc::SYS_creat as i64 => {
                ((libc::O_WRONLY | libc::O_CREAT | libc::O_TRUNC) as u64, None)
            }
            _ => (0, None),
        };

        let writey = flags_imply_write(flags) || flags_openat2.map(flags_imply_write).unwrap_or(false);
        if !writey {
            // conservative read accounting stays as-is
            return;
        }

        // writey: ensure write set has an entry with a sensible marker if no prehash
        if let Some(fid) = file_id_from_proc_fd(pid, fd) {
            if !prehashed.contains(&fid) {
                let created = (flags as i32 & libc::O_CREAT) != 0
                    || flags_openat2
                        .map(|f| (f as i32 & libc::O_CREAT) != 0)
                        .unwrap_or(false);
                let marker = if created {
                    PRE_WRITE_NONEXISTENT
                } else {
                    PRE_WRITE_UNREADABLE
                };
                write_paths.entry(p.clone()).or_insert_with(|| marker.to_string());
                prehashed.insert(fid);
            } else {
                write_paths
                    .entry(p)
                    .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
            }
        }
    }
}

// ---------------- Read/write classification helpers ----------------

fn is_fd_read_syscall(nr: i64) -> bool {
    nr == libc::SYS_read as i64
        || nr == libc::SYS_pread64 as i64
        || nr == libc::SYS_readv as i64
        || nr == libc::SYS_preadv as i64
        || nr == libc::SYS_preadv2 as i64
        || nr == libc::SYS_getdents as i64
        || nr == libc::SYS_getdents64 as i64
}

// metadata-only via FD (e.g., fstat)
fn is_fd_metadata_read_syscall(nr: i64) -> bool {
    nr == libc::SYS_fstat as i64
}

fn is_fd_write_syscall(nr: i64) -> bool {
    nr == libc::SYS_write as i64
        || nr == libc::SYS_pwrite64 as i64
        || nr == libc::SYS_writev as i64
        || nr == libc::SYS_pwritev as i64
        || nr == libc::SYS_pwritev2 as i64
        // copy_file_range is handled separately as a cross-FD op
        || nr == libc::SYS_ftruncate as i64
}

fn flags_imply_write(flags: u64) -> bool {
    let f = flags as i32;
    (f & libc::O_WRONLY) != 0
        || (f & libc::O_RDWR) != 0
        || (f & libc::O_TRUNC) != 0
        || (f & libc::O_CREAT) != 0
}

// openat2: struct open_how { u64 flags; u64 mode; u64 resolve; }
fn read_open_how_flags(pid: Pid, ptr: u64) -> Option<u64> {
    if ptr == 0 {
        return None;
    }
    ptrace::read(pid, ptr as ptrace::AddressType)
        .ok()
        .map(|w| w as u64)
}

// ---------------- Path resolution & hashing ----------------

fn host_openable_path_for_tracee(pid: Pid, dirfd: Option<i32>, tracee_path: &str) -> Option<String> {
    if tracee_path.is_empty() {
        return None;
    }

    let path = Path::new(tracee_path);
    if path.is_absolute() {
        return Some(format!("/proc/{}/root{}", pid, tracee_path));
    }
    match dirfd {
        None => Some(format!("/proc/{}/cwd/{}", pid, tracee_path)),
        Some(fd) if fd == libc::AT_FDCWD => Some(format!("/proc/{}/cwd/{}", pid, tracee_path)),
        Some(fd) if fd >= 0 => Some(format!("/proc/{}/fd/{}/{}", pid, fd, tracee_path)),
        _ => None,
    }
}

// Best-effort resolution that does NOT open the leaf path (works even if it was unlinked).
fn best_effort_real_path_without_open(pid: Pid, dirfd: Option<i32>, tracee_path: &str) -> Option<String> {
    if tracee_path.is_empty() {
        return None;
    }

    let tpath = Path::new(tracee_path);

    if tpath.is_absolute() {
        // Resolve /proc/<pid>/root to host path and join the absolute tracee path.
        if let Ok(root) = fs::read_link(format!("/proc/{}/root", pid)) {
            return Some(
                Path::new(&root)
                    .join(&tracee_path[1..])
                    .to_string_lossy()
                    .into_owned(),
            );
        }
        // Fallback: just return the absolute tracee path string.
        return Some(tracee_path.to_string());
    }

    // Relative: resolve base via dirfd or cwd (symlink read), then join.
    let base = if let Some(dfd) = dirfd {
        if dfd == libc::AT_FDCWD {
            fs::read_link(format!("/proc/{}/cwd", pid)).ok()
        } else if dfd >= 0 {
            fs::read_link(format!("/proc/{}/fd/{}", pid, dfd)).ok()
        } else {
            None
        }
    } else {
        fs::read_link(format!("/proc/{}/cwd", pid)).ok()
    }?;

    Some(Path::new(&base).join(tracee_path).to_string_lossy().into_owned())
}

// Re-resolve a host-openable proc path to a user-facing filesystem path (for set membership).
fn real_fs_path_from_host_openable(host_path: &str) -> Option<String> {
    let f = fs::File::open(host_path).ok()?;
    let link = format!("/proc/self/fd/{}", f.as_raw_fd());
    let target = fs::read_link(link).ok()?;
    Some(target.to_string_lossy().into_owned())
}

// Remove trailing " (deleted)" for nicer user-facing paths
fn normalize_proc_fd_target(s: String) -> String {
    if let Some(stripped) = s.strip_suffix(" (deleted)") {
        stripped.to_string()
    } else {
        s
    }
}

// FD -> symlink target path
fn realpath_of_fd(pid: Pid, fd: i32, cache: &mut HashMap<(Pid, i32), String>) -> Option<String> {
    if fd < 0 {
        return None;
    }
    if let Some(s) = cache.get(&(pid, fd)) {
        return Some(s.clone());
    }
    let link = PathBuf::from(format!("/proc/{}/fd/{}", pid, fd));
    match fs::read_link(&link) {
        Ok(tgt) => {
            let s = normalize_proc_fd_target(tgt.to_string_lossy().into_owned());
            cache.insert((pid, fd), s.clone());
            Some(s)
        }
        Err(_) => None,
    }
}

// Is the host-openable proc path pointing to a regular file?
fn is_regular_file_proc_path(host_proc_path: &str) -> bool {
    fs::metadata(host_proc_path).map(|m| m.is_file()).unwrap_or(false)
}

// For read deps: file OR directory
fn is_readable_node_proc_path(host_proc_path: &str) -> bool {
    fs::metadata(host_proc_path)
        .map(|m| m.is_file() || m.is_dir())
        .unwrap_or(false)
}

// File IDs for deduping pre-hash
fn file_id_from_proc_fd(pid: Pid, fd: i32) -> Option<FileId> {
    let p = format!("/proc/{}/fd/{}", pid, fd);
    fs::metadata(&p).ok().map(|m| (m.dev(), m.ino()))
}
fn file_id_from_host_path(host_path: &str) -> Option<FileId> {
    fs::metadata(host_path).ok().map(|m| (m.dev(), m.ino()))
}

// Hash via /proc/<pid>/fd/<fd>
fn hash_via_proc_fd(pid: Pid, fd: i32) -> io::Result<String> {
    let p = format!("/proc/{}/fd/{}", pid, fd);
    let f = fs::File::open(p)?;
    sha256_reader(f)
}
// Hash via host-openable proc path
fn hash_via_host_path(host_path: &str) -> io::Result<String> {
    let f = fs::File::open(host_path)?;
    sha256_reader(f)
}

// Robust hex encoding
fn sha256_reader<R: Read>(mut r: R) -> io::Result<String> {
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 1 << 16];
    loop {
        let n = r.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    let digest = hasher.finalize();
    let mut s = String::with_capacity(digest.len() * 2);
    for b in digest {
        use std::fmt::Write as _; // only the trait
        let _ = write!(&mut s, "{:x}", b);
    }
    Ok(s)
}

// ---------------- Syscall register plumbing ----------------

#[derive(Clone, Debug)]
struct SysEnter {
    nr: i64,
    a: [u64; 6],
}
impl SysEnter {
    // x86_64: orig_rax=nr; args rdi, rsi, rdx, r10, r8, r9
    #[cfg(target_arch = "x86_64")]
    fn from_regs(r: &libc::user_regs_struct) -> Self {
        Self {
            nr: r.orig_rax as i64,
            a: [r.rdi, r.rsi, r.rdx, r.r10, r.r8, r.r9],
        }
    }

    #[cfg(not(target_arch = "x86_64"))]
    fn from_regs(_: &libc::user_regs_struct) -> Self {
        compile_error!("This tracer currently only wires syscall arg registers for x86_64.");
    }
}

// Read NUL-terminated C string from tracee
fn read_cstr(pid: Pid, addr: u64) -> Result<String> {
    // Fast path with process_vm_readv
    let mut buf = vec![0u8; 4096];
    let local = libc::iovec {
        iov_base: buf.as_mut_ptr() as _,
        iov_len: buf.len(),
    };
    let remote = libc::iovec {
        iov_base: addr as _,
        iov_len: buf.len(),
    };
    let n = unsafe { libc::process_vm_readv(pid.as_raw() as _, &local, 1, &remote, 1, 0) };
    if n > 0 {
        if let Some(z) = buf.iter().position(|&b| b == 0) {
            buf.truncate(z);
            return Ok(String::from_utf8_lossy(&buf).into_owned());
        }
    }

    // Fallback: ptrace::read word-by-word
    let mut out = Vec::new();
    let mut p = addr as usize;
    loop {
        match ptrace::read(pid, p as ptrace::AddressType) {
            Ok(word) => {
                for b in word.to_ne_bytes() {
                    if b == 0 {
                        return Ok(String::from_utf8_lossy(&out).into_owned());
                    }
                    out.push(b);
                    if out.len() > (1 << 20) {
                        return Ok(String::from_utf8_lossy(&out).into_owned());
                    }
                }
                p += std::mem::size_of::<libc::c_long>();
            }
            Err(_) => {
                return Ok(String::from_utf8_lossy(&out).into_owned());
            }
        }
    }
}

// ---------------- Open-like handling (with openat resolution) ----------------

fn handle_open_like_path(
    pid: Pid,
    dirfd: Option<i32>,
    tracee_path: &str,
    legacy_flags: u64,
    openat2_flags: Option<u64>,
    prehashed: &mut HashSet<FileId>,
    read_paths: &mut HashSet<String>,
    write_paths: &mut HashMap<String, String>,
) {
    // Determine write intent from either legacy flags or openat2 flags
    let writey = if let Some(f2) = openat2_flags {
        flags_imply_write(f2)
    } else {
        flags_imply_write(legacy_flags)
    };

    if let Some(host_path) = host_openable_path_for_tracee(pid, dirfd, tracee_path) {
        let proc_ok_file = is_regular_file_proc_path(&host_path);
        let proc_ok_readable = is_readable_node_proc_path(&host_path);
        let real_path = real_fs_path_from_host_openable(&host_path);
        let fid = file_id_from_host_path(&host_path);

        if let (true, Some(real), Some(fid)) = (proc_ok_file, real_path.clone(), fid) {
            if writey {
                if !prehashed.contains(&fid) {
                    let hash = hash_via_host_path(&host_path)
                        .ok()
                        .unwrap_or_else(|| PRE_WRITE_UNREADABLE.to_string());
                    write_paths.entry(real.clone()).or_insert(hash);
                    prehashed.insert(fid);
                } else {
                    write_paths
                        .entry(real)
                        .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
                }
                return;
            }
        }
        // For READS: accept directories or files
        if !writey && proc_ok_readable {
            if let Some(real) = real_path {
                read_paths.insert(real);
            }
        }
    }
}

// prehash when open/creat is truncating
fn maybe_prehash_truncating_open(
    pid: Pid,
    dirfd: Option<i32>,
    tracee_path: &str,
    legacy_flags: u64,
    openat2_flags: Option<u64>,
    prehashed: &mut HashSet<FileId>,
    write_paths: &mut HashMap<String, String>,
) {
    let f_legacy = legacy_flags as i32;
    let f_open2 = openat2_flags.map(|x| x as i32).unwrap_or(0);
    let trunc = (f_legacy & libc::O_TRUNC) != 0 || (f_open2 & libc::O_TRUNC) != 0;
    if !trunc {
        return;
    }
    if let Some(host_path) = host_openable_path_for_tracee(pid, dirfd, tracee_path) {
        if is_regular_file_proc_path(&host_path) {
            if let (Some(real), Some(fid)) = (
                real_fs_path_from_host_openable(&host_path),
                file_id_from_host_path(&host_path),
            ) {
                if !prehashed.contains(&fid) {
                    let hash = hash_via_host_path(&host_path)
                        .ok()
                        .unwrap_or_else(|| PRE_WRITE_UNREADABLE.to_string());
                    write_paths.entry(real.clone()).or_insert(hash);
                    prehashed.insert(fid);
                } else {
                    write_paths
                        .entry(real)
                        .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
                }
            }
        }
    }
}

// mark a path-like operation as a write (overapprox), robust w/o opening leaf
fn mark_path_like_write(
    pid: Pid,
    dirfd: Option<i32>,
    tracee_path: &str,
    write_paths: &mut HashMap<String, String>,
) {
    // Prefer a resolution that doesn't require opening the path (works after unlink)
    if let Some(real) = best_effort_real_path_without_open(pid, dirfd, tracee_path) {
        write_paths
            .entry(real)
            .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
        return;
    }

    // Fallback: try opening the path (original behavior)
    if let Some(host_path) = host_openable_path_for_tracee(pid, dirfd, tracee_path) {
        if let Some(real) = real_fs_path_from_host_openable(&host_path) {
            write_paths
                .entry(real)
                .or_insert_with(|| PRE_WRITE_UNREADABLE.to_string());
        }
    }
}
