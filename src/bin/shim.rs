// src/main.rs
use anyhow::Result;
use nix::sys::ptrace;
use nix::sys::signal::{Signal, raise};
use nix::unistd::execvp;
use std::ffi::CString;
use std::os::unix::ffi::OsStrExt;

fn main() -> Result<()> {
    // argv to run is everything after the shim's own name
    let mut it = std::env::args_os().skip(1);
    eprintln!("starting shim");
    let first = match it.next() {
        Some(s) => s,
        None => {
            eprintln!("usage: shim <program> [args...]");
            std::process::exit(2);
        }
    };

    // Build a Vec<CString> for execvp: [prog, arg1, arg2, ...]
    let mut argv = Vec::<CString>::new();
    argv.push(CString::new(first.as_bytes().to_vec())?);
    for s in it {
        argv.push(CString::new(s.as_bytes().to_vec())?);
    }

    // Ask to be traced and stop so the parent can set ptrace options.
    // (Parent should waitpid() this stop, call ptrace::setoptions, then continue.)
    ptrace::traceme()?;
    eprintln!("raised initial stop");
    raise(Signal::SIGSTOP)?; // initial stop for the tracer
    eprintln!("after initial stop");

    // Replace this shim with the requested program (PATH search preserved)
    execvp(&argv[0], &argv)?;
    unreachable!();
}
