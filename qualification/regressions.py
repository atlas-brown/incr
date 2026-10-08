#!/usr/bin/env python3
"""Focused behavioral regressions. Every invocation has a process-tree deadline."""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
INCR = ROOT / "target/release/incr"
OBSERVE = ROOT.parent / "observe/target/release/observe"
MODE = []


class Regressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=ROOT / "qualification/.work")
        self.work = Path(self.temp.name)
        self.cache = self.work / "cache"
        self.cache.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, args, stdin=b"", expected=0):
        result = run([str(INCR), *MODE, "--try", str(ROOT / "src/scripts/try.sh"),
                      "--observe", str(OBSERVE), "--cache", str(self.cache), "--", *args],
                     stdin=stdin, cwd=self.work, timeout=5)
        self.assertFalse(result["timeout"], result)
        self.assertFalse(result["leaked_descendants"], result)
        self.assertFalse(result["remaining_descendants"], result)
        self.assertEqual(result["returncode"], expected, result)
        return result

    def shell(self, command, **kwargs):
        return self.invoke(["bash", "-c", command], **kwargs)

    def test_parallel_script_wrapper(self):
        import shlex
        script = self.work / "script.sh"
        original = b"printf '%s\\n' \"$1\" | sort\n"
        script.write_bytes(original)
        stamp = script.stat().st_mtime_ns
        env = dict(os.environ, INCR_CACHE_DIR=str(self.cache), INCR_OBSERVE="1",
                   INCR_SYS_PATH=str(INCR), INCR_OBSERVE_PATH=str(OBSERVE),
                   INCR_PYTHON=str(ROOT / "qualification/.venv/bin/python"))
        command = [str(ROOT / "incr.sh"), str(script)]
        shell = shlex.join(command + ["one"]) + " > one & p1=$!; "
        shell += shlex.join(command + ["two"]) + " > two & p2=$!; wait $p1; a=$?; wait $p2; b=$?; test $a = 0 -a $b = 0"
        result = run(["bash", "-c", shell], cwd=self.work, env=env, timeout=5)
        self.assertFalse(result["timeout"], result)
        self.assertEqual((result["returncode"], result["stderr"]), (0, ""), result)
        self.assertEqual((self.work / "one").read_text(), "one\n")
        self.assertEqual((self.work / "two").read_text(), "two\n")
        self.assertEqual(script.read_bytes(), original)
        self.assertEqual(script.stat().st_mtime_ns, stamp)
        self.assertFalse(list(self.cache.glob("incr-script.*")))

    def test_wrapper_preserves_old_marker_text(self):
        script = self.work / "marker.sh"
        source = b"printf '%s\\n' incr__no_op | rev\n"
        script.write_bytes(source)
        environment = dict(os.environ, INCR_CACHE_DIR=str(self.cache), INCR_OBSERVE="1",
                           INCR_PYTHON=str(ROOT / "qualification/.venv/bin/python"))
        result = run([str(ROOT / "incr.sh"), "-b", str(script)], cwd=self.work,
                     env=environment, timeout=5)
        self.assertFalse(result["timeout"], result)
        self.assertFalse(result["leaked_descendants"], result)
        self.assertEqual((result["returncode"], result["stdout"], result["stderr"]),
                         (0, "po_on__rcni\n", ""), result)
        self.assertEqual(script.read_bytes(), source)

    def test_wrapper_readonly_source_and_argv0(self):
        script = self.work / "script with spaces.sh"
        original = b'printf "%s\\n" "$0" "$1" | cat\n'
        script.write_bytes(original)
        script.chmod(0o444)
        stamp = script.stat().st_mtime_ns
        env = dict(os.environ, INCR_CACHE_DIR=str(self.cache), INCR_OBSERVE="1",
                   INCR_PYTHON=str(ROOT / "qualification/.venv/bin/python"))
        result = run([str(ROOT / "incr.sh"), "-b", str(script), "argument with spaces"],
                     cwd=self.work, env=env, timeout=5)
        self.assertEqual((result["returncode"], result["stdout"], result["stderr"]),
                         (0, str(script) + "\nargument with spaces\n", ""), result)
        self.assertEqual((script.read_bytes(), script.stat().st_mtime_ns), (original, stamp))
        self.assertFalse(list(self.cache.glob("incr-script.*")))

    def test_umask_invalidation(self):
        import shlex
        command = [str(INCR), *MODE, "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--",
                   "bash", "-c", "printf content > output"]
        for mask, expected in [("022", 0o644), ("077", 0o600)]:
            result = run(["bash", "-c", "umask " + mask + "; exec " + shlex.join(command)],
                         cwd=self.work, timeout=5)
            self.assertEqual(result["returncode"], 0, result)
            output = self.work / "output"
            self.assertEqual(output.stat().st_mode & 0o777, expected)
            output.unlink()

    def test_terminal_input_is_preserved(self):
        import pty
        import subprocess
        master, slave = pty.openpty()
        command = [str(INCR), *MODE, "--observe", str(OBSERVE), "--cache", str(self.cache),
                   "--", "python3", "-c",
                   "import os,sys; print(os.isatty(0)); print(sys.stdin.readline().strip())"]
        try:
            with subprocess.Popen(command, stdin=slave, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, cwd=self.work) as process:
                os.write(master, b"terminal input\n")
                try:
                    output, errors = process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    self.fail("terminal invocation exceeded deadline")
                self.assertEqual((process.returncode, output, errors),
                                 (0, b"True\nterminal input\n", b""))
        finally:
            os.close(master)
            os.close(slave)

    def test_adversarial_filename_round_trips(self):
        names = ["space name", "single'quote", 'double"quote', "back\\slash", "line\nbreak",
                 "tab\tname", "snow-雪", "replacement-�", "$(touch injected)",
                 "semi;colon", "-leading", "literal (deleted)", "literal <pipe:[42]>"]
        command = ["python3", "-c",
                   "import pathlib,sys; source=pathlib.Path(sys.argv[1]); "
                   "data=source.read_bytes(); pathlib.Path(sys.argv[2]).write_bytes(data); "
                   "sys.stdout.buffer.write(data)"]
        for index, name in enumerate(names):
            with self.subTest(name=name):
                source = self.work / name
                destination = self.work / (name + ".output")
                for generation in range(3):
                    payload = f"{index}:{generation // 2}\n".encode()
                    if not source.exists() or source.read_bytes() != payload:
                        source.write_bytes(payload)
                    result = self.invoke([*command, str(source), str(destination)])
                    self.assertEqual(result["stdout"].encode(), payload)
                    self.assertEqual(destination.read_bytes(), payload)
                    destination.unlink()
        self.assertFalse((self.work / "injected").exists())

    def test_non_utf8_internal_path(self):
        path = os.fsencode(self.work) + b"/file-\xff"
        command = ["python3", "-c", "import os; print(open(b'file-\\xff').read())"]
        for value in [b"one", b"two"]:
            with open(path, "wb") as stream:
                stream.write(value)
            self.assertEqual(self.invoke(command)["stdout"], value.decode() + "\n")
        self.invoke(["python3", "-c", "import os; os.symlink(b'file-\\xff', 'link')"])
        self.assertEqual(os.readlink(os.fsencode(self.work / "link")), b"file-\xff")

    def test_byte_outputs_do_not_alias_unicode_neighbors(self):
        byte_path = os.fsencode(self.work) + b"/output-\xff"
        unicode_path = self.work / "output-�"
        unicode_path.write_bytes(b"unrelated")
        program = "import sys; open(b'output-\\xff','wb').write(sys.stdin.buffer.read())"
        for payload in (b"first", b"second", b"second"):
            self.invoke(["python3", "-c", program], stdin=payload)
            with open(byte_path, "rb") as stream:
                self.assertEqual(stream.read(), payload)
            self.assertEqual(unicode_path.read_bytes(), b"unrelated")

    def test_corrupt_cached_stream(self):
        command = ["cat", "input"]
        (self.work / "input").write_text("expected\n")
        self.invoke(command)
        cached = list(self.cache.rglob("stdout.incr"))
        self.assertTrue(cached)
        for path in cached:
            path.write_bytes(b"corrupt")
        self.assertEqual(self.invoke(command)["stdout"], "expected\n")

    def test_shadowed_system_tool(self):
        from unittest.mock import patch
        directory = self.work / "bin"
        directory.mkdir()
        tool = directory / "rev"
        tool.write_text("#!/bin/sh\ncat input\n")
        tool.chmod(0o755)
        with patch.dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH']):
            for value in ["first", "second"]:
                (self.work / "input").write_text(value)
                self.assertEqual(self.invoke(["rev"])["stdout"], value)

    def test_executable_name_is_a_literal_argument(self):
        for name in ["tool with spaces", "tool'quote", "tool\\slash"]:
            tool = self.work / name
            tool.write_text("#!/bin/sh\nprintf literal")
            tool.chmod(0o755)
            self.assertEqual(self.invoke([str(tool)])["stdout"], "literal")

    def test_executable_with_byte_target(self):
        target = os.fsencode(self.work) + b"/tool-\xff"
        with open(target, "wb") as stream:
            stream.write(b"#!/bin/sh\nprintf byte-target")
        os.chmod(target, 0o755)
        tool = self.work / "tool"
        os.symlink(target, os.fsencode(tool))
        self.assertEqual(self.invoke([str(tool)])["stdout"], "byte-target")

    def test_working_directory_bytes_are_distinct(self):
        original_directory = self.work
        try:
            for suffix in [b"\xff", b"\xfe"]:
                directory = os.fsencode(original_directory) + b"/cwd-" + suffix
                os.mkdir(directory)
                self.work = Path(os.fsdecode(directory))
                result = self.invoke(["python3", "-c", "import os; print(os.getcwdb().hex())"])
                self.assertEqual(result["stdout"], os.path.realpath(directory).hex() + "\n")
            self.assertEqual(len(list(self.cache.glob("batch_*"))), 2)
        finally:
            self.work = original_directory

    def test_pwd_environment_is_a_dependency(self):
        from unittest.mock import patch
        command = ["python3", "-c", "import os,time; time.sleep(.03); print(os.environ['PWD'])"]
        for value in ["first environment value", "second environment value"]:
            with patch.dict(os.environ, PWD=value):
                self.assertEqual(self.invoke(command)["stdout"], value + "\n")

    def test_executable_replacement(self):
        from unittest.mock import patch
        directory = self.work / "bin"
        directory.mkdir()
        tool = directory / "rev"
        tool.symlink_to(shutil.which("rev"))
        with patch.dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH']):
            self.assertEqual(self.invoke(["rev"], stdin=b"one\n")["stdout"], "eno\n")
            tool.unlink()
            tool.write_text("#!/bin/sh\nprintf replacement\n")
            tool.chmod(0o755)
            self.assertEqual(self.invoke(["rev"], stdin=b"one\n")["stdout"], "replacement")

    def test_metadata_write_preserves_changed_content(self):
        path = self.work / "file"
        command = ["python3", "-c", "import os; os.chmod('file', 0o600)"]
        for content in (b"first", b"second", b"second"):
            path.write_bytes(content)
            path.chmod(0o640)
            self.invoke(command)
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_path_truncate_preserves_changed_prefix(self):
        path = self.work / "file"
        command = ["python3", "-c", "import os; os.truncate('file', 3)"]
        for content in (b"first", b"second", b"second"):
            path.write_bytes(content)
            self.invoke(command)
            self.assertEqual(path.read_bytes(), content[:3])

    def test_relative_cache_without_try_override(self):
        result = run([str(INCR), "--cache", "relative-cache", "--observe", str(OBSERVE),
                      "--", "cat"], stdin=b"relative cache", cwd=self.work, timeout=5)
        self.assertEqual((result["returncode"], result["stdout"]), (0, "relative cache"), result)
        self.assertTrue((self.work / "relative-cache").is_dir())

    def test_failed_metadata_write_invalidation(self):
        command = ["python3", "-c", "import os; os.chmod('missing-mode', 0o600)"]
        self.invoke(command, expected=1)
        path = self.work / "missing-mode"
        path.write_bytes(b"new input")
        self.invoke(command)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.read_bytes(), b"new input")

    def test_extended_attribute_invalidation(self):
        path = self.work / "attribute-file"
        path.write_bytes(b"content")
        command = ["python3", "-c", "import os; print(os.getxattr('attribute-file', 'user.incr-test').decode())"]
        for value in (b"first", b"second", b"second"):
            os.setxattr(path, "user.incr-test", value)
            self.assertEqual(self.invoke(command)["stdout"], value.decode() + "\n")

    def test_slow_stdin_spill_and_reuse(self):
        import hashlib
        content = bytes(range(251)) * 25000
        command = ["python3", "-c", "import hashlib,sys,time; time.sleep(.15); print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())"]
        expected = hashlib.sha256(content).hexdigest() + "\n"
        self.assertEqual(self.invoke(command, stdin=content)["stdout"], expected)
        entries = {path: path.stat().st_mtime_ns for path in self.cache.rglob("data.incr")}
        self.assertTrue(entries)
        self.assertEqual(self.invoke(command, stdin=content)["stdout"], expected)
        self.assertEqual({path: path.stat().st_mtime_ns for path in entries}, entries)
        self.assertFalse(list(self.cache.glob("buffer-*.tmp")))

    def test_failed_tracer_launch_cleans_runtime(self):
        result = run([str(INCR), "-f", "--cache", str(self.cache),
                      "--observe", str(self.work / "missing-observe"), "--", "cat"],
                     stdin=b"input", cwd=self.work, timeout=5)
        self.assertEqual(result["returncode"], 1, result)
        self.assertFalse(result["timeout"], result)
        self.assertFalse(result["leaked_descendants"], result)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_creation_collision(self):
        self.invoke(["mkdir", "empty"])
        self.invoke(["mkdir", "empty"], expected=1)
        self.invoke(["ln", "-s", "missing", "link"])
        self.invoke(["ln", "-s", "missing", "link"], expected=1)
        self.shell("set -C; printf data > exclusive")
        self.shell("set -C; printf data > exclusive", expected=1)

    def test_partial_write_dependency(self):
        path = self.work / "file"
        command = ["python3", "-c", "import os; fd=os.open('file',os.O_WRONLY); os.write(fd,b'X'); os.close(fd)"]
        for value in ["one", "two"]:
            path.write_text(value)
            self.invoke(command)
            self.assertEqual(path.read_text(), "X" + value[1:])

    def test_empty_directory_replay(self):
        self.invoke(["mkdir", "empty"])
        (self.work / "empty").rmdir()
        self.invoke(["mkdir", "empty"])
        self.assertTrue((self.work / "empty").is_dir())

    def test_copy_invalidation(self):
        source = self.work / "source"
        dest = self.work / "dest"
        source.write_text("first")
        for _ in range(2):
            self.invoke(["cp", "source", "dest"])
            self.assertEqual(dest.read_text(), "first")
            dest.unlink()
        source.write_text("second")
        self.invoke(["cp", "source", "dest"])
        self.assertEqual(dest.read_text(), "second")

    def test_tmp_input_invalidation(self):
        with tempfile.TemporaryDirectory(prefix="incr-input-") as tmp:
            source = Path(tmp) / "input"
            source.write_text("first")
            self.assertEqual(self.invoke(["cat", str(source)])["stdout"], "first")
            source.write_text("second")
            self.assertEqual(self.invoke(["cat", str(source)])["stdout"], "second")

    def test_append_reexecution(self):
        dest = self.work / "dest"
        dest.write_text("start\n")
        for _ in range(2):
            self.shell("printf 'next\\n' >> dest")
        self.assertEqual(dest.read_text(), "start\nnext\nnext\n")

    def test_symlink_replay(self):
        for _ in range(2):
            self.shell("ln -s missing link")
            self.assertTrue((self.work / "link").is_symlink())
            self.assertEqual(os.readlink(self.work / "link"), "missing")
            (self.work / "link").unlink()

    def test_delete_replay(self):
        for _ in range(2):
            (self.work / "victim").write_text("data")
            self.shell("rm victim")
            self.assertFalse((self.work / "victim").exists())

    def test_status_and_streams(self):
        for _ in range(2):
            r = self.shell("printf out; printf err >&2; exit 42", expected=42)
            self.assertEqual((r["stdout"], r["stderr"]), ("out", "err"))

    def test_file_argument_annotation(self):
        p = self.work / "input"
        p.write_text("b\na\n")
        self.assertEqual(self.invoke(["sort", "input"])["stdout"], "a\nb\n")
        p.write_text("d\nc\n")
        self.assertEqual(self.invoke(["sort", "input"])["stdout"], "c\nd\n")

    def test_read_modify_write(self):
        p = self.work / "input"
        p.write_text("0\n")
        command = "n=$(cat input); echo $((n+1)) > input"
        self.shell(command)
        self.shell(command)
        self.assertEqual(p.read_text(), "2\n")

    def test_cache_hit(self):
        (self.work / "input").write_text("hello\n")
        cmd = ["cat", "input"]
        self.invoke(cmd)
        before = {str(p): p.stat().st_mtime_ns for p in self.cache.rglob("data.incr")}
        self.assertTrue(before)
        self.assertEqual(self.invoke(cmd)["stdout"], "hello\n")
        self.assertEqual(before, {str(p): p.stat().st_mtime_ns for p in self.cache.rglob("data.incr")})

    def test_fifo_interaction(self):
        os.mkfifo(self.work / "fifo")
        command = [str(INCR), *MODE, "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--",
                   "bash", "-c", "printf message > fifo"]
        import shlex
        for _ in range(2):
            result = run(["bash", "-c", shlex.join(command) + " & writer=$!; cat fifo; wait $writer"],
                         cwd=self.work, timeout=3)
            self.assertFalse(result["timeout"], result)
            self.assertFalse(result["remaining_descendants"], result)
            self.assertEqual((result["returncode"], result["stdout"], result["stderr"]), (0, "message", ""))

    def test_missing_input_appearance(self):
        command = "if [ -e optional ]; then cat optional; else printf absent; fi"
        self.assertEqual(self.shell(command)["stdout"], "absent")
        (self.work / "optional").write_text("present")
        self.assertEqual(self.shell(command)["stdout"], "present")

    def test_directory_listing_invalidation(self):
        (self.work / "dir").mkdir()
        command = ["find", "dir", "-type", "f"]
        self.assertEqual(self.invoke(command)["stdout"], "")
        (self.work / "dir/new").write_text("data")
        self.assertEqual(self.invoke(command)["stdout"], "dir/new\n")

    def test_hard_link_replay(self):
        command = "printf data > a; ln a b"
        for _ in range(2):
            self.shell(command)
            self.assertEqual((self.work / "a").stat().st_ino, (self.work / "b").stat().st_ino)
            (self.work / "a").unlink()
            (self.work / "b").unlink()

    def test_early_exit_with_open_stdin(self):
        if "-b" in MODE:
            self.skipTest("batch mode intentionally requires finite stdin")
        command = [str(INCR), "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--", "head", "-n", "1"]
        script = """import subprocess,sys
p=subprocess.Popen(sys.argv[1:],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 p.stdin.write(b'hello\\n'); p.stdin.flush()
 p.wait(timeout=2)
 assert p.returncode == 0 and p.stdout.read() == b'hello\\n' and p.stderr.read() == b''
finally:
 if p.poll() is None: p.kill(); p.wait()
 p.stdin.close()
"""
        result = run(["python3", "-c", script, *command], cwd=self.work, timeout=4)
        self.assertFalse(result["timeout"], result)
        self.assertEqual(result["returncode"], 0, result)

    def test_inherited_file_descriptor(self):
        import shlex
        command = [str(INCR), *MODE, "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--",
                   "python3", "-c", "import os; print(os.read(3, 99).decode())"]
        for text in ["first", "second"]:
            (self.work / "input").write_text(text)
            result = run(["bash", "-c", shlex.join(command) + " 3<input"], cwd=self.work, timeout=5)
            self.assertFalse(result["timeout"], result)
            self.assertEqual((result["returncode"], result["stdout"], result["stderr"]), (0, text + "\n", ""))

    def test_shared_cache_concurrency(self):
        import shlex
        (self.work / "input").write_text("shared\n")
        command = [str(INCR), *MODE, "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--", "cat", "input"]
        for _ in range(2):
            script = "pids=(); " + "; ".join(
                shlex.join(command) + f" > out{i} & pids+=($!)" for i in range(12))
            script += '; result=0; for p in "${pids[@]}"; do wait "$p" || result=1; done; exit "$result"'
            result = run(["bash", "-c", script], cwd=self.work, timeout=5)
            self.assertFalse(result["timeout"], result)
            self.assertEqual((result["returncode"], result["stderr"]), (0, ""), result)
            for i in range(12):
                self.assertEqual((self.work / f"out{i}").read_text(), "shared\n")
        self.assertFalse(list(self.cache.glob("uncached_*")))

    def test_corrupt_cached_effect(self):
        source = self.work / "source"
        source.write_text("valid contents")
        self.invoke(["cp", "source", "dest"])
        payloads = list(self.cache.rglob("file-*"))
        self.assertTrue(payloads)
        for payload in payloads:
            payload.write_text("corrupt")
        (self.work / "dest").unlink()
        self.invoke(["cp", "source", "dest"])
        self.assertEqual((self.work / "dest").read_text(), "valid contents")

    def test_content_change_with_preserved_mtime(self):
        source = self.work / "input"
        source.write_text("first")
        self.assertEqual(self.invoke(["cat", "input"])["stdout"], "first")
        original = source.stat()
        source.write_text("other")
        os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
        self.assertEqual(self.invoke(["cat", "input"])["stdout"], "other")

    def test_failed_open_invalidation(self):
        source = self.work / "optional"
        for text in [None, "present"]:
            if text is not None:
                source.write_text(text)
            result = self.shell("cat optional 2>/dev/null || printf absent")
            self.assertEqual(result["stdout"], text or "absent")

    def test_retarget_symlink(self):
        (self.work / "a").write_text("first")
        (self.work / "b").write_text("second")
        for target, expected in [("a", "first"), ("b", "second")]:
            link = self.work / "link"
            link.unlink(missing_ok=True)
            link.symlink_to(target)
            self.assertEqual(self.invoke(["cat", "link"])["stdout"], expected)

    def test_symlink_parent_component_invalidation(self):
        directory = self.work / "real"
        (directory / "nested").mkdir(parents=True)
        (self.work / "alias").symlink_to(directory / "nested")
        link = directory / "link"
        for target in ["first", "first", "second"]:
            if not link.is_symlink() or os.readlink(link) != target:
                link.unlink(missing_ok=True)
                link.symlink_to(target)
            result = self.invoke(["readlink", "alias/../link"])
            self.assertEqual(result["stdout"], target + "\n")

    def test_symlink_metadata_invalidation(self):
        link = self.work / "link"
        link.symlink_to("unchanged-target")
        for seconds in [1000, 1000, 2000]:
            if link.lstat().st_mtime_ns != seconds * 1_000_000_000:
                os.utime(link, ns=(seconds * 1_000_000_000, seconds * 1_000_000_000),
                         follow_symlinks=False)
            result = self.invoke(["stat", "-c", "%Y", "link"])
            self.assertEqual(result["stdout"], f"{seconds}\n")

    def test_parent_retarget_preserves_leaf_identity(self):
        original = self.work / 'original'
        other = self.work / 'other'
        original.mkdir()
        other.mkdir()
        (original / 'input').write_text('same inode')
        os.link(original / 'input', other / 'input')
        alias = self.work / 'alias'
        alias.symlink_to(original, target_is_directory=True)
        program = "import os; descriptor=os.open('alias/input',os.O_RDONLY); print(os.readlink(f'/proc/self/fd/{descriptor}')); os.close(descriptor)"
        self.assertEqual(self.invoke(['python3', '-c', program])['stdout'], str(original / 'input') + '\n')
        alias.unlink()
        alias.symlink_to(other, target_is_directory=True)
        self.assertEqual(self.invoke(['python3', '-c', program])['stdout'], str(other / 'input') + '\n')

    def test_directory_replaced_by_link_invalidates_resolution(self):
        directory = self.work / 'directory'
        moved = self.work / 'moved'
        directory.mkdir()
        (directory / 'input').write_text('same inode')
        program = "import os; descriptor=os.open('directory/input',os.O_RDONLY); print(os.readlink(f'/proc/self/fd/{descriptor}')); os.close(descriptor)"
        self.assertEqual(self.invoke(['python3', '-c', program])['stdout'], str(directory / 'input') + '\n')
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.invoke(['python3', '-c', program])['stdout'], str(moved / 'input') + '\n')

    def test_parent_write_permission_invalidation(self):
        directory = self.work / "directory"
        directory.mkdir()
        program = "try:\n open('directory/output','w').write('created')\n print('created')\nexcept PermissionError:\n print('denied')"
        self.assertEqual(self.invoke(['python3', '-c', program])['stdout'], 'created\n')
        (directory / 'output').unlink()
        directory.chmod(0o555)
        try:
            self.assertEqual(self.invoke(['python3', '-c', program])['stdout'], 'denied\n')
            self.assertFalse((directory / 'output').exists())
        finally:
            directory.chmod(0o755)

    def test_directory_rename(self):
        for _ in range(2):
            source = self.work / "source"
            source.mkdir()
            (source / "child").write_text("contents")
            self.invoke(["mv", "source", "dest"])
            self.assertFalse(source.exists())
            self.assertEqual((self.work / "dest/child").read_text(), "contents")
            shutil.rmtree(self.work / "dest")

    def test_replace_hardlinked_file(self):
        # Unlink-and-create must not mutate another name for the old inode.
        for _ in range(2):
            (self.work / "a").write_text("old")
            os.link(self.work / "a", self.work / "alias")
            self.shell("rm a; printf new > a")
            self.assertEqual((self.work / "a").read_text(), "new")
            self.assertEqual((self.work / "alias").read_text(), "old")
            (self.work / "a").unlink()
            (self.work / "alias").unlink()

    def test_missing_input_becomes_dangling_link(self):
        command = "if [ -L optional ]; then printf link; else printf absent; fi"
        self.assertEqual(self.shell(command)["stdout"], "absent")
        os.symlink("missing", self.work / "optional")
        self.assertEqual(self.shell(command)["stdout"], "link")

    def test_write_changes_with_stdin(self):
        command = ["awk", '{if ($0 == "write") print "data" > "output"; else print}']
        self.assertEqual(self.invoke(command, stdin=b"read\n")["stdout"], "read\n")
        self.invoke(command, stdin=b"write\n")
        self.assertEqual((self.work / "output").read_text(), "data\n")
        (self.work / "output").unlink()
        self.invoke(command, stdin=b"write\n")
        self.assertEqual((self.work / "output").read_text(), "data\n")

    def test_worker_thread_exec(self):
        program = ('import os,threading; '
                   'worker=threading.Thread(target=lambda:os.execv("/bin/cat",["cat","input"])); '
                   'worker.start(); worker.join()')
        for content in ["first", "first", "changed"]:
            source = self.work / "input"
            if not source.exists() or source.read_text() != content:
                source.write_text(content)
            result = self.invoke(["python3", "-c", program])
            self.assertEqual((result["stdout"], result["stderr"]), (content, ""))

    def test_closed_output_preserves_completed_effects(self):
        import shlex
        (self.work / "outputs").mkdir()
        command = [str(INCR), *MODE, "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--",
                   "bash", "-c", "printf done > outputs/output; head -c 1048576 /dev/zero"]
        pipeline = shlex.join(command) + " | head -c 1"
        previous_entries = None
        for _ in range(2):
            result = run(["bash", "-o", "pipefail", "-c", pipeline], cwd=self.work, timeout=5)
            self.assertFalse(result["timeout"], result)
            self.assertFalse(result["leaked_descendants"], result)
            self.assertFalse(result["remaining_descendants"], result)
            self.assertEqual((result["returncode"], result["stdout"], result["stderr"]),
                             (141, "\0", ""), result)
            self.assertEqual((self.work / "outputs/output").read_text(), "done")
            (self.work / "outputs/output").unlink()
            entries = {path: path.stat().st_mtime_ns for path in self.cache.glob("batch_*/data.incr")}
            if "-b" in MODE and previous_entries is not None:
                self.assertEqual(previous_entries, entries, "warm test did not reuse the cache")
            previous_entries = entries

    def test_infinite_producer(self):
        if "-b" in MODE:
            self.skipTest("batch mode intentionally requires finite stdin")
        import shlex
        command = [str(INCR), "-s", "--try", str(ROOT / "src/scripts/try.sh"),
                   "--observe", str(OBSERVE), "--cache", str(self.cache), "--", "head", "-n", "1"]
        result = run(["bash", "-c", "yes hello | " + shlex.join(command)], cwd=self.work, timeout=3)
        self.assertFalse(result["timeout"], result)
        self.assertEqual(result["stdout"], "hello\n")
        self.assertEqual(result["returncode"], 0, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--effect-policy", choices=["live", "final"])
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--annotations", action="store_true")
    args, rest = parser.parse_known_args()
    if args.batch:
        MODE = ["-b"]
    if args.effect_policy:
        MODE += ["--effect-policy", args.effect_policy]
    if args.compress:
        MODE.append("-z")
    if args.full:
        MODE.append("-f")
    if args.annotations:
        MODE.append("-a")
    if args.binary:
        INCR = args.binary.resolve()
    (ROOT / "qualification/.work").mkdir(exist_ok=True)
    unittest.main(argv=[__file__, *rest])
