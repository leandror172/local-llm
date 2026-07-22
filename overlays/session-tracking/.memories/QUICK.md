# session-tracking overlay — Quick Memory

*Working memory. Current-state only, keep under ~30 lines — chronology lives in
`.claude/archive/session-tracking-handoff-history.md`; concepts in `KNOWLEDGE.md`.*

## Current State (2026-07-09, session 111)

- **Version:** v11 — **R-D9 packaging flip.** Code ships as the `session-tracking` Python
  package; the overlay installs config + docs only. `always_user_files:` is gone.
  Installed + committed in **all five repos**; `--verify` exit 0 everywhere.
- **Engine:** `uv tool install --editable overlays/session-tracking` → entry points
  `st-handoff` / `st-resume`. Shim order: `st-handoff` → source tree → legacy
  `~/.claude/tools/handoff/` (dormant fallback). **PR #71 is MERGED and `src/` is on
  master** (verified 2026-07-21), so the editable install is safe on any branch — the
  old "checking out master breaks `st-resume` in four repos" hazard is resolved.
  The legacy `~/.claude/tools/handoff/` copy still exists on disk and is now deletable.
- **Layout:** `src/sessiontracking/{register,handoff,resume}`. `register/` = `registry_io`
  + `locator` — the primitive both products import; products never import each other.
  `pyproject.toml` at the overlay root; tests in `tests/`.
- **resume is config-driven (R-D1/R-D2):** `files/resume.yaml` (ships via
  `manual_if_exists`) lists steps — `text` / `region` / `log_next` / `git_log` /
  `git_status` / `run`. `region:` names a **register role**, resolved through the SAME
  `locate()` the handoff writes with. A step earns a fixed kind when the overlay owns the
  invariant it depends on; `run:` is the escape hatch. `resume.sh` is a thin shim.
- **Every repo invokes the handoff identically** — no `--registry`. The engine resolves
  `<repo-root>/.claude/handoff/registry.yaml`. The home repo is not special; it holds a
  register copy like any consumer. `--registry` survives for a register living elsewhere.
- **Schema guard:** `load_register` refuses an unrecognised `registry.yaml: version:`
  (exit 2); an absent version means schema 1. Three version facts, never conflate: package
  `--version` (machine-global) ≠ `registry.yaml: version:` (per-file contract) ≠ CLAUDE.md
  `<!-- overlay:session-tracking vN -->` (per-repo config generation).
- **Tests:** 296 across the overlay suite (`make -C overlays test`); 214 in the package
  (verified 2026-07-21).
- **Key files:** `pyproject.toml`, `src/sessiontracking/`, `tests/`, `manifest.yaml`,
  `files/handoff/run-handoff.sh` (shim), `files/registry.yaml`, `files/resume.yaml`,
  `files/resume.sh` (shim), `files/rotate-session-log.sh`,
  `files/handoff-harvest.sh` (boundary `^chore(session-handoff): session `),
  `files/session-handoff/SKILL.md`.
- **Gotcha (recurring):** never run the installer to "just refresh the engine" without
  `--dry-run` + diff-review — it also reconciles project-level files.
- **Gotcha (SKILL shadow):** `SKILL.md` installs via `user_files` = skip-if-present, so a
  **project-level copy shadows the global and silently stops updating**. llm's was three
  versions stale (documented a `stage_failed` status the CLI never emits). Removed session
  111. Do not create one unless the repo genuinely needs a different skill.
- **Deferred:** local-model Placer (E1–E2) fills the value-only payload schema;
  Increment-4 separate-window synthesis (documented only); **T-83** install-time baseline
  (`docs/plans/overlay-install-baseline.md`).

## Deeper Memory → KNOWLEDGE.md

Concept-organized semantic memory: pipeline map, the register (safety boundary +
customization seam), invariants, payload contract, CLI + failure taxonomy, storage
topology, distribution, operational hazards. Each section is `ref:`-keyed and ends with
"Source / more detail" pointers.
