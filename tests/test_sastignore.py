"""Every rule-test fixture in rules/microhealth/ is listed in .sastignore.

This repository scans itself with its own workflow, which passes each
.sastignore line to Opengrep as --exclude. A fixture holds deliberate
`ruleid:` cases, so one left out of .sastignore becomes a code scanning alert
against the rule's own test (alerts #66 and #67: the C# certificate-validation
fixture, added without its entry).
"""

from __future__ import annotations

import fnmatch
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patterns() -> list[str]:
    out = []
    for line in (ROOT / ".sastignore").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def excluded(path: str, globs: list[str]) -> bool:
    for glob in globs:
        if glob.endswith("/"):
            if path.startswith(glob):
                return True
        elif fnmatch.fnmatchcase(path, glob):
            return True
        elif "/" not in glob and fnmatch.fnmatchcase(path.rsplit("/", 1)[-1], glob):
            return True
    return False


def fixtures() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "rules/microhealth"], cwd=ROOT,
                             check=True, capture_output=True, text=True).stdout.split()
    return [p for p in tracked if not p.endswith(".yaml")]


class SastignoreTests(unittest.TestCase):
    def test_every_rule_fixture_is_excluded_from_the_self_scan(self):
        globs = patterns()
        found = fixtures()
        self.assertIn("rules/microhealth/csharp/certificate-validation-disabled.cs", found)
        missing = [p for p in found if not excluded(p, globs)]
        self.assertEqual(missing, [], "rule-test fixtures missing from .sastignore: add each, "
                                      "with a comment saying it is a fixture")

    def test_rule_definitions_are_still_scanned(self):
        globs = patterns()
        rules = ["rules/microhealth/csharp/certificate-validation-disabled.yaml",
                 "rules/microhealth/python/fips-non-approved-hash.yaml"]
        self.assertEqual([p for p in rules if excluded(p, globs)], [])


if __name__ == "__main__":
    unittest.main()
