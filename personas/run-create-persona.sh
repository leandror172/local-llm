#!/usr/bin/env bash
# run-create-persona.sh — Interactively create a new Ollama persona.
#
# Security rationale: This wrapper is safe to whitelist in Claude Code's
# "don't ask again" prompts. Whitelisting the bare `python3` command would
# grant permission for ALL Python scripts; this wrapper limits scope.
#
# Usage (interactive):
#   personas/run-create-persona.sh
#
# Usage (non-interactive / scripting):
#   personas/run-create-persona.sh --non-interactive \
#     --role "React 18+ TypeScript developer" \
#     --domain code --language react \
#     --name my-react-q3 [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Non-interactive WSL shells (spawned by Claude Desktop, cron, etc.) do not
# source ~/.bashrc, so ~/.local/bin (uv, etc.) won't be on PATH.
export PATH="$HOME/.local/bin:$PATH"

exec python3 "$SCRIPT_DIR/create-persona.py" "$@"
