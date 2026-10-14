#!/usr/bin/env bash
# Copy what git would see in a checkout into a scratch directory, so a scan
# reads the same files CI does: tracked files and new files that are not
# ignored, including uncommitted edits, and never build output or other
# .gitignore'd files (a nested git worktree under an excluded path included).
#
#   git-view.sh <checkout> <empty destination directory>
#
# Only regular files are copied. A tracked entry that is NOT one — a symlink to
# a directory, a submodule, a file deleted but not yet staged — is skipped, and
# the filter must still exit 0 for it: `[ -f x ] && printf` returns 1 there,
# xargs turns that into 123, and pipefail ended the whole scan silently with no
# report and no message, in any repository holding one such entry.
set -euo pipefail
src="$1" dest="$2"
(cd "$src" && git ls-files -z --cached --others --exclude-standard \
   | xargs -0 -r sh -c 'for f; do if [ -f "$f" ]; then printf "%s\0" "$f"; fi; done' _ \
   | tar --null -T - -cf -) | tar -xf - -C "$dest"
cp "$src/.sastignore" "$dest/" 2>/dev/null || true
