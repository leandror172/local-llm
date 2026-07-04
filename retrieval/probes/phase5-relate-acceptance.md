# LTG Phase 5 — relate(a,b) Acceptance Results

**Date:** 2026-07-03 (session 105). **Branch:** `feature/ltg-phase5-relate`.
**Plan:** `docs/plans/ltg-phase5-relate.md` (`ref:ltg-phase5-plan`). **Index:** 1022 nodes / 3367 edges / communities 207 coarse / 214 fine (post session-104 rebuild).
**Runtime:** seconds per pair warm (one qwen3:14b call via `relate_summary` role); cold start adds model load.

<!-- ref:ltg-phase5-acceptance -->
## Verdict bands — FINAL (P5-D4)

Kept at the provisional values; acceptance found no evidence to move them.

| Band | Rule (cascade, evaluated in order) | Grounding |
|------|-----------------------------------|-----------|
| strong | any `same_as` edge, OR max **similarity-kind** edge weight ≥ 0.85 | `anchors.COSINE_THRESHOLD` (Phase 2.5-validated) |
| moderate | any similarity edge exists (≥ τ by construction) | `config.yaml graph.tau_floor` = 0.70 |
| weak | no similarity edge; nearest-miss cosine ≥ 0.55 | `WEAK_COSINE_FLOOR` (relate.py; Phase 2 "related" floor) |
| unrelated | below | — |

**Documented inversion (kept deliberately):** `nearest_miss` reports the best cross-file pair, which can exceed τ when the pair merely lost the union-top-K cut — so a `weak` pair can carry a higher nearest_miss (e.g. hypothetically 0.72) than a `moderate` pair's single 0.70 edge. This is evidence-honest: "the graph linked them" vs "it didn't" is the primary signal, cosine magnitude the secondary. Pinned by `test_weak_can_carry_above_tau_nearest_miss`. Revisit only if a real consumer misreads it.

## Acceptance pairs (4 planned + 1 added probe)

| # | Pair | Expected (plan) | Result | Assessment |
|---|------|-----------------|--------|------------|
| 1 | `smart-rag-llm-wiki` ↔ `smart-rag-obsidian-mind` | ≥1 shared topic AND ≥1 divergence | **moderate** — 3 similarity edges (max 0.77: infrastructure links ↔ infrastructure integration; graph-based retrieval), 2 shared anchors, coarse Jaccard 0.5 | PASS on shared topics; divergence **cannot** be surfaced — the output schema has no divergence field and prose may only cite structured facts. Criterion amended → deferred divergence view (T-75). |
| 2 | `smart-rag-llm-wiki` ↔ `smart-rag-dify` | Low similarity with a specific reason | **moderate** — one edge @ 0.79 (`wiki_application_use_cases` ↔ `rag-dify`), 1 shared anchor, Jaccard 0.25 | ACCEPTED as correct-over-expectation: the plan's "low" predates Phase 4; both docs genuinely discuss RAG tooling and 0.79 is a real single-topic link. The *specific reason* requirement is met in the other direction (prose names the lone edge and its limits). |
| 3 | `smart-rag-repowise` ↔ `smart-rag-claude-mem` | Coherent shared-concept report | **weak** — zero cross-file edges, 1 shared coarse community, nearest_miss 0.67 (`llm_wiki_and_rag` ↔ `semantic_summarization`) | PASS on shape: the negative case is first-class exactly as designed (zero edge_stats + nearest_miss + specific prose reason). Verdict lower than the plan guessed; the report is coherent about *why*. |
| 4 | `smart-rag-mempalace` ↔ `QUICK-MEMORY` | Connection between never-citing docs; cross-group provenance | **moderate** — 2 edges (max 0.743, infrastructure ↔ architecture/design), 2 shared anchors incl. `ref:memory-files` | PASS on the connection. Provenance NOT exercised: both files are `docs-research` (plan's substitution assumed different groups). Covered by probe 5. |
| 5 | `retrieval/.memories/QUICK.md` ↔ `smart-rag-mempalace` (added) | Cross-group provenance + negative shape | **weak** — provenance `{memories: 8}` × `{docs-research: 8}`, zero edges, nearest_miss 0.631 | PASS — provenance crosses groups for real; prose cites the specific nearest-miss pair and cosine. |

## Prose fidelity (P5-D5 hallucination check)

Every numeric/structural claim in the five final summaries was checked against the structured dicts — no fabrication. Two defects found in the first iteration, both **rendering-layer** bugs, fixed in code not prompt-wrestling:

1. `_fmt_community_overlap` rendered raw community **id lists** (`shared [4]`) → model read "four shared communities". Fix: render counts (`len(shared)`).
2. `_fmt_nearest_miss(None)` rendered an explanatory sentence → model paraphrased it as speculation about why the field was absent. Fix: render `n/a` + prompt rule "do not mention absent fields".

Prompt file gained rules 6–7 (no absent-field narration; quote similarity numbers as-is, no magnitude editorializing — kills the vacuous "score below one" claim). Residual (accepted): the model occasionally spends one sentence noting nearest_miss is unavailable — faithful, non-speculative, merely redundant.

## Other findings

- **Fine resolution carried signal in all pairs** (fine Jaccard ≠ coarse in pairs 1/4) — the "207→214 barely splits" risk did not bite; `resolutions.fine` left untouched.
- **Shared-anchor over-trigger did not materialize** — 0–2 anchors per pair, all topically sensible; no generic-anchor filtering needed.
- **P5-D7 / P5-D1 guards** untriggered on the live runs (index fresh); covered by tests.
- General acceptance bar (master plan): outputs are specific and verifiable — each verdict names its exact evidence. **Phase 5 relate(a,b) ACCEPTED.**
<!-- /ref:ltg-phase5-acceptance -->
