#!/usr/bin/env bash
# Live acceptance for the P4 judge gate (A1/A2 replay + A5 live run).
# Makes real Ollama calls — needs the judge persona loaded and takes about a minute.
# Pass case names to narrow it:  ./run-acceptance-p4.sh A1 A2
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/scripts/acceptance_p4.py" "$@"
