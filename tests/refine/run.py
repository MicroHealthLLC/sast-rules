#!/usr/bin/env python3
"""Check every `refine` entry of overrides.yaml against its fixture here.

The rule is taken exactly as dist/internal.yaml ships it, so the build's
refinement is what is tested. A fixture line `ruleid: <mh id>` expects that
rule to report the NEXT line; `ok: <mh id>` expects it not to; any other
finding fails. Every refined rule must be named by at least one fixture.

    OPENGREP=<engine command> python3 tests/refine/run.py

Run from the repository root. $OPENGREP defaults to `opengrep`; it may be a
command line (a wrapper that runs the engine in the FIPS scan image with the
repository as its working directory), so every path here is relative.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path("tests/refine")
MARK = re.compile(r"\b(ruleid|ok):\s*(mh\.[\w.-]+)")


def main() -> int:
    refined = set(yaml.safe_load(Path("overrides.yaml").read_text())["refine"])
    rules = [r for r in yaml.safe_load(Path("dist/internal.yaml").read_text())["rules"] if r["id"] in refined]
    missing = refined - {r["id"] for r in rules}
    if missing:
        print(f"refined rules not in dist/internal.yaml: {sorted(missing)}", file=sys.stderr)
        return 1
    fixtures = sorted(p for p in HERE.iterdir() if p.is_file() and p.name != "run.py")
    with tempfile.TemporaryDirectory(prefix=".refine-test.", dir=".") as work:
        cfg = Path(work) / "refined.yaml"
        cfg.write_text(yaml.safe_dump({"rules": rules}, sort_keys=False, width=1_000_000))
        # Files, not the directory: the engine's default ignore list skips tests/.
        cmd = [*shlex.split(os.environ.get("OPENGREP", "opengrep")), "scan", "--config",
               os.path.relpath(cfg), "--no-rewrite-rule-ids", "--json", "--quiet",
               "--disable-version-check", *map(str, fixtures)]
        out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    report = json.loads(out)
    if report.get("errors"):
        print(json.dumps(report["errors"][:5], indent=1), file=sys.stderr)
        return 1
    found = {(r["path"], r["start"]["line"], r["check_id"]) for r in report["results"]}
    expected, named, bad = set(), set(), []
    for f in fixtures:
        for i, line in enumerate(f.read_text().splitlines(), 1):
            m = MARK.search(line)
            if not m:
                continue
            kind, rid = m.groups()
            named.add(rid)
            key = (str(f), i + 1, rid)
            if kind == "ruleid":
                expected.add(key)
                if key not in found:
                    bad.append(f"{f}:{i + 1}: expected a finding from {rid}")
            elif key in found:
                bad.append(f"{f}:{i + 1}: unexpected finding from {rid}")
    for p, line, rid in sorted(found - expected):
        if not any(b.startswith(f"{p}:{line}:") for b in bad):
            bad.append(f"{p}:{line}: unannotated finding from {rid}")
    bad += [f"no fixture in {HERE} names {rid}" for rid in sorted(refined - named)]
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 1
    print(f"refine fixtures: {len(refined)} refined rules, {len(expected)} expected findings, all pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
