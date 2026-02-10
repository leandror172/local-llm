#!/usr/bin/env bash
# Run a decomposed visual prompt pipeline.
# Usage: run-decomposed.sh <model> <stages-dir> [extra-args...]
# Examples:
#   run-decomposed.sh my-creative-coder-q3 prompts/decomposed/01-bouncing-ball/ --no-think
#   run-decomposed.sh my-creative-coder prompts/decomposed/01-bouncing-ball/ --start 2 --inject results/decomposed/.../stage-1.html

set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${1:?Usage: run-decomposed.sh <model> <stages-dir> [extra-args...]}"
STAGES="${2:?Usage: run-decomposed.sh <model> <stages-dir> [extra-args...]}"
shift 2

python3 lib/decomposed-run.py --model "$MODEL" --stages "$STAGES" "$@"
