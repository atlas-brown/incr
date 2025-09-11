#!/usr/bin/env python3

import base64
import hashlib
from io import BytesIO
import json
from json import JSONDecodeError
import os
from pathlib import Path
import selectors
import subprocess
import sys
from typing import Any, Optional

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

def run_command(args: list[str], input: Optional[bytes]) -> dict[str, Any]:
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    if input is not None:
        try:
            process.stdin.write(input)
            process.stdin.close()
        except Exception as exception:
            print("Error writing stdin:", exception, file=sys.stderr)

    captured_stdout = BytesIO()
    captured_stderr = BytesIO()
    os.set_blocking(process.stdout.fileno(), False)
    os.set_blocking(process.stderr.fileno(), False)

    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, data=(sys.stdout.buffer, captured_stdout))
    selector.register(process.stderr, selectors.EVENT_READ, data=(sys.stderr.buffer, captured_stderr))

    while selector.get_map():
        for key, _ in selector.select():
            destination, record = key.data
            data = key.fileobj.read()
            if data:
                destination.write(data)
                destination.flush()
                record.write(data)
            else:
                selector.unregister(key.fileobj)
                key.fileobj.close()

    return_code = process.wait()
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