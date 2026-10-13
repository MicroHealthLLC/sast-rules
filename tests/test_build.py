"""The build's own guards: a configuration file may not repeat a key (YAML
would silently keep only the last), and a `refine` override can only narrow
an upstream rule."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build import load_config, refine  # noqa: E402


class StrictConfig(unittest.TestCase):
    def test_duplicate_top_level_key_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "overrides.yaml"
            p.write_text("disabled:\n  a: one\ndisabled:\n  b: two\n")
            with self.assertRaises(yaml.YAMLError):
                load_config(p)

    def test_overrides_yaml_loads(self) -> None:
        load_config(Path(__file__).resolve().parents[1] / "overrides.yaml")


class Refine(unittest.TestCase):
    def test_add_appends_to_patterns(self) -> None:
        rule = {"id": "r", "patterns": [{"pattern": "f($X)"}]}
        self.assertIsNone(refine(rule, {"add": [{"pattern-not": "f(1)"}]}))
        self.assertEqual(rule["patterns"], [{"pattern": "f($X)"}, {"pattern-not": "f(1)"}])

    def test_lone_pattern_is_wrapped(self) -> None:
        rule = {"id": "r", "pattern-regex": "abc"}
        self.assertIsNone(refine(rule, {"add": [{"pattern-not-regex": "abcd"}]}))
        self.assertNotIn("pattern-regex", rule)
        self.assertEqual(rule["patterns"], [{"pattern-regex": "abc"}, {"pattern-not-regex": "abcd"}])

    def test_exclude_paths_extends_existing(self) -> None:
        rule = {"id": "r", "pattern": "x", "paths": {"exclude": ["*.svg"]}}
        self.assertIsNone(refine(rule, {"exclude_paths": ["*.lock"]}))
        self.assertEqual(rule["paths"]["exclude"], ["*.svg", "*.lock"])

    def test_only_narrowing_clauses(self) -> None:
        rule = {"id": "r", "patterns": [{"pattern": "x"}]}
        self.assertIsNotNone(refine(rule, {"add": [{"pattern-either": [{"pattern": "y"}]}]}))

    def test_taint_rules_are_refused(self) -> None:
        rule = {"id": "r", "mode": "taint", "pattern-sources": [], "pattern-sinks": []}
        self.assertIsNotNone(refine(rule, {"add": [{"pattern-not": "x"}]}))

    def test_empty_refinement_is_refused(self) -> None:
        self.assertIsNotNone(refine({"id": "r", "pattern": "x"}, {"reason": "r"}))


if __name__ == "__main__":
    unittest.main()
