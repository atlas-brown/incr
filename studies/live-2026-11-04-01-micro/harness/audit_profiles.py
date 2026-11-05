"""Audit every expected dynamic wrapper in a separate profiling pilot."""

import argparse
import collections
import json
import math
from pathlib import Path

from workloads import PHASES


def calls(scenario, phase, count):
    generation = PHASES.index(phase)
    if scenario == "builtin-control":
        return 0
    if scenario == "compute-control":
        return 1
    if scenario == "text-summaries":
        return 2 * count
    if scenario == "staged-artifacts":
        return 4 * count
    if scenario == "partitioned-logs":
        return 3 * count + 1
    if scenario == "parameter-sweep":
        return (3 if generation < 2 else 4) * count
    if scenario == "growing-manifest":
        return (
            count
            + (1 if generation >= 2 else 0)
            + (math.ceil(count * 0.01) if generation >= 3 else 0)
            + (math.ceil(count * 0.1) if generation >= 4 else 0)
        )
    if scenario in ("localized-script-edit", "shared-dependency"):
        return 2 * count
    if scenario == "streaming-stages":
        return 3 * count
    if scenario == "build-graph":
        return count + 2 * min(count, 10) + 1
    return count


def main(root):
    rows = []
    for sample in root.glob("samples/*/*/*/*/*.json"):
        value = json.loads(sample.read_text())
        if value["mode"] not in ("observe", "sandbox"):
            continue
        profiles = list((sample.parent / (value["phase"] + "-profile")).glob("*.json"))
        expected = calls(value["scenario"], value["phase"], value["count"])
        if len(profiles) != expected:
            raise RuntimeError(
                f"Dynamic coverage mismatch {sample}: {len(profiles)}/{expected}"
            )
        counts = collections.Counter()
        for path in profiles:
            report = json.loads(path.read_text())
            labels = {p[0] for p in report["phases_ns"]}
            required = (
                "backend_observe" if value["mode"] == "observe" else "backend_sandbox"
            )
            if required not in labels:
                raise RuntimeError("Wrong backend: " + str(path))
            counts["executions_captured"] += "capture_save" in labels
            counts["fast_replays"] += "spawn" not in labels
            counts["speculative_replays"] += "replay" in labels and "spawn" in labels
        rows.append(
            {k: value[k] for k in ("scenario", "scale", "repetition", "mode", "phase")}
            | {
                "expected_wrappers": expected,
                "verified_wrappers": len(profiles),
                **counts,
            }
        )
    (root / "profile-audit.json").write_text(
        json.dumps({"valid": True, "rows": rows}, indent=2) + "\n"
    )
    print("Verified dynamic backend coverage for", len(rows), "profiled phases.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    main(parser.parse_args().run)
