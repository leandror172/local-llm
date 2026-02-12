#!/usr/bin/env bash
# A/B test: same prompt with and without few-shot examples.
# Usage: run-fewshot-test.sh <model> <prompt-file> <examples-category>
# Example: run-fewshot-test.sh my-coder-q3 prompts/backend/03-merge-intervals.md backend

set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${1:?Usage: run-fewshot-test.sh <model> <prompt-file> <examples-category>}"
PROMPT="${2:?Usage: run-fewshot-test.sh <model> <prompt-file> <examples-category>}"
CATEGORY="${3:?Usage: run-fewshot-test.sh <model> <prompt-file> <examples-category>}"

SLUG="${MODEL//[:\/]/-}"
NAME=$(basename "$PROMPT" .md)
OUTDIR="results/fewshot"

mkdir -p "$OUTDIR"

echo "=== Without examples ==="
python3 lib/ollama-probe.py \
    --model "$MODEL" \
    --prompt-file "$PROMPT" \
    --vary think=false \
    --output "${OUTDIR}/${SLUG}-${NAME}-baseline.json"

echo ""
echo "=== With ${CATEGORY} examples ==="
python3 lib/ollama-probe.py \
    --model "$MODEL" \
    --prompt-file "$PROMPT" \
    --examples "$CATEGORY" \
    --vary think=false \
    --output "${OUTDIR}/${SLUG}-${NAME}-fewshot.json"

echo ""
echo "Results saved to ${OUTDIR}/"
