#!/usr/bin/env bash
# which-bridge.sh — list live ollama-bridge MCP server processes with their
# git SHA, branch, client_id, and log file. Reads the structured debug log
# to enrich /proc data.
#
# Usage: ./which-bridge.sh [path-to-log]
#   Default log: $OLLAMA_BRIDGE_LOG_FILE or /tmp/ollama-bridge.jsonl

set -u
LOG="${1:-${OLLAMA_BRIDGE_LOG_FILE:-/tmp/ollama-bridge.jsonl}}"

# Helper: extract a single field from a JSON line via python3.
# Usage: jget '<json line>' '<field-name>'
jget() {
    python3 -c '
import json, sys
try:
    rec = json.loads(sys.argv[1])
    print(rec.get(sys.argv[2], "?"))
except Exception:
    print("?")
' "$1" "$2"
}

mapfile -t LIVE_PIDS < <(pgrep -f "python.*-m ollama_mcp" | sort -n)

if [[ ${#LIVE_PIDS[@]} -eq 0 ]]; then
    echo "no live ollama-bridge processes found"
    exit 0
fi

if [[ ! -f $LOG ]]; then
    echo "log file not found: $LOG" >&2
    echo "(set OLLAMA_BRIDGE_LOG_LEVEL=INFO or DEBUG and restart a bridge to populate it)" >&2
fi

printf "%-7s %-7s %-9s %-9s %-7s %-50s %s\n" PID PPID CLIENT_ID GIT_SHA LEVEL BRANCH STARTED
printf "%-7s %-7s %-9s %-9s %-7s %-50s %s\n" ------- ------- --------- --------- ------- -------------------------------------------------- -------

for pid in "${LIVE_PIDS[@]}"; do
    # Find the most recent server_start event for this PID.
    if [[ -f $LOG ]]; then
        line=$(grep -F "\"pid\": $pid," "$LOG" 2>/dev/null \
            | grep '"ev": "server_start"' \
            | tail -n 1)
    else
        line=""
    fi

    if [[ -n $line ]]; then
        ppid=$(jget "$line" ppid)
        client=$(jget "$line" client_id)
        git=$(jget "$line" git)
        branch=$(jget "$line" branch)
        level=$(jget "$line" log_level)
        started=$(jget "$line" t)
    else
        # No banner — bridge predates the logging change, or
        # OLLAMA_BRIDGE_LOG_LEVEL is unset/WARNING so server_start was suppressed.
        ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ' || echo "?")
        client="(no banner — restart with OLLAMA_BRIDGE_LOG_LEVEL=INFO)"
        git="?"
        branch="?"
        level="?"
        started="?"
    fi

    printf "%-7s %-7s %-9s %-9s %-7s %-50s %s\n" \
        "$pid" "$ppid" "$client" "$git" "$level" "$branch" "$started"
done
