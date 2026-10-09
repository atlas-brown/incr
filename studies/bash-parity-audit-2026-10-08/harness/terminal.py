#!/usr/bin/env python3
"""Give a bounded test a controlling terminal without merging its output streams."""
import fcntl
import os
import pty
import select
import signal
import sys
import termios


def main():
    args = sys.argv[1:]
    terminal_stdin = args[0] == "--stdin"
    if terminal_stdin:
        args.pop(0)
    master, slave = pty.openpty()
    pid = os.fork()
    if pid == 0:
        os.close(master)
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        if terminal_stdin:
            os.dup2(slave, 0)
        os.close(slave)
        # Python ignores these signals; normal subprocess exec restores them.
        # Preserve ordinary shell pipeline and trap behavior across this helper.
        for name in ("SIGPIPE", "SIGXFZ", "SIGXFSZ"):
            signum = getattr(signal, name, None)
            if signum is not None:
                signal.signal(signum, signal.SIG_DFL)
        os.execvp(args[0], args)
    os.close(slave)
    try:
        while True:
            child, status = os.waitpid(pid, os.WNOHANG)
            if child:
                code = os.waitstatus_to_exitcode(status)
                return code if code >= 0 else 128 - code
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                try:
                    data = os.read(master, 65536)
                    if data:
                        os.write(2, data)
                except OSError:
                    pass
    finally:
        os.close(master)


if __name__ == "__main__":
    raise SystemExit(main())
