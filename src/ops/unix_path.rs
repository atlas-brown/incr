//! Decode Observe JSON paths without replacing arbitrary Unix filename bytes.
use serde::{Deserialize, Deserializer};
use std::ffi::OsString;
use std::os::unix::ffi::{OsStrExt, OsStringExt};
use std::path::PathBuf;

pub fn deserialize<'input, Input: Deserializer<'input>>(
    deserializer: Input,
) -> Result<PathBuf, Input::Error> {
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum Representation {
        Text(String),
        Bytes { bytes: Vec<u8> },
    }
    let path = match Representation::deserialize(deserializer)? {
        Representation::Text(text) => PathBuf::from(text),
        Representation::Bytes { bytes } => PathBuf::from(OsString::from_vec(bytes)),
    };
    if path.as_os_str().as_bytes().contains(&0) {
        return Err(serde::de::Error::custom("path contains a null byte"));
    }
    Ok(path)
}
