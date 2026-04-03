# overlays/ — Knowledge (Semantic Memory)

*Overlay system decisions. Read on demand.*

## Why Overlays Exist (2026-03)

Three repos need the same operational patterns: ref-indexing for documentation lookups,
session tracking for continuity across Claude Code sessions, local model conventions
for verdict recording and retry policy. Copying files manually drifts. Overlays make
cross-repo consistency installable and version-tracked.

**Rationale:** The alternative was documenting conventions and hoping each repo
implements them correctly. Overlays encode conventions as installable packages.
**Implication:** New cross-cutting patterns should become overlays, not wiki pages.

## Merge Markers for Versioning (2026-03)

Overlay content injected into shared files (like CLAUDE.md) is wrapped in markers:
`<!-- overlay:ref-indexing v1 -->`. On update, the installer detects the old version,
removes the old content, and inserts the new version.

**Rationale:** CLAUDE.md is a shared file — multiple overlays and manual content coexist.
Markers let the installer find and replace its own content without touching the rest.
**Implication:** Manual edits inside overlay markers will be overwritten on update.
Customizations should go outside the markers.

## AI-Assisted Merge Mode (2026-03)

When `--mode ai` is used, an LLM plans where to insert overlay sections into existing
files. The planner outputs structured JSON (insert_after_line, delete_ranges), which
is then applied deterministically — the AI plans, code executes.

Backends (priority order): Ollama qwen3:14b with thinking, Ollama deepseek-r1:14b,
Claude CLI subprocess, Claude API direct.

**Rationale:** CLAUDE.md files have varying structure. Hard-coding insertion points
would break across repos. AI reads the target file and decides the right location.
**Implication:** AI merge is optional — manual mode always works. AI mode saves time
on initial install but manual review is still recommended.

## Manifest Schema (2026-03)

Each overlay has a `manifest.yaml` defining what to install:
- `files` — copy to destination (tools, scripts)
- `templates` — create only if missing (user-managed after creation)
- `merge_sections` — inject into shared files with merge hints
- `append_lines` — idempotent append to .gitignore, .githooks, etc.
- `manual_if_exists` — flag files that need human judgment if already present

**Rationale:** Declarative manifest over imperative script. The installer interprets
the manifest; the overlay author declares intent.
**Implication:** Adding a new overlay requires only a manifest and content files,
no changes to the installer itself.

## User-Level vs Project-Level Skills (2026-03)

Some overlays install Claude Code skills. `--skill-level user` puts them in
`~/.claude/skills/` (available in all repos). `--skill-level project` puts them
in the repo's `.claude/skills/` (repo-specific). Default is user-level.

**Rationale:** Skills like session-handoff and create-persona are useful everywhere,
not just in one repo. User-level avoids duplicating them across projects.
**Implication:** User-level skills are not version-controlled per repo. Changes
require updating the user-level installation separately.
