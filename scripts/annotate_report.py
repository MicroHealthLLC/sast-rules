#!/usr/bin/env python3
"""Stamp a scan's JSON report with the ruleset and engine that produced it.

    annotate_report.py <report.json> <bundle.yaml> <bundle-name> <rules-commit> <engine-version>

Adds a top-level `ruleset` object:

    {"name": "sast-rules", "bundle": "internal", "commit": "<sha>",
     "bundle_sha256": "<sha256>", "engine": {"name": "opengrep", "version": "1.30.2"},
     "rules_evaluated": ["mh.gitlab....", ...]}

`rules_evaluated` is every rule the scan ran. A consumer that auto-resolves
findings absent from a report must only do so for rules in this list: a rule
that was retired or disabled did not look, so its absence says nothing about
the code (Tueri Core treats it that way).

Every result's `check_id` is reduced to its `mh.` id, in case an engine adds a
path prefix (`--no-rewrite-rule-ids` already prevents it in Opengrep).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml


def stable_id(check_id: str) -> str:
    if check_id.startswith("mh."):
        return check_id
    i = check_id.find(".mh.")
    return check_id[i + 1 :] if i >= 0 else check_id


def main(argv: list[str]) -> int:
    report_path, bundle_path, bundle, commit, engine_version = argv
    raw = Path(bundle_path).read_bytes()
    rules = yaml.safe_load(raw)["rules"]
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    for result in report.get("results") or []:
        result["check_id"] = stable_id(str(result.get("check_id", "")))
    report["ruleset"] = {
        "name": "sast-rules",
        "bundle": bundle,
        "commit": commit,
        "bundle_sha256": hashlib.sha256(raw).hexdigest(),
        "engine": {"name": "opengrep", "version": engine_version},
        "rules_evaluated": sorted(r["id"] for r in rules),
    }
    Path(report_path).write_text(json.dumps(report) + "\n", encoding="utf-8")
    found = sum(1 for r in report.get("results") or [] if not (r.get("extra") or {}).get("is_ignored"))
    print(f"{found} findings ({len(report['ruleset']['rules_evaluated'])} rules, bundle {bundle} @ {commit[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
