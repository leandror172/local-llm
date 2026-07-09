# session-tracking overlay — Quick Memory

*Working memory. Current-state only, keep under ~30 lines — chronology lives in
`.claude/archive/session-tracking-handoff-history.md`; concepts in `KNOWLEDGE.md`.*

## Current State (2026-07-08, session 110)

- **Version:** v10 — the `customizable:` install category (T-61) closed the
  overlay-clobbers-local-edits problem. `resume.sh` ships with one repo-owned region,
  `overlay-keep:reading-guide`.
- **Tests:** 221 across the overlay suite (`make test`); 178 in the handoff pipeline.
- **Engine:** shared user-level `~/.claude/tools/handoff/` — ALL repos execute it. llm runs
  it from source via the shim's co-located-`handoff.py` preference.
- **Installed:** per-repo files synced **v9**; llm's own `resume.sh` is on **v10**.
  Consumers (expenses/code, web-research, career-search, latent-topic-graph) still on v9.
- **Next:** **T-79** — propagate v10 to the four consumers.
  ⚠️ career-search's `resume.sh` §2b is customized with **no `overlay-keep` markers** →
  a naive install resets it (decision-3 clobber). Pre-wrap in markers first.
  Procedure + watch-outs: `docs/plans/overlay-v10-propagation.md`.
- **Open PR:** #70 (`feature/overlay-customizable-regions`).
- **Key files:** `files/handoff/` (10 modules + shim), `manifest.yaml`,
  `files/registry.yaml`, `files/resume.sh`, `files/rotate-session-log.sh`,
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
