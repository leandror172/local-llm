## 2026-06-16 - Session 90: Handoff topology/value-only/harvest redesign (P1–P5) + 4-repo migration + PR #52

### Context

Continuation of the session-handoff redesign across /compact boundaries — P1–P2 (latest-only topology, value-only payload) landed earlier; this window drove P3–P5, the live data migration, and the end-to-end smoke test.

### What Was Done

- **P3** (`8e55a66`): `handoff-harvest.sh` seeds `what_was_done` from `git log` since the last handoff; SKILL Step 2 calls it, Step 3 reuses resident interiors instead of re-`ref-lookup`. 5 hermetic tests.
- **P4** (`82ef14f`): manifest v5→v6; overlay installed into expenses/code, web-research, career-search — every `files:` entry byte-verified with `cmp` (14/14 per repo); per-consumer SKILL update (global + project-level shadows); llm installed rotate/harvest refreshed; target registries left untouched (`manual_if_exists`).
- **Data migration**: all 4 repos' `session-log.md` migrated to latest-only (`rotate --keep 1` + drop the `Previous logs:` line, incl. expenses/code's multi-line wrapped pointer); career-search's byte-identical duplicate Session 56 collapsed (healed). Commits `eefcdfa` (llm), `d2714c0`/`77ff98b`/`4e500fe` (targets).
- **P5** (`823e292`): overlays QUICK/KNOWLEDGE + plan status → IMPLEMENTED; auto-memory updated; PR #52 retitled + body extended (166 tests).
- **Advisor-gated end-to-end smoke test**: SKILL-authored value-only payload → parse → render → prepend locator (anchored in the migrated header) → F4 verify → `stage_ok` (Session 90); aborted cleanly, tracking tree untouched. First true integration run of the new path.

### Decisions Made

- **D1 = value-only 2-full**, **D2 = clean break (v6, lockstep migration, no dual-accept)** — finalized and shipped.
- **Target registries left untouched**: the orphaned `header-previous-logs` role is inert because the pipeline only walks payload→register, never the reverse (verified in source).
- **PR #52 merges with 3 unrelated commits** (app.py SSR fix, sync-context.sh pair) — confirmed acceptable scope.

### Next

- Merge PR #52 (approved; `feature/ltg-phase3-anchors` already in master, no rebase needed).
- Resume LTG Phase 3 — write `anchors.py` (TDD); decisions frozen session 82 (`ref:ltg-phase3-decisions`).

### Gotchas

- `handoff-harvest.sh` keys off `^chore(session-handoff):`, which also matched the P4 commit (it reused that prefix), so harvest returned only 2 of this session's commits — a false boundary. Non-handoff commits should not reuse the prefix, or harvest should match `^chore(session-handoff): session ` (the promote format). See T-59.
- The live handoff that recorded THIS entry is itself the production end-to-end test of the new value-only pipeline.

