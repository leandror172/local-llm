#!/usr/bin/env bash
# run-record-verdicts.sh — Record verdicts for a completed comparison run.
#
# Use when compare-models.py ran non-interactively (e.g., inside Claude Code)
# and couldn't collect verdicts. Run this in a real terminal afterward.
#
# Usage:
#   ./run-record-verdicts.sh                          # last entry in default results file
#   ./run-record-verdicts.sh --list                   # show all entries with timestamps
#   ./run-record-verdicts.sh --entry 0                # first entry
#   ./run-record-verdicts.sh --file results/my.jsonl  # specific file

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$SCRIPT_DIR/record-verdicts.py" "$@"
