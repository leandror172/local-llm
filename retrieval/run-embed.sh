#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/embed.py" "$@"
