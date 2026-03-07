#!/usr/bin/env python3
"""ollama-post-tool.py — PostToolUse hook for mcp__ollama-bridge__* calls.

Fires after every ollama-bridge tool call. Reads the most recent call
record from calls.jsonl to get the prompt_hash, then injects a compact
verdict template into Claude's context via additionalContext.

Claude fills the template inline in its response. The Stop hook
(verdict-capture.py) later scans the transcript and appends the
structured verdict record to calls.jsonl.

Hook output: JSON with "additionalContext" key (Claude Code spec).
"""

import json
import pathlib
import sys

CALLS_LOG = pathlib.Path.home() / ".local/share/ollama-bridge/calls.jsonl"

data = json.load(sys.stdin)

# Find the most recent *call* record (skip any verdict records at the tail).
prompt_hash = "unknown"
if CALLS_LOG.exists():
    for line in reversed(CALLS_LOG.read_text(encoding="utf-8").strip().splitlines()):
        try:
            entry = json.loads(line)
            if entry.get("type") != "verdict":
                prompt_hash = entry.get("prompt_hash", "unknown")
                break
        except Exception:
            continue

# Inject a compact template. Claude fills it before continuing its response.
# The prompt_hash is embedded so the Stop hook can match verdict → call record.
template = (
    f"[VERDICT prompt_hash={prompt_hash}]\n"
    "verdict: ACCEPTED | IMPROVED | REJECTED  ← pick one, delete the others\n"
    "reason: <one line>\n"
    "est_claude_tokens: <number — (prompt chars + response chars) / 4, mentally>\n"
    "[/VERDICT]"
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": template,
    }
}))
