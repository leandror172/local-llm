#!/usr/bin/env bash
# run-benchmark.sh — Run evaluation benchmark across personas × prompts.
#
# Usage:
#   ./evaluator/run-benchmark.sh \
#     --prompts evaluator/prompts/go \
#     --personas my-go-q3,my-coder-q3 \
#     --rubric evaluator/rubrics/code-go.yaml \
#     --judge-model my-codegen-q3 \
#     [--all-coding] [--dry-run] [--no-warmup] [--timeout 600]
#     [--skip-phase1] [--skip-phase2]
#
# Safe to whitelist in Claude Code — only runs evaluator/lib/benchmark.py.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec python3 -u "$SCRIPT_DIR/lib/benchmark.py" "$@"
