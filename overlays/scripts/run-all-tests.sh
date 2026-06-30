#!/bin/bash
# Run every overlay test suite and print a per-suite summary.
#
# Exit 0 only if ALL suites pass; nonzero if any fail. Deliberately NOT `set -e`
# on the loop — every suite runs even when an earlier one fails, so the summary
# is complete. This is the single entry point `make test` delegates to.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# name:runner — add a line here when a new overlay gains a suite.
SUITES=(
  "ref-indexing:$HERE/test-ref-indexing.sh"
  "session-tracking:$HERE/test-session-tracking.sh"
  "installer:$HERE/test-installer.sh"
)

fail=0
results=()
for entry in "${SUITES[@]}"; do
  name="${entry%%:*}"
  script="${entry#*:}"
  echo "──────── $name ────────"
  if "$script"; then
    results+=("PASS  $name")
  else
    results+=("FAIL  $name")
    fail=1
  fi
  echo
done

echo "════════ overlay test summary ════════"
for r in "${results[@]}"; do echo "  $r"; done
[ "$fail" -eq 0 ] && echo "  → all suites green" || echo "  → at least one suite FAILED"
exit "$fail"
