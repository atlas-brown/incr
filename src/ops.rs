use anyhow::{Result, anyhow};
use bincode::config::{Configuration, Fixint, LittleEndian, NoLimit};
use bincode::{Decode, Encode};
use std::io::{Error as IoError, ErrorKind};
use std::path::Path;

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

pub fn encode_to_vec<T>(value: T) -> Result<Vec<u8>>
where
    T: Encode,
{
    bincode::encode_to_vec(value, get_bincode_config()).map_err(|e| e.into())
}

fn get_bincode_config() -> Configuration<LittleEndian, Fixint, NoLimit> {
    bincode::config::standard()
        .with_little_endian()
        .with_fixed_int_encoding()
}

pub mod serialize_byte_slice {
    use base64::prelude::*;
    use serde::{Serialize, Serializer};

    pub fn serialize<S>(bytes: &[u8], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        if serializer.is_human_readable() {
            let encoded = BASE64_STANDARD.encode(bytes);
            encoded.serialize(serializer)
        } else {
            bytes.serialize(serializer)
        }
    }
}

pub mod serialize_byte_vec {
    use base64::prelude::*;
    use serde::de::Error as DeserializeError;
    use serde::{Deserialize, Deserializer, Serialize, Serializer};

    pub fn serialize<S>(bytes: &Vec<u8>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        if serializer.is_human_readable() {
            let encoded = BASE64_STANDARD.encode(bytes);
            encoded.serialize(serializer)
        } else {
            bytes.serialize(serializer)
        }
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
    where
        D: Deserializer<'de>,
    {
        if deserializer.is_human_readable() {
            let encoded = String::deserialize(deserializer)?;
            BASE64_STANDARD
                .decode(encoded)
                .map_err(DeserializeError::custom)
        } else {
            Vec::<u8>::deserialize(deserializer)
        }
    }
}
