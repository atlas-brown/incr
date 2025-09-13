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
import subprocess
import sys
from threading import Thread
from typing import Any, IO, Optional

class CacheEncoding(IntEnum):
    """
    The encoding used to save stdin, stdout, and stderr bytes in cache files. UTF-8 is mainly
    useful for debugging but may not support all bytes while base64 can represent all bytes.
    """
    UTF8 = 0
    Base64 = 1

@dataclass
class CommandOutput:
    """The output of a shell command."""
    return_code: int
    stdout: bytes
    stderr: bytes

# Constant parameters
CACHE_ENCODING: CacheEncoding = CacheEncoding.UTF8
CACHE_DIRECTORY: Path = Path("outputs")
STREAM_CHUNK_SIZE: int = 65536

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
        for chunk in iter(lambda: stream.read(STREAM_CHUNK_SIZE), b""):
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
            count = stream.write(data_view[sent_count:sent_count + STREAM_CHUNK_SIZE])
            sent_count += count if count is not None else 0
        stream.flush()
    finally:
        try:
            stream.close()
        except Exception:
            pass

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

def run_command(args: list[str], stdin: Optional[bytes]) -> CommandOutput:
    """Runs the command in a subprocess and collects the outputs."""
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE if stdin is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    stdout = BytesIO()
    stderr = BytesIO()

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

    return CommandOutput(return_code, stdout.getvalue(), stderr.getvalue())

def main():
    if len(sys.argv) == 1:
        sys.exit()

    # Read the inputs and generate the cache key
    args = sys.argv[1:]
    stdin = None
    if not sys.stdin.isatty():
        stdin = sys.stdin.buffer.read()
    hash, key_data = generate_command_hash(args, stdin, dict(os.environ))
    cache_file = CACHE_DIRECTORY / f"{hash}.json"

    # Read the cached data if it exists
    cache_data = None
    try:
        with open(cache_file, "r") as file:
            cache_data = json.load(file)
            assert "return_code" in cache_data
            assert "stdout" in cache_data
            assert "stderr" in cache_data
    except FileNotFoundError:
        pass
    except JSONDecodeError:
        pass

    # Output the cached data if it exists
    if cache_data is not None:
        stdout, stderr = (decode_bytes(cache_data["stdout"]), decode_bytes(cache_data["stderr"]))
        sys.stdout.buffer.write(stdout)
        sys.stderr.buffer.write(stderr)
        sys.stdout.buffer.flush()
        sys.stderr.buffer.flush()
        sys.exit(cache_data["return_code"])

    # Run the command and cache the outputs
    result = run_command(args, stdin)
    with open(cache_file, "w") as file:
        data = {
            "key_data": key_data,
            "return_code": result.return_code,
            "stdout": encode_bytes(result.stdout),
            "stderr": encode_bytes(result.stderr),
        }
        file.write(json.dumps(data, indent=4))

    sys.exit(result.return_code)

if __name__ == "__main__":
    main()