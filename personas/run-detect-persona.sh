#!/usr/bin/env bash
# run-detect-persona.sh — Analyze a codebase to detect appropriate Ollama personas.
#
# Security rationale: This wrapper is safe to whitelist in Claude Code's
# "don't ask again" prompts. Whitelisting the bare `python3` command would
# grant permission for ALL Python scripts; this wrapper limits scope.
#
# Usage:
#   personas/run-detect-persona.sh /path/to/codebase
#   personas/run-detect-persona.sh --verbose /path/to/codebase
#   personas/run-detect-persona.sh --json-compact /path/to/codebase

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Non-interactive WSL shells (spawned by Claude Desktop, cron, etc.) do not
# source ~/.bashrc, so ~/.local/bin (uv, etc.) won't be on PATH.
export PATH="$HOME/.local/bin:$PATH"

exec python3 "$SCRIPT_DIR/detect-persona.py" "$@"
