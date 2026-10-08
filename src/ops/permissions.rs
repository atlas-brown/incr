//! Temporary owner permissions while installing cached filesystem contents.
use anyhow::Result;
use std::collections::HashSet;
use std::fs;
use std::io::ErrorKind;
use std::os::fd::AsRawFd;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};

struct SavedPermissions {
    path: PathBuf,
    file: fs::File,
    permissions: fs::Permissions,
}

/// Restore temporary permission changes on failure. A successful caller must
/// install final modes and commit. O_PATH descriptors keep the original inodes
/// alive, so cleanup cannot chmod a replacement that reuses a pathname or inode.
#[derive(Default)]
pub(crate) struct TemporaryPermissions {
    saved: Vec<SavedPermissions>,
}

impl TemporaryPermissions {
    /// Grant access only to managed ancestors, restoring their modes after the
    /// operation. Descriptor use is bounded by path depth, not output count.
    pub(crate) fn with_parents(
        path: &Path,
        managed_paths: &HashSet<&Path>,
        operation: impl FnOnce() -> Result<()>,
    ) -> Result<()> {
        let parents: Vec<_> = path
            .ancestors()
            .skip(1)
            .filter(|parent| managed_paths.contains(parent))
            .collect();
        let mut permissions = Self::default();
        let result = (|| {
            for parent in parents.into_iter().rev() {
                permissions.directory(parent)?;
            }
            operation()
        })();
        permissions.finish(result)
    }

    /// Keep the file's final mode after a successful write; undo temporary access
    /// if the write fails. No file lease survives into the next output operation.
    pub(crate) fn with_file(path: &Path, operation: impl FnOnce() -> Result<()>) -> Result<()> {
        let mut permissions = Self::default();
        permissions.file(path)?;
        let result = operation();
        if result.is_ok() {
            permissions.commit();
            result
        } else {
            permissions.finish(result)
        }
    }

    fn finish(&mut self, result: Result<()>) -> Result<()> {
        match (result, self.restore()) {
            (Err(error), Err(cleanup)) => {
                Err(error.context(format!("permission cleanup failed: {cleanup:#}")))
            }
            (Err(error), _) => Err(error),
            (_, restored) => restored,
        }
    }

    /// Allow directory traversal and child updates without touching replacement files.
    pub(crate) fn directory(&mut self, path: &Path) -> Result<()> {
        self.allow(path, 0o700, fs::Metadata::is_dir)
    }

    /// Allow in-place writes without following symlinks or changing directories.
    pub(crate) fn file(&mut self, path: &Path) -> Result<()> {
        self.allow(path, 0o200, fs::Metadata::is_file)
    }

    fn allow(&mut self, path: &Path, access: u32, eligible: fn(&fs::Metadata) -> bool) -> Result<()> {
        let metadata = match fs::symlink_metadata(path) {
            Ok(metadata) => metadata,
            Err(error) if matches!(error.kind(), ErrorKind::NotFound | ErrorKind::NotADirectory) => {
                return Ok(());
            }
            Err(error) => return Err(error.into()),
        };
        if !eligible(&metadata) {
            return Ok(());
        }
        let required = (access >> 6) as u8;
        let owner_access = metadata.uid() == unsafe { libc::geteuid() } && metadata.mode() & access == access;
        if owner_access || effective_access(path)? & required == required {
            return Ok(());
        }
        let file = match fs::OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_PATH | libc::O_NOFOLLOW)
            .open(path)
        {
            Ok(file) => file,
            Err(error) if matches!(error.kind(), ErrorKind::NotFound | ErrorKind::NotADirectory) => {
                return Ok(());
            }
            Err(error) => return Err(error.into()),
        };
        let metadata = file.metadata()?;
        if !eligible(&metadata) || metadata.mode() & access == access {
            return Ok(());
        }
        set_permissions(&file, fs::Permissions::from_mode(metadata.mode() | access))?;
        self.saved.push(SavedPermissions {
            path: path.to_owned(),
            file,
            permissions: metadata.permissions(),
        });
        Ok(())
    }

    /// Keep final permissions already installed by the caller.
    pub(crate) fn commit(mut self) {
        self.saved.clear();
    }

    /// Attempt every restoration, reporting the first failure after cleanup.
    pub(crate) fn restore(&mut self) -> Result<()> {
        let mut failure = None;
        for saved in self.saved.drain(..).rev() {
            if let Err(error) = set_permissions(&saved.file, saved.permissions) {
                failure.get_or_insert_with(|| {
                    error.context(format!("restore permissions for {}", saved.path.display()))
                });
            }
        }
        failure.map_or(Ok(()), Err)
    }
}

/// Remove a replacement tree without following symlinks. Only the active
/// directory chain needs temporary access, including for read-only deletions.
pub(crate) fn remove_tree(path: &Path) -> Result<()> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if matches!(error.kind(), ErrorKind::NotFound | ErrorKind::NotADirectory) => return Ok(()),
        Err(error) => return Err(error.into()),
    };
    if !metadata.is_dir() {
        fs::remove_file(path)?;
        return Ok(());
    }
    let mut permissions = TemporaryPermissions::default();
    permissions.directory(path)?;
    let result = (|| {
        for child in fs::read_dir(path)? {
            remove_tree(&child?.path())?;
        }
        fs::remove_dir(path)?;
        Ok(())
    })();
    permissions.finish(result)
}

/// fchmod does not accept O_PATH descriptors. Procfs provides a stable reference
/// to their inodes, including files renamed or unlinked during restoration.
fn set_permissions(file: &fs::File, permissions: fs::Permissions) -> Result<()> {
    fs::set_permissions(format!("/proc/self/fd/{}", file.as_raw_fd()), permissions)?;
    Ok(())
}

impl Drop for TemporaryPermissions {
    fn drop(&mut self) {
        let _ = self.restore();
    }
}

/// Probe effective access, including ACL decisions, without changing permissions.
pub(crate) fn effective_access(path: &Path) -> std::io::Result<u8> {
    use std::os::unix::ffi::OsStrExt;
    let path = std::ffi::CString::new(path.as_os_str().as_bytes())
        .map_err(|error| std::io::Error::new(std::io::ErrorKind::InvalidInput, error))?;
    let mut access = 0;
    for requested in [libc::R_OK, libc::W_OK, libc::X_OK] {
        if unsafe { libc::faccessat(libc::AT_FDCWD, path.as_ptr(), requested, libc::AT_EACCESS) } == 0 {
            access |= requested as u8;
        } else {
            let error = std::io::Error::last_os_error();
            if error.kind() != std::io::ErrorKind::PermissionDenied {
                return Err(error);
            }
        }
    }
    Ok(access)
}
