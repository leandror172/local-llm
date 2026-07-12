#!/usr/bin/env bash
# watch-run.sh — tail an oficina run to a terminal state (P1-D10 whitelisting seam).
# Usage: ./watch-run.sh <run_id> [--interval SECONDS]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec uv run --project "$SCRIPT_DIR" python -m ollama_mcp.oficina.cli watch "$@"
