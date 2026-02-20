#!/usr/bin/env bash
# compare-persona-designer.sh — Compare persona designer quality across models.
#
# Security rationale: Safe to whitelist in Claude Code's "don't ask again" prompts.
# Whitelisting the bare `python3` command would grant permission for ALL Python
# scripts; this wrapper limits scope to this specific benchmark.
#
# Usage:
#   benchmarks/compare-persona-designer.sh
#   benchmarks/compare-persona-designer.sh --skip-claude
#   benchmarks/compare-persona-designer.sh --skip-14b
#   benchmarks/compare-persona-designer.sh --verbose
#   benchmarks/compare-persona-designer.sh --cases benchmarks/prompts/persona-designer-test-cases.txt
#   benchmarks/compare-persona-designer.sh --skip-claude --skip-14b  # quick local-only, 8b only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Non-interactive WSL shells do not source ~/.bashrc, so user-installed tools
# (uv, etc.) won't be on PATH without this.
export PATH="$HOME/.local/bin:$PATH"

exec python3 -u "$SCRIPT_DIR/lib/compare-persona-designer.py" "$@"
