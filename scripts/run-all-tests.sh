#!/usr/bin/env bash
# Run every test suite in this repo and print a per-suite summary with counts.
#
# WHY THIS EXISTS (T-136). The repo had FIVE test corpora and no single command covering
# them. "416 green" was quoted as the repo's test result while 410 further tests sat
# outside it. A boundary nobody compares drifts silently, and this one drifted twice over:
# overlays/Makefile's help claimed 196 against an actual 296, and benchmarks/lib was run
# by nothing at all.
#
# NOTE ON HOW THE SET WAS FOUND. The first draft of this script listed THREE suites,
# because it enumerated Makefiles rather than test runners — .claude/index.md is what
# surfaced the other two. That is the same failure the script exists to fix, committed
# inside the fix. When adding an area, enumerate `git ls-files | grep test_.*\.py` and
# compare against SUITES below; do not trust this list to be complete by inspection.
#
# So counts here are SUMMED FROM THE RUN, never asserted in prose. If a number in a
# doc disagrees with this script, this script is right.
#
# Exit 0 only if ALL suites pass. Deliberately NOT `set -e` on the loop — every suite
# runs even when an earlier one fails, so the summary is complete (the same choice
# overlays/scripts/run-all-tests.sh makes, and for the same reason).
#
# Note the suites do not share an interpreter: mcp-server runs under `uv run` (project
# venv), overlays and benchmarks under system python3. That is a real boundary; it is
# recorded here rather than hidden.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/.."

# name:runner — add a line here when an area gains a suite.
SUITES=(
  "mcp-server:mcp-server/scripts/run-tests.sh"
  "overlays:overlays/scripts/run-all-tests.sh"
  "benchmarks:benchmarks/lib/run-tests.sh"
  "hooks:.claude/hooks/tests/run-tests.sh"
  "personas:personas/run-tests.sh"
  "hf-space:docs/portfolio/hf-space/run-tests.sh"
)

# DELIBERATELY EXCLUDED, so the boundary is stated rather than accidental:
#   benchmarks/test-fixtures/ollama-client/test_*.py — fixture DATA (a fake project the
#     code validator runs against), not a suite of this repo's own tests.
#   make -C mcp-server accept-p4 — live acceptance against a real model, not a test.

fail=0
results=()
total=0
failtotal=0
for entry in "${SUITES[@]}"; do
  name="${entry%%:*}"
  script="${entry#*:}"
  echo "════════ $name ════════"
  out="$(mktemp)"
  if "$script" 2>&1 | tee "$out"; then
    status="PASS"
  else
    status="FAIL"
    fail=1
  fi
  # Sum every "N passed"/"N failed" the suite reported — overlays emits one per sub-suite.
  # Failures are summed too: a summary that totals only passes reads healthier than the
  # run actually was, which is the silent-and-narrow direction (ref:corpus-divergence-pattern).
  n="$(grep -oE '[0-9]+ passed' "$out" | grep -oE '[0-9]+' | awk '{s+=$1} END {print s+0}')"
  nf="$(grep -oE '[0-9]+ failed' "$out" | grep -oE '[0-9]+' | awk '{s+=$1} END {print s+0}')"
  rm -f "$out"
  total=$((total + n))
  failtotal=$((failtotal + nf))
  line="$status  $(printf '%-12s' "$name") $(printf '%5d' "$n") passed"
  [ "$nf" -gt 0 ] && line="$line, $nf failed"
  results+=("$line")
  echo
done

echo "════════ repo test summary ════════"
for r in "${results[@]}"; do echo "  $r"; done
totline="$(printf '  %-18s %5d passed' "TOTAL" "$total")"
[ "$failtotal" -gt 0 ] && totline="$totline, $failtotal failed"
echo "$totline"
[ "$fail" -eq 0 ] && echo "  → all suites green" || echo "  → at least one suite FAILED"
exit "$fail"
