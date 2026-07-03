# LTG Phase 4 — Step-0 Degree Probe (T3)

<!-- ref:ltg-phase4-degree-probe -->
**Date:** 2026-07-02 (session 102). **Branch:** `feature/ltg-phase4-graph`.
**Purpose:** freeze `graph.tau_floor` / `graph.top_k` (P4-D2) from measured degree
distributions instead of guesses. Gates T5 (live edge build).
**Index:** 1018 rows (875 topics + 143 anchors), qwen3-embedding:8b 4096-dim, built session 96.
**Command:** `uv run python graph.py --degree-probe` (defaults: τ ∈ {0.65, 0.70, 0.75, 0.80} × K ∈ {5, 10, 15}).

## Node population

| group | nodes | share |
|-------|-------|-------|
| archive | 436 | 42.8% |
| docs-research | 189 | 18.6% |
| memories | 116 | 11.4% |
| docs-ideas | 105 | 10.3% |
| ungrouped (anchors outside corpus roots) | 98 | 9.6% |
| claude-meta | 74 | 7.3% |

(Group counts include anchor rows, hence the deltas vs the session-96 topic-only counts.)

## Grid results

| tau | k | edges | isolated | p50 | p90 | p99 | max | archive_share |
|-----|---|-------|----------|-----|-----|-----|-----|---------------|
| 0.65 | 5 | 3105 | 53 | 5.0 | 11.0 | 21.0 | 42 | 0.2709 |
| 0.70 | 5 | 2181 | 184 | 4.0 | 9.0 | 18.8 | 34 | 0.2563 |
| 0.75 | 5 | 1231 | 382 | 1.0 | 6.0 | 14.0 | 24 | 0.2396 |
| 0.80 | 5 | 535 | 630 | 0.0 | 3.0 | 9.8 | 18 | 0.1944 |
| 0.65 | 10 | 5193 | 53 | 10.0 | 19.0 | 35.0 | 86 | 0.2532 |
| **0.70** | **10** | **3189** | **184** | **4.0** | **15.0** | **28.8** | **62** | **0.2440** |
| 0.75 | 10 | 1542 | 382 | 1.0 | 10.0 | 23.0 | 44 | 0.2302 |
| 0.80 | 10 | 602 | 630 | 0.0 | 3.0 | 12.0 | 24 | 0.1827 |
| 0.65 | 15 | 6710 | 53 | 13.0 | 25.0 | 46.8 | 119 | 0.2440 |
| 0.70 | 15 | 3703 | 184 | 4.0 | 18.0 | 38.5 | 83 | 0.2390 |
| 0.75 | 15 | 1681 | 382 | 1.0 | 10.0 | 26.0 | 55 | 0.2326 |
| 0.80 | 15 | 613 | 630 | 0.0 | 3.0 | 13.0 | 25 | 0.1827 |

**Cross-validation:** `similarity_edges(ids, vectors, 0.70, 10)` returns exactly **3189 edges** —
the vectorized probe grid and the production pair-loop agree (independent code paths).

## Findings

1. **The archive hairball did not materialize.** Archive holds 42.8% of nodes; random
   pairing would put ~18.3% of edges archive×archive ((436·435)/(1018·1017)). Observed
   share is 18–27% across the whole grid — at most a 1.5× over-representation, and only
   24.4% at the chosen operating point. Union top-K caps it structurally; no
   group-aware cap (T-65-style lever) needed.
2. **The floor, not K, controls isolation.** Isolated counts depend only on τ
   (53 / 184 / 382 / 630 at 0.65→0.80) — a node is isolated iff its nearest neighbor
   falls below τ, which no K can change. At τ=0.80 the floor dominates so hard that K
   barely matters (535/602/613 edges).
3. **τ=0.65 admits sub-meaningful edges.** The Phase 2.5 calibration put the
   tech-adjacent band at cosine ≈0.72; a 0.65 floor keeps pairs below that band,
   adds +63% edges (3189→5193) and fattens the max hub 62→86 for marginal semantic value.
4. **τ≥0.75 disconnects too much.** 37.5% (382) isolated at 0.75, 61.9% (630) at 0.80 —
   community detection over a graph where most nodes are singletons is pointless.
5. **K=10 vs 15 is diminishing returns.** +16% edges (3189→3703) but p99 29→39 and
   max 62→83 — fatter hubs, no new connectivity (isolation identical).

## Decision (FROZEN)

**`tau_floor = 0.70`, `top_k = 10`** — the provisional values survive the probe.

- 3189 similarity edges, mean degree ≈ 6.3, p50 4, p90 15, max 62.
- 184 isolated nodes (18%) are genuinely peripheral (no neighbor ≥ 0.70 anywhere);
  many are anchors that will gain `references`/`same_as` edges in the full graph.
- Consistent with the calibration bands: edges ≥0.70 sit at/above the tech-adjacent
  boundary (~0.72); the known T-63 near-miss (0.8379) is comfortably retained.

**Retune triggers:** corpus growth past ~2k nodes; acceptance walk-through (T7) showing
top-edge junk (raise τ) or fragmented communities (lower τ or raise K); mutual-kNN
remains the documented tightening lever (P4-D2).
<!-- /ref:ltg-phase4-degree-probe -->
