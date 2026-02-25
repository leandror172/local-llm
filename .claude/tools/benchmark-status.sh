#!/bin/bash
# Compact benchmark readiness summary — replaces listing rubrics, prompts, results separately.
# Run before a benchmark session to see what's available.
#
# Usage: .claude/tools/benchmark-status.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVAL_DIR="$PROJECT_ROOT/evaluator"
PERSONA_REGISTRY="$PROJECT_ROOT/personas/registry.yaml"

echo "═══════════════════════════════════════════════════"
echo "  BENCHMARK STATUS — $(date +%Y-%m-%d)"
echo "═══════════════════════════════════════════════════"
echo ""

# 1. Rubrics
echo "── Rubrics ─────────────────────────────────────────"
if [ -d "$EVAL_DIR/rubrics" ]; then
  for f in "$EVAL_DIR"/rubrics/*.yaml; do
    name=$(basename "$f" .yaml)
    criteria=$(grep -c "^  - name:" "$f" 2>/dev/null || echo "?")
    printf "  %-20s %s criteria\n" "$name" "$criteria"
  done
else
  echo "  (no rubrics found)"
fi
echo ""

# 2. Prompt sets
echo "── Prompts ──────────────────────────────────────────"
if [ -d "$EVAL_DIR/prompts" ]; then
  total=0
  for d in "$EVAL_DIR"/prompts/*/; do
    domain=$(basename "$d")
    count=$(find "$d" -name "*.md" | wc -l)
    total=$((total + count))
    printf "  %-20s %s prompts\n" "$domain" "$count"
  done
  echo "  ─────────────────────────"
  printf "  %-20s %s total\n" "TOTAL" "$total"
else
  echo "  (no prompts found)"
fi
echo ""

# 3. Active persona count from registry
echo "── Personas ─────────────────────────────────────────"
if [ -f "$PERSONA_REGISTRY" ]; then
  active=$(grep -c "^[a-z][a-z0-9_-]*:$" "$PERSONA_REGISTRY" 2>/dev/null || echo "?")
  echo "  $active active personas in registry.yaml"
  echo "  (use: ref-lookup.sh layer3-inventory for full list)"
else
  echo "  (registry.yaml not found)"
fi
echo ""

# 4. Existing result runs
echo "── Existing results ─────────────────────────────────"
RESULTS_DIR="$EVAL_DIR/results"
if [ -d "$RESULTS_DIR" ]; then
  run_count=$(ls -d "$RESULTS_DIR"/*/  2>/dev/null | wc -l)
  if [ "$run_count" -gt 0 ]; then
    echo "  $run_count run(s) in evaluator/results/:"
    ls -dt "$RESULTS_DIR"/*/ 2>/dev/null | head -5 | while read -r d; do
      run_id=$(basename "$d")
      gen=$(find "$d/raw" -name "*.json" 2>/dev/null | wc -l)
      printf "  %-25s %s generation(s)\n" "$run_id" "$gen"
    done
    [ "$run_count" -gt 5 ] && echo "  ... ($(( run_count - 5 )) more)"
  else
    echo "  (no runs yet)"
  fi
else
  echo "  (results directory not found)"
fi
echo ""

echo "═══════════════════════════════════════════════════"
echo "  Run: ./evaluator/run-benchmark.sh --help"
echo "  Resume: ./evaluator/run-benchmark.sh --resume <RUN_ID>"
echo "═══════════════════════════════════════════════════"
