use anyhow::{Result, anyhow};
use bincode::config::{Configuration, Fixint, LittleEndian, NoLimit};
use bincode::{Decode, Encode};
use serde::Serialize;
use serde::de::DeserializeOwned;
use std::fs::File;
use std::io::{BufReader, BufWriter, Error as IoError, ErrorKind, Write};
use std::path::Path;

use crate::config::{CHUNK_SIZE, DEBUG};

pub const SUCCESS_CODE: ExitCode = ExitCode(0);
pub const FAILURE_CODE: ExitCode = ExitCode(1);
pub const BROKEN_PIPE_CODE: ExitCode = ExitCode(141);

#[derive(Clone, Copy, Debug)]
pub struct ExitCode(pub i32);

pub fn path_to_string(path: &Path) -> Result<&str> {
    path.to_str().ok_or(anyhow!("Could not format path"))
}

pub fn add_data_extension(mut file_name: String) -> String {
    if !DEBUG {
        file_name.push_str(".incr");
    } else {
        file_name.push_str(".json");
    }
    file_name
}

pub fn ignore_not_found(result: Result<(), IoError>) -> Result<()> {
    match result {
        Ok(()) => Ok(()),
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(()),
        Err(error) => Err(error.into()),
    }
}

pub fn output_data<D>(data: &[u8], mut destination: D) -> Result<bool>
where
    D: Write,
{
    if data.is_empty() {
        return Ok(true);
    }
    if let Err(error) = destination.write_all(data) {
        if error.kind() == ErrorKind::BrokenPipe {
            return Ok(false);
        }
        return Err(error.into());
    }
    if let Err(error) = destination.flush() {
        if error.kind() == ErrorKind::BrokenPipe {
            return Ok(false);
        }
        return Err(error.into());
    }
    Ok(true)
}

pub fn encode_to_vec<T>(value: &T) -> Result<Vec<u8>>
where
    T: Encode,
{
    bincode::encode_to_vec(value, get_bincode_config()).map_err(|e| e.into())
}

pub fn encode_to_file<T>(value: &T, directory: &Path, file_name: String) -> Result<()>
where
    T: Encode + Serialize,
{
    let file_name = add_data_extension(file_name);
    let file = File::create(directory.join(file_name))?;
    let mut file_writer = BufWriter::with_capacity(CHUNK_SIZE, file);
    if !DEBUG {
        bincode::encode_into_std_write(value, &mut file_writer, get_bincode_config())?;
    } else {
        serde_json::to_writer_pretty(&mut file_writer, value)?;
    }
    file_writer.flush()?;
    Ok(())
}

pub fn decode_from_file<T>(directory: &Path, file_name: String) -> Result<Option<T>>
where
    T: Decode<()> + DeserializeOwned,
{
    let file_name = add_data_extension(file_name);
    let file = match File::open(directory.join(file_name)) {
        Ok(file) => file,
        Err(error) if error.kind() == ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(error.into()),
    };

    let mut file_reader = BufReader::with_capacity(CHUNK_SIZE, file);
    let value = if !DEBUG {
        match bincode::decode_from_std_read(&mut file_reader, get_bincode_config()) {
            Ok(value) => value,
            Err(_) => return Ok(None),
        }
    } else {
        match serde_json::from_reader(file_reader) {
            Ok(value) => value,
            Err(_) => return Ok(None),
        }
    };

    Ok(Some(value))
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
            BASE64_STANDARD.decode(encoded).map_err(DeserializeError::custom)
        } else {
            Vec::<u8>::deserialize(deserializer)
        }
    }
}
