#!/usr/bin/env python3

import base64
from dataclasses import dataclass
from enum import IntEnum
import hashlib
from io import BytesIO
import json
from json import JSONDecodeError
import os
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Thread
import time
from typing import Any, IO, Optional

import file_trace
from file_trace import Context

class CacheEncoding(IntEnum):
    """
    The encoding used to save stdin, stdout, and stderr bytes in cache files. UTF-8 is mainly
    useful for debugging but may not support all bytes while base64 can represent all bytes.
    """
    UTF8 = 0
    Base64 = 1

@dataclass(kw_only=True)
class CommandOutput:
    """The output of a shell command not including file modifications."""
    return_code: int
    stdout: bytes
    stderr: bytes
    read_dependencies: dict[str, str]

@dataclass(kw_only=True)
class CacheData:
    """The cached output of a shell command not including file modifications."""
    return_code: int
    stdout: bytes
    stderr: bytes
    read_dependencies: dict[str, str]
    key_data: Optional[dict[str, Any]]

    @staticmethod
    def from_command(command_output: CommandOutput, key_data: dict[str, Any]) -> 'CacheData':
        return CacheData(
            return_code=command_output.return_code,
            stdout=command_output.stdout,
            stderr=command_output.stderr,
            read_dependencies=command_output.read_dependencies,
            key_data=key_data,
        )

    def serialize(self) -> str:
        data = {
            "return_code": self.return_code,
            "stdout": encode_bytes(self.stdout),
            "stderr": encode_bytes(self.stderr),
            "read_dependencies": self.read_dependencies,
        }
        if self.key_data is not None:
            data["key_data"] = self.key_data
        return json.dumps(data, indent=4)

    @staticmethod
    def deserialize(string: str) -> Optional['CacheData']:
        try:
            data: dict[str, Any] = json.loads(string)
            for property in ("return_code", "stdout", "stderr", "read_dependencies"):
                if property not in data:
                    return None
            return CacheData(
                return_code=data["return_code"],
                stdout=decode_bytes(data["stdout"]),
                stderr=decode_bytes(data["stderr"]),
                read_dependencies=data["read_dependencies"],
                key_data=data.get("key_data"),
            )
        except JSONDecodeError:
            pass
        return None

# Constant parameters
CACHE_ENCODING: CacheEncoding = CacheEncoding.UTF8
STRACE_COMMAND: str = "strace"
TRY_COMMAND: str = "python/try.sh"
CACHE_DIRECTORY: Path = Path("cache")
CACHE_FILE: str = "data.json"
TRY_DIRECTORY: str = "sandbox"

PATH_DNE: str = "<PATH_DOES_NOT_EXIST>"
CHUNK_SIZE: int = 65536
SUDO_REMOVE: bool = True

def encode_bytes(data: bytes) -> str:
    """Encodes raw bytes as a string which is storable in a JSON object."""
    if CACHE_ENCODING == CacheEncoding.UTF8:
        return data.decode("utf-8")
    elif CACHE_ENCODING == CacheEncoding.Base64:
        return base64.b64encode(data).decode("utf-8")
    raise RuntimeError("Invalid encoding mode")

def decode_bytes(data: str) -> bytes:
    """Decodes a data string stored in a JSON object back into bytes."""
    if CACHE_ENCODING == CacheEncoding.UTF8:
        return data.encode("utf-8")
    elif CACHE_ENCODING == CacheEncoding.Base64:
        return base64.b64decode(data)
    raise RuntimeError("Invalid encoding mode")

def read_stream(stream: IO[bytes], destination: IO[bytes], record: BytesIO):
    """Reads data from the stream while writing it to the destination and the record."""
    try:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            if chunk:
                destination.write(chunk)
                destination.flush()
                record.write(chunk)
    finally:
        try:
            stream.close()
        except Exception:
            pass

def write_stream(stream: IO[bytes], data: bytes):
    """Writes data to the stream while it has capacity."""
    try:
        data_view = memoryview(data)
        total_length = len(data_view)
        sent_count = 0
        while sent_count < total_length:
            count = stream.write(data_view[sent_count:sent_count + CHUNK_SIZE])
            sent_count += count if count is not None else 0
        stream.flush()
    finally:
        try:
            stream.close()
        except Exception:
            pass

def compute_file_hash(path_name: str) -> Optional[str]:
    """Computes the SHA256 hash of a file if it exists."""
    path = Path(path_name)
    if path.is_dir():
        return None
    if not path.exists():
        return PATH_DNE

    hash = hashlib.sha256()
    with open(path, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)
            if not chunk:
                break
            hash.update(chunk)

    return hash.hexdigest()

def generate_command_hash(
    args: list[str], 
    stdin: Optional[bytes],
    env: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    """Converts the command input into a hash used as the cache key."""
    data = {
        "args": args,
        "stdin": encode_bytes(stdin) if stdin is not None else None,
        "env": env,
    }
    hash = hashlib.sha256()
    hash.update(json.dumps(data, sort_keys=True).encode("utf-8"))
    return (hash.hexdigest(), data)

def read_cache_data(command_directory: Path) -> Optional[CacheData]:
    """Reads and parses the cache file in a command directory if it exists."""
    try:
        with open(command_directory / CACHE_FILE, "r") as file:
            return CacheData.deserialize(file.read())
    except FileNotFoundError:
        pass
    return None

def check_read_dependencies(dependencies: dict[str, str]) -> bool:
    """Checks if the content hash of each read dependency matches the cached hash."""
    return False

def run_command(hash: str, command_directory: Path, args: list[str], stdin: Optional[bytes]) -> CommandOutput:
    """Runs the command in a subprocess and collects the outputs."""
    trace_file = f"trace_{hash}_{time.time_ns()}.txt"
    try_directory = command_directory / TRY_DIRECTORY
    trace_command = [
        STRACE_COMMAND, "-y", "-f", "--seccomp-bpf", "--trace=fork,clone,%file",
        "-o", f"/tmp/{trace_file}", "env", "-i", "bash", "-c", " ".join(args),
    ]
    try_command = [TRY_COMMAND, "-D", str(try_directory)] + trace_command

    try_directory.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        try_command,
        stdin=subprocess.PIPE if stdin is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    stdout = BytesIO()
    stderr = BytesIO()
    read_dependencies = {}

    # Write the input data to the process
    stdin_writer = None
    if stdin is not None:
        stdin_writer = Thread(
            target=write_stream,
            args=(process.stdin, stdin),
            daemon=True,
        )
        stdin_writer.start()

    # Read the output data from the process
    stdout_reader = Thread(
        target=read_stream,
        args=(process.stdout, sys.stdout.buffer, stdout),
        daemon=True,
    )
    stderr_reader = Thread(
        target=read_stream,
        args=(process.stderr, sys.stderr.buffer, stderr),
        daemon=True,
    )
    stdout_reader.start()
    stderr_reader.start()

    # Wait for the process to exit
    return_code = process.wait()
    if stdin_writer is not None:
        stdin_writer.join()
    stdout_reader.join()
    stderr_reader.join()

    # Parse file system dependencies from trace
    with open(try_directory / f"upperdir/tmp/{trace_file}", "r") as file:
        data = file.readlines()
        context = Context()
        context.set_dir(os.getcwd())
        read_set, write_set = file_trace.parse_and_gather_cmd_rw_sets(data, context)

        for path in read_set:
            file_hash = compute_file_hash(path)
            if file_hash is not None:
                read_dependencies[path] = file_hash

    # Commit file system changes
    subprocess.run([TRY_COMMAND, "commit", str(try_directory)], check=True)

    return CommandOutput(
        return_code=return_code,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
        read_dependencies=read_dependencies,
    )

def main():
    if len(sys.argv) == 1:
        sys.exit()

    # Read the inputs and generate the cache key
    args = sys.argv[1:]
    stdin = None
    if not sys.stdin.isatty():
        stdin = sys.stdin.buffer.read()
    hash, key_data = generate_command_hash(args, stdin, dict(os.environ))
    command_directory = CACHE_DIRECTORY / hash

    # Output the cached data if it is valid
    cache_data = read_cache_data(command_directory)
    if cache_data is not None and check_read_dependencies(cache_data.read_dependencies):
        sys.stdout.buffer.write(cache_data.stdout)
        sys.stderr.buffer.write(cache_data.stderr)
        sys.stdout.buffer.flush()
        sys.stderr.buffer.flush()
        sys.exit(cache_data.return_code)

    # Set up the cache directory
    if SUDO_REMOVE:
        subprocess.run(["sudo", "rm", "-rf", str(command_directory)], check=True)
    else:
        shutil.rmtree(command_directory)
    command_directory.mkdir(parents=True, exist_ok=True)

    # Run the command and cache the outputs
    result = run_command(hash, command_directory, args, stdin)
    cache_data = CacheData.from_command(result, key_data)
    with open(command_directory / CACHE_FILE, "w") as file:
        file.write(cache_data.serialize())

    sys.exit(result.return_code)

if __name__ == "__main__":
    main()