#!/usr/bin/env python3
"""Move every MicroHealth FIPS image pin to the digest its tag points at now,
or (--check) refuse to go on while any pin is stale.

fips-container rebuilds the images nightly and on every release, so a tag
moves and the pinned digest goes stale. No release of this repository may run
on a stale base (owner's order, 2026-10-22): `.github/workflows/fips-base-images.yml`
runs this (weekly, and whenever fips-container dispatches it after a release),
opens ONE pull request into integration and merges it at once; `ci.yml` and
`release.yml` run `--check` before anything else on integration and main.

Pins look like `<registry>/microhealthllc/fips-<image>:<tag>@sha256:<digest>`
and are found in every tracked text file that can carry one (today only
fips-images.json; every workflow and script reads them through
scripts/fips-image.sh, and no pin may be written into .github/workflows/:
tests/test_workflow.py). `tests/`, `upstream/` and `dist/` are not pins.

The digest is read with `aws ecr batch-get-image`, which needs only the pull
permission the CI role already has (it holds no ecr:DescribeImages).

    scripts/fips_bump.py                       rewrite stale pins
    scripts/fips_bump.py --check               exit 1 if any pin is stale or unresolvable; writes nothing
    scripts/fips_bump.py --from-file d.json    {"fips-go:dev-latest": "sha256:..."} instead of ECR (offline)
    scripts/fips_bump.py --summary out.md      a markdown table of the changes

Without --check, a tag that cannot be resolved keeps its pin and is reported
(it must not stop every other image from moving); nothing resolving at all
(credentials, region) is an error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = "295669632222.dkr.ecr.us-east-1.amazonaws.com"
PIN = re.compile(
    re.escape(REGISTRY) + r"/microhealthllc/(fips-[a-z0-9-]+):([A-Za-z0-9._-]+)@(sha256:[0-9a-f]{64})"
)
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
CANDIDATE = re.compile(r"(^|/)Dockerfile($|\.)|\.Dockerfile$|\.(ya?ml|json|sh|py|toml)$")
NOT_PINS = ("tests/", "upstream/", "dist/")
MEDIA = [
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
]
PENDING = ("the FIPS bump is pending — wait for fips-base-images.yml to merge "
           "(or dispatch it), then promote integration again.")


def candidates(root: Path) -> list[str]:
    """Tracked files that can carry a pin."""
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if CANDIDATE.search(p) and not p.startswith(NOT_PINS)]


def ecr_digest(image: str, tag: str) -> str | None:
    out = subprocess.run(
        ["aws", "ecr", "batch-get-image", "--registry-id", REGISTRY.split(".")[0],
         "--region", os.environ.get("AWS_REGION", "us-east-1"),
         "--repository-name", f"microhealthllc/{image}", "--image-ids", f"imageTag={tag}",
         "--accepted-media-types", *MEDIA,
         "--query", "images[0].imageId.imageDigest", "--output", "text"],
        capture_output=True, text=True,
    )
    if out.returncode:
        last = (out.stderr.strip().splitlines() or [f"exit {out.returncode}"])[-1]
        print(f"fips_bump: aws: {last}", file=sys.stderr)
    return out.stdout.strip()


def resolver(from_file: str | None):
    if from_file:
        table = json.loads(Path(from_file).read_text(encoding="utf-8"))
        return lambda image, tag: table.get(f"{image}:{tag}")
    return ecr_digest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--from-file")
    ap.add_argument("--summary")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)
    root = Path(args.root)
    resolve = resolver(args.from_file)

    texts: dict[str, str] = {}
    seen: dict[str, set[str]] = {}  # "fips-go:dev-latest" -> digests pinned now
    for rel in candidates(root):
        text = (root / rel).read_text(encoding="utf-8")
        hits = PIN.findall(text)
        if not hits:
            continue
        texts[rel] = text
        for image, tag, digest in hits:
            seen.setdefault(f"{image}:{tag}", set()).add(digest)

    if not seen:
        print("::error::fips_bump: no microhealthllc/fips-* pin found in the tracked files (fips-images.json has them)")
        return 1

    latest: dict[str, str] = {}
    unresolved: list[str] = []
    for key in sorted(seen):
        image, tag = key.split(":", 1)
        digest = resolve(image, tag) or ""
        if DIGEST.fullmatch(digest):
            latest[key] = digest
        else:
            print(f"fips_bump: cannot resolve {key} in {REGISTRY} (got {digest!r}); pin left as is", file=sys.stderr)
            unresolved.append(key)

    changes = [(key, old, latest[key]) for key in sorted(seen) if key in latest
               for old in sorted(seen[key]) if old != latest[key]]

    touched: list[str] = []
    if not args.check:
        def sub(m: re.Match) -> str:
            key = f"{m.group(1)}:{m.group(2)}"
            return f"{REGISTRY}/microhealthllc/{key}@{latest[key]}" if key in latest else m.group(0)
        for rel, text in texts.items():
            new = PIN.sub(sub, text)
            if new != text:
                (root / rel).write_text(new, encoding="utf-8")
                touched.append(rel)

    table = "\n".join(["| Image | Old digest | New digest |", "|---|---|---|",
                       *(f"| `{k}` | `{o[7:19]}` | `{n[7:19]}` |" for k, o, n in changes)])
    missing = (f"Not resolvable in ECR (pin left as is): {', '.join(f'`{k}`' for k in unresolved)}"
               if unresolved else "")
    if args.summary:
        Path(args.summary).write_text((table + "\n" if changes else "") + (missing + "\n" if missing else ""),
                                      encoding="utf-8")
    print(f"fips_bump: {len(seen)} image tag(s), {len(changes)} stale pin(s), {len(touched)} file(s) rewritten"
          + (f": {', '.join(touched)}" if touched else ""))
    if changes:
        print(table)
    if missing:
        print(missing)

    if args.check:
        if changes or unresolved:
            what = ", ".join([*(f"{k} is stale" for k, _, _ in changes), *(f"{k} is unresolvable" for k in unresolved)])
            print(f"::error title=Stale FIPS image pin::{what}: {PENDING}")
            return 1
        print("fips_bump: every FIPS image pin is the newest digest of its tag.")
        return 0
    if seen and not latest:
        print(f"::error::fips_bump: none of {', '.join(sorted(seen))} could be resolved in {REGISTRY}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
