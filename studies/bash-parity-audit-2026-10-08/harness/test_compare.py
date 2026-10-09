"""Guard the comparison contract against accidentally hiding real failures."""

import copy
import unittest
from compare import compare, line_counts, normalize


def record(text="ok\n"):
    return dict(
        case="quote",
        phase="cold",
        captures=[dict(actual=text, expected="ok\n", expected_path="quote.right")],
        stdout="",
        stderr="",
        returncode=0,
        timeout=False,
        remaining_descendants=[],
        leaked_descendants=False,
    )


class ComparisonTests(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(compare(record(), record())[0]["match"])

    def test_real_output_change(self):
        self.assertFalse(compare(record(), record("wrong\n"))[0]["match"])

    def test_missing_capture(self):
        candidate = record()
        candidate["captures"] = []
        self.assertFalse(compare(record(), candidate)[0]["match"])

    def test_changed_expected_file(self):
        candidate = record()
        candidate["captures"][0]["expected"] = "wrong\n"
        self.assertFalse(compare(record(), candidate)[0]["match"])

    def test_line_locations_are_trivial(self):
        self.assertEqual(
            normalize("./quote: line 42: error\n", "quote"),
            normalize("./quote: line 1: error\n", "quote"),
        )

    def test_exit_status_is_not_a_line_number(self):
        self.assertFalse(compare(record("127\n"), record("0\n"))[0]["match"])

    def test_timeout_rejected(self):
        candidate = record()
        candidate["timeout"] = True
        self.assertFalse(compare(record(), candidate)[0]["match"])

    def test_extra_descendants_rejected(self):
        candidate = record()
        candidate["leaked_descendants"] = True
        self.assertFalse(compare(record(), candidate)[0]["match"])

    def test_identical_baseline_cleanup_allowed(self):
        candidate = record()
        candidate["leaked_descendants"] = True
        self.assertTrue(compare(candidate, copy.deepcopy(candidate))[0]["match"])

    def test_unexplained_status_change_rejected(self):
        candidate = record()
        candidate["returncode"] = 2
        self.assertFalse(compare(record(), candidate)[0]["match"])

    def test_identical_abnormal_driver_status_rejected(self):
        candidate = record()
        candidate["returncode"] = 2
        self.assertFalse(compare(candidate, copy.deepcopy(candidate))[0]["match"])

    def test_extra_nondiff_driver_output_rejected(self):
        candidate = record()
        candidate["stdout"] = "unexpected extra message\n"
        self.assertFalse(compare(record(), candidate)[0]["match"])

    def test_zombie_baseline_does_not_hide_live_candidate_child(self):
        reference = record()
        reference["leaked_descendants"] = True
        reference["diagnostics"] = [{"status": "Name:\tsudo\nState:\tZ (zombie)\n"}]
        candidate = copy.deepcopy(reference)
        candidate["diagnostics"].append({"status": "Name:\tsleep\nState:\tS (sleeping)\n"})
        self.assertFalse(compare(reference, candidate)[0]["match"])

    def test_matching_intentional_background_children_allowed(self):
        reference = record()
        reference["leaked_descendants"] = True
        reference["diagnostics"] = [{"status": "Name:\tsleep\nState:\tS (sleeping)\n"}]
        self.assertTrue(compare(reference, copy.deepcopy(reference))[0]["match"])

    def test_empty_transcript_has_no_lines(self):
        self.assertEqual(line_counts("", "")["matched"], 0)

    def test_line_diff_accounts_for_both_sides(self):
        counts = line_counts("one\ntwo\n", "one\nthree\nfour\n")
        self.assertEqual(counts["matched"], 1)
        self.assertEqual(counts["replaced_reference"], 1)
        self.assertEqual(counts["replaced_candidate"], 2)


if __name__ == "__main__":
    unittest.main()
