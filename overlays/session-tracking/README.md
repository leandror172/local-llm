# session-tracking overlay

Packages the session continuity system for any Claude Code project.

## What it installs

| Action | Target | Condition |
|--------|--------|-----------|
| COPY | `.claude/tools/resume.sh` | Always (backup if differs) |
| COPY | `.claude/tools/rotate-session-log.sh` | Always (backup if differs) |
| COPY | `~/.claude/skills/session-handoff/SKILL.md` | User-level by default; `--skill-level project` installs per-repo |
| CREATE | `.claude/session-log.md` | Only if missing |
| CREATE | `.claude/session-context.md` | Only if missing |
| CREATE | `.claude/tasks.md` | Only if missing |
| MERGE | `CLAUDE.md` | Injects session-tracking section with overlay markers |

## Prerequisites

- `ref-indexing` overlay recommended (provides `ref-lookup.sh` used by `resume.sh`)

## Usage

```bash
# Install with session-handoff skill at user level (default)
./overlays/install-overlay.py session-tracking --target /path/to/repo

# Install with session-handoff skill per-repo instead
./overlays/install-overlay.py session-tracking --target /path/to/repo --skill-level project

# AI-assisted CLAUDE.md merge
./overlays/install-overlay.py session-tracking --target /path/to/repo --mode ai --yes

# Dry run
./overlays/install-overlay.py session-tracking --target /path/to/repo --dry-run
```

## After install

1. Edit `.claude/session-context.md` — fill in project-specific `user-prefs` and `current-status`
2. Edit `.claude/tasks.md` — replace placeholder phases with actual project phases
3. Edit `.claude/session-log.md` — update the first entry with actual session notes
4. Run `.claude/tools/resume.sh` to verify it outputs current status and ref keys
