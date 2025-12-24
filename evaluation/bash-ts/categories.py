tests = {
    "Globbing": [
        "extglob",
        "extglob2",
        "extglob3",
        "glob-test",
        "globstar",
    ],

    "Data structures": [
        "array",
        "array2",
        "assoc",
    ],

    "Quoting": [
        "iquote",
        "nquote",
        "nquote1",
        "nquote2",
        "nquote3",
        "nquote4",
        "nquote5",
        "quote",
        "quotearray",
    ],

    "Expansion": [
        "procsub",
        "comsub",
        "arith",
        "alias",
        "comsub-eof",
        "tilde",
        "tilde2",
        "ifs",
        "more-exp",
        "new-exp",
        "dollars",
        "dynvar",
        "rhs-exp",
        "precedence",
        "exp-tests",
        "braces",
    ],

    "Utils": [
        "getopts",
        "strip",
    ],

    "I/O": [
        "exportfunc",
        "appendop",
        "attr",
        "complete",
        "cprint",
        "dirstack",
        "histexpand",
        "history",
        "input-test",
        "nameref",
        "printf",
        "read",
        "rsh",
        "type",
    ],

    "Constructs": [
        "func",
        "parser",
        "arith-for",
        "case",
        "casemod",
        "cond",
        "test",
        "builtins",
        "heredoc",
        "herestr",
        "errors",
        "intl",
        "invert",
    ],

    "IPC": [
        "jobs",
        "lastpipe",
        "mapfile",
        "trap",
        "varenv",
        "vredir",
        "coproc",
        "dbg-support",
        "dbg-support2",
        "redir",
        "execscript",
    ],

    "POSIX": [
        "comsub-posix",
        "ifs-posix",
        "posix2",
        "posixexp",
        "posixexp2",
        "posixpat",
        "posixpipe",
    ],

    "Options": [
        "set-e",
        "set-x",
        "shopt",
    ],
}

from pathlib import Path
from typing import Dict, List, Tuple


def summarize_right_files() -> Tuple[Dict[str, int], List[str]]:
    tests_dir = Path(__file__).resolve().parent / "tests"
    totals: Dict[str, int] = {}
    missing: List[str] = []
    all_sum = 0

    for category, names in tests.items():
        total_lines = 0
        for name in names:
            path = tests_dir / f"{name}.right"
            if not path.exists():
                missing.append(str(path))
                continue
            with path.open(encoding="utf-8", errors="ignore") as f:
                total_lines += sum(1 for _ in f)
        totals[category] = total_lines
        all_sum += total_lines
    totals["All"] = all_sum

    return totals, missing


def main() -> None:
    totals, missing = summarize_right_files()
    for category, total in totals.items():
        print(f"{category}: {total}")

    # print the whole sum
    print(f"\nTotal lines in all .right files: {totals['All']}")


    if missing:
        print("\nMissing .right files:")
        for path in missing:
            print(f"- {path}")


if __name__ == "__main__":
    main()
