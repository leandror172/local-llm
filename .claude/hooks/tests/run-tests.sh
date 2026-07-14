#!/usr/bin/env bash
# Hermetic tests for .claude/hooks/ scripts (whitelisting seam — never invoke python3 directly).
# Runs every test_*.py in this dir; exits nonzero if any suite fails.
cd "$(dirname "$0")" || exit 1
rc=0
for t in test_*.py; do
  echo "== $t =="
  python3 "$t" || rc=1
done
exit $rc
