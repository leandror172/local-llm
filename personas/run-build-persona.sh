#!/usr/bin/env bash
# run-build-persona.sh — LLM-driven persona builder.
#
# Security rationale: This wrapper is safe to whitelist in Claude Code's
# "don't ask again" prompts. Whitelisting the bare `python3` command would
# grant permission for ALL Python scripts; this wrapper limits scope.
#
# Usage:
#   personas/run-build-persona.sh --describe "Java Spring Boot developer"
#   personas/run-build-persona.sh --describe "Go dev" --codebase /path/to/repo
#   personas/run-build-persona.sh --dry-run --describe "Python FastAPI dev"
#   personas/run-build-persona.sh --designer-model qwen3:14b --describe "Rust async dev"
#   personas/run-build-persona.sh --verbose --describe "Go dev"  # prints prompts to stderr
#   personas/run-build-persona.sh  # interactive mode

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Non-interactive WSL shells (spawned by Claude Desktop, cron, etc.) do not
# source ~/.bashrc, so ~/.local/bin (uv, etc.) won't be on PATH.
export PATH="$HOME/.local/bin:$PATH"

exec python3 -u "$SCRIPT_DIR/build-persona.py" "$@"
