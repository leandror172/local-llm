#!/usr/bin/env python3
"""PreToolUse(Bash) guard — block bulk `git add` that stages unrelated files.

Wired from .claude/settings.json as a PreToolUse hook on the Bash tool. Reads
the tool call as JSON on stdin and, if the command runs `git add -A`,
`git add .`, or `git add --all` (anywhere — including `rtk git add -A` or a
`&&`/`;`/`|` chain), emits a deny decision so the command never executes.

Why: `git add -A/./--all` sweeps in unrelated pre-existing untracked files
(scratch dirs, other features' WIP) — exactly the mistake this repo wants to
prevent. Explicit paths or `git add -u` (tracked-only) are the safe forms.

The match is anchored to a COMMAND POSITION (start of string, or after a
separator `; & | newline ( {`), with an optional `rtk ` prefix, so that a
commit message, grep, or doc that merely *mentions* `git add -A` is NOT blocked
— only an actual invocation is. The argument side stays tight:
  (^|[\\n;&|({])\\s*(rtk\\s+)?git\\s+add\\s+(-A\\b | --all\\b | \\.(\\s|$))
so `git add path`, `git add -u`, and `git add .claude/x` all pass.
"""
import json
import re
import sys

# Bulk-add forms only: -A, --all, or a bare "." (followed by whitespace or EOL).
#   - command-position anchor [\n;&|({] (covers && || | ; subshells) — avoids
#     matching the pattern inside a quoted arg (e.g. `git commit -m "git add -A"`).
#   - optional `rtk ` prefix (this repo wraps git in rtk).
#   - a leading "." in a path like ".claude/x" is NOT bare (next char isn't \s|$).
_BULK_ADD = re.compile(r"(?:^|[\n;&|({])\s*(?:rtk\s+)?git\s+add\s+(?:-A\b|--all\b|\.(?:\s|$))")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # unparseable input → never block (fail open)

    command = (data.get("tool_input") or {}).get("command", "")
    if not _BULK_ADD.search(command):
        return 0  # not a bulk add → allow silently

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Bulk `git add -A` / `git add .` / `git add --all` is blocked — "
                "it stages unrelated pre-existing untracked files. Stage explicit "
                "paths (`git add path/a path/b`), or only tracked-file changes "
                "(`git add -u`, which never grabs new untracked files)."
            ),
        }
    }
    print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
