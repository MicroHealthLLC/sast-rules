"""The shared workflow keeps the controls every caller relies on.

Callers (each MicroHealth repository's sast.yml) only pin this workflow; what
the scan guarantees is decided here, so it is tested here:

* the scan is a blocking step; a SARIF upload failure is not (GitHub code
  scanning may be unavailable), and both outcomes are recorded under always();
* the scan runs with --network none, and its text output is not printed;
* the bundle is checked against dist/SHA256SUMS and the engine against
  engine.json before anything runs;
* rule ids are reported as published (--no-rewrite-rule-ids);
* every action is pinned to a commit with a version comment, every job's
  permissions are explicit, and nothing runs on pull_request_target.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
PIN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)(?:\s+#\s*(.*))?$")


def load(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def steps(name: str) -> dict[str, dict]:
    (job,) = load(name)["jobs"].values()
    return {s.get("id") or s.get("name"): s for s in job["steps"]}


class SharedWorkflowTests(unittest.TestCase):
    def test_scan_blocks_and_publication_does_not(self) -> None:
        s = steps("opengrep.yml")
        self.assertNotIn("continue-on-error", s["scan"])
        self.assertEqual(s["sarif_publication"].get("continue-on-error"), "true")
        self.assertIn("always()", s["sarif_publication"]["if"])
        self.assertIn("always()", s["publication_status"]["if"])
        env = str(s["publication_status"]["env"])
        self.assertIn("steps.scan.outcome", env)
        self.assertIn("steps.sarif_publication.outcome", env)

    def test_code_scanning_gets_no_inline_suppressions(self) -> None:
        # GitHub opens an alert for a SARIF result marked suppressed, so a
        # reviewed noopengrep failed the pull request that added it.
        s = steps("opengrep.yml")
        filt = s["sarif_for_github"]
        self.assertIn("sarif_for_code_scanning.py /out/sast.sarif /out/sast.github.sarif", filt["run"])
        self.assertIn("--network none", filt["run"])
        self.assertTrue(s["sarif_publication"]["with"]["sarif_file"].endswith("/out/sast.github.sarif"))
        self.assertIn("steps.sarif_for_github.outcome", s["sarif_publication"]["if"])
        # The artifact is still the full report, suppressed results included.
        self.assertIn("/out/sast.sarif", s["Upload report artifacts"]["with"]["path"])

    def test_scan_has_no_network_and_prints_no_source(self) -> None:
        run = steps("opengrep.yml")["scan"]["run"]
        self.assertIn("--network none", run)
        self.assertIn("--no-rewrite-rule-ids", run)
        self.assertIn(">/dev/null", run)

    def test_rules_and_engine_are_verified_before_use(self) -> None:
        run = steps("opengrep.yml")["engine"]["run"]
        self.assertIn("SHA256SUMS", run)
        self.assertIn("sha256sum -c", run)
        self.assertIn("engine.json", run)

    def test_every_scanner_is_on_by_default(self) -> None:
        inputs = load("security-scan.yml")["on"]["workflow_call"]["inputs"]
        for toggle in ("sast", "trivy", "sbom", "zap"):
            self.assertEqual(inputs[toggle]["default"], "true", toggle)
        jobs = load("security-scan.yml")["jobs"]
        self.assertEqual(jobs["report"]["needs"], ["sast", "trivy", "zap"])
        self.assertEqual(jobs["report"]["if"], "always()")
        for name in ("sast", "trivy", "zap"):
            self.assertTrue(jobs[name]["uses"].startswith("./.github/workflows/"), name)

    def test_no_partial_scan_feeds_ingest(self) -> None:
        dest = (WORKFLOWS.parent.parent / "scripts" / "destination.sh").read_text()
        self.assertIn("pull_request", dest)
        self.assertIn("_branch-scans/branch=", dest)
        for name in ("trivy.yml", "zap.yml", "security-scan.yml"):
            self.assertIn("steps.dest.outputs.upload == 'true'", (WORKFLOWS / name).read_text(), name)

    def test_actions_are_pinned_and_permissions_explicit(self) -> None:
        for path in WORKFLOWS.glob("*.yml"):
            text = path.read_text()
            self.assertNotIn("pull_request_target", text, path.name)
            for line in text.splitlines():
                m = PIN.match(line)
                if not m or m.group(1).startswith("./"):
                    continue
                self.assertRegex(m.group(1), r"@[0-9a-f]{40}$", f"{path.name}: {line.strip()}")
                self.assertTrue(m.group(2) and re.search(r"v\d", m.group(2)), line.strip())
            wf = yaml.load(text, Loader=yaml.BaseLoader)
            self.assertEqual(wf.get("permissions"), {"contents": "read"}, path.name)
            for name, job in wf["jobs"].items():
                self.assertIsInstance(job.get("permissions"), dict, f"{path.name}:{name}")
                for step in job.get("steps") or []:
                    if "docker build" in step.get("run", ""):
                        for line in step["run"].splitlines():
                            # `FROM scratch` only exports files from a FIPS
                            # stage (engines.yml); nothing runs in it.
                            if line.strip().startswith("FROM ") and line.strip() != "FROM scratch":
                                self.assertRegex(line, r"microhealthllc/fips-[a-z0-9-]+:dev-latest@sha256:[0-9a-f]{64}", path.name)


if __name__ == "__main__":
    unittest.main()
