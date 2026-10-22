#!/usr/bin/env bash
# main releases ONLY what integration already holds (AI_RULES.md §1). Every
# non-merge commit the release would ship must already be on
# origin/integration. ci.yml runs it on every push to main.
#   HEAD_SHA=<sha> scripts/require-from-integration.sh
set -euo pipefail
HEAD_SHA="${HEAD_SHA:-HEAD}"
git fetch --quiet --no-tags origin "+refs/heads/integration:refs/remotes/origin/integration"
stray="$(git rev-list --no-merges --format='%h %s' "origin/integration..${HEAD_SHA}" | grep -v '^commit ' || true)"
if [ -n "$stray" ]; then
  echo "::error::main may only receive commits that are already on integration. Not on integration:"
  printf '%s\n' "$stray"
  echo "Merge the change into integration first, then promote integration to main."
  exit 1
fi
echo "Every commit is already on integration."
