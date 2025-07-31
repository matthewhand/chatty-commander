#!/usr/bin/env bash
# Warn (do not fail) if tests are invoked in CI without using the canonical command.
set -euo pipefail

# Only activate inside CI
if [[ "${CI:-}" != "true" && "${CI:-}" != "1" ]]; then
  exit 0
fi

# Allow-list the canonical invocation
# We consider canonical if:
# - An env var says we are calling via npm run test:ci
# - Or argv resembles "jest --ci --runInBand --watch=false"
canonical=false

if [[ "${NPM_LIFECYCLE_EVENT:-}" == "test:ci" ]]; then
  canonical=true
fi

# Fallback heuristic: check process arguments for the exact flags we standardize on.
if ps -o command= -p $$ | grep -qE "jest.*--ci.*--runInBand.*--watch=false"; then
  canonical=true
fi

if [[ "$canonical" != "true" ]]; then
  echo "[warn] CI detected (CI=$CI) but tests were not invoked via npm
