# LTG Phase 4 — Acceptance Findings (T7)

<!-- ref:ltg-phase4-acceptance -->
**Date:** 2026-07-02 (session 102). **Branch:** `feature/ltg-phase4-graph`.
**Input:** 1018-row index (session 96) + 3332-edge table (T5 build @ frozen τ=0.70/K=10).
**Commands:** `retrieval/run-graph.sh` then `retrieval/run-communities.sh`.

## Result summary

| Criterion (ref:ltg-phase4-plan) | Verdict |
|---|---|
| Coarse communities roughly track semantic domains | **PASS** (with structure note below) |
| Archive group does not absorb everything | **PASS** — crosstab: c5 (n=56) is docs-research/ideas-dominated (49/56); c7 (n=38) is 87% docs-research |
| Fine communities split within domains (wiki+obsidian vs dify) | **PASS** (directional) — fine-community overlap wiki~obsidian 0.38 > wiki~dify 0.29 = obsidian~dify 0.29 |
| Top-20 edges by weight mostly defensible | **PASS** — 20/20 defensible on manual walk-through |
| All 21 alias merges present as `same_as` edges | **PASS** (T5) — 21 merged topics → 28 M:N pairs == 28 edges exact |
| Known near-miss visible as similarity edge | **PASS** (T5) — `ref:plan-latent-topic-graph` top similarity edge = 0.8379 (the T-63 value) |
| Full rebuild < 60 s, zero model calls | **PASS** — graph 5.1 s + communities 5.9 s ≈ 11 s |

## Community structure

- 1021 nodes assigned (see "phantom nodes" below), 203 coarse / 213 fine communities.
- Top coarse sizes: 194, 146, 121, 120, 71, 56, 41, 38, 17 — then a long singleton tail
  (the 184 τ-isolated nodes become singleton communities, as designed).
- smart-rag corpus (124 nodes): concentrated in c5 (44) + c1 (39) with c2 (12) — the
  research-hub vs broader-research split; remainder are isolated singletons. "Roughly
  track" satisfied; a single mega-community would actually have failed the intent.
- Coarse × source_group crosstab (from the run report): archive is the plurality in the
  4 largest mixed communities but never a monopoly; two research communities (c5, c7)
  are archive-light. The probe's no-hairball finding holds after clustering.

## Top-20 edge walk-through (all defensible)

Highlights: `ollama_installation` across two archive docs (0.9549); LDR ollama pipeline ↔
`ref:patterns-ollama-api` (0.9543); `ref:ddd-web-research-application` ↔
`ref:vision-web-research` (0.9535); sibling DDD anti-pattern topics (0.9533);
`smart-rag3:hybrid_search` ↔ `smart-rag-index:hybrid_retrieval` (0.9465);
`ref:ltg-phase3-decisions` ↔ `ref:ltg-phase3-discussion` (0.9312); MCP patch-file
acceptance pair (0.9302); `session-context` ↔ `tasks` ltg_phase_development (0.9146).
No junk edges in the top 20.

## Phantom nodes — staleness artifact (known, benign)

`references` edges are scanned repo-wide at graph-build time, but the nodes table is
frozen at its last anchors rebuild (session 96). Three anchors created since then appear
as edge endpoints with no node row: `ref:cache-warmed-fanout` (session 97),
`ref:ltg-phase4-plan`, `ref:ltg-phase4-decisions` (session 101). networkx auto-creates
them as graph nodes (hence 1021 assigned vs 1018 written; `write_communities` maps by
table id, so phantoms are silently not persisted — no corruption).

**Resolution:** the documented rebuild order (extract → embed → store → anchors →
graph → communities) makes this disappear — a fresh anchors rebuild ingests the new
anchors first. Left as-is for this acceptance run since the affected anchors are
Phase-4's own documentation.

## Notes for Phase 5

- Consumers should read relationships from the `edges` table only (P4-D6); community
  columns are derived data — null means "not yet computed since last anchors rebuild".
- Resolutions 0.5/1.5 produced a fine partition barely finer than coarse (203 → 213).
  If Phase 5 wants sharper intra-domain splits, raise `graph.resolutions.fine` (2.0+)
  and re-run `run-communities.sh` (~6 s) — cheap to iterate.
- Isolated-singleton tail: 184 nodes. If retrieval wants them attached, T-63 escalation
  or a lower τ with mutual-kNN are the levers; revisit with real relate() usage.

## Post-acceptance addendum (same session)

The user-requested fresh anchors rebuild exposed a **rebuild idempotency bug**
(`rebuild_index` re-read prior anchor rows as topics → duplicated anchors +
cosine≈1.0 self-alias matches, `same_as` 28→229). Fixed (`_topic_rows_only`,
+1 regression test) and the index rebuilt clean via the full documented order:
875 topics + **147 anchors** (the 3 phantoms above plus `ref:ltg-phase4-findings`)
= 1022 nodes, **3367 edges** (3222/28/117), zero dupes/phantoms/self-edges,
communities 207 coarse / 214 fine at 1022/1022 coverage. Details:
`ref:ltg-phase4-findings` (KNOWLEDGE.md) + PR #66.
<!-- /ref:ltg-phase4-acceptance -->
