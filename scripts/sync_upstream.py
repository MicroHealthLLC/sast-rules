#!/usr/bin/env python3
"""Vendor one upstream source at a ref: copy its rule files and licenses into
upstream/<name>/, record the pin in sources.yaml, rebuild, and write a summary
of what changed for the pull request.

    python3 scripts/sync_upstream.py gitlab                 # newest vX.Y.Z tag
    python3 scripts/sync_upstream.py gitlab --ref v2.10.1   # a given ref
    python3 scripts/sync_upstream.py opengrep --ref main    # one-time import

A source marked `track: frozen` is refused unless --ref is given: it is not
expected to change (opengrep-rules was archived on 2025-11-28).

Only rule documents (YAML with a top-level `rules:` list) and LICENSE files are
copied. Upstream files are never edited here or by hand; turn a rule off or
re-grade it in overrides.yaml, or copy it into rules/microhealth/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (sibling script, not a package)

ROOT = build.ROOT
_SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def newest_tag(url: str) -> str:
    tags = []
    for line in git("ls-remote", "--tags", "--refs", url).splitlines():
        name = line.split("refs/tags/", 1)[-1]
        m = _SEMVER.match(name)
        if m:
            tags.append((tuple(int(x) for x in m.groups()), name))
    if not tags:
        raise SystemExit(f"no vX.Y.Z tags at {url}")
    return max(tags)[1]


def set_pin(name: str, ref: str, commit: str) -> None:
    path = ROOT / "sources.yaml"
    text = path.read_text(encoding="utf-8")
    block = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  \S|\Z)", text)
    if not block:
        raise SystemExit(f"sources.yaml has no source {name!r}")
    body = block.group(1)
    body = re.sub(r"(?m)^(    ref: ).*$", rf"\g<1>{ref}", body)
    body = re.sub(r"(?m)^(    commit: ).*$", rf"\g<1>{commit}", body)
    path.write_text(text[: block.start(1)] + body + text[block.end(1) :], encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source")
    ap.add_argument("--ref")
    ap.add_argument("--summary", type=Path, help="write a Markdown change summary here")
    args = ap.parse_args()

    sources = build.load_yaml(ROOT / "sources.yaml")["sources"]
    src = sources.get(args.source)
    if not src or "url" not in src:
        raise SystemExit(f"{args.source!r} is not an upstream source in sources.yaml")
    if src.get("track") == "frozen" and not args.ref:
        raise SystemExit(f"{args.source} is frozen; pass --ref to re-import it deliberately")
    ref = args.ref or newest_tag(src["url"])
    if ref == src.get("ref") and not args.ref:
        print(f"{args.source} is already at {ref}.")
        return 0

    before = json.loads(build.LOCK.read_text()) if build.LOCK.exists() else {"rules": {}}
    dest = ROOT / src["path"]
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "src"
        git("clone", "--quiet", "--depth", "1", "--branch", ref, src["url"], str(clone))
        commit = git("rev-parse", "HEAD", cwd=clone)
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        include = src.get("include") or ["."]
        licenses = build.load_yaml(ROOT / "licenses.yaml")
        no_vendor = {k for k, v in licenses["licenses"].items() if v.get("vendor") is False}
        for top in include:
            base = clone / top
            for path, _rel, _doc in build.rule_files(base):
                if src["license"] == "per-file":
                    lic = build.classify(path.read_text(encoding="utf-8"), licenses.get("headers", {}))
                    if lic in no_vendor:
                        continue  # not ours to redistribute (licenses.yaml says why)
                target = dest / path.relative_to(clone)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        roots = [clone] + [clone / top for top in include if top != "."]
        found = {f for r in roots for f in r.glob("LICENSE*")}
        found |= {f for top in include for f in (clone / top).rglob("LICENSE*")}
        for lic in sorted(found):
            if build.SKIP_PARTS & set(lic.relative_to(clone).parts):
                continue
            target = dest / lic.relative_to(clone)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(lic, target)
    set_pin(args.source, ref, commit)
    if build.build(check=False):
        return 1

    after = json.loads(build.LOCK.read_text())
    old, new = before.get("rules", {}), after["rules"]
    added = sorted(k for k in new if k not in old)
    retired = sorted(k for k, v in new.items() if v["status"] == "retired" and old.get(k, {}).get("status") != "retired")
    changed = sorted(k for k in new if k in old and new[k]["sha256"] != old[k]["sha256"] and new[k]["status"] != "retired")
    relicensed = sorted(k for k in new if k in old and new[k]["license"] != old[k].get("license"))
    lines = [
        f"## {args.source}: {src.get('ref')} → {ref}",
        "",
        f"Upstream commit `{commit}`. Bundles: "
        + ", ".join(f"{b} {n}" for b, n in after["bundles"].items()),
        "",
        f"- added: {len(added)}",
        f"- changed: {len(changed)}",
        f"- retired (left upstream; kept in the lock, out of every bundle): {len(retired)}",
        f"- license changed: {len(relicensed)}",
        "",
    ]
    for title, ids in (("Added", added), ("Changed", changed), ("Retired", retired), ("License changed", relicensed)):
        if ids:
            lines += [f"<details><summary>{title} ({len(ids)})</summary>", ""]
            lines += [f"- `{i}` ({new[i]['license']})" for i in ids]
            lines += ["", "</details>", ""]
    text = "\n".join(lines)
    if args.summary:
        args.summary.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
