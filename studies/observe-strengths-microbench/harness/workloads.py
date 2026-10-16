"""Deterministic shell workloads; edits happen outside measured execution."""

from pathlib import Path
import math
import os

SCENARIOS = {
    "builtin-control": "Native shell arithmetic control: no external command can be accelerated",
    "compute-control": "Deterministic PBKDF2 computation: useful CPU work dominates execution overhead",
    "dummy-straightline": "128 explicitly listed distinct dummy commands; overhead stress control",
    "dummy-loop": "Hundreds to thousands of distinct dummy commands in a loop; overhead stress control",
    "checksums": "Independent per-file checksums; command substitution and for loops",
    "text-summaries": "Independent file-backed readers inside shell functions",
    "directory-inventory": "Shell glob expansion with external name formatting",
    "artifact-generation": "Per-source filesystem artifact installation",
    "redirected-transform": "Read-only stdin filter with shell output redirection; limit case",
    "staged-artifacts": "Copy, transform, rename and cleanup effects",
    "partitioned-logs": "Per-partition pipelines followed by a file-backed aggregate",
    "parameter-sweep": "Nested loops with stable parameter/task identities",
    "growing-manifest": "While-read manifest processing, appending stable work items",
    "localized-script-edit": "A local change to one task pipeline; other command identities survive",
    "shared-dependency": "Shared configuration combined with independent sources",
    "streaming-stages": "Piped stdin validation with unchanged downstream arguments",
    "build-graph": "Independent leaves, grouped intermediates and a final aggregate",
}
PHASES = ("cold", "unchanged", "one-edit", "one-percent", "ten-percent", "global-edit")


def write_input(path, item, generation, rows):
    # Deterministic edits change content and line counts, making invalidation observable.
    line = f"alpha token1 token2 token3 item{item:06d} version{generation:02d}\n"
    path.write_text(line * (rows + generation))
    os.utime(path, (1700000000 + generation, 1700000000 + generation))


def setup(root, count, rows):
    for name in ("inputs", "outputs"):
        (root / name).mkdir(parents=True)
    for i in range(count):
        write_input(root / f"inputs/item{i:06d}.txt", i, 0, rows)
        folder = root / f"inputs/dir{i:06d}"
        folder.mkdir()
        (folder / "a file [x] λ.txt").write_text("alpha\n")
    (root / "config.txt").write_text("configuration00\n")
    os.utime(root / "config.txt", (1700000000, 1700000000))
    (root / "manifest.txt").write_text(
        "".join(f"inputs/item{i:06d}.txt\n" for i in range(count))
    )
    (root / "parameters.txt").write_text("1 2 3\n")
    (root / "limit.txt").write_text(str(count) + "\n")


def edit(root, scenario, phase, count, rows):
    generation = PHASES.index(phase)
    if generation < 2:
        return
    affected = (
        1
        if generation == 2
        else max(1, math.ceil(count * (0.01 if generation == 3 else 0.1)))
        if generation < 5
        else count
    )
    if scenario == "growing-manifest" and generation < 5:
        start = len(list((root / "inputs").glob("item*.txt")))
        for i in range(start, start + affected):
            write_input(root / f"inputs/item{i:06d}.txt", i, 0, rows)
        (root / "manifest.txt").write_text(
            "".join(
                str(p.relative_to(root)) + "\n"
                for p in sorted((root / "inputs").glob("item*.txt"))
            )
        )
    elif scenario == "parameter-sweep" and generation == 2:
        (root / "parameters.txt").write_text("1 2 3 4\n")
    elif scenario in ("dummy-straightline", "compute-control") or (
        scenario == "shared-dependency" and generation == 5
    ):
        (root / "config.txt").write_text(f"configuration{generation:02d}\n")
        os.utime(root / "config.txt", (1700000005, 1700000005))
    elif scenario == "directory-inventory":
        for i in range(affected):
            (root / f"inputs/dir{i:06d}/extra{generation}.txt").write_text("new\n")
    elif scenario == "localized-script-edit" and generation == 2:
        pass  # Only the program is edited at this step.
    else:
        files = sorted((root / "inputs").glob("item*.txt"))
        for i, path in enumerate(files[: affected if generation < 5 else len(files)]):
            write_input(path, i, generation, rows)


def program(scenario, phase, source_root=None):
    source = (source_root or Path(__file__).resolve().parents[1] / "scenarios") / (
        scenario + ".sh"
    )
    text = source.read_text()
    if scenario == "localized-script-edit" and PHASES.index(phase) >= 2:
        text = text.replace("/usr/bin/tr a-z A-Z", "/usr/bin/tr a-z a-z", 1)
    return text
