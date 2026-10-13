#!/usr/bin/env bash
# Rule-test fixture for bash.ifs-global; never executed.
parts=(a b c)
# ruleid: bash.ifs-global
IFS=,
# ok: bash.ifs-global
joined="$(IFS=,; echo "${parts[*]}")"
# ok: bash.ifs-global
( IFS=:; echo "$PATH" )
join() {
  local IFS
  # ok: bash.ifs-global
  IFS="$1"
  shift
  echo "$*"
}
echo "$joined" "$(join , "${parts[@]}")"
