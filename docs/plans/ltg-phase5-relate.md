# LTG Phase 5 — `relate(a, b)` Tool: Implementation Plan

**Status:** PLANNED — design frozen session 104 (2026-07-03); implementation next session.
**Context:** Master plan `ref:ltg-plan-phase-5`. Upstream: Phase 4 graph + communities
(`ref:ltg-phase4-plan`, findings `ref:ltg-phase4-findings`, dataflow `ref:ltg-phase4-dataflow`).
Input index: 1022 nodes (875 topics / 113 files + 147 anchors) + `edges` table (3367 edges:
3222 similarity @ τ=0.70/K=10, 28 same_as, 117 references) + Leiden communities 207 coarse / 214 fine.
Calibration: `retrieval/probes/phase2.5-calibration.md`.

**Phase character:** first *consumer* of the graph — everything through Phase 4 built structure;
`relate()` is the first query surface. Read + aggregate over existing tables, plus exactly
**one model call** (the prose summary). Precursor exists: Phase 2's acceptance "P1 relate
preview" in `ltg_inspect.py` (mean pairwise cosine) — Phase 5 upgrades that probe into a tool.

---

<!-- ref:ltg-phase5-plan -->
## Decisions locked (session 104)

| # | Decision | Locked value |
|---|----------|--------------|
| P5-D1 | Input contract | **File paths only** (corpus-relative, as stored in `file_path`). Anchor-key / concept input deferred → T-73 (same aggregation, different node-set selector; anchors are nodes already). Unknown path → hard error listing nearest manifest matches. |
| P5-D2 | Relation evidence | **Direct cross-file edges + community overlap only. No multi-hop.** Similarity edges are semantic (no citation chain needed for the "never reference each other" case), and shared Leiden community membership *is* a precomputed transitive signal. **Escalation trigger (written, not speculative):** if an acceptance pair returns weak/unrelated despite shared fine-community membership or an obvious common third concept, add a constrained 1-hop-via-shared-anchor view then. Known multi-hop costs: hub contamination from generic anchors, unprincipled path scoring, speculative prose. |
| P5-D3 | `nearest_miss` — narrow exception to P4-D6 | The edges table is τ-pruned (0.70); an unrelated pair may have **zero** cross-file edges, and "no edges" is not the *specific reason* acceptance demands. `relate()` may read raw node **vectors** to compute exact pairwise cosine between the two files' node sets (tens × tens matmul, trivial) and report the best sub-threshold pair. Boundary stays principled: P4-D6's intent is that consumers never re-derive *aliasing* (`alias_of`) or rebuild graph structure; sub-τ evidence cannot exist in the edges table by construction. Only computed when the pair is weak/unrelated. **Implementation note:** compute cosine directly on stored unit-normalized vectors (matmul), never via LanceDB ANN search — search returns **L2 distance**, a documented foot-gun (`ref:ltg-phase2-findings`; conversion `L2 = sqrt(2*(1-cos))` exists but direct cosine sidesteps it). |
| P5-D4 | Verdict banding | `verdict ∈ {strong, moderate, weak, unrelated}` **derived from recorded thresholds, not vibes** — anchored to the frozen τ=0.70 edge floor and the 0.85 alias-merge cosine (Phase 2.5-calibrated). Provisional bands (tune at acceptance, record final values in the results doc): strong = any same_as edge OR max cosine ≥ 0.85; moderate = max cosine ≥ 0.70 (i.e., edges exist); weak = nearest-miss cosine ≥ ~0.55; unrelated below. Threshold retunes (T-34/T-63) move verdicts automatically. |
| P5-D5 | Prose synthesis | qwen3:14b (frozen prose arm) via a new `relate_summary` role in `config.yaml` — structured relation data in, 3–5 sentence summary out. `think: false` top-level. **The only model call in relate().** Prose must cite only facts present in the structured output (prompt constraint); the structured output is the source of truth, prose is presentation. |
| P5-D6 | Provenance | `source_group` counts of contributing nodes are **reported, never weighted** — T-65 query-type weighting belongs to the Phase 5/6 retrieval surface, not pairwise relate (T-74). |
| P5-D7 | Staleness guard | Null `community_coarse`/`community_fine` on any contributing node means "not regenerated since last anchors rebuild" (P4-D5 semantics) → `relate()` **aborts** with the remedy (`run-graph.sh` + `run-communities.sh`, or `run-rebuild-all.sh`), never silently reports missing overlap. |

## Output schema (structured result; prose rendered from it)

```
relate(file_a, file_b) -> {
  inputs:            {file_a, file_b, nodes_a: N, nodes_b: M}
  verdict:           "strong" | "moderate" | "weak" | "unrelated"
  thresholds:        {tau_floor, merge_cosine, bands}          # recorded, so verdicts are auditable
  shared_anchors:    [ {anchor_key, linked_from_a, linked_from_b} ]
  community_overlap: {coarse: {shared: [ids], jaccard}, fine: {shared: [ids], jaccard}}
  top_edges:         [ {node_a, node_b, edge_kind, weight} ]   # cross-file edges, top-N by weight (N≈10)
  edge_stats:        {similarity: n, same_as: n, references: n, max_weight, mean_weight}
  provenance:        {a: {source_group: count}, b: {source_group: count}}
  nearest_miss:      {node_a, node_b, cosine} | null           # P5-D3; only for weak/unrelated verdicts
  summary:           "3–5 sentence prose"                      # P5-D5
}
```

Load-bearing detail: the **negative case is a first-class output shape** — for low-overlap pairs
the tool reports what it looked for and didn't find (`edge_stats` all zero, disjoint communities,
`nearest_miss` with the sub-τ best pair) so "low similarity" always carries a specific reason.

## Deliverables

| Artifact | Purpose |
|----------|---------|
| `retrieval/relate.py` | File→node-set selection, cross-file edge aggregation, community overlap, verdict banding, nearest-miss matmul, prose synthesis, JSON + human-readable output. |
| `retrieval/run-relate.sh` | Bash wrapper (`uv run --project`, repo convention). |
| `config.yaml` `relate_summary` role | qwen3:14b prose arm, `think: false`. |
| `retrieval/prompts/relate_summary.txt` | Synthesis prompt as a standalone file (same pattern as `prompts/extract.txt`) — prompt iterations are diffable/trackable without touching code. Template slots for the structured relation data. |
| `retrieval/probes/phase5-relate-acceptance.md` | Acceptance results on the four pairs (replaces the master plan's `relate-test-results.md` name — matches the `probes/` convention). |

## Task breakdown (TDD; local-model-first per `ref:local-model-conventions`)

1. **T1 — loaders + selectors (TDD):** read nodes+edges tables (reuse `ltg_inspect`/`store` patterns); `nodes_for_file(path)`; P5-D7 null-community guard; unknown-path error. Optional ride-along: T-72(2) — read the topics table once and pass it through instead of double reads, if touching those paths anyway.
2. **T2 — aggregation (TDD, synthetic):** cross-file edge collection from the edges table, `edge_stats`, `community_overlap` (shared ids + Jaccard at both resolutions), `shared_anchors` (anchor nodes with edges into both files' node sets), `provenance` counts. Synthetic fixtures — no Ollama, no live index.
3. **T3 — `nearest_miss` + verdict banding (TDD, synthetic):** unit-vector fixtures at known angles; assert band edges at the recorded thresholds; `nearest_miss` computed only for weak/unrelated.
4. **T4 — prose synthesis:** `relate_summary` role in config.yaml; prompt lives in `retrieval/prompts/relate_summary.txt` (loaded at call time, `prompts/extract.txt` pattern) with template slots the code fills from the structured dict; delegate prompt-body drafting to the local model per repo convention; contract test with mocked `ModelClient` + a test that the prompt file loads and all template slots resolve.
5. **T5 — CLI + wrapper:** `relate.py --a <path> --b <path> [--index] [--json]`; `run-relate.sh`; `__main__` guard at EOF (Phase 4 gotcha #5).
6. **T6 — live acceptance:** run the four pairs against the live index; manual review (specific + verifiable?); write `probes/phase5-relate-acceptance.md`; tune/record final verdict bands; update `.claude/index.md`, memories (QUICK current-state + KNOWLEDGE ledger), master-plan checkoff.

## Acceptance (from `ref:ltg-plan-phase-5`, pairs re-verified against the frozen manifest session 104)

| Pair | Expectation |
|------|-------------|
| `docs/research/smart-rag-llm-wiki.md` ↔ `docs/research/smart-rag-obsidian-mind.md` | ≥1 shared topic (pre-compile, graph-first…) AND ≥1 divergence (typed KG vs routing hook) surfaced. |
| `docs/research/smart-rag-llm-wiki.md` ↔ `docs/research/smart-rag-dify.md` | Low overall similarity **with a specific reason** (negative-case shape: zero/weak edges + disjoint communities + nearest_miss). |
| `docs/research/smart-rag-repowise.md` ↔ `docs/research/smart-rag-claude-mem.md` | Coherent shared-concept report. |
| `docs/research/smart-rag-mempalace.md` ↔ `docs/research/QUICK-MEMORY.md` | **Substituted pair** (original `memory-architecture-design.md` lives in the web-research repo, outside this corpus): surfaces the per-folder memory-scoping connection between docs that never cite each other — and crosses source groups, exercising `provenance` for real. |

General: outputs specific and verifiable → system works; vague or wrong → revisit Phase 1 prompt
engineering (per master plan). Runtime target: seconds (one model call).

**Optional corpus extension (only if the substituted pair underperforms):** copy
`web-research/docs/research/memory-architecture-design.md` into this repo's corpus —
requires `corpus.yaml` change + `run-build-corpus-manifest.sh` + extract/embed/rebuild
for the new file. Not planned by default; corpus stays repo-scoped.

## Risks

- **Prose hallucination:** the model may embellish beyond the structured data. Mitigation: prompt constraint + acceptance review checks every prose claim against the structured output; structured output is authoritative.
- **Verdict-band tuning:** provisional bands may misclassify the moderate/weak boundary on real pairs — T6 explicitly tunes and records them; bands live next to the thresholds they derive from.
- **Fine resolution barely splits (207 coarse → 214 fine, session 102):** `community_overlap.fine` may carry almost no information beyond coarse. Known lever (Phase 4 handoff): raise `graph.resolutions.fine` in `config.yaml` and regenerate (~11 s, zero model calls) if relate() needs sharper intra-domain splits — decide at T6 acceptance, re-probe per the config.yaml rule before freezing a new value.
- **Shared-anchor definition:** "anchor with edges into both node sets" may over-trigger via generic anchors (`ref:bash-wrappers` touches everything). If noisy at acceptance, filter shared_anchors by edge weight or exclude top-degree anchors (degree data available from the graph run report).
- **Phase 6 boundary:** relate() stays a repo-local CLI; the MCP tool + T-33 repo-separation gate are Phase 6. Nothing in relate.py may import from outside `retrieval/`.
<!-- /ref:ltg-phase5-plan -->
