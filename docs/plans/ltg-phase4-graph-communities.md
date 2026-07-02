# LTG Phase 4 — Graph Assembly + Community Detection: Implementation Plan

**Status:** EXECUTED — complete, all acceptance criteria PASS (session 102, 2026-07-02, PR #66).
**Reports:** Step-0 degree probe → `retrieval/probes/phase4-degree-probe.md` (`ref:ltg-phase4-degree-probe`,
froze τ=0.70/K=10); acceptance findings + idempotency-fix addendum → `retrieval/probes/phase4-acceptance.md`
(`ref:ltg-phase4-acceptance`); condensed gotchas → `retrieval/.memories/KNOWLEDGE.md` (`ref:ltg-phase4-findings`).
**Context:** Master plan `ref:ltg-plan-phase-4`. Frozen upstream decisions: `retrieval/DECISIONS.md`
(`ref:ltg-graph-lib`, `ref:ltg-storage-layout`, `ref:ltg-phase3-decisions`).
Input index: 1018 rows (875 topics / 113 files + 143 anchors), qwen3-embedding:8b 4096-dim,
built session 96 (`ref:ltg-phase2.5-corpus`). Calibration: `retrieval/probes/phase2.5-calibration.md`.

**Phase character:** first LTG phase with **zero model calls** — pure derivation from the index.
Everything here regenerates from `topics.lance` in seconds; all thresholds are cheap to re-tune.

---

<!-- ref:ltg-phase4-plan -->
> **EXECUTED session 102 (PR #66) — all acceptance PASS.** Results: `ref:ltg-phase4-degree-probe`
> (τ/K freeze), `ref:ltg-phase4-acceptance` (criteria + idempotency-fix addendum),
> `ref:ltg-phase4-findings` (condensed gotchas).

## Decisions locked (session 101)

| # | Decision | Locked value |
|---|----------|--------------|
| P4-D1 | Similarity computation | **Exact** — one `M @ M.T` matmul over unit-normalized vectors (1018×4096 ≈ 100–300 ms, 8 MB result). No ANN (silent recall loss can disconnect nodes; same reasoning as Phase 3 exact matching). Revisit with `ref:ltg-graph-lib` at ~10k nodes. |
| P4-D2 | Similarity-edge retention | **Threshold floor + top-K cap, configurable.** Edge kept iff `cosine >= tau_floor` AND within either endpoint's top-K (union kNN; mutual-kNN is the tightening lever). Floor kills manufactured edges in sparse regions; cap kills the archive hairball (51% of corpus is mutually-similar session logs). Values frozen from the Step-0 degree probe, not guessed. Provisional: `tau_floor≈0.70`, `top_k≈10`. |
| P4-D3 | Anchor↔anchor `references` edges | **Mention-based, repo-wide:** scan each anchor's ref-block body for `ref:[a-z0-9-]+` mentions of other *known* keys (excluding self + own markers). Catches both `<!-- ref:KEY -->` and `[ref:KEY]` styles; superset of the DECISIONS "index.md cross-refs" phrasing. Directed, weight 1.0. Table co-location alone is NOT an edge. |
| P4-D4 | Edge table schema | New LanceDB `edges` table in `retrieval/index/` (see schema below). Undirected kinds stored once with canonical `src_id < dst_id`. |
| P4-D5 | Community storage | Two **nullable** columns on the nodes table (`community_coarse`, `community_fine`, int32). All existing writers default them to null; `communities.py` fills them. An anchors rebuild nulls them (fine — regenerate after; derived data). Separate membership table only if Phase 5 needs community-level metadata. `node_kind="community"` stays reserved, unused in Phase 4 (no community nodes yet). |
| P4-D6 | `alias_of` "relocation" semantics | `alias_of` on topic rows **stays** as the anchor-rebuild artifact (source of truth at match time); `graph.py` *projects* it into `same_as` edges at graph build. Consumers (Phase 5 `relate`, retrieval) read the edge table, never the row column. Satisfies "no downstream code hard-depends on the topic-row location" without a schema migration or rebuild-order coupling. |
| P4-D7 | Leiden setup | networkx for construction/traversal (frozen); convert to igraph for `leidenalg`. `RBConfigurationVertexPartition`, edge weights = `weight`, fixed `seed` for reproducibility. Two resolutions, configurable: provisional coarse `0.5`, fine `1.5` — tune at acceptance. |

## Configuration (`retrieval/config.yaml`)

New top-level `graph:` section (config.yaml graduates from model-client-only config —
consistent with the existing `COSINE_THRESHOLD` → config.yaml TODO):

```yaml
graph:
  tau_floor: 0.70      # similarity-edge floor — FROZEN FROM STEP-0 PROBE, provisional until then
  top_k: 10            # per-node kNN cap (union semantics)
  resolutions:
    coarse: 0.5        # leiden RBConfiguration resolution_parameter
    fine: 1.5
  seed: 42             # leiden RNG seed — reproducible partitions
```

Read via a small `load_graph_config()` helper in `graph.py`; `model_client.load_config()`
untouched (roles resolution stays model-only).

## Edge table schema (`edges` table, same LanceDB dir)

| Field | Type | Notes |
|-------|------|-------|
| `src_id` | string | node `id` (topic id, or `ref:KEY` for anchors) |
| `dst_id` | string | canonical `src_id < dst_id` for undirected kinds |
| `edge_kind` | string | `same_as` \| `similarity` \| `references` |
| `weight` | float32 | cosine for `similarity`; `1.0` for `same_as`/`references`. Edge-confidence == weight (DECISIONS "edge confidence" resolved here). |
| `directed` | bool | true only for `references` |
| `created_at` | string | ISO-8601 UTC |
| `run_id` | string | graph-build run id; build params (`tau_floor`, `top_k`) recorded in the run report under `retrieval/runs/`, not per-row |

## Deliverables

| Artifact | Purpose |
|----------|---------|
| `retrieval/graph.py` | Node load → exact similarity → retention rule → `same_as` projection (from `alias_of`) → `references` scan (reuse `anchors.ingest_anchors` + `_read_block_lines`) → write `edges` table. `--degree-probe` mode prints the τ×K grid stats without writing. |
| `retrieval/communities.py` | Read nodes+edges → networkx → igraph → Leiden at 2 resolutions → write `community_coarse`/`community_fine` back (overwrite + backup, store.py pattern) → sanity report (community sizes, community × `source_group` crosstab). |
| `retrieval/run-graph.sh`, `retrieval/run-communities.sh` | Bash wrappers (`uv run --project`, repo convention). |
| `retrieval/probes/phase4-degree-probe.md` | Step-0 findings: degree percentiles at τ ∈ {0.65, 0.70, 0.75, 0.80} × K ∈ {5, 10, 15} + archive×archive edge share → frozen `tau_floor`/`top_k`. |
| Optional | GraphML export (`networkx.write_graphml`) under `retrieval/runs/` for manual viz. |

## Task breakdown (TDD; local-model-first per `ref:local-model-conventions`)

1. **T1 — deps + config:** add `networkx`, `leidenalg` (pulls `python-igraph`) to `retrieval/pyproject.toml`; verify wheels install under uv/3.12. Add `graph:` section + `load_graph_config()` (TDD).
2. **T2 — `similarity_edges()` (TDD):** synthetic unit vectors at known angles; assert floor, union-top-K, canonical ordering, no self-edges. No Ollama needed.
3. **T3 — Step-0 degree probe:** run `--degree-probe` against the live index; write `probes/phase4-degree-probe.md`; **freeze `tau_floor`/`top_k` in config.yaml** (gate for T5).
4. **T4 — `same_as_edges()` + `reference_edges()` (TDD):** alias_of JSON-list projection (M:N → one edge per pair); mention scan with self-exclusion + unknown-key filtering.
5. **T5 — edges table write + `run-graph.sh`:** live build; spot-check the 21 known alias merges land as `same_as` edges and `plan-latent-topic-graph`↔topic appears as a ~0.84 `similarity` edge (the T-63 near-miss made visible).
6. **T6 — `communities.py` (TDD):** deterministic partition on a small synthetic graph (two obvious clusters + bridge); nullable-column defaults added to existing writers (`store.rows_to_arrow_table`, `anchors.build_anchor_rows`/`apply_aliases`); schema 23→25.
7. **T7 — live run + acceptance:** criteria below; findings doc; `.claude/index.md` + memories updates.

## Acceptance (from `ref:ltg-plan-phase-4`, concretized)

- Coarse communities roughly track semantic domains — all `smart-rag-*` files cluster; the `archive` group does not absorb everything (check the crosstab).
- Fine communities split within domains — LLM-wiki + Obsidian-Mind closer to each other than either to Dify.
- Manual walk-through of top-20 edges by weight: mostly defensible.
- All 21 alias merges present as `same_as` edges; known near-miss visible as `similarity` edge.
- Full graph + communities rebuild < 60 s, no model calls.

## Risks

- **leidenalg install** (C extension): manylinux wheels exist for 3.12; if uv install fails, igraph-native Leiden (`igraph.community_leiden`) is the fallback — same algorithm, one fewer dep.
- **Archive hairball** (51% of corpus): Step-0 probe measures it before we commit; if top-K alone can't tame it, the `source_group` field enables group-aware caps (T-65-style lever) without touching extraction/embedding.
- **Resolution values are corpus-relative:** 0.5/1.5 are conventional starting points; acceptance step 1 is the real tuner.
<!-- /ref:ltg-phase4-plan -->

---

## Rebuild ordering (operational note)

Full pipeline is now: extract → embed → store → anchors → **graph → communities**.
Graph and communities are pure projections — always regenerate after any anchors rebuild
(`run-anchors.sh` rewrites the nodes table and nulls community columns). No wrapper chaining
built in Phase 4; revisit a `run-rebuild-all.sh` when the sequence stabilizes.
