#!/usr/bin/env bash
# Hermetic tests for .claude/hooks/ scripts (whitelisting seam — never invoke python3 directly).
# Runs every test_*.py in this dir; exits nonzero if any suite fails.
#
# Prints a "N passed, M failed" summary so the repo-root aggregator
# (scripts/run-all-tests.sh) can count this suite like every other one. Without it a
# suite that reports no total is counted as ZERO, which reads as false health — the
# failure direction T-136 is filed against.
set -o pipefail
cd "$(dirname "$0")" || exit 1
rc=0
log="$(mktemp)"
for t in test_*.py; do
  echo "== $t =="
  python3 "$t" 2>&1 | tee -a "$log" || rc=1
done
passed=$(grep -c '^PASS ' "$log" || true)
failed=$(grep -c '^FAIL ' "$log" || true)
rm -f "$log"
echo
echo "${passed:-0} passed, ${failed:-0} failed"
exit $rc
