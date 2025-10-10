use anyhow::{Result, anyhow};
use bincode::config::{Configuration, Fixint, LittleEndian, NoLimit};
use bincode::{Decode, Encode};
use serde::Serialize;
use serde::de::DeserializeOwned;
use std::fs::{File, OpenOptions};
use std::io::{BufReader, BufWriter, Error as IoError, ErrorKind, Write};
use std::path::Path;
use std::sync::{Mutex, OnceLock};
use time::format_description::FormatItem;
use time::macros::format_description;
use time::{OffsetDateTime, UtcOffset};

use crate::config::{CHUNK_SIZE, DEBUG, DEBUG_LOG_FILE, DEBUG_LOGS};

pub(crate) const SUCCESS_CODE: ExitCode = ExitCode(0);
pub(crate) const FAILURE_CODE: ExitCode = ExitCode(1);
pub(crate) const BROKEN_PIPE_CODE: ExitCode = ExitCode(141);

macro_rules! debug_log {
    ($($arg:tt)*) => {
        if $crate::config::DEBUG_LOGS {
            let line = format!($($arg)*);
            $crate::ops::log_line(&line);
        }
    };
}

pub(crate) use debug_log;

static LOG_FILE: OnceLock<Mutex<File>> = OnceLock::new();

#[derive(Clone, Copy, Debug)]
pub(crate) struct ExitCode(pub(crate) i32);

pub(crate) fn initialize_log_file() {
    if DEBUG_LOGS {
        LOG_FILE.get_or_init(|| {
            let file = OpenOptions::new()
                .append(true)
                .create(true)
                .open(DEBUG_LOG_FILE)
                .unwrap();
            Mutex::new(file)
        });
    }
}

pub(crate) fn log_line(line: &str) {
    const FORMAT: &[FormatItem<'_>] = format_description!("[hour]:[minute]:[second].[subsecond digits:3]");
    let offset = UtcOffset::current_local_offset().unwrap_or(UtcOffset::UTC);
    let timestamp = OffsetDateTime::now_utc()
        .to_offset(offset)
        .format(&FORMAT)
        .unwrap();
    let mut file = LOG_FILE.get().unwrap().lock().unwrap();
    writeln!(file, "[{timestamp}] {line}").unwrap();
}

pub(crate) fn path_to_string(path: &Path) -> Result<&str> {
    path.to_str().ok_or(anyhow!("Could not format path"))
}

pub(crate) fn add_data_extension(mut file_name: String) -> String {
    if !DEBUG {
        file_name.push_str(".incr");
    } else {
        file_name.push_str(".json");
    }
    file_name
}

pub(crate) fn ignore_not_found(result: Result<(), IoError>) -> Result<()> {
    match result {
        Ok(()) => Ok(()),
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(()),
        Err(error) => Err(error.into()),
    }
}

pub(crate) fn output_data<D>(data: &[u8], mut destination: D) -> Result<bool>
where
    D: Write,
{
    if data.is_empty() {
        return Ok(true);
    }
    let write_result = destination.write_all(data).and_then(|_| destination.flush());
    match write_result {
        Ok(()) => Ok(true),
        Err(error) if error.kind() == ErrorKind::BrokenPipe => Ok(false),
        Err(error) => Err(error.into()),
    }
}

pub(crate) fn encode_to_vec<T>(value: &T) -> Result<Vec<u8>>
where
    T: Encode,
{
    bincode::encode_to_vec(value, get_bincode_config()).map_err(|e| e.into())
}

pub(crate) fn encode_to_file<T>(value: &T, directory: &Path, file_name: String) -> Result<()>
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

pub(crate) fn decode_from_file<T>(directory: &Path, file_name: String) -> Result<Option<T>>
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

pub(crate) mod serialize_byte_slice {
    use base64::prelude::*;
    use serde::{Serialize, Serializer};

    pub(crate) fn serialize<S>(bytes: &Option<&[u8]>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        if let Some(bytes) = bytes
            && serializer.is_human_readable()
        {
            let encoded = BASE64_STANDARD.encode(bytes);
            encoded.serialize(serializer)
        } else {
            bytes.serialize(serializer)
        }
    }
}

pub(crate) mod serialize_byte_vec {
    use base64::prelude::*;
    use serde::de::Error as DeserializeError;
    use serde::{Deserialize, Deserializer, Serialize, Serializer};

    pub(crate) fn serialize<S>(bytes: &Vec<u8>, serializer: S) -> Result<S::Ok, S::Error>
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

    pub(crate) fn deserialize<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
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
