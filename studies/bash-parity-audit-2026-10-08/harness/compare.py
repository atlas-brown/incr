"""Narrow presentation normalization and line-based differential accounting."""

from collections import Counter
import difflib
import re


def normalize(text, case):
    text = re.sub(
        r"(?<!\S)\S+/incr-script\.[A-Za-z0-9]+/script/([^\s:]+)(?=:(?: eval:)? line)", r"./\1", text
    )
    text = re.sub(r": line \d+:", ": line <line>:", text)
    text = re.sub(
        r"cannot set terminal process group \(\d+\)",
        "cannot set terminal process group (<pid>)",
        text,
    )
    if case == "type":
        text = re.sub(
            r"(?m)^(    )\S+/target/release/incr --try \S+ --cache \S+ --observe \S+ (?=rm -f a b c;|grep \. a b c$)",
            r"\1",
            text,
        )
    return text


def lines(text):
    """LF-delimited lines, consistent with the paper's transcript accounting."""
    parts = text.split("\n")
    return parts[:-1] if parts[-1] == "" else parts


def line_counts(expected, actual):
    left, right = lines(expected), lines(actual)
    counts = dict(
        reference_lines=len(left),
        candidate_lines=len(right),
        matched=0,
        deleted=0,
        inserted=0,
        replaced_reference=0,
        replaced_candidate=0,
    )
    if left == right:
        counts["matched"] = len(left)
        return counts
    for tag, a, b, c, d in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if tag == "equal":
            counts["matched"] += b - a
        elif tag == "delete":
            counts["deleted"] += b - a
        elif tag == "insert":
            counts["inserted"] += d - c
        else:
            counts["replaced_reference"] += b - a
            counts["replaced_candidate"] += d - c
    return counts


def live_descendants(record):
    """Ignore adopted zombies while counting processes still alive at cleanup."""
    names = Counter()
    for diagnostic in record.get("diagnostics", []):
        status = diagnostic.get("status", "")
        state = re.search(r"^State:\s+(\S)", status, re.MULTILINE)
        name = re.search(r"^Name:\s+([^\n]+)", status, re.MULTILINE)
        if state and state[1] != "Z":
            names[name[1] if name else "<unknown>"] += 1
    return names


def compare(reference, candidate):
    case = reference["case"]
    a, b = reference["captures"], candidate["captures"]
    fields = [("stderr", reference["stderr"], candidate["stderr"])]
    captures_valid = len(a) == len(b) > 0
    expected_valid = captures_valid and all(
        x["expected"] == y["expected"] and x["expected_path"] == y["expected_path"]
        for x, y in zip(a, b)
    )
    for index in range(max(len(a), len(b))):
        fields.append(
            (
                f"capture-{index}",
                a[index]["actual"] if index < len(a) else "<MISSING>",
                b[index]["actual"] if index < len(b) else "<MISSING>",
            )
        )
    normalized = [(label, normalize(x, case), normalize(y, case)) for label, x, y in fields]
    output_match = all(x == y for _, x, y in normalized)
    lifecycle = not any(r["timeout"] or r["remaining_descendants"] for r in (reference, candidate))
    lifecycle &= not candidate["leaked_descendants"] or reference["leaked_descendants"]
    reference_live = live_descendants(reference)
    candidate_live = live_descendants(candidate)
    live_valid = all(count <= reference_live[name] for name, count in candidate_live.items())
    lifecycle &= live_valid
    status_equal = reference["returncode"] == candidate["returncode"]
    diff_only = all(
        all(
            re.fullmatch(
                r"(?:\d+(?:,\d+)?[acd]\d+(?:,\d+)?|[<>] .*|---|\\ No newline at end of file)", line
            )
            for line in r["stdout"].splitlines()
        )
        for r in (reference, candidate)
    )
    driver_output_valid = diff_only or reference["stdout"] == candidate["stdout"]
    status_valid = (
        reference["returncode"] in (0, 1)
        and candidate["returncode"] in (0, 1)
        and (status_equal or (output_match and diff_only))
    )
    result = dict(
        case=case,
        phase=candidate["phase"],
        exact=all(x == y for _, x, y in fields),
        output_match=output_match,
        captures_valid=captures_valid,
        expected_valid=expected_valid,
        lifecycle_valid=bool(lifecycle),
        reference_live_descendants=dict(reference_live),
        candidate_live_descendants=dict(candidate_live),
        status_equal=status_equal,
        status_valid=status_valid,
        driver_output_valid=driver_output_valid,
        reference_status=reference["returncode"],
        candidate_status=candidate["returncode"],
        match=bool(
            output_match and captures_valid and expected_valid and lifecycle and status_valid
            and driver_output_valid
        ),
        lines=[line_counts(x, y) for _, x, y in normalized[1:]],
    )
    diffs = {}
    for name, entries in [("raw", fields), ("normalized", normalized)]:
        diffs[name] = "".join(
            "".join(
                difflib.unified_diff(
                    x.splitlines(True),
                    y.splitlines(True),
                    fromfile=f"bash/{label}",
                    tofile=f"observe/{label}",
                )
            )
            for label, x, y in entries
        )
    return result, diffs
