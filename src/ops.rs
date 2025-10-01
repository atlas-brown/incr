use anyhow::{Result, anyhow};
use sha2::{Digest, Sha256};
use std::io::{Error as IoError, ErrorKind};
use std::path::Path;

pub fn hash_string(string: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(string);
    format!("{:x}", hasher.finalize())
}

pub fn path_to_string(path: &Path) -> Result<&str> {
    path.to_str().ok_or(anyhow!("Could not format path"))
}

pub fn ignore_not_found(result: Result<(), IoError>) -> Result<()> {
    match result {
        Ok(()) => Ok(()),
        Err(error) => match error.kind() {
            ErrorKind::NotFound => Ok(()),
            _ => Err(error.into()),
        },
    }
}
