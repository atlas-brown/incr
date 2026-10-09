"""Ensure the terminal helper does not alter ordinary shell signal semantics."""

from pathlib import Path
import subprocess
import sys
import unittest

HELPER = Path(__file__).with_name("terminal.py")


class TerminalTests(unittest.TestCase):
    def test_sigpipe_is_not_inherited_as_ignored(self):
        result = subprocess.run(
            [sys.executable, str(HELPER), "/bin/sh", "-c", "kill -PIPE $$; echo wrongly-survived"],
            capture_output=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 141)
        self.assertEqual(result.stdout, b"")

    def test_controlling_terminal_and_optional_terminal_input(self):
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "--stdin",
                "/bin/sh",
                "-c",
                "test -t 0 && test -r /dev/tty",
            ],
            capture_output=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
