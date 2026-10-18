use super::*;

struct TestDirectory(PathBuf);

impl TestDirectory {
    fn create() -> Result<Self> {
        let directory = Self(std::env::temp_dir().join(format!("incr-effects-{}", rand::random::<u128>())));
        fs::create_dir(&directory.0)?;
        Ok(directory)
    }
}

impl Drop for TestDirectory {
    fn drop(&mut self) {
        let _ = remove_tree(&self.0);
    }
}

fn capture(directory: &Path, writes: &HashSet<PathBuf>, replaced_paths: &HashSet<PathBuf>) -> Result<()> {
    super::capture(directory, writes, replaced_paths, &HashMap::new())
}

fn capture_with_dependencies(
    directory: &Path,
    writes: &HashSet<PathBuf>,
    replaced_paths: &HashSet<PathBuf>,
    dependencies: &HashMap<PathBuf, crate::cache::DependencyKey>,
) -> Result<()> {
    super::capture(directory, writes, replaced_paths, dependencies)
}

fn test_metadata(mode: u32) -> MetadataState {
    MetadataState {
        mode,
        uid: unsafe { libc::getuid() },
        gid: unsafe { libc::getgid() },
        mtime_sec: 0,
        mtime_nsec: 0,
        extended_attributes: Vec::new(),
    }
}

#[test]
fn invalid_hard_link_is_rejected_before_deletion() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let directory = fixture.0.join("directory");
    let cache = fixture.0.join("cache");
    fs::create_dir(&cache)?;
    fs::write(&output, b"preserve")?;
    let directory_metadata = fs::symlink_metadata(&directory).or_else(|_| {
        fs::create_dir(&directory)?;
        fs::symlink_metadata(&directory)
    })?;
    let manifest = Manifest {
        version: 5,
        entries: vec![
            Entry {
                path: output.clone(),
                effect: Effect::Missing,
            },
            Entry {
                path: directory.clone(),
                effect: Effect::Directory {
                    metadata: MetadataState::capture(&directory, &directory_metadata)?,
                },
            },
            Entry {
                path: fixture.0.join("link"),
                effect: Effect::HardLink { target: directory },
            },
        ],
    };
    fs::write(cache.join(MANIFEST), serde_json::to_vec(&manifest)?)?;
    assert!(replay(&cache).is_err());
    assert_eq!(fs::read(output)?, b"preserve");
    Ok(())
}

#[test]
fn replaced_directory_children_are_absent() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let removed_child = output.join("child");
    let cache = fixture.0.join("cache");
    fs::write(&output, b"replacement")?;
    capture(
        &cache,
        &HashSet::from([output.clone(), removed_child]),
        &HashSet::from([output.clone()]),
    )?;
    replay(&cache)?;
    assert_eq!(fs::read(output)?, b"replacement");
    Ok(())
}
#[test]
fn replay_populates_existing_readonly_directory() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let child = output.join("child");
    let cache = fixture.0.join("cache");
    fs::create_dir_all(&output)?;
    fs::write(&child, b"cached content")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o500))?;
    let result = (|| -> Result<()> {
        capture(
            &cache,
            &HashSet::from([output.clone(), child.clone()]),
            &HashSet::new(),
        )?;
        fs::set_permissions(&output, fs::Permissions::from_mode(0o700))?;
        fs::remove_file(&child)?;
        fs::set_permissions(&output, fs::Permissions::from_mode(0o500))?;
        replay(&cache)?;
        assert_eq!(fs::read(&child)?, b"cached content");
        assert_eq!(fs::metadata(&output)?.permissions().mode() & 0o777, 0o500);
        Ok(())
    })();
    fs::set_permissions(&output, fs::Permissions::from_mode(0o700))?;
    result
}

#[test]
fn replay_failure_restores_directory_permissions() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let cache = fixture.0.join("cache");
    fs::create_dir_all(&output)?;
    fs::create_dir(&cache)?;
    fs::write(output.join("blocker"), b"not a directory")?;
    let manifest = Manifest {
        version: 5,
        entries: vec![
            Entry {
                path: output.clone(),
                effect: Effect::Directory {
                    metadata: test_metadata(0o500),
                },
            },
            Entry {
                path: output.join("blocker/child"),
                effect: Effect::Symlink {
                    target: PathBuf::from("target"),
                    metadata: test_metadata(0o777),
                },
            },
        ],
    };
    fs::write(cache.join(MANIFEST), serde_json::to_vec(&manifest)?)?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o500))?;
    let replayed = replay(&cache);
    let mode = fs::metadata(&output)?.permissions().mode() & 0o777;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o700))?;
    assert!(replayed.is_err());
    assert_eq!(mode, 0o500);
    Ok(())
}

#[test]
fn replay_updates_readonly_file_without_breaking_aliases() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let alias = fixture.0.join("alias");
    let cache = fixture.0.join("cache");
    fs::write(&output, b"cached")?;
    fs::hard_link(&output, &alias)?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o444))?;
    capture(&cache, &HashSet::from([output.clone()]), &HashSet::new())?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o644))?;
    fs::write(&output, b"current")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o444))?;
    replay(&cache)?;
    assert_eq!(fs::read(&alias)?, b"cached");
    assert_eq!(fs::metadata(&output)?.permissions().mode() & 0o777, 0o444);
    Ok(())
}

#[test]
fn directory_replacement_keeps_removed_file_alias_permissions() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let cache = fixture.0.join("cache");
    fs::create_dir_all(&cache)?;
    let output = fixture.0.join("output");
    let alias = fixture.0.join("alias");
    fs::write(&output, b"original")?;
    fs::hard_link(&output, &alias)?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o444))?;
    let manifest = Manifest {
        version: 5,
        entries: vec![Entry {
            path: output.clone(),
            effect: Effect::Directory {
                metadata: test_metadata(0o500),
            },
        }],
    };
    fs::write(cache.join(MANIFEST), serde_json::to_vec(&manifest)?)?;
    replay(&cache)?;
    assert!(output.is_dir());
    assert_eq!(fs::metadata(alias)?.permissions().mode() & 0o777, 0o444);
    Ok(())
}

#[test]
fn permission_cleanup_follows_the_original_inode() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let moved = fixture.0.join("moved");
    fs::write(&output, b"original")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o400))?;
    let mut permissions = crate::ops::permissions::TemporaryPermissions::default();
    permissions.file(&output)?;
    fs::rename(&output, &moved)?;
    fs::write(&output, b"replacement")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o644))?;
    permissions.restore()?;
    assert_eq!(fs::metadata(moved)?.permissions().mode() & 0o777, 0o400);
    assert_eq!(fs::metadata(output)?.permissions().mode() & 0o777, 0o644);
    Ok(())
}

#[test]
fn replay_preserves_overwrite_and_replacement_alias_semantics() -> Result<()> {
    for replace in [false, true] {
        let fixture = TestDirectory::create()?;
        let output = fixture.0.join("output");
        let alias = fixture.0.join("alias");
        let replacement = fixture.0.join("replacement");
        let cache = fixture.0.join("cache");
        fs::write(&output, b"old")?;
        fs::hard_link(&output, &alias)?;
        if replace {
            fs::write(&replacement, b"new")?;
            fs::rename(&replacement, &output)?;
        } else {
            fs::write(&output, b"new")?;
        }
        let expected_alias = fs::read(&alias)?;
        let writes = HashSet::from([output.clone()]);
        let replacements = if replace { writes.clone() } else { HashSet::new() };
        capture(&cache, &writes, &replacements)?;

        fs::remove_file(&output)?;
        fs::write(&alias, b"old")?;
        fs::hard_link(&alias, &output)?;
        replay(&cache)?;
        assert_eq!(fs::read(&output)?, b"new");
        assert_eq!(fs::read(&alias)?, expected_alias);
        assert_eq!(
            fs::metadata(&output)?.ino() == fs::metadata(&alias)?.ino(),
            !replace
        );
    }
    Ok(())
}

#[test]
fn replay_restores_file_owner_mode_and_mtime() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let cache = fixture.0.join("cache");
    fs::write(&output, b"cached bytes")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o640))?;
    set_mtime(&output, 1_600_000_000, 123_000_000)?;
    capture(&cache, &HashSet::from([output.clone()]), &HashSet::new())?;

    fs::write(&output, b"changed bytes")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o600))?;
    set_mtime(&output, 1_700_000_000, 456_000_000)?;
    replay(&cache)?;

    let metadata = fs::metadata(&output)?;
    assert_eq!(fs::read(&output)?, b"cached bytes");
    assert_eq!(metadata.uid(), unsafe { libc::getuid() });
    assert_eq!(metadata.gid(), unsafe { libc::getgid() });
    assert_eq!(metadata.mode() & 0o7777, 0o640);
    assert_eq!(
        (metadata.mtime(), metadata.mtime_nsec()),
        (1_600_000_000, 123_000_000)
    );
    Ok(())
}

#[test]
fn replay_links_output_to_an_unchanged_dependency_inode() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let source = fixture.0.join("source");
    let output = fixture.0.join("output");
    let cache = fixture.0.join("cache");
    fs::write(&source, b"shared input")?;
    fs::hard_link(&source, &output)?;

    let metadata = fs::metadata(&source)?;
    let dependencies = HashMap::from([(
        source.clone(),
        crate::cache::DependencyKey::ContentState {
            modified: metadata
                .modified()?
                .duration_since(std::time::UNIX_EPOCH)?
                .as_nanos(),
            size: metadata.len(),
            mode: metadata.mode(),
            uid: metadata.uid(),
            gid: metadata.gid(),
            access: crate::ops::permissions::effective_access(&source)?,
            hash: crate::ops::data::hash_stream(&mut fs::File::open(&source)?)?,
        },
    )]);
    capture_with_dependencies(
        &cache,
        &HashSet::from([output.clone()]),
        &HashSet::new(),
        &dependencies,
    )?;
    fs::remove_file(&output)?;
    replay(&cache)?;

    assert_eq!(fs::read(&output)?, b"shared input");
    assert_eq!(fs::metadata(&source)?.ino(), fs::metadata(&output)?.ino());
    Ok(())
}

#[test]
fn replay_restores_extended_attributes_and_removes_uncaptured_attributes() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let cache = fixture.0.join("cache");
    fs::write(&output, b"cached")?;
    set_test_xattr(&output, b"user.incr-cache", b"original")?;
    capture(&cache, &HashSet::from([output.clone()]), &HashSet::new())?;

    set_test_xattr(&output, b"user.incr-cache", b"changed")?;
    set_test_xattr(&output, b"user.extra", b"remove me")?;
    replay(&cache)?;

    assert_eq!(get_test_xattr(&output, b"user.incr-cache")?, b"original");
    assert!(get_test_xattr(&output, b"user.extra").is_err());
    Ok(())
}

fn set_test_xattr(path: &Path, name: &[u8], value: &[u8]) -> Result<()> {
    let path = CString::new(path.as_os_str().as_bytes())?;
    let name = CString::new(name)?;
    if unsafe {
        libc::setxattr(
            path.as_ptr(),
            name.as_ptr(),
            value.as_ptr().cast(),
            value.len(),
            0,
        )
    } != 0
    {
        return Err(std::io::Error::last_os_error().into());
    }
    Ok(())
}

fn get_test_xattr(path: &Path, name: &[u8]) -> Result<Vec<u8>> {
    let path = CString::new(path.as_os_str().as_bytes())?;
    let name = CString::new(name)?;
    let length = unsafe { libc::getxattr(path.as_ptr(), name.as_ptr(), std::ptr::null_mut(), 0) };
    if length < 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    let mut value = vec![0u8; length as usize];
    let length = unsafe {
        libc::getxattr(
            path.as_ptr(),
            name.as_ptr(),
            value.as_mut_ptr().cast(),
            value.len(),
        )
    };
    if length < 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    value.truncate(length as usize);
    Ok(value)
}

fn set_mtime(path: &Path, seconds: i64, nanoseconds: i64) -> Result<()> {
    let path = CString::new(path.as_os_str().as_bytes())?;
    let times = [
        libc::timespec {
            tv_sec: 0,
            tv_nsec: libc::UTIME_OMIT,
        },
        libc::timespec {
            tv_sec: seconds,
            tv_nsec: nanoseconds as _,
        },
    ];
    if unsafe { libc::utimensat(libc::AT_FDCWD, path.as_ptr(), times.as_ptr(), 0) } != 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    Ok(())
}

#[test]
fn replay_many_readonly_files() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let cache = fixture.0.join("cache");
    let mut outputs = HashSet::new();
    for index in 0..80 {
        let path = fixture.0.join(format!("output-{index}"));
        fs::write(&path, b"cached")?;
        fs::set_permissions(&path, fs::Permissions::from_mode(0o400))?;
        outputs.insert(path);
    }
    capture(&cache, &outputs, &HashSet::new())?;
    for path in &outputs {
        fs::set_permissions(path, fs::Permissions::from_mode(0o600))?;
        fs::write(path, b"current")?;
        fs::set_permissions(path, fs::Permissions::from_mode(0o400))?;
    }
    replay(&cache)?;
    for path in outputs {
        assert_eq!(fs::read(&path)?, b"cached");
        assert_eq!(fs::metadata(path)?.permissions().mode() & 0o777, 0o400);
    }
    Ok(())
}

#[test]
fn replay_handles_parent_symlink_aliases() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let real_directory = fixture.0.join("real");
    let alias_directory = fixture.0.join("alias");
    let cache = fixture.0.join("cache");
    fs::create_dir(&real_directory)?;
    symlink(&real_directory, &alias_directory)?;
    let output = real_directory.join("output");
    let alias = alias_directory.join("output");
    fs::write(&output, b"cached")?;
    capture(&cache, &HashSet::from([output.clone(), alias]), &HashSet::new())?;
    fs::write(&output, b"changed")?;
    replay(&cache)?;
    assert_eq!(fs::read(output)?, b"cached");
    Ok(())
}

#[test]
fn replay_removes_many_readonly_directory_trees() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let cache = fixture.0.join("cache");
    let roots: HashSet<_> = (0..80)
        .map(|index| fixture.0.join(format!("tree-{index}")))
        .collect();
    capture(&cache, &roots, &HashSet::new())?;
    for root in &roots {
        let nested = root.join("nested");
        fs::create_dir_all(&nested)?;
        fs::write(nested.join("output"), b"remove")?;
        fs::set_permissions(&nested, fs::Permissions::from_mode(0o500))?;
        fs::set_permissions(root, fs::Permissions::from_mode(0o500))?;
    }
    replay(&cache)?;
    assert!(roots.iter().all(|root| !root.exists()));
    Ok(())
}

#[test]
#[ignore = "requires noninteractive sudo to create a foreign-owned fixture"]
fn replay_preserves_group_writable_file_ownership() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let cache = fixture.0.join("cache");
    fs::write(&output, b"cached")?;
    fs::set_permissions(&output, fs::Permissions::from_mode(0o460))?;
    let metadata = fs::metadata(&output)?;
    anyhow::ensure!(metadata.uid() != 0, "run this test as a non-root user");
    let status = std::process::Command::new("sudo")
        .args(["-n", "chown", &format!("0:{}", metadata.gid())])
        .arg(&output)
        .status()?;
    anyhow::ensure!(status.success(), "foreign-owned fixture setup failed");
    capture(&cache, &HashSet::from([output.clone()]), &HashSet::new())?;
    fs::write(&output, b"changed")?;
    replay(&cache)?;
    assert_eq!(fs::read(&output)?, b"cached");
    let restored = fs::metadata(output)?;
    assert_eq!(restored.uid(), 0);
    assert_eq!(restored.mode() & 0o777, 0o460);
    Ok(())
}
