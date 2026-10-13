"""A rule's license decides its bundles, also for MicroHealth's modified copies
of upstream rules: a copy keeps the upstream license in its `# License:` header,
and an LGPL or Commons Clause rule must never reach the product bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOCK = json.loads((ROOT / "rules.lock.json").read_text())["rules"]
LICENSES = yaml.safe_load((ROOT / "licenses.yaml").read_text())
HEADER = re.compile(r"^#\s*License:\s*(.+?)\s*$", re.MULTILINE)


def license_of(path: Path) -> str:
    m = HEADER.search(path.read_text(encoding="utf-8"))
    assert m, f"{path}: no # License: header"
    for pattern, key in LICENSES["headers"].items():
        if re.search(pattern, m.group(1)):
            return key
    raise AssertionError(f"{path}: license header not recognised")


def test_microhealth_rules_keep_their_header_license():
    seen = 0
    for rid, entry in LOCK.items():
        if entry["source"] != "microhealth" or entry["status"] == "retired":
            continue
        seen += 1
        assert entry["license"] == license_of(ROOT / entry["path"]), rid
        assert set(entry["bundles"]) <= set(LICENSES["licenses"][entry["license"]]["bundles"]), rid
    assert seen


def test_product_bundle_holds_only_product_licenses():
    allowed = {k for k, v in LICENSES["licenses"].items() if "product" in v.get("bundles", [])}
    rules = yaml.safe_load((ROOT / "dist" / "product.yaml").read_text())["rules"]
    bad = [r["id"] for r in rules if r["metadata"]["mh_license"] not in allowed]
    assert not bad, bad


def test_upstream_copies_are_disabled_in_favour_of_their_replacement():
    for rid, entry in LOCK.items():
        if entry["source"] != "microhealth":
            continue
        rule = yaml.safe_load((ROOT / entry["path"]).read_text())["rules"][0]
        old = (rule.get("metadata") or {}).get("mh_replaces")
        if old:
            assert LOCK[old]["status"] == "disabled", old
            assert rid in LOCK[old]["reason"], old
