#!/usr/bin/env python3
"""Move engine.json to the newest Opengrep release (or --version X.Y.Z).

Downloads each musl asset, records its sha256, and prints what changed. The
shared workflow downloads the same asset and refuses it unless the hash matches,
so a release replaced after the fact cannot reach a scan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine.json"
REPO = "opengrep/opengrep"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "sast-rules-bump"})
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (fixed https URL)
        return resp.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version")
    args = ap.parse_args()
    engine = json.loads(ENGINE.read_text())
    if args.version:
        version = args.version.lstrip("v")
    else:
        latest = json.loads(fetch(f"https://api.github.com/repos/{REPO}/releases/latest"))
        version = str(latest["tag_name"]).lstrip("v")
    if version == engine["version"]:
        print(f"Opengrep is already at {version}.")
        return 0
    for arch, asset in engine["assets"].items():
        url = f"https://github.com/{REPO}/releases/download/v{version}/{asset['file']}"
        asset["sha256"] = hashlib.sha256(fetch(url)).hexdigest()
        print(f"{arch}: {asset['file']} {asset['sha256']}")
    old = engine["version"]
    engine["version"] = version
    ENGINE.write_text(json.dumps(engine, indent=2) + "\n")
    print(f"Opengrep {old} → {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
