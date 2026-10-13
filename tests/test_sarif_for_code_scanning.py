"""GitHub code scanning gets the SARIF without the results suppressed in
source: it opens an alert for them otherwise, and a reviewed suppression fails
the pull request that added it. A suppression that is not accepted yet is not
one, and the full report keeps everything."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from sarif_for_code_scanning import for_code_scanning  # noqa: E402


def _result(rule: str, *suppressions: dict) -> dict:
    r: dict = {"ruleId": rule, "message": {"text": rule}}
    if suppressions:
        r["suppressions"] = list(suppressions)
    return r


def _sarif(*results: dict) -> dict:
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Opengrep OSS"}}, "results": list(results)}]}


class ForCodeScanningTests(unittest.TestCase):
    def test_accepted_suppressions_are_left_out(self) -> None:
        sarif, kept, dropped = for_code_scanning(
            _sarif(_result("open"), _result("quiet", {"state": "accepted"}), _result("quiet-no-state", {"kind": "inSource"}))
        )
        self.assertEqual([r["ruleId"] for r in sarif["runs"][0]["results"]], ["open"])
        self.assertEqual((kept, dropped), (1, 2))

    def test_a_suppression_not_yet_accepted_still_reports(self) -> None:
        sarif, kept, dropped = for_code_scanning(
            _sarif(_result("review", {"state": "underReview"}), _result("rejected", {"state": "rejected"}))
        )
        self.assertEqual(len(sarif["runs"][0]["results"]), 2)
        self.assertEqual((kept, dropped), (2, 0))

    def test_rules_and_tool_are_passed_through(self) -> None:
        src = _sarif(_result("quiet", {"state": "accepted"}))
        src["runs"][0]["tool"]["driver"]["rules"] = [{"id": "quiet"}]
        sarif, _, _ = for_code_scanning(src)
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["rules"], [{"id": "quiet"}])

    def test_cli_writes_the_copy_and_leaves_the_input_alone(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d, "sast.sarif"), Path(d, "sast.github.sarif")
            original = _sarif(_result("open"), _result("quiet", {"state": "accepted"}))
            src.write_text(json.dumps(original))
            out = subprocess.run(
                [sys.executable, str(SCRIPTS / "sarif_for_code_scanning.py"), str(src), str(dst)],
                check=True, capture_output=True, text=True,
            ).stdout
            self.assertEqual(out.strip(), "1 1")
            self.assertEqual(json.loads(src.read_text()), original)
            self.assertEqual(len(json.loads(dst.read_text())["runs"][0]["results"]), 1)


if __name__ == "__main__":
    unittest.main()
