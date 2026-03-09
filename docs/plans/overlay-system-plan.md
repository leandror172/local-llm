# Plan: Overlay System for Portable Repo Augmentation

**Status:** Planned (designed in session 39b, not yet implemented)
**First overlay:** `ref-indexing`
**Test target:** `~/workspaces/expenses/code` (update/retrofit case — partial manual install exists)

---

## Context

We have reusable infrastructure patterns (ref indexing, session tracking, ollama scaffolding)
developed in the LLM repo that need to be portable to other repos. Today they're applied
manually and inconsistently. We need a system that:

- Packages a pattern as a self-contained "overlay"
- Installs it to a target repo (deterministic file copy + intelligent merge)
- Detects existing (un-marked) installations and retrofits markers
- Supports updates when the overlay version changes
- Produces a report of every action taken and why
- Works in three modes: manual (TODO list), AI-assisted interactive, AI-assisted unattended

## Design decisions (from session 39b discussion)

- **Marker format:** `<!-- overlay:NAME vN -->` / `<!-- /overlay:NAME -->` — no conflict with `<!-- ref:KEY -->` pattern (different prefix, verified against ref-lookup.sh and check-ref-integrity.py regex patterns)
- **Manifest format:** YAML (pyyaml already available; supports comments)
- **Installer language:** Python (bash proved too fragile for parsing tasks — ref integrity checker lesson)
- **AI backend for merges:** auto-detect: Ollama (local, free) → `claude -p` (frontier) → manual
- **`agent_targets` block** (renamed from "integrations"): declares which AI tool configs are targeted. Only `claude-code` for v1.
- **Report:** structured output of every action + rationale; stdout default, `--report FILE` for file, `--report-format json` for programmatic
- **Scope:** ref-indexing overlay only; produces a template for future overlays
- **Retrofit strategy:** first "update" on expense repo injects markers into existing content; all subsequent updates are marker-driven

---

## Phase 1: Directory structure + manifest

### Step 1.1 — Create overlay directory

```
overlays/
  ref-indexing/
    manifest.yaml
    files/
      ref-lookup.sh
      check-ref-integrity.py
      check-ref-integrity.sh
    templates/
      index.md.tmpl
    sections/
      claude-md-ref-rules.md
      gitignore-lines.txt
    APPLY.md
    README.md
```

### Step 1.2 — Write manifest.yaml

```yaml
name: ref-indexing
version: 1
description: >
  Ref block documentation system: [ref:KEY] tags in CLAUDE.md point to
  <!-- ref:KEY --> blocks in *.md files. Includes lookup tool, integrity
  checker, and pre-commit hook.

# Files to copy to target repo (source relative to files/, dest relative to repo root)
files:
  ref-lookup.sh: .claude/tools/ref-lookup.sh
  check-ref-integrity.py: .claude/tools/check-ref-integrity.py
  check-ref-integrity.sh: .claude/tools/check-ref-integrity.sh

# Files to create from templates (only if dest doesn't exist — never overwrites)
templates:
  index.md.tmpl: .claude/index.md

# Lines to append to existing files (idempotent — grep before append)
append_lines:
  .gitignore:
    - ".claude/local/"

# Sections to inject into shared files using <!-- overlay:NAME vN --> markers
# merge_hint gives the AI a placement hint; ignored in deterministic mode
merge_sections:
  CLAUDE.md:
    file: sections/claude-md-ref-rules.md
    merge_hint: "insert near the top, after the main heading"

# Files that need manual merge if target already exists
manual_if_exists:
  - .githooks/pre-commit

# Which AI-tool configurations this overlay targets
agent_targets:
  claude-code:
    tools_dir: .claude/tools
    rules_file: CLAUDE.md
```

### Step 1.3 — Extract current ref-indexing files

- Copy current `ref-lookup.sh`, `check-ref-integrity.py`, `check-ref-integrity.sh` into `overlays/ref-indexing/files/`
- Write `sections/claude-md-ref-rules.md` — the CLAUDE.md section content (extracted from current LLM repo CLAUDE.md, wrapped in overlay markers)
- Write `templates/index.md.tmpl` — a starter `index.md` with placeholder structure
- Write `APPLY.md` — AI-readable instructions for the merge-sensitive parts
- Write `README.md` — human-readable explanation of the overlay

### Step 1.4 — Write gitignore-lines.txt

Simple text file with lines to append: `.claude/local/`

**Checkpoint:** directory structure complete, no installer yet. Verify files are correct by manual inspection.

---

## Phase 2: Installer script (`install-overlay.py`)

### Step 2.1 — Core installer logic

Create `overlays/install-overlay.py` with:

```
Usage: python3 overlays/install-overlay.py <overlay-name> --target <repo-path> [options]

Options:
  --target PATH       Target repo root (required)
  --mode manual|ai    Merge mode: manual (default) or ai-assisted
  --yes               Auto-accept AI decisions (unattended mode)
  --backend ollama|claude|auto   AI backend for merge mode (default: auto)
  --report FILE       Write report to file (default: stdout)
  --report-format text|json   Report format (default: text)
  --dry-run           Show what would be done without doing it
```

### Step 2.2 — Implement deterministic actions

In order:
1. Read `manifest.yaml` from overlay directory
2. Validate target repo exists
3. **File copy:** for each entry in `files:`, compare source vs dest:
   - Dest missing → copy, report `[COPY]`
   - Dest matches source (sha256) → skip, report `[SKIP] up to date`
   - Dest differs → copy + backup original, report `[UPDATE]`
4. **Templates:** for each entry in `templates:`, check if dest exists:
   - Dest missing → instantiate template, report `[CREATE]`
   - Dest exists → skip, report `[SKIP] already exists (user-managed)`
5. **Append lines:** for each entry in `append_lines:`, grep target file:
   - Line missing → append, report `[APPEND]`
   - Line present → skip, report `[SKIP] line already present`
6. **Manual-if-exists:** for each entry, check if dest exists:
   - Dest missing → copy from `files/` if available, report `[COPY]`
   - Dest exists → report `[TODO] manual merge needed`

### Step 2.3 — Implement merge-sensitive actions

For each entry in `merge_sections:`:
1. Read target file (e.g., CLAUDE.md)
2. Check for existing `<!-- overlay:NAME -->` marker:
   - **Marker found, same version** → skip, report `[SKIP] already installed v1`
   - **Marker found, older version** → replace section content, update version in marker, report `[UPDATE] v0 → v1`
   - **No marker, but content appears present** (retrofit case) → if `--mode ai`: ask AI to identify and wrap existing content with markers. If `--mode manual`: report `[TODO] retrofit markers`
   - **No marker, content absent** → if `--mode ai`: ask AI to merge. If `--mode manual`: report `[TODO] add section`
3. Write modified file (with backup)

### Step 2.4 — AI merge integration

Create `_ai_merge()` function:
1. Auto-detect backend: try Ollama at `localhost:11434`, fall back to `claude -p`, fall back to error
2. Build prompt with existing file content + section to add + merge rules
3. Parse response (expect the complete merged file)
4. If `--yes`: write directly. Otherwise: show diff, ask for confirmation
5. Report `[MERGE:AI]` with backend used and action taken

### Step 2.5 — Report generation

Accumulate all actions in a list of `{action, target, reason, details}` dicts.
At the end:
- Print summary table (copied/skipped/updated/merged/manual counts)
- If `--report FILE`: write full report to file
- If `--report-format json`: output as JSON array

**Checkpoint:** installer works for fresh installs. Test on a temp directory first.

---

## Phase 3: Test against expense repo (retrofit/update case)

### Step 3.1 — Dry run

```bash
python3 overlays/install-overlay.py ref-indexing \
  --target ~/workspaces/expenses/code \
  --dry-run
```

Expect: report showing which files already exist, which need markers, which need merge.

### Step 3.2 — Retrofit with AI

```bash
python3 overlays/install-overlay.py ref-indexing \
  --target ~/workspaces/expenses/code \
  --mode ai
```

Expect: AI detects existing `ref-lookup.sh` (copies/updates), identifies the CLAUDE.md ref section (wraps with markers), skips `index.md` (already exists).

### Step 3.3 — Verify

- Run `check-ref-integrity.sh --root ~/workspaces/expenses/code` — should find fewer issues than before
- Check that `<!-- overlay:ref-indexing v1 -->` markers are in expense repo's CLAUDE.md
- Run `ref-lookup.sh --root ~/workspaces/expenses/code list` — should list all keys

### Step 3.4 — Test idempotency

Run the installer again — expect all `[SKIP]` actions.

**Checkpoint:** overlay system works for both fresh install and retrofit. Expense repo is clean.

---

## Phase 4: Template for future overlays

### Step 4.1 — Document the overlay authoring process

Write `overlays/README.md` explaining:
- Directory structure convention
- manifest.yaml schema
- How to write merge sections with markers
- How to write APPLY.md for AI-assisted merges
- How to test an overlay (dry-run, fresh, update, idempotency)

### Step 4.2 — Identify next overlay candidates

Candidates from this repo:
- `session-tracking` — session-log.md, session-context.md, tasks.md, resume.sh, rotate-session-log.sh, session-handoff skill
- `ollama-scaffolding` — CLAUDE.md rules for local model usage, verdict capture hooks
- `verdict-hooks` — PostToolUse/Stop/SubagentStop hooks (user-level, not repo-level)

**Checkpoint:** one working overlay + documented template. Future overlays follow the same pattern.

---

## Estimated effort

| Phase | Scope | Size |
|---|---|---|
| Phase 1 | Directory structure + files | ~1 hour (mostly file extraction) |
| Phase 2 | Installer script | ~2-3 hours (core logic + AI merge + report) |
| Phase 3 | Expense repo test | ~1 hour (run + verify + fix) |
| Phase 4 | Documentation | ~30 min |

## Dependencies

- `pyyaml` — already available in the MCP server venv; system-wide via `pip3`
- Ollama running (for AI merge mode) — already standard in this project
- Expense repo at `~/workspaces/expenses/code` — already present
