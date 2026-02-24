---
id: sh-04-git-hook
domain: shell
difficulty: medium

description: Git commit-msg hook enforcing Conventional Commits
---

Write a Git `commit-msg` hook that enforces Conventional Commits spec.

Valid format: `<type>(<scope>): <description>`
- `type`: feat, fix, docs, style, refactor, perf, test, chore, ci, revert
- `scope`: optional, letters/numbers/hyphens in parentheses
- `description`: mandatory, ≥10 chars, not ending with period

The hook script (`$1` = commit message file):
1. Skips merge/revert/fixup commits
2. Validates format with regex
3. Prints colored errors (red): wrong type, missing `: `, description too short
4. Exit 0 for valid, 1 for invalid

Also write `install-hooks.sh` that copies to `.git/hooks/commit-msg` and makes executable.

Requirements: pure bash + grep/sed only, ANSI colors, works with `--amend` and `-m`
