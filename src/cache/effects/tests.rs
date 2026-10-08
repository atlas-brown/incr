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

#[test]
fn invalid_hard_link_is_rejected_before_deletion() -> Result<()> {
    let fixture = TestDirectory::create()?;
    let output = fixture.0.join("output");
    let directory = fixture.0.join("directory");
    let cache = fixture.0.join("cache");
    fs::create_dir(&cache)?;
    fs::write(&output, b"preserve")?;
    let manifest = Manifest {
        version: 3,
        entries: vec![
            Entry {
                path: output.clone(),
                effect: Effect::Missing,
            },
            Entry {
                path: directory.clone(),
                effect: Effect::Directory { mode: 0o755 },
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
        version: 3,
        entries: vec![
            Entry {
                path: output.clone(),
                effect: Effect::Directory { mode: 0o500 },
            },
            Entry {
                path: output.join("blocker/child"),
                effect: Effect::Symlink {
                    target: PathBuf::from("target"),
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
        version: 3,
        entries: vec![Entry {
            path: output.clone(),
            effect: Effect::Directory { mode: 0o500 },
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
