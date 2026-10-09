#!/usr/bin/env python3
"""Recheck saved evidence and generate the exhaustive per-group study ledger."""
import argparse
import csv
import difflib
import hashlib
import io
import gzip
import json
from pathlib import Path

from compare import compare, line_counts, lines, normalize

STUDY = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(
        gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    )


def markdown_code(value):
    return "`" + value.replace("`", "'") + "`"


def write_line_ledger(results, groups, records):
    """Give every reference/output line a stable ID; retain raw text in records."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "case",
            "phase",
            "capture",
            "reference_line",
            "candidate_line",
            "status",
            "raw_equal",
            "reference_normalized_sha256",
            "candidate_normalized_sha256",
        ]
    )

    def digest(text):
        return hashlib.sha256(text.encode(errors="surrogateescape")).hexdigest()

    for case in groups:
        for phase in ("cold", "warm"):
            a = records[case, "bash", phase]["captures"]
            b = records[case, "observe", phase]["captures"]
            for index in range(max(len(a), len(b))):
                raw_a = a[index]["actual"] if index < len(a) else ""
                raw_b = b[index]["actual"] if index < len(b) else ""
                left, right = lines(normalize(raw_a, case)), lines(normalize(raw_b, case))
                original_left, original_right = lines(raw_a), lines(raw_b)
                opcodes = (
                    [("equal", 0, len(left), 0, len(right))]
                    if left == right
                    else difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes()
                )
                for tag, start_a, end_a, start_b, end_b in opcodes:
                    for offset in range(max(end_a - start_a, end_b - start_b)):
                        x, y = start_a + offset, start_b + offset
                        have_a, have_b = x < end_a, y < end_b
                        writer.writerow(
                            [
                                case,
                                phase,
                                index,
                                x + 1 if have_a else "",
                                y + 1 if have_b else "",
                                tag,
                                have_a and have_b and original_left[x] == original_right[y],
                                digest(left[x]) if have_a else "",
                                digest(right[y]) if have_b else "",
                            ]
                        )
    (results / "line-results.csv.gz").write_bytes(
        gzip.compress(buffer.getvalue().encode(), mtime=0)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    results = args.results.resolve()
    summary = load(results / "summary.json")
    provenance = load(results / "provenance.json")
    notes = dict(
        line.split("\t", 1) for line in (STUDY / "case-notes.tsv").read_text().splitlines()
    )
    source_files = {row["path"] for row in load(STUDY / "corpus-provenance.json")["files"]}
    groups = provenance["case_order"]
    assert len(groups) == summary["groups"] and summary["complete"]
    records = {}
    for case in groups:
        for mode in ("bash", "observe"):
            for phase in ("cold", "warm"):
                path = results / "records" / f"{case}.{mode}.{phase}.json.gz"
                records[case, mode, phase] = load(path)
    assert len(list((results / "records").glob("*.json.gz"))) == len(records)
    report = [
        "# Case-by-case Bash analysis",
        "",
        "Generated from retained raw records. Counts are LF-delimited output lines, not separately numbered assertions. "
        "Each group has native cold/warm and Observe cold/warm evidence. Warm retains the same fixture/cache. "
        "Source locations, terminal process-group IDs, and the reviewed function executable prefixes are the only normalizations used here.",
        "",
        "| Group | Native lines cold/warm | Cold match | Warm match | Cache entries cold/warm | Unchanged warm metadata |",
        "|---|---:|:---:|:---:|---:|---:|",
    ]
    metrics = {
        "groups": len(groups),
        "phases": {},
        "native_expected_differences": [],
        "cold_warm_variations": [],
        "possible_skip_diagnostics": [],
        "cases": [],
    }
    sections = []
    for case in groups:
        pair_rows = {}
        for phase in ("cold", "warm"):
            a, b = records[case, "bash", phase], records[case, "observe", phase]
            row, _ = compare(a, b)
            pair_rows[phase] = row
            aggregate = metrics["phases"].setdefault(
                phase,
                {
                    "matching_groups": 0,
                    "exact_groups": 0,
                    "reference_lines": 0,
                    "matched_lines": 0,
                    "deleted_lines": 0,
                    "inserted_lines": 0,
                    "replaced_reference_lines": 0,
                    "replaced_candidate_lines": 0,
                    "expected_lines": 0,
                    "cache_entries": 0,
                    "retained_metadata": 0,
                    "groups_with_cache": 0,
                    "groups_with_retained_metadata": 0,
                    "timeouts": 0,
                    "survivors": 0,
                },
            )
            aggregate["matching_groups"] += row["match"]
            aggregate["exact_groups"] += row["exact"]
            for count in row["lines"]:
                for target, source in [
                    ("reference_lines", "reference_lines"),
                    ("matched_lines", "matched"),
                    ("deleted_lines", "deleted"),
                    ("inserted_lines", "inserted"),
                    ("replaced_reference_lines", "replaced_reference"),
                    ("replaced_candidate_lines", "replaced_candidate"),
                ]:
                    aggregate[target] += count[source]
            aggregate["expected_lines"] += sum(
                line_counts(c["expected"], c["actual"])["reference_lines"] for c in a["captures"]
            )
            aggregate["cache_entries"] += b["cache_entries"]
            aggregate["groups_with_cache"] += b["cache_entries"] > 0
            aggregate["retained_metadata"] += b["retained_metadata"]
            aggregate["groups_with_retained_metadata"] += b["retained_metadata"] > 0
            aggregate["timeouts"] += a["timeout"] + b["timeout"]
            aggregate["survivors"] += len(a["remaining_descendants"]) + len(
                b["remaining_descendants"]
            )
            for record in (a, b):
                # These strings identify known upstream warning paths, not a proof of all branch coverage.
                for line in (
                    record["stderr"] + "\n".join(c["actual"] for c in record["captures"])
                ).splitlines():
                    if (
                        "tests to be skipped" in line
                        or "cannot change locale" in line
                        or "/dev/tty: No such device" in line
                    ):
                        metrics["possible_skip_diagnostics"].append(
                            {"case": case, "mode": record["mode"], "phase": phase, "line": line}
                        )
        a, b, warm = (
            records[case, "bash", "cold"],
            records[case, "observe", "cold"],
            records[case, "observe", "warm"],
        )
        native_lines = [
            sum(x["reference_lines"] for x in pair_rows[p]["lines"]) for p in ("cold", "warm")
        ]
        report.append(
            f'| {case} | {native_lines[0]}/{native_lines[1]} | {pair_rows["cold"]["match"]} | {pair_rows["warm"]["match"]} | {b["cache_entries"]}/{warm["cache_entries"]} | {warm["retained_metadata"]} |'
        )
        invocations = {
            arg.removeprefix("./")
            for rec in (a, b, warm)
            for call in rec["invocations"]
            for arg in call["argv"][1:]
            if arg.removeprefix("./") in source_files
        }
        expected_counts = [line_counts(c["expected"], c["actual"]) for c in a["captures"]]
        expected_match = all(c["actual"] == c["expected"] for c in a["captures"])
        if not expected_match:
            metrics["native_expected_differences"].append(case)
        variations = []
        for mode in ("bash", "observe"):
            stable, _ = compare(records[case, mode, "cold"], records[case, mode, "warm"])
            if not stable["output_match"]:
                variations.append(mode)
                metrics["cold_warm_variations"].append({"case": case, "mode": mode})
        metrics["cases"].append(
            {
                "case": case,
                "cold": pair_rows["cold"],
                "warm": pair_rows["warm"],
                "invoked_source_files": sorted(invocations),
                "expected_comparison": expected_counts,
            }
        )
        sections += [
            "",
            f"## {case}",
            "",
            notes[case],
            "",
            f"- Native reference: {native_lines[0]} cold / {native_lines[1]} warm lines; normalized Observe matches: "
            f'{pair_rows["cold"]["match"]} / {pair_rows["warm"]["match"]}. Byte-exact including stderr: '
            f'{pair_rows["cold"]["exact"]} / {pair_rows["warm"]["exact"]}.',
            f'- Driver status, native/Observe: cold {a["returncode"]}/{b["returncode"]}; warm '
            f'{records[case,"bash","warm"]["returncode"]}/{warm["returncode"]}. Native matches literal expected operands: {expected_match}.',
            f'- Cache entries cold/warm: {b["cache_entries"]}/{warm["cache_entries"]}; unchanged warm metadata files: '
            f'{warm["retained_metadata"]}. These are retention evidence, not a per-command hit count.',
            f'- Native/Observe cleanup required: cold {a["leaked_descendants"]}/{b["leaked_descendants"]}; warm '
            f'{records[case,"bash","warm"]["leaked_descendants"]}/{warm["leaked_descendants"]}. '
            f'Cold/warm output variation: {", ".join(variations) or "none"}.',
            f'- Shell-launcher calls, native/Observe: cold {len(a["invocations"])}/{len(b["invocations"])}; warm '
            f'{len(records[case,"bash","warm"]["invocations"])}/{len(warm["invocations"])}.',
            "- Corpus files seen at shell-launcher entry points: "
            + (
                ", ".join(map(markdown_code, sorted(invocations)))
                or "stdin/command-string invocation; no named corpus file"
            )
            + ".",
            "- Expected transcript(s): "
            + ", ".join(markdown_code(c["expected_path"]) for c in a["captures"])
            + ".",
            f"- Evidence: `records/{case}.{{bash,observe}}.{{cold,warm}}.json.gz`; nonempty differences are under `diffs/{case}.*`.",
        ]
        if not expected_match:
            sections += [
                "",
                "Native versus expected-file differences (shared baseline context, not an Observe regression):",
                "",
                "```diff",
                a["stdout"].rstrip(),
                "```",
            ]
        for phase in ("cold", "warm"):
            delta = results / "diffs" / f"{case}.{phase}.normalized.diff"
            if delta.exists():
                sections += [
                    "",
                    f"Remaining normalized {phase} difference:",
                    "",
                    "```diff",
                    delta.read_text().rstrip(),
                    "```",
                ]
    accounting = load(STUDY / "paper-accounting.json")
    metrics["paper_subset"] = {}
    for phase in ("cold", "warm"):
        categories = {}
        for category, names in accounting["categories"].items():
            totals = {
                "expected_lines": 0,
                "reference_lines": 0,
                "matched_lines": 0,
                "inserted_lines": 0,
                "deleted_lines": 0,
                "replaced_reference_lines": 0,
            }
            for case in names:
                if case not in groups:
                    continue
                reference = records[case, "bash", phase]["captures"]
                candidate = records[case, "observe", phase]["captures"]
                for left, right in zip(reference, candidate):
                    if Path(left["expected_path"]).name != case + ".right":
                        continue
                    count = line_counts(
                        normalize(left["actual"], case), normalize(right["actual"], case)
                    )
                    totals["expected_lines"] += len(lines(left["expected"]))
                    for key, field in [
                        ("reference_lines", "reference_lines"),
                        ("matched_lines", "matched"),
                        ("inserted_lines", "inserted"),
                        ("deleted_lines", "deleted"),
                        ("replaced_reference_lines", "replaced_reference"),
                    ]:
                        totals[key] += count[field]
            categories[category] = totals
        metrics["paper_subset"][phase] = categories
    write_line_ledger(results, groups, records)
    (results / "analysis.json").write_text(json.dumps(metrics, indent=2) + "\n")
    destination = args.report or results / "CASE_ANALYSIS.md"
    destination.write_text("\n".join(report + sections) + "\n")
    print(json.dumps({k: v for k, v in metrics.items() if k != "cases"}, indent=2))
    return int(any(p["matching_groups"] != len(groups) for p in metrics["phases"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
