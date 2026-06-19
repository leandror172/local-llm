# session-tracking overlay

Packages the session continuity system for any Claude Code project.

## What it installs

| Action | Target | Condition |
|--------|--------|-----------|
| COPY | `.claude/tools/resume.sh` | Always (backup if differs) |
| COPY | `.claude/tools/rotate-session-log.sh` | Always (backup if differs) |
| COPY | `.claude/tools/handoff/*.py` (10 runtime modules) | Always — the deterministic handoff pipeline (test_*.py not shipped) |
| COPY | `.claude/tools/handoff/run-handoff.sh` | Always — pipeline entrypoint |
| MANUAL | `.claude/handoff/registry.yaml` | Copied if missing; **flagged for manual merge if present** (per-repo register — `manual_if_exists`) |
| COPY | `~/.claude/skills/session-handoff/SKILL.md` | User-level by default; `--skill-level project` installs per-repo |
| CREATE | `.claude/session-log.md` | Only if missing |
| CREATE | `.claude/session-context.md` | Only if missing |
| CREATE | `.claude/tasks.md` | Only if missing |
| MERGE | `CLAUDE.md` | Injects session-tracking section with overlay markers |

## Prerequisites

- `ref-indexing` overlay recommended (provides `ref-lookup.sh` used by `resume.sh` **and** by the handoff skill to fetch replace-mode interiors)
- **PyYAML** required by the handoff pipeline (`pip install pyyaml`) — only `registry_io.py` imports it; the F1–F6 safety core is stdlib-only

## Deterministic handoff pipeline

The `session-handoff` skill no longer edits the tracking files directly. It authors one
F7 payload (`.claude/local/handoff-pending.md`) and drives a two-phase CLI,
`.claude/tools/handoff/run-handoff.sh`: `--payload <file>` **stages** (locates each region via
the **register** `.claude/handoff/registry.yaml`, applies+verifies in memory, emits a JSON
handle; nothing written to tracking files) and `--id <handle>` **promotes** (applies, runs log
rotation, commits — rolling back on any failure). A failed stage leaves the payload at its
original path. Follow-up verbs: `--payload <file> --amend` attaches an additive-only run
(tasks-append + checkoffs, no scalars/header bump) to the last committed session;
`--abort <handle>` discards a pending run. The register is the per-repo customization
seam **and** the handoff-owned-vs-content boundary — every ref key NOT listed in it is content
the pipeline must never touch.

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

## resume.sh output sections

`resume.sh` prints an ~80-100 line summary at session start. Section order:

| # | Section | Source |
|---|---------|--------|
| 1 | Current status | `ref:current-status` in `session-context.md` (head -30) |
| 2 | Last session "Next" pointer | Parsed from top entry in `session-log.md` under `### Next` |
| 3 | Key file locations | `ref:quick-pointers` in `session-context.md` (full) |
| 4 | Active decisions | `ref:active-decisions` in `session-context.md` (head -12) |
| 5 | Recent git commits + uncommitted changes | `git log` / `git status` |
| 6 | Footer: user preferences + ref key count | `ref:user-prefs` in `session-context.md` |

All ref blocks are optional — missing blocks print a `(no ref:X block found)` notice rather than failing.

The `### Next` section in `session-log.md` entries should end with a `---` separator for the parser to find it cleanly.

## After install

1. Edit `.claude/session-context.md` — populate `ref:current-status`, `ref:quick-pointers`, `ref:active-decisions`, and `ref:user-prefs` blocks
2. Edit `.claude/tasks.md` — replace placeholder phases with actual project phases
3. Edit `.claude/session-log.md` — add a `### Next` subsection to the first entry
4. Run `.claude/tools/resume.sh` to verify all sections output correctly
