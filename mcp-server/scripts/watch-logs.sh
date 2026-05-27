#!/usr/bin/env bash
# watch-logs.sh — tail the ollama-bridge debug log with pretty formatting.
#
# Usage:
#   ./watch-logs.sh              # all bridges
#   ./watch-logs.sh abcd1234     # filter to one bridge's client_id
#   OLLAMA_BRIDGE_LOG_FILE=/path ./watch-logs.sh
#
# Output columns: time(HH:MM:SS.mmm) level event client=... pid=...  {extra-fields}

set -u
LOG="${OLLAMA_BRIDGE_LOG_FILE:-/tmp/ollama-bridge.jsonl}"
FILTER="${1:-}"

if [[ ! -f $LOG ]]; then
    echo "note: $LOG does not exist yet — will appear when a bridge starts" >&2
    # Create an empty file so tail -F doesn't spin on a missing path.
    : > "$LOG" 2>/dev/null || true
fi

# tail -F follows by name (survives rotation / recreation). The Python
# prettifier reads stdin line-by-line, formats each record, and flushes
# immediately so output is live, not buffered.
tail -F "$LOG" 2>/dev/null | PYTHON_FILTER="$FILTER" python3 -c '
import json, os, sys

want = os.environ.get("PYTHON_FILTER", "")
RESERVED = ("t", "level", "ev", "pid", "client_id")

for line in sys.stdin:
    try:
        r = json.loads(line)
    except Exception:
        sys.stdout.write(line)
        sys.stdout.flush()
        continue
    if want and r.get("client_id") != want:
        continue
    ts = r.get("t", "")[11:23] or "?"
    level = r.get("level", "?")
    ev = r.get("ev", "?")
    cid = r.get("client_id", "?")
    pid = r.get("pid", "?")
    extra = {k: v for k, v in r.items() if k not in RESERVED}
    print(f"{ts} {level:5s} {ev:18s} client={cid} pid={pid}  {extra}", flush=True)
'
