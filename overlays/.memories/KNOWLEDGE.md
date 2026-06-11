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

## Session-Handoff Pipeline Architecture (2026-06)

The `session-tracking` overlay's handoff pipeline (`files/handoff/`) replaces the token-heavy
"Claude reads every tracking file and writes each section via many Edits" skill with a
register-driven deterministic transaction. Scope A uses **NO local model**.

- **Register** (`registry.yaml`): per-repo source of truth mapping each handoff-owned region to a
  file + locator (4 kinds: ref_block / structural / field / checklist) + write mode (replace /
  prepend / append / checkoff / nomodel). It also draws the safety boundary — every OTHER ref key is
  content / LTG anchor the pipeline MUST NOT touch.
- **F1 Locator → F3 Applier → F4 Verifier** (safety core): pure functions over `(role/Region, text)`.
  `Region(start,end,interior)` is the single boundary source of truth. F4 = recompute-and-compare
  (re-derive expected text byte-exact, independent of apply) + ref-marker multiset invariant — the
  trust boundary that will let an untrusted model run in the deferred enhancement.
- **F5 Mechanics** (`mechanics.py`): header-field bumps through the **nomodel fence** (the applier
  *refuses* nomodel so the payload path can never write headers — only the script can; the verifier
  *accepts* nomodel as replace), next-session-N (bootstraps to 1 on a fresh repo), date, rotation invoker.
- **F6 Orchestrator** (`orchestrator.py` + injected `gitio` adapter): atomic stage → apply → verify →
  write → rotate → commit, with **two safety layers** — in-memory verify-then-write + git checkout
  rollback — guarded by a clean-tree precondition on the tracking files.
- **Per-run logging** (`runlog.py`): `.claude/local/handoff-runs/session-<N>-<ts>/` holds `input.md`
  (verbatim payload = recovery artifact) + `report.md` (audit).
- **F7 payload + entrypoint** (`payload.py` schema; `registry_io.py` PyYAML loader; `handoff.py` CLI +
  `run-handoff.sh`): payload = first-two-`---` frontmatter (`session_title`/`current_layer`/`checkoffs`)
  + `## role:` sections. `--dry-run` runs the pure half (`_stage_and_apply`) and writes nothing — the
  rehearsal and the foundation for the T-53 preflight. PyYAML is allowed only in the entrypoint glue
  (`registry_io`); the F1–F6 safety core stays stdlib-only.
- **Install layout** (`manifest.yaml`): 10 runtime modules + `run-handoff.sh` ship via `files:` →
  `.claude/tools/handoff/`; the **register** ships via `manual_if_exists` → `.claude/handoff/registry.yaml`
  (**Option C**: copy-once, then *flag-on-update* — it's load-bearing yet per-repo, so neither silent
  overwrite nor silent skip is right). `handoff.py` resolves `repo_root` via `git rev-parse`, so the
  default registry path is correct without flags in installed repos.

**Rationale:** keep *decide content* with Claude, collapse *read+write* into one deterministic
register-driven call — no new in-file markers (they would pollute the LTG corpus that ingests
`.claude/` + `.memories/`). **Implication:** the register is both the repo-customization seam and the
handoff-owned-vs-content boundary; load-bearing contracts (register, F7 schema, F6 orchestration) stay
Claude-authored, while leaf modules (F5, logging) are local-model-delegable. Status (session 87):
**B1–B4 complete — Scope A fully done, 77 tests, dog-food-validated** (clone run on real content/register).
**PR #50** open (stacked on `feature/ltg-phase3-anchors`; retarget to master after the LTG PR merges).
**Home-repo activation:** the skill is installed *project-level* in the llm repo; the pipeline code is
NOT copied into `.claude/tools/` there (would duplicate the overlay source) — the skill's home-repo note
runs `overlays/session-tracking/files/handoff/run-handoff.sh` with an explicit `--registry`. Target repos
get the canonical `.claude/tools/handoff/` layout via the installer instead.

**Dog-food learning (session 86):** F4's invariants are *out-of-region bytes* + *ref-marker multiset* —
neither sees a **missing newline before a present marker**. A payload's last `## role:` section has no
trailing blank, so `payload.py` returned non-newline-terminated content, and append/replace/prepend glued
the line onto the closing marker. Fixed at the seam (`_normalize_block` in `_collect_edits`), NOT in the
safety core: the applier/verifier share an implicit "content is newline-terminated" contract and must
stay byte-identical, so normalize once upstream where both consume the same `items`.
