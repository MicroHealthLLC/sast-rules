"""The scan outcome and the SARIF publication outcome are recorded separately:
an upload that fails never hides a scan that failed, and a scan that passed is
never reported as failed because GitHub could not take its SARIF."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from publication_status import status_from_outcomes, summary_for_status  # noqa: E402

AT = "2026-10-12T10:00:00Z"
RUN = "https://github.com/o/r/actions/runs/1"


class PublicationOutcomeTests(unittest.TestCase):
    def test_upload_failure_warns_but_keeps_scan_success_separate(self) -> None:
        status = status_from_outcomes("success", "failure", recorded_at_utc=AT)
        summary = summary_for_status(status, RUN)
        self.assertEqual(status["scan_status"], "success")
        self.assertEqual(status["sarif_publication_status"], "degraded")
        self.assertIn("::warning::", summary)
        self.assertIn("**SUCCESS**", summary)
        self.assertIn("**DEGRADED**", summary)

    def test_scanner_failure_remains_failed_even_if_upload_also_fails(self) -> None:
        status = status_from_outcomes("failure", "failure", recorded_at_utc=AT)
        summary = summary_for_status(status, RUN)
        self.assertEqual(status["scan_status"], "failed")
        self.assertIn("::error::The SAST scan did not succeed.", summary)

    def test_successful_publication_does_not_hide_a_scanner_failure(self) -> None:
        status = status_from_outcomes("failure", "success", recorded_at_utc=AT)
        self.assertEqual(status["scan_status"], "failed")
        self.assertEqual(status["sarif_publication_status"], "published")

    def test_unavailable_publication_is_not_reported_as_success(self) -> None:
        status = status_from_outcomes("success", "skipped", recorded_at_utc=AT)
        self.assertEqual(status["sarif_publication_status"], "degraded")

    def test_the_command_writes_its_record_and_exits_successfully(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "publication_status.py"
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ | {
                "SCAN_OUTCOME": "success",
                "SARIF_UPLOAD_OUTCOME": "failure",
                "GITHUB_REPOSITORY": "org/repo",
                "GITHUB_SHA": "0123456789abcdef",
                "GITHUB_REF": "refs/heads/main",
                "GITHUB_RUN_ID": "42",
                "GITHUB_RUN_ATTEMPT": "1",
                "GITHUB_SERVER_URL": "https://github.com",
                "GITHUB_STEP_SUMMARY": str(Path(tmp) / "summary.md"),
                "GITHUB_OUTPUT": str(Path(tmp) / "output"),
            }
            result = subprocess.run(
                [sys.executable, str(script)], cwd=tmp, env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads((Path(tmp) / "publication-status.json").read_text())
            self.assertEqual(record["sarif_publication_status"], "degraded")
            self.assertIn("sarif_publication_status=degraded", (Path(tmp) / "output").read_text())


if __name__ == "__main__":
    unittest.main()
