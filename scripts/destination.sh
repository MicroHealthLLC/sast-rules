#!/usr/bin/env bash
# Where a scan's reports may go, written to $GITHUB_OUTPUT:
#   upload  true | false
#   base    the key prefix after <project>/ ("" or "_branch-scans/branch=<slug>/")
#   branch, commit
# Only a full scan of the default branch feeds Tueri Core's findings. Another
# branch's scan goes under <project>/_branch-scans/branch=<slug>/..., which
# Tueri Core's ingest never reads (the convention its own code scanner uses),
# so work in progress never opens or resolves a finding. A pull-request or
# diff scan sees part of the code, and absence in a partial view is not
# evidence: it is not uploaded at all.
#   destination.sh <checkout-dir> [diff]
# Needs DEFAULT_BRANCH in the environment.
set -euo pipefail
src="$1" diff="${2:-}"
branch="$(git -C "$src" rev-parse --abbrev-ref HEAD)"
[ "$branch" = HEAD ] && branch="${GITHUB_HEAD_REF:-${GITHUB_REF_NAME}}"
commit="$(git -C "$src" rev-parse HEAD)"
if [ -n "$diff" ] || [ "${GITHUB_EVENT_NAME:-}" = pull_request ]; then
  upload=false base=""
  echo "Diff or pull-request scan: reports are artifacts only, never uploaded for ingest." >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
elif [ "$branch" = "${DEFAULT_BRANCH:-}" ]; then
  upload=true base=""
else
  upload=true base="_branch-scans/branch=$(printf '%s' "$branch" | tr -c 'A-Za-z0-9._-' '-' | cut -c1-80)/"
fi
{
  echo "upload=$upload"
  echo "base=$base"
  echo "branch=$branch"
  echo "commit=$commit"
} >> "$GITHUB_OUTPUT"
