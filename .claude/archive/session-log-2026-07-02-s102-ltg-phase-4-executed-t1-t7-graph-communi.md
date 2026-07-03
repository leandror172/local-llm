## 2026-07-02 - Session 102: LTG Phase 4 executed T1–T7 — graph + communities live (PR #66) + anchors-rebuild idempotency fix

### Context

Session started from the resume guide's "Phase 4 — plan ready, EXECUTE" entry; user approved starting at T1 after the reading list, with interactive pacing per task.

### What Was Done

- docs(ltg): freeze Phase 4 decisions in DECISIONS.md (ref:ltg-phase4-decisions) — landed pre-session, merged with PR #65
- feat(ltg): Phase 4 T1 — graph deps (networkx 3.6.1 + leidenalg 0.12.0 under uv/3.12) + `graph:` config + load_graph_config (8 tests)
- feat(ltg): Phase 4 T2 — similarity_edges exact-matmul + union top-K retention (6 synthetic-angle tests)
- feat(ltg): Phase 4 T3 — degree probe run over live 1018-row index; tau_floor=0.70/top_k=10 FROZEN (`ref:ltg-phase4-degree-probe`); probe grid cross-validated == similarity_edges (3189 edges exact)
- feat(ltg): Phase 4 T4 — same_as alias_of projection (P4-D6) + mention-based references edges via re-read block bodies (P4-D3)
- feat(ltg): Phase 4 T5 — edges table live build: 3332 edges; spot-checks pass (21 alias merges → 28 M:N same_as exact; T-63 near-miss visible at 0.8379)
- feat(ltg): Phase 4 T6 — communities.py (Leiden RBConfiguration, seeded, 2 resolutions) + nullable community columns, schema 23→25
- docs(ltg): Phase 4 T7 — acceptance PASS on all criteria (`ref:ltg-phase4-acceptance`); rebuild ≈11 s, zero model calls
- fix(ltg): anchors rebuild made idempotent — `_topic_rows_only` filters prior anchor rows from the topic read; index rebuilt clean (875 topics + 147 anchors = 1022 nodes, 3367 edges, zero dupes/phantoms/self-edges)
- PR #66 opened (all 8 Phase-4 commits + fix); docs sweep: reports ref-anchored, plan docs + index.md point EXECUTED → report refs, QUICK memories de-episodized (T-67 pattern)
- Local-model-first honored: 12 generate_code calls (4×verdict 2, 6×verdict 1, 1×verdict 0→stubs-retry→1), ~19K est. Claude tokens saved

### Decisions Made

- tau_floor=0.70 / top_k=10 frozen from the Step-0 probe, not guesses — τ=0.65 admits sub-meaningful edges (+63% edges), τ≥0.75 isolates 37–62% of nodes, K=15 fattens hubs without connectivity (`ref:ltg-phase4-degree-probe`)
- Archive-hairball risk closed empirically: 24.4% archive×archive edge share vs 18.3% random baseline — union top-K caps it structurally, no group-aware lever needed
- communities.py backs up via copytree (not store.py's move) — the index dir now holds topics + edges tables; move-then-recreate would orphan edges
- QUICK.md hygiene (T-67 pattern applied here): retrieval QUICK rewritten current-state-only; per-session ledger lives in KNOWLEDGE.md "Phase history ledger"; new entries go THERE

### Next

- LTG Phase 5 — `relate(a,b)` tool (`ref:ltg-plan-phase-5`): consumers read the edges table, never `alias_of` (P4-D6); Phase 4 reports at `ref:ltg-phase4-degree-probe` / `ref:ltg-phase4-acceptance` / `ref:ltg-phase4-findings`
- T-63 (near-miss escalation) now unblocked — Phase 4 edge evidence in hand (near-miss visible as 0.8379 similarity edge; ~26 anchors in the 0.80–0.85 band)

### Gotchas

- rebuild_index was NOT idempotent (fixed): it read the whole topics table as topic rows, so any anchors rebuild not preceded by a fresh store re-ingested prior anchor rows as topics — duplicated anchors + cosine≈1.0 self-alias matches (same_as 28→229). Green tests never caught it; only the operationally-realistic "just refresh anchors" run did.
- Single-slot index.bak composes badly across pipeline stages: anchors backed up the good index, then communities' backup overwrote that same .bak with the corrupted state → T-71.
- Timed-out MCP generate_code calls keep running server-side and serialize the Ollama queue — a trivial probe call waited 25 s of a 25.3 s round-trip. Split big generations instead of retrying blind; check /api/ps + a direct trivial chat to distinguish queue backlog from model failure.
- Append-driven file growth left `if __name__ == "__main__"` mid-file in graph.py — imports (tests) never notice, only the live CLI run failed. Guard belongs at EOF.
- Local-model snippet-append calls omit imports for names outside their visible context (3 occurrences: ingest_anchors, sys, load_graph_config) — prompt for "import every name you use that isn't in the visible context".
