#!/usr/bin/env bash
# run-evaluate.sh — Evaluate a single LLM output against a rubric.
#
# Usage:
#   ./evaluator/run-evaluate.sh \
#     --prompt evaluator/prompts/go/01-http-handler.md \
#     --output /path/to/llm-output.txt \
#     --rubric evaluator/rubrics/code-go.yaml \
#     --judge-model my-codegen-q3 \
#     [--skip-phase1] [--skip-phase2] [--quiet]
#
# Safe to whitelist in Claude Code — only runs evaluator/lib/evaluate.py.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec python3 -u "$SCRIPT_DIR/lib/evaluate.py" "$@"
