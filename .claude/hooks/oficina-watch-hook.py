#!/usr/bin/env python3
"""PostToolUse(mcp__ollama-bridge__submit_run) — inject the watch instruction.

Wired from .claude/settings.json as a PostToolUse hook matching the oficina
submit_run MCP tool. Reads the hook input JSON on stdin, extracts the accepted
run_id from tool_response (plain dict or JSON-escaped nested string), and emits
additionalContext instructing Claude to background watch-run.sh — so the
harness, not the model's memory, drives result injection (T-89 / V-D12).

Fail open: on any parse failure or missing run_id (e.g. an intake-rejected
submit), print nothing and exit 0 — a hook must never break the tool flow.
"""
import json
import os
import re
import sys

# Matches "run_id": "<value>" in serialized JSON whether quotes are plain or
# backslash-escaped (tool_response may nest the result as a JSON-encoded string).
_RUN_ID_PATTERN = re.compile(r'\\{0,2}"run_id\\{0,2}"\s*:\s*\\{0,2}"([A-Za-z0-9_-]+)')

def _parse_stdin() -> dict | None:
    """Parse stdin as JSON. Return the parsed data or None if parsing fails."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return None

def _extract_run_id(data: dict) -> str | None:
    """Extract run_id from tool_response, handling both plain dicts and nested JSON strings."""
    tool_response = data.get("tool_response")
    if not tool_response:
        return None
    match = _RUN_ID_PATTERN.search(json.dumps(tool_response))
    return match.group(1) if match else None

def _watch_script() -> str:
    """Absolute watcher path — the shell's cwd may have drifted from the repo root."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "/mnt/i/workspaces/llm")
    return f"{project_dir}/mcp-server/watch-run.sh"


def _generate_watch_instruction(run_id: str) -> str:
    """Generate the watch instruction message with the given run_id."""
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"oficina run {run_id} accepted. Immediately run the Bash tool with command {_watch_script()} {run_id} and run_in_background=true — the harness will inject the run's result (the Delivered event carries it) into this conversation when the watcher exits. Do not poll run_status in a loop."
        }
    })

def main() -> int:
    """Main entry point for the hook script."""
    data = _parse_stdin()
    if not data:
        return 0
    
    if data.get("tool_name") != "mcp__ollama-bridge__submit_run":
        return 0
    
    run_id = _extract_run_id(data)
    if not run_id:
        return 0
    
    print(_generate_watch_instruction(run_id))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # fail open — a hook must never break the tool flow
