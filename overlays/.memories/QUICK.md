# Overlays — Quick Memory

*Working memory for the overlay SYSTEM. Current-state only, keep under ~30 lines —
concepts live in `KNOWLEDGE.md`, chronology in `git log -- overlays/`.*

## Current State (2026-07-08)

- **Scope note:** the `session-tracking` overlay has its own memory —
  `overlays/session-tracking/.memories/{QUICK,KNOWLEDGE}.md`. This file is the system only.
- **Installer capabilities:** six install categories; `--verify` drift check (T-58, exit 1 on
  any `DIFF`/`MISSING`/`SRC-MISSING`, EOL-normalized); `customizable:` keep-regions (T-61,
  overlay v10) — `_extract_regions` / `_splice_regions` / `handle_customizable` in
  `lib/actions.py`.
- **Discriminating signals (T-54 + T-80a, session 111):** `manual_if_exists` records `SAME`
  when the installed file is EOL-normalized-identical to source (was: unconditional `TODO`);
  `customizable:` decision-3 records `INFO … no-op` when the overlay default is already
  present verbatim, else `WARN-CLOBBER`. **Silence only on proof of safety** —
  `WARN-CLOBBER` means "cannot prove safe", not "will destroy". Helpers `_same_content` /
  `_reset_is_provable_noop` in `lib/actions.py`.
- **Tests: 231 total** via `make -C overlays test` — `test-ref-indexing` (bash, 9) +
  `test-session-tracking` (pytest, 178) + `test-installer` (pytest, 44: `test_verify.py` +
  `test_customizable.py` + `test_signals.py`). Bare `make` prints help; `ARGS='-k x'` filters
  one suite. Not a test: `test-merge-plan.py` (manual Ollama diagnostic, network).
- **ref-indexing overlay:** v4 — hermetic overlay-shipped suite at `files/tests/`.
  PR **#63** (`feat/t42-ref-lookup-paths`) not yet merged into umbrella `batch/session-97-base` (#57).
- **session-tracking overlay:** v10. Open PR **#70**. Consumers still on v9 — see T-79.
- **Deferred:** T-76 shared model-registry library (triggers: first non-Ollama provider in LTG,
  first external adopter, or a third internal consumer). Until then: when evolving
  `ai-backends.yaml`, check LTG's `config.yaml` vocabulary first — no gratuitous divergence.
- **Discipline (recurring):** a new suite must be listed in `run-all-tests.sh`, or it runs green
  while testing nothing. Never propagate an overlay without `--verify` or a per-file `cmp`.

## Deeper Memory → KNOWLEDGE.md

Concept-organized semantic memory: system rationale, merge markers, AI merge mode, manifest
schema (6 categories), install levels, customizable keep-regions, `--verify` design, product
topology rule, test convention. Each section is `ref:`-keyed with "Source / more detail" pointers.
