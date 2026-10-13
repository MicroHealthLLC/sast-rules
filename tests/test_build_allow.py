"""overrides.yaml `allow:` narrows a rule; it never loses one silently.

An allow entry is a reviewed false positive in rule form, so the build must
refuse one with no reason, one that names no rule, one whose regex does not
compile, and one aimed at a taint rule (where a not-regex has no single place
to go), and must add exactly the not-regex it was given to every rule it names.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build  # noqa: E402

IDS = {"mh.opengrep.generic.secrets.a": "", "mh.opengrep.generic.secrets.b": "", "mh.gitlab.other": ""}


def entries(*items: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    return build.allow_entries({"allow": list(items)}, IDS, errors), errors


class AllowEntries(unittest.TestCase):
    def test_prefix_names_every_rule_under_it(self) -> None:
        found, errors = entries({"rules": ["mh.opengrep.generic.secrets.*"], "not-regex": "x", "reason": "r"})
        self.assertEqual(errors, [])
        self.assertEqual(sorted(found), ["mh.opengrep.generic.secrets.a", "mh.opengrep.generic.secrets.b"])

    def test_refuses_no_reason(self) -> None:
        _, errors = entries({"rules": ["mh.gitlab.other"], "not-regex": "x"})
        self.assertTrue(any("no reason" in e for e in errors))

    def test_refuses_a_name_that_matches_nothing(self) -> None:
        _, errors = entries({"rules": ["mh.gitlab.missing"], "not-regex": "x", "reason": "r"})
        self.assertTrue(any("names no rule" in e for e in errors))

    def test_refuses_a_regex_that_does_not_compile(self) -> None:
        _, errors = entries({"rules": ["mh.gitlab.other"], "not-regex": "(", "reason": "r"})
        self.assertTrue(any("does not compile" in e for e in errors))


class ApplyAllow(unittest.TestCase):
    def test_wraps_a_bare_pattern_regex(self) -> None:
        rule = {"id": "r", "pattern-regex": "AKIA"}
        self.assertIsNone(build.apply_allow(rule, [{"not-regex": "EXAMPLE"}]))
        self.assertEqual(rule["patterns"], [{"pattern-regex": "AKIA"}, {"pattern-not-regex": "EXAMPLE"}])
        self.assertNotIn("pattern-regex", rule)

    def test_appends_to_patterns(self) -> None:
        rule = {"id": "r", "patterns": [{"pattern": "$X"}]}
        self.assertIsNone(build.apply_allow(rule, [{"not-regex": "a"}, {"not-regex": "b"}]))
        self.assertEqual(rule["patterns"][1:], [{"pattern-not-regex": "a"}, {"pattern-not-regex": "b"}])

    def test_refuses_a_taint_rule(self) -> None:
        rule = {"id": "r", "mode": "taint", "pattern-sinks": []}
        self.assertIn("search-mode", build.apply_allow(rule, [{"not-regex": "a"}]) or "")


if __name__ == "__main__":
    unittest.main()
