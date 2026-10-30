#!/usr/bin/env bash
# Record a FIPS Trivy build (published by .github/workflows/engines.yml) in
# engine.json: its download URL and the sha256 the release states, checked
# against the downloaded file.   scripts/record_trivy.sh <version> [build]
# Build 1 is the release `engine-trivy-<version>`; a rebuild N of the same
# version is `engine-trivy-<version>-b<N>` (engines.yml never replaces one).
set -euo pipefail
v="$1"; b="${2:-1}"; root="$(cd "$(dirname "$0")/.." && pwd)"
tag="engine-trivy-${v}"; [ "$b" = 1 ] || tag="${tag}-b${b}"
file="trivy-${v}-linux-amd64-fips"
url="https://github.com/MicroHealthLLC/sast-rules/releases/download/${tag}/${file}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
curl -fsSL --retry 5 -o "$tmp/$file" "$url"
curl -fsSL --retry 5 -o "$tmp/$file.sha256" "$url.sha256"
(cd "$tmp" && sha256sum -c "$file.sha256")
sum="$(cut -d' ' -f1 "$tmp/$file.sha256")"
python3 - "$root/engine.json" "$v" "$b" "$url" "$sum" <<'PY'
import json, sys
path, v, b, url, s = sys.argv[1:]
e = json.load(open(path))
e["trivy"].update(version=v, version_built=v, build_built=int(b), url=url, sha256=s)
open(path, "w").write(json.dumps(e, indent=2) + "\n")
PY
echo "engine.json: Trivy ${v} build ${b} ${sum}"
