#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# run-server.sh — Launch the Ollama MCP server
#
# This wrapper follows the project convention of invoking Python via bash
# scripts (safe to whitelist in "don't ask again" prompts, unlike bare
# `python3` commands which would whitelist ALL Python execution).
#
# Usage:
#   ./mcp-server/run-server.sh          # Run the MCP server (stdio transport)
#
# The server communicates via stdin/stdout (JSON-RPC). Claude Code spawns
# it as a subprocess and discovers tools automatically.
# ──────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Resolve the directory this script lives in, regardless of where it's
# called from. This ensures `uv run --project` always points to the right
# pyproject.toml.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# `uv run` does three things automatically:
#   1. Creates a virtual environment if one doesn't exist
#   2. Installs/syncs dependencies from pyproject.toml
#   3. Runs the command inside the virtual environment
# The --project flag tells uv where to find pyproject.toml.
exec uv run --project "$SCRIPT_DIR" python -m ollama_mcp "$@"
