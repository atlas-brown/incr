"""Reject incomplete, corrupted and semantically mismatched saved experiments."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from audit import audit
from workloads import PHASES


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write(
            self.root / "configuration.json",
            {
                "sandbox": False,
                "diagnostic": False,
                "only": "checksums",
                "scales": "small",
                "repetitions": 3,
            },
        )
        self.write(self.root / "status.json", {"state": "complete"})
        self.write(self.root / "provenance.json", {"annotations": False})
        digest = hashlib.sha256(b"").hexdigest()
        for rep in range(3):
            for mode in ("bash", "original", "observe"):
                for phase in PHASES:
                    parent = self.root / "samples/checksums/small" / str(rep) / mode
                    capture = parent / (phase + "-capture")
                    capture.mkdir(parents=True)
                    for name in ("stdout", "stderr"):
                        (capture / name).write_bytes(b"")
                    self.write(
                        parent / (phase + ".json"),
                        {
                            "scenario": "checksums",
                            "scale": "small",
                            "repetition": rep,
                            "mode": mode,
                            "phase": phase,
                            "valid": True,
                            "returncode": 0,
                            "failure": None,
                            "remaining_descendants": [],
                            "inputs_unchanged": True,
                            "elapsed_sec": 1.0,
                            "stdout_sha256": digest,
                            "stderr_sha256": digest,
                            "outputs": {},
                            "cache_entries": 1,
                        },
                    )
        self.sample = self.root / "samples/checksums/small/0/observe/cold.json"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def change(self, **fields):
        value = json.loads(self.sample.read_text())
        value.update(fields)
        self.write(self.sample, value)

    def test_complete_valid_cohort(self):
        audit(self.root)
        self.assertEqual(
            json.loads((self.root / "audit.json").read_text())["verified"], 54
        )

    def test_missing_measurement_is_rejected(self):
        self.sample.unlink()
        with self.assertRaisesRegex(RuntimeError, "Coverage"):
            audit(self.root)

    def test_corrupted_capture_is_rejected(self):
        (self.sample.parent / "cold-capture/stdout").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "Capture changed"):
            audit(self.root)

    def test_changed_output_manifest_is_rejected(self):
        self.change(outputs={"unexpected": {"bytes": 1}})
        with self.assertRaisesRegex(RuntimeError, "Native reference"):
            audit(self.root)

    def test_live_descendants_are_rejected(self):
        self.change(remaining_descendants=[99999])
        with self.assertRaisesRegex(RuntimeError, "Invalid sample"):
            audit(self.root)

    def test_nonfinite_timing_is_rejected(self):
        self.change(elapsed_sec=float("nan"))
        with self.assertRaisesRegex(RuntimeError, "Invalid sample"):
            audit(self.root)


if __name__ == "__main__":
    unittest.main()
