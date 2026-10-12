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


if __name__ == "__main__":
    unittest.main()
