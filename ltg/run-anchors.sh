#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
# Instance wrapper: run from the instance dir (CWD-relative engine defaults),
# corpus root = the llm repo (parent). Caller flags override the defaults.
cd "$SCRIPT_DIR"
exec uv run --project . ltg-anchors --repo-root .. "$@"
