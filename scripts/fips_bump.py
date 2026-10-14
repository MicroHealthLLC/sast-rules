#!/usr/bin/env python3
"""Move every MicroHealth FIPS image pin in fips-images.json to the digest its
tag points at now (fips-container rebuilds the images nightly).

The pins live only there: every workflow and script reads them through
scripts/fips-image.sh. upstream.yml runs this daily and pushes the result with
an Actions token, which GitHub never lets change .github/workflows/.

Pins look like `<registry>/microhealthllc/<image>:<tag>@sha256:<digest>`. The
digest is read with `aws ecr batch-get-image`, which needs only the pull
permission the CI role already has. An image that cannot be resolved keeps
its pin and is reported.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN = re.compile(
    r"(295669632222\.dkr\.ecr\.us-east-1\.amazonaws\.com/microhealthllc/)([a-z0-9-]+):([\w.-]+)@(sha256:[0-9a-f]{64})"
)
MEDIA = [
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
]


def resolve(image: str, tag: str) -> str | None:
    out = subprocess.run(
        ["aws", "ecr", "batch-get-image", "--registry-id", "295669632222",
         "--region", os.environ.get("AWS_REGION", "us-east-1"),
         "--repository-name", f"microhealthllc/{image}", "--image-ids", f"imageTag={tag}",
         "--accepted-media-types", *MEDIA,
         "--query", "images[0].imageId.imageDigest", "--output", "text"],
        capture_output=True, text=True,
    )
    digest = out.stdout.strip()
    return digest if re.fullmatch(r"sha256:[0-9a-f]{64}", digest) else None


def main() -> int:
    path = ROOT / "fips-images.json"
    text = path.read_text(encoding="utf-8")
    latest: dict[tuple[str, str], str | None] = {}

    def sub(m: re.Match) -> str:
        key = (m.group(2), m.group(3))
        if key not in latest:
            latest[key] = resolve(*key)
        new = latest[key]
        if new is None:
            return m.group(0)
        return f"{m.group(1)}{m.group(2)}:{m.group(3)}@{new}"

    new_text = PIN.sub(sub, text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    for (image, tag), digest in sorted(latest.items()):
        print(f"{image}:{tag} -> {digest or 'UNRESOLVED (pin kept)'}")
    print("changed: " + ("fips-images.json" if new_text != text else "nothing"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
