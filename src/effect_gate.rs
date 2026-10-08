//! Shared atomic handshake with Observe before the first externally visible effect.
//! v1 layout: native u32 version, then atomic u32 (0 running, 1 replay, 2 live, 3 awaiting attachment).
use anyhow::{Context, Result};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::fd::AsRawFd;
use std::path::PathBuf;
use std::ptr::NonNull;
use std::sync::atomic::{AtomicU32, Ordering};

#[derive(Debug)]
pub(crate) struct EffectGate {
    pub(crate) path: PathBuf,
    mapping: NonNull<libc::c_void>,
}

// The mapping is shared only through a correctly aligned, lock-free AtomicU32.
// Its lifetime is managed by Arc at the call site; Drop cannot race an accessor.
unsafe impl Send for EffectGate {}
unsafe impl Sync for EffectGate {}

impl EffectGate {
    pub(crate) fn create(path: PathBuf) -> Result<Self> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        let mut file = OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .open(&path)?;
        file.write_all(&1u32.to_ne_bytes())?;
        file.write_all(&3u32.to_ne_bytes())?; // not ready until a compatible Observe attaches
        let raw = unsafe {
            libc::mmap(
                std::ptr::null_mut(),
                8,
                libc::PROT_READ | libc::PROT_WRITE,
                libc::MAP_SHARED,
                file.as_raw_fd(),
                0,
            )
        };
        if raw == libc::MAP_FAILED {
            let error = std::io::Error::last_os_error();
            let _ = fs::remove_file(&path);
            return Err(error).context("map Observe effect gate");
        }
        Ok(Self {
            path,
            mapping: NonNull::new(raw).expect("mmap returned null"),
        })
    }

    pub(crate) fn has_live_effects(&self) -> bool {
        let state = unsafe { &*self.mapping.as_ptr().cast::<AtomicU32>().add(1) };
        state.load(Ordering::SeqCst) == 2
    }

    /// Win the race against the first live effect. A losing execution must finish.
    pub(crate) fn claim_replay(&self) -> bool {
        let state = unsafe { &*self.mapping.as_ptr().cast::<AtomicU32>().add(1) };
        let deadline = std::time::Instant::now() + std::time::Duration::from_millis(100);
        while state.load(Ordering::SeqCst) == 3 {
            if std::time::Instant::now() >= deadline {
                return false;
            }
            std::thread::sleep(std::time::Duration::from_micros(50));
        }
        state
            .compare_exchange(0, 1, Ordering::SeqCst, Ordering::SeqCst)
            .is_ok()
    }
}

impl Drop for EffectGate {
    fn drop(&mut self) {
        unsafe {
            libc::munmap(self.mapping.as_ptr(), 8);
        }
        let _ = fs::remove_file(&self.path);
    }
}
