#!/usr/bin/env bash
# Open a pull request in every consumer (consumers.yaml) moving its sast-rules
# pins to a release:  GH_TOKEN=... scripts/bump_consumers.sh <tag> <sha>
#
# A pin is `MicroHealthLLC/sast-rules…@<40-hex>` (with an optional
# `# vYYYY.MM.N` comment) or `SAST_RULES_COMMIT=<40-hex>`. Only files that
# already hold one are touched. git, gh and sed only: runner glue.
set -uo pipefail
tag="$1" sha="$2"
root="$(cd "$(dirname "$0")/.." && pwd)"
branch="deps/sast-rules-${tag}"
failed=()
while read -r repo base; do
  work="$(mktemp -d)"
  if ! gh repo clone "$repo" "$work/r" -- --quiet --depth 1 --branch "$base" 2>"$work/err"; then
    echo "$repo: clone failed: $(head -c 300 "$work/err")" >&2; failed+=("$repo"); continue
  fi
  files="$(git -C "$work/r" grep -l -E 'MicroHealthLLC/sast-rules[^@ ]*@[0-9a-f]{40}|SAST_RULES_COMMIT=[0-9a-f]{40}' || true)"
  if [ -z "$files" ]; then echo "$repo: no pins"; rm -rf "$work"; continue; fi
  for f in $files; do
    sed -i -E \
      -e "s#(MicroHealthLLC/sast-rules[^@ ]*@)[0-9a-f]{40}( \# v[0-9.]+)?#\1${sha} \# ${tag}#g" \
      -e "s#(SAST_RULES_COMMIT=)[0-9a-f]{40}#\1${sha}#g" "$work/r/$f"
  done
  if git -C "$work/r" diff --quiet; then echo "$repo: already at $tag"; rm -rf "$work"; continue; fi
  (
    cd "$work/r" &&
    git checkout -qB "$branch" &&
    git -c user.name='github-actions[bot]' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
      commit -qam "chore(sast): sast-rules ${tag}" &&
    # gh clones over https but git has no credential for it on a runner:
    # hand git gh's token (GH_TOKEN) for this push only.
    git -c credential.helper= -c 'credential.helper=!gh auth git-credential' \
      push -qf origin "$branch" &&
    if [ "$(gh pr view "$branch" --json state -q .state 2>/dev/null)" != OPEN ]; then
      gh pr create --base "$base" --head "$branch" --title "chore(sast): sast-rules ${tag}" \
        --body "Moves the sast-rules pins to ${tag} (\`${sha}\`). What changed in the rules — added, changed, retired: https://github.com/MicroHealthLLC/sast-rules/releases/tag/${tag}" >/dev/null
    fi
  ) && echo "$repo: PR on $branch" || { echo "$repo: push/PR failed" >&2; failed+=("$repo"); }
  rm -rf "$work"
done < <(sed -n -E 's/^ *- *\{repo: *([^,]+), *branch: *([^}]+)\}.*/\1 \2/p' "$root/consumers.yaml")
if [ ${#failed[@]} -gt 0 ]; then echo "::error::no pin PR in: ${failed[*]}"; exit 1; fi
