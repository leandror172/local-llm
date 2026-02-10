#!/usr/bin/env bash
# Run structured output tests against a model using ollama-probe.
# Usage: run-structured-tests.sh <model> [test-number]
# Examples:
#   run-structured-tests.sh my-coder-q3          # all 5 tests
#   run-structured-tests.sh my-coder 03          # just test 03

set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${1:?Usage: run-structured-tests.sh <model> [test-number]}"
FILTER="${2:-}"

mkdir -p results/structured

for prompt in prompts/structured/*.md; do
    num=$(basename "$prompt" | cut -d- -f1)
    name=$(basename "$prompt" .md)
    schema="${prompt%.md}.schema.json"

    if [[ -n "$FILTER" && "$num" != "$FILTER" ]]; then
        continue
    fi

    slug="${MODEL//[:\/]/-}"
    echo "=== Test $num: $name (model=$MODEL) ==="
    python3 lib/ollama-probe.py \
        --model "$MODEL" \
        --prompt-file "$prompt" \
        --format-file "$schema" \
        --vary format=on,off \
        --no-think \
        --output "results/structured/${slug}-${num}.json"
    echo ""
done
