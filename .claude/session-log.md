# Session Log

**Current Layer:** LTG Phase 3 COMPLETE → Phase 4 (graph + communities) next
**Current Session:** 2026-06-20 — Session 92: LTG Phase 3 anchor integration — anchors.py shipped (PR #55)

---
## 2026-06-20 - Session 92: LTG Phase 3 anchor integration — anchors.py shipped (PR #55)

### Context

Standing next work item was LTG Phase 3 `anchors.py` (decisions frozen session 82). Built it via the multi-subagent TDD pattern to conserve main-session context: a main-owned contract-pin + four sequential subagent slices (reused warm agent for SA-1→3, fresh for SA-4) + main-session integration review and live-model acceptance.

### What Was Done

- Contract-pin (main/Opus): extended `store.py` `build_schema` in place 18→22 fields (`source_class`, `confidence`, `anchor_key`, `alias_of`); created `retrieval/anchors.py` skeleton — `Anchor`/`RebuildReport` dataclasses, `COSINE_THRESHOLD` + method constants, `NotImplementedError` stubs; pinned `match_anchors` M:N seam `dict[topic_id -> list[anchor_key]]`.
- SA-1: `ingest_anchors` (git grep tracked `*.md`, dedup, 143 anchors), `parse_first_prose_line`, three `describe_*` + dispatch. 33 tests.
- SA-2: `match_anchors` exact in-memory cosine over unit vectors. 15 tests. Ollama verdict 2.
- SA-3: `build_anchor_rows` (field table §4) + `apply_aliases` (M:N JSON list, confidence unchanged by aliasing). 32 tests. Surfaced the description-source contract gap.
- SA-4: `rebuild_index` + `staleness_warnings` + near-miss diagnostic + `run-anchors.sh` + approved `descriptions` param. 26 tests.
- Live acceptance: rebuilt index = 212 rows (69 topics + 143 anchors); `concept-latent-topic-graph` merged both `.memories` topics, M:N proven (`ltg_implementation` aliased by 2 anchors), orphan `ltg-corpus` no-merge, staleness + near-miss firing. 254 tests green. PR #55 opened.

### Decisions Made

- Schema extended in `store.py` in place (one canonical schema) rather than a separate `build_schema_v3` wrapper — avoids drift.
- Matching is exact in-memory cosine, not LanceDB ANN — M:N alias correctness needs exactness; 143×69 is free.
- Escalation deferred (diagnostic-only): near-miss band report, no LLM/conditional logic in Phase 3.
- `build_anchor_rows` gained an optional `descriptions` param so non-default methods store the embedded text (approved mid-session after SA-3 flagged the gap rather than hacking).
- Staleness handled by warn-not-fix: reuse stored topic vectors, preserve provenance fields, emit mtime warnings (D6 #4). Re-extraction deferred to Phase 2.5.

### Next

- LTG Phase 4 — graph + communities. `alias_of` lists are proto-edges to relocate into the edge table; anchor↔anchor edges (index.md cross-refs) also land here.
- Merge PR #55 when ready.

### Gotchas

- Two bugs slipped past green tests because they are integration-only: (1) `from retrieval.X import` failed at runtime — the `run-*.sh` wrappers put the script dir on `sys.path`, so siblings must be `from model_client import ...` (mocked tests never executed the lazy import lines); (2) the frozen decision docs write `ref:concept-ltg` / `ref:plan-ltg` as shorthand — the real keys are `ref:concept-latent-topic-graph` / `ref:plan-latent-topic-graph`. This is why a live-model acceptance step (not just mocked TDD) was reserved for main session.
- `plan-latent-topic-graph` did not merge (top 0.7742, below threshold AND below NEARMISS_LOW) — D3 operational-metadata failure (`**Status:**`-opening) on a drifted corpus. Probe predicted 0.898 on the session-82 snapshot. Expected provisional/Phase-2.5 outcome, not a bug.
