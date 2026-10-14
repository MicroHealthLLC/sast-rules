#!/usr/bin/env bash
# Run MicroHealth's SAST scan locally, exactly as CI runs it: the same rules
# bundle and the same Opengrep, both checked against their sha256, in a
# container FROM MicroHealth's FIPS Python image, with no network.
#
#   scan-local.sh [--bundle internal|product] [--fail-on error|warning|none] [--json out.json] [path]
#
# A repository does not copy this file. It keeps a small wrapper
# (local/sast.sh in this repository, copied to scripts/sast.sh or the like)
# that fetches sast-rules at the commit its security workflow pins and runs
# this script from there, so a local scan and the CI scan are the same rules.
#
# Needs: git, curl, sha256sum, python3, and docker or nerdctl logged in to
# MicroHealth's ECR (`make ecr-login` in most repositories).
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
bundle=internal fail_on=error json="" target="."
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) bundle="$2"; shift 2 ;;
    --fail-on) fail_on="$2"; shift 2 ;;
    --json) json="$2"; shift 2 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) target="$1"; shift ;;
  esac
done
case "$bundle" in (internal|product) ;; (*) echo "bundle must be internal or product" >&2; exit 2;; esac
engine() { for c in nerdctl docker; do command -v "$c" >/dev/null 2>&1 && { echo "$c"; return; }; done
           echo "No container runtime (docker or nerdctl)." >&2; exit 2; }
rt="$(engine)"

(cd "$here/dist" && grep " ${bundle}.yaml\$" SHA256SUMS | sha256sum -c --quiet -) \
  || { echo "dist/${bundle}.yaml does not match dist/SHA256SUMS" >&2; exit 1; }

case "$(uname -m)" in (x86_64|amd64) arch=x86_64;; (aarch64|arm64) arch=aarch64;; (*) echo "unsupported $(uname -m)" >&2; exit 2;; esac
read -r version file want < <(python3 -I -c 'import json,sys; e=json.load(open(sys.argv[1])); a=e["assets"][sys.argv[2]]; print(e["version"], a["file"], a["sha256"])' "$here/engine.json" "$arch")
cache="${XDG_CACHE_HOME:-$HOME/.cache}/sast-rules/opengrep-${version}-${arch}"
if ! echo "${want}  ${cache}" | sha256sum -c --quiet - 2>/dev/null; then
  mkdir -p "$(dirname "$cache")"
  curl -fsSL -o "$cache.tmp" "https://github.com/opengrep/opengrep/releases/download/v${version}/${file}"
  echo "${want}  ${cache}.tmp" | sha256sum -c --quiet - || { echo "Opengrep download does not match engine.json" >&2; exit 1; }
  mv "$cache.tmp" "$cache"; chmod 0755 "$cache"
fi

image="$("$here/scripts/fips-image.sh" python)"
# SAST_IMAGE: the same FIPS image under another name (a mirror, or a copy
# already pulled when ECR cannot be reached). Never another base.
image="${SAST_IMAGE:-$image}"
src="$(cd "$target" && git rev-parse --show-toplevel 2>/dev/null || pwd)"
out="$(mktemp -d)"
# Scan what git would see, as CI does: scripts/git-view.sh copies the tracked
# and new-but-not-ignored files into a scratch directory (the scan image has no
# git to decide that itself). Outside a git checkout, the directory as it is.
if git -C "$src" rev-parse --git-dir >/dev/null 2>&1; then
  view="$(mktemp -d)"
  "$here/scripts/git-view.sh" "$src" "$view"
  src_view="$view"
else
  src_view="$src"
fi
args=()
if [ -f "$src/.sastignore" ]; then
  while IFS= read -r line; do line="${line%%#*}"; line="$(printf '%s' "$line" | xargs)"; [ -n "$line" ] && args+=("--exclude=$line"); done < "$src/.sastignore"
fi
"$rt" run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$src_view:/src:ro" -v "$here/dist:/rules:ro" -v "$cache:/usr/local/bin/opengrep:ro" -v "$out:/out" \
  -w /src --entrypoint /usr/local/bin/opengrep "$image" \
  scan --config "/rules/${bundle}.yaml" --no-rewrite-rule-ids --json-output=/out/sast.json \
  --quiet "${args[@]}" . >/dev/null
[ -n "$json" ] && cp "$out/sast.json" "$json"

read -r errors warnings infos < <(python3 -I - "$out/sast.json" <<'PY'
import json, sys
rs = [r for r in json.load(open(sys.argv[1]))["results"] if not (r.get("extra") or {}).get("is_ignored")]
for r in sorted(rs, key=lambda r: (r["path"], r["start"]["line"])):
    print(f'{r["extra"].get("severity")}\t{r["path"]}:{r["start"]["line"]}\t{r["check_id"]}', file=sys.stderr)
sev = [r["extra"].get("severity") for r in rs]
print(sev.count("ERROR"), sev.count("WARNING"), sev.count("INFO"))
PY
)
echo "SAST (sast-rules ${bundle}, Opengrep ${version}): ${errors} error, ${warnings} warning, ${infos} info"
rm -rf "$out"
[ "$src_view" != "$src" ] && rm -rf "$src_view"
case "$fail_on" in
  error) [ "$errors" -eq 0 ] ;;
  warning) [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ] ;;
  none) true ;;
  *) echo "--fail-on must be error, warning or none" >&2; exit 2 ;;
esac
