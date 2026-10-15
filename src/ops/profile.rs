//! Opt-in phase timing for development; no descriptors are held across exec.
use std::path::PathBuf;
use std::sync::{Mutex, OnceLock};
use std::time::Instant;

struct Profile {
    directory: PathBuf,
    started: Instant,
    phases: Mutex<Vec<(&'static str, u128)>>,
    events: Mutex<Vec<serde_json::Value>>,
}

static PROFILE: OnceLock<Option<Profile>> = OnceLock::new();

pub(crate) fn initialize() {
    PROFILE.get_or_init(|| {
        std::env::var_os("INCR_PROFILE_DIR").map(|directory| Profile {
            directory: directory.into(),
            started: Instant::now(),
            phases: Mutex::new(Vec::new()),
            events: Mutex::new(Vec::new()),
        })
    });
}

pub(crate) fn event(value: impl FnOnce() -> serde_json::Value) {
    if let Some(profile) = PROFILE.get().and_then(Option::as_ref)
        && let Ok(mut events) = profile.events.lock()
    {
        events.push(value());
    }
}

pub(crate) fn measure<T>(label: &'static str, operation: impl FnOnce() -> T) -> T {
    let Some(profile) = PROFILE.get().and_then(Option::as_ref) else {
        return operation();
    };
    let started = Instant::now();
    let result = operation();
    if let Ok(mut phases) = profile.phases.lock() {
        phases.push((label, started.elapsed().as_nanos()));
    }
    result
}

pub(crate) fn finish() {
    use std::os::unix::ffi::OsStrExt;
    use std::os::unix::fs::OpenOptionsExt;
    let Some(profile) = PROFILE.get().and_then(Option::as_ref) else {
        return;
    };
    let Ok(phases) = profile.phases.lock() else { return };
    let arguments: Vec<Vec<u8>> = std::env::args_os().map(|arg| arg.as_bytes().to_vec()).collect();
    let report = serde_json::json!({
        "pid": std::process::id(), "arguments_bytes": arguments,
        "elapsed_ns": profile.started.elapsed().as_nanos(), "phases_ns": *phases,
        "events": profile.events.lock().ok().as_deref(),
    });
    // The caller owns the directory. Diagnostic failure must not change status
    // or application stdout/stderr, and repeated probes never overwrite evidence.
    let path = profile.directory.join(format!(
        "{}-{}.json",
        std::process::id(),
        profile.started.elapsed().as_nanos()
    ));
    if let Ok(file) = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(path)
    {
        use std::io::Write;
        let mut writer = std::io::BufWriter::new(file);
        let _ = serde_json::to_writer(&mut writer, &report);
        let _ = writer.flush();
    }
}
