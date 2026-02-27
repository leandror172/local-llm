#!/usr/bin/env bash
# run-compare-models.sh — Multi-model comparison wrapper.
#
# Sends the same prompt to multiple Ollama models side-by-side.
# Collects verdict (ACCEPTED/IMPROVED/REJECTED) per model response.
# Designed for Layer 5+ DPO data collection.
#
# Usage:
#   ./run-compare-models.sh --models my-go-q3,my-go-q25c14 --preset go-struct
#   ./run-compare-models.sh --models my-go-q3,my-go-q25c14,my-go-q3-30b --prompt "Write a Go HTTP handler"
#   ./run-compare-models.sh --models my-go-q3,my-go-q25c14 --prompt-file prompts/custom.md
#   ./run-compare-models.sh --models my-go-q3,my-go-q25c14 --preset go-struct --no-verdict
#   ./run-compare-models.sh --models my-go-q3,my-go-q25c14 --preset go-struct --output results/compare-run.jsonl
#
# Default model pair (no --models given): my-go-q3 vs my-go-q25c14

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default model pair for quick smoke-testing
DEFAULT_MODELS="my-go-q3,my-go-q25c14"

# Pass all arguments to the Python script
# If --models is not in $@, prepend the default
has_models=false
for arg in "$@"; do
    if [[ "$arg" == "--models" ]]; then
        has_models=true
        break
    fi
done

if [[ "$has_models" == "false" ]]; then
    set -- "--models" "$DEFAULT_MODELS" "$@"
fi

exec python3 "$SCRIPT_DIR/compare-models.py" "$@"
