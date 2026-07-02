## 2026-07-02 - Session 101: LTG Phase 4 design locked (P4-D1–D7) + implementation plan authored

### Context

Session resumed right after PR #65 (machine-config move) merged and local master updated; goal was choosing next steps, which became the LTG Phase 4 design session.

### What Was Done

- PR #65 merge landed on master (`chore(ollama): move machine-specific config out of repo to ~/workspaces/ollama-infra`).
- Assessed T-63 as a Phase-4 blocker: NO — session-96 calibration shows sub-0.85 near-misses are coincidental topical adjacency, not missed aliases; the one real miss (`plan-latent-topic-graph` @ 0.8379) will still surface in the Phase-4 graph as a ~0.84 similarity edge. T-63 stays deferred; Phase 4's top-edge walk-through will supply its tuning evidence.
- LTG Phase 4 design discussion: decisions P4-D1–D7 locked (see decisions below).
- Authored `docs/plans/ltg-phase4-graph-communities.md` (`ref:ltg-phase4-plan`) — edge/community specs, 7-task TDD breakdown, Step-0 degree probe gating the thresholds — plus its `.claude/index.md` entry.
- Updated QUICK.md memories to Phase-4-plan-ready state (root repo-structure + LTG bullet were stale at "Phase 3 next"; retrieval QUICK got the session-101 status line). All committed together (`docs(ltg)` commit).

### Decisions Made

- **P4-D1 exact over ANN:** 1018×4096 pairwise cosine is one numpy matmul (~100–300 ms, 8 MB); ANN's silent recall loss can disconnect nodes from communities. Mirrors Phase-3 exact-matching rationale. Revisit at ~10k nodes with `ref:ltg-graph-lib`.
- **P4-D2 similarity-edge retention = `tau_floor` + union top-K, configurable:** new `graph:` section in `retrieval/config.yaml` (`tau_floor`, `top_k`, `resolutions`, `seed`); values frozen from a degree-distribution probe (τ ∈ {0.65–0.80} × K ∈ {5,10,15} + archive×archive edge share), not guessed. Floor kills manufactured edges; cap kills the archive hairball (51% of corpus).
- **P4-D6 `alias_of` projected, not migrated:** the column stays as the anchors-rebuild artifact; `graph.py` projects it into `same_as` edges; downstream consumers read the edge table only. Avoids schema migration and rebuild-order coupling while honoring "nothing depends on the row location".
- **P4-D5 wrinkle:** `community_coarse`/`community_fine` are nullable columns, all writers default null; an anchors rebuild nulls them → regenerate. Rebuild order is now extract → embed → store → anchors → graph → communities.

### Next

- Execute Phase 4 per `ref:ltg-phase4-plan`: T1 (networkx+leidenalg deps + `graph:` config) → T2 (`similarity_edges` TDD, synthetic vectors) → T3 (degree probe — freezes `tau_floor`/`top_k`, gates T5) → T4–T7.

### Gotchas

- `Anchor` dataclass retains only `heading`/`first_prose`, no block body — `reference_edges()` must re-read block bodies via `_read_block_lines` rather than extending the frozen dataclass (recorded in plan P4-D3 notes).
