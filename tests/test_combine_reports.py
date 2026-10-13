"""The combined report never reads a scan that did not run as a clean one."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "combine_reports.py"


def run(art: Path, env: dict[str, str]) -> tuple[int, dict]:
    out = art.parent / "out"
    base = {k: v for k, v in os.environ.items() if not k.startswith(("ENABLED_", "RESULT_", "GITHUB_STEP"))}
    p = subprocess.run([sys.executable, str(SCRIPT), str(art), str(out)], env=base | env,
                       capture_output=True, text=True)
    return p.returncode, json.loads((out / "security-report.json").read_text())


def write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc))


ON = {f"ENABLED_{s}": "true" for s in ("SAST", "TRIVY", "SBOM", "ZAP")}


class CombineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.art = self.tmp / "artifacts"
        write(self.art / "sast-reports" / "sast.json", {"results": [
            {"check_id": "mh.a", "extra": {"severity": "ERROR"}},
            {"check_id": "mh.b", "extra": {"severity": "WARNING", "is_ignored": True}},
        ], "ruleset": {"rules_evaluated": ["mh.a", "mh.b"], "bundle": "internal"}})
        write(self.art / "trivy-repository" / "trivy-fs.json", {"Results": [
            {"Vulnerabilities": [{"Severity": "CRITICAL"}], "Misconfigurations": [{"Severity": "LOW", "Status": "PASS"}]}]})
        write(self.art / "trivy-repository" / "sbom.cdx.json", {"bomFormat": "CycloneDX", "components": [{}, {}]})
        write(self.art / "zap-reports" / "zap-status.json", {"status": "not_run", "reason": "no target URL"})

    def test_everything_on_combines_into_one_report(self) -> None:
        rc, doc = run(self.art, ON)
        self.assertEqual(rc, 0)
        sc = doc["scanners"]
        self.assertEqual(sc["sast"]["findings"]["HIGH"], 1)  # the suppressed one is not counted
        self.assertEqual(sc["sast"]["suppressed_inline"], 1)
        self.assertEqual(sc["trivy"]["targets"][0]["findings"]["vulnerabilities"]["CRITICAL"], 1)
        self.assertEqual(sc["trivy"]["targets"][0]["findings"]["misconfigurations"]["LOW"], 0)
        self.assertEqual(sc["sbom"]["documents"], [{"target": "repository", "components": 2}])
        self.assertEqual(sc["zap"]["status"], "not_run")
        self.assertIsNone(sc["zap"]["alerts"])  # not run is not zero
        self.assertEqual(doc["totals"]["CRITICAL"], 1)

    def test_a_scanner_that_was_on_and_left_no_report_fails_the_run(self) -> None:
        (self.art / "sast-reports" / "sast.json").unlink()
        rc, doc = run(self.art, ON | {"RESULT_SAST": "failure"})
        self.assertEqual(rc, 1)
        self.assertEqual(doc["scanners"]["sast"]["status"], "failed")
        self.assertIsNone(doc["scanners"]["sast"]["findings"])

    def test_a_scanner_switched_off_is_disabled_not_clean(self) -> None:
        rc, doc = run(self.art, ON | {"ENABLED_ZAP": "false"})
        self.assertEqual(doc["scanners"]["zap"], {"status": "disabled", "alerts": None})
        self.assertEqual(rc, 0)

    def test_a_planned_image_that_left_no_report_fails_the_run(self) -> None:
        planned = json.dumps([{"kind": "repo", "ref": ""},
                              {"kind": "image", "ref": "1.dkr.ecr.us-east-1.amazonaws.com/a/vllm:sha-1"}])
        rc, doc = run(self.art, ON | {"TRIVY_TARGETS": planned, "RESULT_TRIVY": "failure"})
        self.assertEqual(rc, 1)
        names = {t["target"]: t["status"] for t in doc["scanners"]["trivy"]["targets"]}
        self.assertEqual(names, {"repository": "ran", "vllm": "failed"})
        self.assertEqual(doc["scanners"]["trivy"]["status"], "partial")

    def test_fail_on_counts_every_scanner(self) -> None:
        self.assertEqual(run(self.art, ON | {"FAIL_ON": "critical"})[0], 1)
        self.assertEqual(run(self.art, ON | {"FAIL_ON": "none"})[0], 0)


if __name__ == "__main__":
    unittest.main()
