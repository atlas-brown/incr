#!/usr/bin/env python3
"""Behavioral checks for guarded inherited files and shared descriptor offsets."""
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
OBSERVE = ROOT.parent / "observe/target/release/observe"
SOURCE = r'''
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <fcntl.h>
int main(int argc, char **argv) {
    if (argc != 2) return 90;
    char buffer[4096], c = 'x';
    while (read(0, buffer, sizeof buffer) > 0) {}
    const char *mode = argv[1];
    if (!strcmp(mode, "conditional")) {
        int fd = open("control", O_RDONLY);
        if (fd < 0 || read(fd, &c, 1) != 1) return 91;
        close(fd);
        mode = c == 'r' ? "read" : "unused";
        c = 'x';
    }
    if (!strcmp(mode, "read")) { if (read(3, &c, 1) != 1) return 92; }
    else if (!strcmp(mode, "pread")) { if (pread(3, &c, 1, 0) != 1) return 93; }
    else if (!strcmp(mode, "dup")) {
        int fd = dup(3); if (fd < 0 || read(fd, &c, 1) != 1) return 94;
    } else if (!strcmp(mode, "mmap")) {
        char *p = mmap(0, 1, PROT_READ, MAP_PRIVATE, 3, 0);
        if (p == MAP_FAILED) return 95;
        c = *p; munmap(p, 1);
    } else if (!strcmp(mode, "fork")) {
        pid_t pid = fork(); if (pid < 0) return 96;
        if (!pid) { if (read(3, &c, 1) != 1) _exit(97); _exit(write(1, &c, 1) == 1 ? 0 : 99); }
        int status; if (waitpid(pid, &status, 0) < 0 || !WIFEXITED(status)) return 98;
        return WEXITSTATUS(status);
    }
    return write(1, &c, 1) == 1 ? 0 : 99;
}
'''


class InheritedFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory(prefix="fd-build-", dir=ROOT / "qualification/.work")
        cls.addClassCleanup(cls.build.cleanup)
        directory = Path(cls.build.name)
        source = directory / "probe.c"
        source.write_text(SOURCE)
        cls.probe = directory / "probe"
        subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-O2", str(source), "-o", str(cls.probe)],
                       check=True, timeout=15)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fd-case-", dir=ROOT / "qualification/.work")
        self.work = Path(self.temp.name)
        self.cache = self.work / "cache"
        self.cache.mkdir()
        (self.work / "input").write_text("abc")

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, mode, *, data=b"", prefix="", suffix="", redirect="3<input"):
        command = [str(ROOT / "target/release/incr"), "--observe", str(OBSERVE),
                   "--cache", str(self.cache), "--", str(self.probe), mode]
        script = "exec " + redirect + "; " + prefix + shlex.join(command) + suffix
        result = run(["bash", "-c", script], cwd=self.work, stdin=data, timeout=5)
        self.assertFalse(result["timeout"] or result["remaining_descendants"], result)
        self.assertEqual((result["returncode"], result["stderr"]), (0, ""), result)
        return result["stdout"]

    def payloads(self):
        return sorted(self.cache.glob("batch_*/data.incr"))

    def test_unused_file_replays_with_empty_and_streamed_stdin(self):
        for data in (b"", b"finite stream\n" * 1000):
            with self.subTest(data_bytes=len(data)):
                self.assertEqual(self.invoke("unused", data=data), "x")
                before = {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in self.payloads()}
                self.assertTrue(before)
                self.assertEqual(self.invoke("unused", data=data), "x")
                self.assertEqual(before, {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in before})

    def test_accesses_stay_live_and_preserve_parent_offset(self):
        suffix = '; IFS= read -r -n 1 -u 3 next; printf ":%s" "$next"'
        for mode in ("read", "pread", "dup", "mmap", "fork"):
            for data in (b"", b"finite stream\n" * 100):
                for _ in range(2):
                    with self.subTest(mode=mode, data_bytes=len(data)):
                        next_byte = "b" if mode in ("read", "dup", "fork") else "a"
                        self.assertEqual(self.invoke(mode, data=data, suffix=suffix), "a:" + next_byte)
                        self.assertFalse(self.payloads())

    def test_changed_dependency_cannot_replay_before_descriptor_read(self):
        control = self.work / "control"
        control.write_text("u")
        self.assertEqual(self.invoke("conditional", data=b"stream"), "x")
        self.assertTrue(self.payloads())
        control.write_text("r")
        suffix = '; IFS= read -r -n 1 -u 3 next; printf ":%s" "$next"'
        self.assertEqual(self.invoke("conditional", data=b"stream", suffix=suffix), "a:b")

    def test_inherited_identity_and_offset_namespace_entries(self):
        self.assertEqual(self.invoke("unused"), "x")
        count = len(self.payloads())
        self.assertEqual(self.invoke("unused", prefix="IFS= read -r -n 1 -u 3 discarded; "), "x")
        self.assertGreater(len(self.payloads()), count)
        count = len(self.payloads())
        replacement = self.work / "replacement"
        replacement.write_text("def")
        replacement.replace(self.work / "input")
        self.assertEqual(self.invoke("unused"), "x")
        self.assertGreater(len(self.payloads()), count)

    def test_writable_file_keeps_the_native_boundary(self):
        for _ in range(2):
            self.assertEqual(self.invoke("unused", redirect="3<>input"), "x")
            self.assertFalse(self.payloads())

    def test_multiple_unused_files_can_replay(self):
        redirect = "3<input 4<input"
        self.assertEqual(self.invoke("unused", redirect=redirect), "x")
        before = {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in self.payloads()}
        self.assertTrue(before)
        self.assertEqual(self.invoke("unused", redirect=redirect), "x")
        self.assertEqual(before, {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in before})


if __name__ == "__main__":
    (ROOT / "qualification/.work").mkdir(exist_ok=True)
    unittest.main()
