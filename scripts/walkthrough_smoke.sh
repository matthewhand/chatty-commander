#!/usr/bin/env bash
# ChattyCommander walkthrough smoke script
set -euo pipefail

# Ensure local wrapper is discoverable during development
export PATH="${PWD}:$PATH"

section() {
  echo
  echo "== $1 =="
}

run() {
  echo "+ $*"
  # shellcheck disable=SC2068
  $@ 2>&1 | sed -e 's/^/  /'
}

section "CLI help"
run chatty --help | sed -n '1,40p'

section "List configured commands"
run chatty list

section "Config help"
run chatty config --help | sed -n '1,80p'

section "System help"
run chatty system --help
run chatty system start-on-boot --help
run chatty system updates --help

section "System smoke"
run chatty system start-on-boot status || true
run chatty system start-on-boot enable || true
run chatty system start-on-boot disable || true
run chatty system updates check || true

section "Optional: Adjust state models (demo)"
# This writes to $XDG_CONFIG_HOME/chatty-commander/config.json; uncomment to try.
# run chatty config --set-state-model idle "model1,model2"

section "Done"
echo "Walkthrough complete. Review the output above for any unexpected errors."
