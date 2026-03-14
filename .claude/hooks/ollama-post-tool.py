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

# Only generation tools produce output worth a verdict.
# Infrastructure/management tools (warm_model, list_models, ref_lookup,
# query_personas) are fire-and-forget — no verdict needed.
GENERATION_TOOLS = {
    "mcp__ollama-bridge__ask_ollama",
    "mcp__ollama-bridge__generate_code",
    "mcp__ollama-bridge__summarize",
    "mcp__ollama-bridge__translate",
    "mcp__ollama-bridge__classify_text",
    "mcp__ollama-bridge__build_persona",
    "mcp__ollama-bridge__detect_persona",
}
tool_name = data.get("tool_name", "")
if tool_name not in GENERATION_TOOLS:
    print(json.dumps({}))
    sys.exit(0)

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
