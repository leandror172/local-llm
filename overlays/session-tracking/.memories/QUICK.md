# session-tracking overlay — Quick Memory

*Working memory. Current-state only, keep under ~30 lines — chronology lives in
`.claude/archive/session-tracking-handoff-history.md`; concepts in `KNOWLEDGE.md`.*

## Current State (2026-07-09, session 111)

- **Version:** v11 — **R-D9 packaging flip.** Code ships as the `session-tracking` Python
  package; the overlay installs config + docs only. `always_user_files:` is gone.
- **Engine:** `uv tool install --editable overlays/session-tracking` → console entry point
  `st-handoff`. The shim resolves `st-handoff` → source tree → **legacy**
  `~/.claude/tools/handoff/` (transitional; delete once every repo is migrated).
- **Layout:** `src/sessiontracking/{register,handoff}`. `register/` = `registry_io` +
  `locator` — the primitive, shared with the coming `resume/`; products never import each
  other. `pyproject.toml` at the overlay root; tests moved to `tests/`.
- **Schema guard:** `load_register` refuses an unrecognised `registry.yaml: version:`
  (exit 2); an absent version means schema 1. Three version facts, never conflate: package
  `--version` (machine-global) ≠ `registry.yaml: version:` (per-file contract) ≠ CLAUDE.md
  `<!-- overlay:session-tracking vN -->` (per-repo config generation).
- **Tests:** 236 across the overlay suite (`make test`); 183 in the package.
- **Installed:** consumer repos still execute the **legacy** flat-module engine and read
  CLAUDE.md v10. Migrating them to the package rides with the `resume.yaml` work.
- **Key files:** `pyproject.toml`, `src/sessiontracking/`, `tests/`, `manifest.yaml`,
  `files/handoff/run-handoff.sh` (shim), `files/registry.yaml`, `files/resume.sh`,
  `files/rotate-session-log.sh`,
  `files/handoff-harvest.sh` (boundary `^chore(session-handoff): session `),
  `files/session-handoff/SKILL.md`.
- **Gotcha (recurring):** never run the installer to "just refresh the engine" without
  `--dry-run` + diff-review — it also reconciles project-level files.
- **Deferred:** local-model Placer (E1–E2) fills the existing value-only payload schema;
  Increment-4 separate-window synthesis (documented only); pip-editable distribution.

## Deeper Memory → KNOWLEDGE.md

Concept-organized semantic memory: pipeline map, the register (safety boundary +
customization seam), invariants, payload contract, CLI + failure taxonomy, storage
topology, distribution, operational hazards. Each section is `ref:`-keyed and ends with
"Source / more detail" pointers.
