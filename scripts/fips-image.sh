#!/bin/sh
# Print the pinned FIPS base image (fips-images.json) for `python` or `go`.
# Refuses anything that is not a microhealthllc/fips-* image in MicroHealth's
# ECR pinned by sha256, so an edit to the data file can neither unpin a build
# nor point it at another registry.   scripts/fips-image.sh python
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
case "${1:-}" in (python|go) ;; (*) echo "usage: $0 python|go" >&2; exit 2;; esac
# jq on a runner (CI runs no Python outside the FIPS image); python3 locally.
if command -v jq >/dev/null 2>&1; then
  ref="$(jq -r --arg k "$1" '.[$k] // ""' "$root/fips-images.json")"
else
  ref="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ""))' "$root/fips-images.json" "$1")"
fi
if ! printf '%s' "$ref" | grep -Eqx "295669632222\.dkr\.ecr\.us-east-1\.amazonaws\.com/microhealthllc/fips-$1:[A-Za-z0-9._-]+@sha256:[0-9a-f]{64}"; then
  echo "fips-images.json: '$1' is not a pinned MicroHealth FIPS image: $ref" >&2; exit 1
fi
printf '%s\n' "$ref"
