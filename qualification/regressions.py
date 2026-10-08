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

    def test_non_utf8_internal_path(self):
        path = os.fsencode(self.work) + b"/file-\xff"
        command = ["python3", "-c", "import os; print(open(b'file-\\xff').read())"]
        for value in [b"one", b"two"]:
            with open(path, "wb") as stream:
                stream.write(value)
            self.assertEqual(self.invoke(command)["stdout"], value.decode() + "\n")
        self.invoke(["python3", "-c", "import os; os.symlink(b'file-\\xff', 'link')"])
        self.assertEqual(os.readlink(os.fsencode(self.work / "link")), b"file-\xff")

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
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--annotations", action="store_true")
    args, rest = parser.parse_known_args()
    if args.batch:
        MODE = ["-b"]
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
