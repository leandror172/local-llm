# Overlays — Quick Memory

*Working memory for the overlay SYSTEM. Current-state only, keep under ~30 lines —
concepts live in `KNOWLEDGE.md`, chronology in `git log -- overlays/`.*

## Current State (2026-07-09, session 111)

- **Scope note:** the `session-tracking` overlay has its own memory —
  `overlays/session-tracking/.memories/{QUICK,KNOWLEDGE}.md`. This file is the system only.
- **Installer capabilities:** six install categories; `--verify` (see below);
  `customizable:` keep-regions (T-61) — `_extract_regions` / `_splice_regions` /
  `handle_customizable` in `lib/actions.py`. **`customizable:` now has ZERO call-sites**
  (`resume.sh` became a shim); that is the healthy steady state for an escape hatch.
- **Discriminating signals (T-80a, session 111):** `manual_if_exists` records `SAME`
  when the installed file is EOL-normalized-identical to source (was: unconditional `TODO`);
  `customizable:` decision-3 records `INFO … no-op` when the overlay default is already
  present verbatim, else `WARN-CLOBBER`. **Silence only on proof of safety** —
  `WARN-CLOBBER` means "cannot prove safe", not "will destroy". Helpers `_same_content` /
  `_reset_is_provable_noop` in `lib/actions.py`.
  ⚠️ **This is NOT T-54.** T-54 asks for a `--force-manual` override and is still unbuilt.
  Three session-111 commits mislabel the identical-file fix as T-54.
- **session-tracking is a PACKAGE (v11, R-D9):** code ships via
  `uv tool install --editable overlays/session-tracking` (entry point `st-handoff`);
  the overlay installs config + docs only. `always_user_files:` removed. The shim resolves
  `st-handoff` first, so all repos run the package; the legacy `~/.claude/tools/handoff/`
  copy is a dormant fallback and can be deleted.
- **`--verify` (T-82):** three questions, one per ownership — overlay-owned files byte-diff
  (gates); merge_sections version marker (gates); user-managed files record non-gating
  `EXPECTED` and are protected by the **locator contract** (`verify_locators:`): every
  register role must resolve, write roles gate (`BROKEN`), read-only advise (`ABSENT`).
  Exits 0 on all five repos. It found the starter templates did not satisfy their own
  register — a fresh install's first handoff would have failed on four roles.
- **Tests: 287 total** via `make -C overlays test` — `test-ref-indexing` (bash, 9) +
  `test-session-tracking` (pytest, 214) + `test-installer` (pytest, 64: `test_verify.py` +
  `test_customizable.py` + `test_signals.py`). Bare `make` prints help; `ARGS='-k x'` filters
  one suite. Not a test: `test-merge-plan.py` (manual Ollama diagnostic, network).
- **ref-indexing overlay:** v4 — hermetic overlay-shipped suite at `files/tests/`.
  PR **#63** (`feat/t42-ref-lookup-paths`) not yet merged into umbrella `batch/session-97-base` (#57).
- **session-tracking overlay:** v11 (packaging flip + config-driven resume), installed and
  committed in all five repos. `--verify` exit 0 everywhere. **PR #71**, branch
  `feature/resume-config-steps` — must merge before llm leaves the branch: the editable
  install points at the working tree, and `src/` does not exist on master.
- **Deferred:** **T-83** install-time baseline / lockfile — the installer records nothing about
  what it installed, so `manual_if_exists` cannot tell "source moved since you reconciled" from
  "legitimately differs" (7 unconditional `[TODO]`s across 4 repos). `dpkg` conffiles are the
  prior art. Plan: `docs/plans/overlay-install-baseline.md`; sequence T-54 after it.
  **T-81** `--mode ai` cannot be previewed (`--dry-run` never calls the model) and did not finish.
- **Deferred:** T-76 shared model-registry library (triggers: first non-Ollama provider in LTG,
  first external adopter, or a third internal consumer). Until then: when evolving
  `ai-backends.yaml`, check LTG's `config.yaml` vocabulary first — no gratuitous divergence.
- **Discipline (recurring):** a new suite must be listed in `run-all-tests.sh`, or it runs green
  while testing nothing. Never propagate an overlay without `--verify` or a per-file `cmp`.

- **Editing a `merge_sections` file does NOT propagate without a manifest `version:` bump
  (learned 2026-07-21, T-105, ollama-scaffolding v2→v3).** CLAUDE.md merges are gated on the
  installed `<!-- overlay:<name> vN -->` marker, so a content-only change to
  `sections/*.md` dry-runs as `[SKIP] CLAUDE.md — already installed v2` while the `files:`
  entry (hash-based) updates normally. The result is a **half-propagated overlay** that
  reports success. Rule: change a section → bump the version in the same commit.
- **Always dry-run against the real repo root.** `expenses` is not a repo — `expenses/code`
  is. Targeting the parent reported `[CREATE] CLAUDE.md — file missing`, i.e. it would have
  fabricated a CLAUDE.md and `.claude/` in a non-repo directory.

## Deeper Memory → KNOWLEDGE.md

Concept-organized semantic memory: system rationale, merge markers, AI merge mode, manifest
schema (6 categories), install levels, customizable keep-regions, `--verify` design, product
topology rule, test convention. Each section is `ref:`-keyed with "Source / more detail" pointers.
