#!/usr/bin/env python3

import base64
import hashlib
from io import BytesIO
import json
from json import JSONDecodeError
from pathlib import Path
import subprocess
import sys
from threading import Thread
from typing import Any, IO, Optional

CHUNK_SIZE: int = 65536
CACHE_DIRECTORY: Path = Path("outputs")

def generate_command_hash(args: list[str], input: Optional[bytes]):
    encoded_input = None
    if input is not None:
        encoded_input = base64.b64encode(input).decode("utf-8")
    data = {
        "args": args,
        "encoded_input": encoded_input,
    }
    hash = hashlib.sha256()
    hash.update(json.dumps(data, sort_keys=True).encode("utf-8"))
    return hash.hexdigest()

def read_stream(stream: IO[bytes], destination: IO[bytes], record: BytesIO):
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

def run_command(args: list[str], input: Optional[bytes]) -> dict[str, Any]:
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    captured_stdout = BytesIO()
    captured_stderr = BytesIO()

    stdin_writer = None
    if input is not None:
        stdin_writer = Thread(
            target=write_stream,
            args=(process.stdin, input),
            daemon=True,
        )
        stdin_writer.start()

    stdout_reader = Thread(
        target=read_stream,
        args=(process.stdout, sys.stdout.buffer, captured_stdout),
        daemon=True,
    )
    stderr_reader = Thread(
        target=read_stream,
        args=(process.stderr, sys.stderr.buffer, captured_stderr),
        daemon=True,
    )
    stdout_reader.start()
    stderr_reader.start()

    return_code = process.wait()
    if stdin_writer is not None:
        stdin_writer.join()
    stdout_reader.join()
    stderr_reader.join()

    return {
        "return_code": return_code,
        "encoded_stdout": base64.b64encode(captured_stdout.getvalue()).decode("utf-8"),
        "encoded_stderr": base64.b64encode(captured_stderr.getvalue()).decode("utf-8"),
    }

def main():
    if len(sys.argv) == 1:
        sys.exit()

    args = sys.argv[1:]
    input = None
    if not sys.stdin.isatty():
        input = sys.stdin.buffer.read()
    hash = generate_command_hash(args, input)
    cache_file = CACHE_DIRECTORY / f"{hash}.json"

    cache_data = None
    try:
        with open(cache_file, "r") as file:
            cache_data = json.load(file)
    except FileNotFoundError:
        pass
    except JSONDecodeError:
        pass

    if cache_data is not None:
        stdout_data = base64.b64decode(cache_data["encoded_stdout"])
        stderr_data = base64.b64decode(cache_data["encoded_stderr"])
        sys.stdout.buffer.write(stdout_data)
        sys.stderr.buffer.write(stderr_data)
        sys.stdout.buffer.flush()
        sys.stderr.buffer.flush()
        sys.exit(cache_data["return_code"])

    result = run_command(args, input)
    with open(cache_file, "w") as file:
        file.write(json.dumps(result))
    sys.exit(result["return_code"])

if __name__ == "__main__":
    main()