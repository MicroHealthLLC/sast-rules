#!/usr/bin/env python3
"""Move every MicroHealth FIPS image pin to the newest image of its channel,
or (--check) refuse to go on while any pin is stale.

fips-container rebuilds the images nightly and on every release, so the
pinned digest goes stale. No release of this repository may run
on a stale base (owner's order, 2026-10-22): `.github/workflows/fips-base-images.yml`
runs this (weekly, and whenever fips-container dispatches it after a release),
opens ONE pull request into integration and merges it at once; `ci.yml` and
`release.yml` run `--check` before anything else on integration and main.

Pins look like `<registry>/microhealthllc/fips-<image>:<tag>@sha256:<digest>`
and are found in every tracked text file that can carry one (today only
fips-images.json; every workflow and script reads them through
scripts/fips-image.sh, and no pin may be written into .github/workflows/:
tests/test_workflow.py). `tests/`, `upstream/` and `dist/` are not pins.

WHICH IMAGE IS NEWEST (ECR.2, ~/ecr2-analysis/CONTRACT.md §3; the same
algorithm in every MicroHealth bump script and freshness gate). The fips-* ECR
repositories are becoming IMMUTABLE, so the moving `dev-latest` tag goes away.
Every integration build of fips-container pushes a unique dev-channel tag,
`dev-<YYYYMMDDHHMM>-<sha8>` (`<pgmajor>-dev-...` for fips-cnpg-postgres*). For
a pin on the dev channel (`dev-latest` or a dev-channel tag):
  1. `aws ecr describe-images --filter tagStatus=TAGGED` (the CLI pages);
  2. candidates are images with a tag matching DEV_TAG;
  3. the one with the greatest imagePushedAt wins: the pin becomes
     `<that tag>@<its imageDigest>`;
  4. no candidate (fips-container not migrated yet): fall back to
     `batch-get-image imageTag=dev-latest`, keep the `dev-latest` tag, and say
     so. Remove this fallback once fips-container stops pushing dev-latest.
Any other tag is unique and is resolved as itself with batch-get-image.
"Fresh" means the pinned DIGEST equals that answer: a `dev-latest@sha256:D`
pin whose D is the newest image is fresh (the pull is by digest); the next
bump renames it to `<dev tag>@sha256:D`. The CI role may describe fips-* images
only (dsc-aws-applications stacks/ecr/ci-image-discovery.tf).

    scripts/fips_bump.py                       rewrite stale (and renamed) pins
    scripts/fips_bump.py --check               exit 1 if any pin is stale or unresolvable; writes nothing
    scripts/fips_bump.py --from-file d.json    answers instead of ECR (offline):
        {"fips-go": "dev-202611271200-0123abcd@sha256:..."}   the dev channel's newest image
        {"fips-go:<tag>": "sha256:..."}                          one tag's digest
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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = "295669632222.dkr.ecr.us-east-1.amazonaws.com"
PIN = re.compile(
    re.escape(REGISTRY) + r"/microhealthllc/(fips-[a-z0-9-]+):([A-Za-z0-9._-]+)@(sha256:[0-9a-f]{64})"
)
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
DEV_TAG = re.compile(r"^(\d+-)?dev-\d{12}-[0-9a-f]{8}$")
TAG = re.compile(r"[A-Za-z0-9._-]+")
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


def follows_dev_channel(tag: str) -> bool:
    """A pin on the dev channel: the old moving tag, or a dev-channel tag."""
    return tag == "dev-latest" or bool(DEV_TAG.match(tag))


def newest_dev_image(details: list[dict]) -> tuple[str, str] | None:
    """(tag, digest) of the image with a DEV_TAG tag and the greatest imagePushedAt."""
    best: tuple[datetime, str, str] | None = None
    for image in details or []:
        digest = image.get("imageDigest") or ""
        try:
            pushed = datetime.fromisoformat(str(image.get("imagePushedAt")))
        except ValueError:
            continue
        if not DIGEST.fullmatch(digest):
            continue
        for tag in image.get("imageTags") or []:
            if DEV_TAG.match(tag) and (best is None or (pushed, tag) > (best[0], best[1])):
                best = (pushed, tag, digest)
    return (best[1], best[2]) if best else None


def aws_ecr(*args: str) -> str:
    out = subprocess.run(
        ["aws", "ecr", *args, "--registry-id", REGISTRY.split(".")[0],
         "--region", os.environ.get("AWS_REGION", "us-east-1"), "--output", "json"],
        capture_output=True, text=True,
    )
    if out.returncode:
        last = (out.stderr.strip().splitlines() or [f"exit {out.returncode}"])[-1]
        raise RuntimeError(f"aws: {last}")
    return out.stdout


def ecr_digest(image: str, tag: str) -> str | None:
    return json.loads(aws_ecr(
        "batch-get-image", "--repository-name", f"microhealthllc/{image}", "--image-ids", f"imageTag={tag}",
        "--accepted-media-types", *MEDIA, "--query", "images[0].imageId.imageDigest"))


def ecr_images(image: str) -> list[dict]:
    # No --no-paginate: the CLI follows nextToken, so this is every tagged image.
    return json.loads(aws_ecr(
        "describe-images", "--repository-name", f"microhealthllc/{image}", "--filter", "tagStatus=TAGGED",
        "--query", "imageDetails[].{imageTags: imageTags, imageDigest: imageDigest, imagePushedAt: imagePushedAt}",
    )) or []


def resolver(from_file: str | None, fell_back: list[str]):
    """resolve(image, tag) -> (tag, digest): the pin the image should carry now."""
    if from_file:
        table = json.loads(Path(from_file).read_text(encoding="utf-8"))

        def offline(image: str, tag: str) -> tuple[str, str | None]:
            answer = table.get(image)
            if follows_dev_channel(tag) and isinstance(answer, str) and "@" in answer:
                dev_tag, digest = answer.split("@", 1)
                return dev_tag, digest
            return tag, table.get(f"{image}:{tag}")
        return offline

    channel: dict[str, tuple[str, str | None]] = {}

    def online(image: str, tag: str) -> tuple[str, str | None]:
        if not follows_dev_channel(tag):
            return tag, ecr_digest(image, tag)
        if image not in channel:
            newest = newest_dev_image(ecr_images(image))
            if newest:
                channel[image] = newest
            else:
                # FALLBACK: remove once fips-container stops pushing dev-latest.
                print(f"fips_bump: {image} has no dev-<YYYYMMDDHHMM>-<sha8> tag in ECR yet; falling back to dev-latest")
                fell_back.append(image)
                channel[image] = ("dev-latest", ecr_digest(image, "dev-latest"))
        return channel[image]
    return online


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--from-file")
    ap.add_argument("--summary")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)
    root = Path(args.root)
    fell_back: list[str] = []
    resolve = resolver(args.from_file, fell_back)

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

    latest: dict[str, tuple[str, str]] = {}  # "fips-go:dev-latest" -> (tag, digest) to pin
    unresolved: list[str] = []
    for key in sorted(seen):
        image, tag = key.split(":", 1)
        try:
            new_tag, digest = resolve(image, tag)
        except (RuntimeError, ValueError) as err:
            new_tag, digest = tag, str(err)
        digest = digest or ""
        if DIGEST.fullmatch(digest) and TAG.fullmatch(new_tag or ""):
            latest[key] = (new_tag, digest)
        else:
            print(f"fips_bump: cannot resolve {key} in {REGISTRY} (got {digest!r}); pin left as is", file=sys.stderr)
            unresolved.append(key)

    # (key, old digest, new tag, new digest): every pin to rewrite. Stale means
    # the digest moved; a pin only renamed (dev-latest -> its dev tag) is fresh.
    changes = [(key, old, *latest[key]) for key in sorted(seen) if key in latest
               for old in sorted(seen[key]) if (key.split(":", 1)[1], old) != latest[key]]
    stale = [c for c in changes if c[1] != c[3]]

    touched: list[str] = []
    if not args.check:
        def sub(m: re.Match) -> str:
            key = f"{m.group(1)}:{m.group(2)}"
            if key not in latest:
                return m.group(0)
            tag, digest = latest[key]
            return f"{REGISTRY}/microhealthllc/{m.group(1)}:{tag}@{digest}"
        for rel, text in texts.items():
            new = PIN.sub(sub, text)
            if new != text:
                (root / rel).write_text(new, encoding="utf-8")
                touched.append(rel)

    table = "\n".join(["| Image | Old digest | New pin |", "|---|---|---|",
                       *(f"| `{k}` | `{o[7:19]}` | `{t}@{n[7:19]}` |" for k, o, t, n in changes)])
    missing = (f"Not resolvable in ECR (pin left as is): {', '.join(f'`{k}`' for k in unresolved)}"
               if unresolved else "")
    fallback = (f"Resolved through the dev-latest fallback (no dev-channel tag yet): "
                f"{', '.join(f'`{i}`' for i in sorted(set(fell_back)))}" if fell_back else "")
    if args.summary:
        Path(args.summary).write_text((table + "\n" if changes else "") + (missing + "\n" if missing else "")
                                      + (fallback + "\n" if fallback else ""), encoding="utf-8")
    print(f"fips_bump: {len(seen)} image tag(s), {len(stale)} stale pin(s), {len(changes)} pin(s) to rewrite, "
          f"{len(touched)} file(s) rewritten" + (f": {', '.join(touched)}" if touched else ""))
    if changes:
        print(table)
    if missing:
        print(missing)
    if fallback:
        print(fallback)

    if args.check:
        if stale or unresolved:
            what = ", ".join([*(f"{k} is stale" for k, *_ in stale), *(f"{k} is unresolvable" for k in unresolved)])
            print(f"::error title=Stale FIPS image pin::{what}: {PENDING}")
            return 1
        print("fips_bump: every FIPS image pin is the newest digest of its channel.")
        return 0
    if seen and not latest:
        print(f"::error::fips_bump: none of {', '.join(sorted(seen))} could be resolved in {REGISTRY}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
