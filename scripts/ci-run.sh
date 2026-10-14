#!/usr/bin/env bash
# Run a command in the tools image: FROM MicroHealth's FIPS Python image (the
# pin every workflow uses, from fips-images.json), plus Alpine's git, py3-yaml
# and aws-cli.
# Every CI job runs its Python, git and AWS calls here, never on the runner.
#   scripts/ci-run.sh python3 scripts/build.py --check
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
base="$("$root/scripts/fips-image.sh" python)"
if ! docker image inspect sast-tools:fips >/dev/null 2>&1; then
  docker build -q --build-arg BASE="$base" --build-arg APK_REFRESH="${GITHUB_RUN_ID:-local}" \
    -t sast-tools:fips -f - "$root" >/dev/null <<'DOCKERFILE'
ARG BASE
FROM ${BASE}
ARG APK_REFRESH
USER root
RUN apk add --no-cache git py3-yaml aws-cli && apk upgrade --no-cache \
    && git config --system --add safe.directory '*'
DOCKERFILE
fi
env_args=()
for v in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_REGION GITHUB_STEP_SUMMARY; do
  [ -n "${!v:-}" ] && env_args+=(-e "$v")
done
tmp_mount=()
[ -n "${RUNNER_TEMP:-}" ] && tmp_mount=(-v "$RUNNER_TEMP:$RUNNER_TEMP")
exec docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp "${env_args[@]}" "${tmp_mount[@]}" \
  -v "$root:/repo" -w /repo sast-tools:fips "$@"
