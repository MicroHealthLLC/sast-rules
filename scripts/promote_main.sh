#!/usr/bin/env bash
# Promote a validated integration commit to main, then fast-forward
# integration to the merge so main never has a commit integration lacks
# (AI_RULES.md §1).
#
#   scripts/promote_main.sh <validated-sha> [remote]
#
# ci.yml's promote-main job calls it ONLY after build and self-scan passed on
# that commit (owner's decision 2026-10-18). It refuses a commit that is not
# on integration, does nothing when main already has it or its content, and
# pushes nothing unless the merge's tree is exactly the validated tree. Plain
# pushes only: both branches refuse a force push. PROMOTE_NOTE (optional) is
# added to the merge commit message.
set -euo pipefail
sha="$(git rev-parse --verify "${1:?validated commit}^{commit}")"
remote="${2:-origin}"
short="${sha:0:8}"

git fetch -q --no-tags "$remote" \
  "+refs/heads/main:refs/remotes/$remote/main" \
  "+refs/heads/integration:refs/remotes/$remote/integration"
main="$(git rev-parse "$remote/main")"

if ! git merge-base --is-ancestor "$sha" "$remote/integration"; then
  echo "::error::promote_main: $short is not on integration; not promoted"
  exit 1
fi
if git merge-base --is-ancestor "$sha" "$main"; then
  echo "promote_main: $short is already on main"
  exit 0
fi
if git diff --quiet "$main" "$sha"; then
  echo "promote_main: main already has the content of $short"
  exit 0
fi

git checkout -q --detach "$main"
msg="Promote integration $short to main"
if [ -n "${PROMOTE_NOTE:-}" ]; then msg="$msg

$PROMOTE_NOTE"; fi
if ! git merge -q --no-ff -m "$msg" "$sha"; then
  git merge --abort || true
  echo "::error::promote_main: $short does not merge cleanly into main; merge main into integration first"
  exit 1
fi
if [ "$(git rev-parse 'HEAD^{tree}')" != "$(git rev-parse "$sha^{tree}")" ]; then
  echo "::error::promote_main: main has changes integration lacks:"
  git diff --stat "$sha" HEAD
  echo "::error::not promoted; merge main into integration first"
  exit 1
fi
merge="$(git rev-parse HEAD)"
git push -q "$remote" "$merge:refs/heads/main"
echo "promote_main: main is now ${merge:0:8} (merge of $short)"

# integration may have moved since this run started; then the next promotion
# brings main's merge in (its merge commit descends from both).
if git push -q "$remote" "$merge:refs/heads/integration"; then
  echo "promote_main: integration fast-forwarded to ${merge:0:8}"
else
  echo "::warning::promote_main: integration moved on; it is not fast-forwarded to ${merge:0:8} this time"
fi
