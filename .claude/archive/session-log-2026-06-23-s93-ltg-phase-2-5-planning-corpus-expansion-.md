## 2026-06-23 - Session 93: LTG Phase 2.5 planning — corpus expansion plan + source-group provenance (T-65)

### Context

Planning/orientation session. PR #55 (LTG Phase 3 anchors) was merged to master externally; opened by discussing next steps and drilling into Phase 2.5.

### What Was Done

- Drafted `docs/plans/ltg-phase2.5-corpus.md` — full Phase 2.5 execution plan: scope, 7 steps, compute estimate, config-driven ignore + group tags.
- Measured the real MVP corpus: 66 files / ~618 KB / ~155 K tokens after excluding `.claude/local/` (679 KB handoff-run noise) and resolving the long-file branch point.
- Added task T-65 (source-group provenance + query-type-dependent retrieval weighting) and a durable memory for the future Phase-5 weighting feature.
- Indexed the plan in `.claude/index.md`; committed (docs(ltg-phase2.5)).

### Decisions Made

- `.claude/archive/` IS ingested in Phase 2.5 but tagged as its own group (not excluded) — enables future query-type-dependent weighting (up-weight for "past decisions" queries).
- Long-file branch point RESOLVED by measurement: largest legit file ~8.7 K tokens < 16 K ceiling → no chunking for this MVP.
- Code-file ingestion DEFERRED (Phase 8 territory); MVP stays prose-only.
- Exclusions should be config-driven (`corpus.yaml` or a `corpus:` block) declaring include_roots / exclude_globs / group tags — not hardcoded in a script.
- Source-group provenance: cheap half (capture group at ingest) lands in Phase 2.5; the actual query-type weighting logic is deferred to Phase 5 (T-65).

### Next

- Build LTG Phase 2.5 starting at Step 0 (corpus-selection config + frozen manifest). Two build-time choices deferred: `corpus.yaml` vs a `corpus:` block in `config.yaml`; add a `source_group` schema field now vs manifest-only.
- Then LTG Phase 4 — graph + communities (`alias_of` lists are proto-edges).

### Gotchas

- Estimated local-GPU cost for Phase 2.5 extraction is ~45–70 min wall-clock (Step 1 dominates), worst realistic ~90 min; ~$0 (local inference).
