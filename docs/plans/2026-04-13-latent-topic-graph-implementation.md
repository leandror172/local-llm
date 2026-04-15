<!-- ref:plan-latent-topic-graph -->
# Implementation Plan: Latent Topic Graph (LTG) Substrate

*Created 2026-04-13 (session 51). To be executed in a future session. Scope: llm repo as the first implementation site, with the substrate designed to be consumable from career chatbot, Claude Code (any repo), and web-research Dispatcher.*

**Status:** Ready for execution. Phase 0 decisions should be resolved at the start of the executing session. As of session 52 (2026-04-14), Phase 0 decisions are frozen in `retrieval/DECISIONS.md` — see `ref:ltg-scope`, `ref:ltg-embedding`, `ref:ltg-vector-store`, `ref:ltg-graph-lib`, `ref:ltg-extractor`, `ref:ltg-placement`, `ref:ltg-storage-layout`, `ref:ltg-corpus`.

## Goal

Build a working LTG substrate in the llm repo with enough surface area to validate the concept and to be consumable by at least two downstream consumers. Minimum definition of done: the `relate(file_a, file_b)` acceptance test returns a meaningful, specific, verifiable answer for files in the smart-rag research cluster.
<!-- /ref:plan-latent-topic-graph -->

---

<!-- ref:ltg-plan-required-reading -->
## Required Reading Before Starting

1. **Concept:** `ref:concept-latent-topic-graph` (`docs/research/latent-topic-graph.md`) — the idea this plan implements.
2. **Research cluster hub:** `ref:smart-rag-research` (`docs/research/smart-rag-index.md`) — the 7-source survey that motivated the design.
3. **Architectural discussion:** `docs/ideas/smart-rag3.md` — the conversation that refined "files as containers, topics as nodes."
4. **Prior conversations:** `docs/ideas/smart-rag.md`, `docs/ideas/smart-rag2.md` — initial survey + four-consumer framing.
5. **Memory layer context:** `~/workspaces/web-research/docs/research/memory-architecture-design.md`, `memory-layer-design.md` — how LTG fits the existing tier model.
6. **Phase 0 decisions (session 52):** `retrieval/DECISIONS.md` — frozen Phase 0 decisions with rationale and revisit triggers.

A fresh session should read these in order before touching code.
<!-- /ref:ltg-plan-required-reading -->

<!-- ref:ltg-plan-phase-0 -->
## Phase 0 — Decisions to Confirm Before Coding

None of the following should be assumed without an explicit choice at session start. Defaults in parentheses are the current lean, not commitments.

- **Index scope model.** One-per-repo with a federation layer, or one global index with scoped queries? *(Default: per-repo + federation — preserves permission boundaries and matches existing `.memories/` + `ref:KEY` conventions.)*
- **Embedding model.** `nomic-embed-text`, `bge-small-en-v1.5`, `bge-m3` (multilingual + multi-vector + sparse), or something else? *(Default: bge-m3 for quality + multilingual headroom + future multi-vector option; fallback `nomic-embed-text` if VRAM budget tight.)*
- **Vector store.** LanceDB (embedded, no server), Qdrant (server, richer queries), or sqlite-vss? *(Default: LanceDB — aligns with "simple embedded storage" direction in smart-rag2.md.)*
- **Graph library.** networkx + leidenalg, igraph, or graph-tool? *(Default: networkx + leidenalg — most Pythonic and widely documented, matches repowise's choice.)*
- **Topic extractor model.** qwen3:14b (quality, slower), gemma3:12b (3–4× faster, IMPROVED verdict), qwen2.5-coder:14b (if structural extraction helps)? *(Default: gemma3:12b for iteration phase, rerun with qwen3:14b for final index to compare.)*
- **Placement in repo.** New top-level `retrieval/` directory, or extend `mcp-server/` with a retrieval sub-package? *(Default: new `retrieval/` top-level — clean module boundary, easy to extract later; `mcp-server/` gets a thin adapter.)*
- **Storage of extracted graph.** JSON + LanceDB side-by-side, SQLite as metadata store, or pure LanceDB? *(Default: SQLite for nodes/edges metadata + LanceDB for embeddings — plays to each tool's strength.)*
- **Scope of corpus for MVP.** Whole llm repo, or only a curated subset (e.g., `docs/research/` + `.claude/` + `.memories/`)? *(Default: curated subset for Phase 1; widen in later phases.)*

The executing session should confirm or revise each of these before Phase 1. Decisions are then frozen and recorded in a `DECISIONS.md` at the top of the `retrieval/` directory.

**Resolution (session 52, 2026-04-14):** All 8 decisions resolved and frozen in `retrieval/DECISIONS.md`. Notable revisions from defaults: embedding model confirmed `bge-m3` via Ollama (Ollama-native, eliminating runtime-split objection); storage simplified to pure LanceDB (SQLite layer rejected for MVP); extractor model deferred to empirical A/B in Phase 1 with an 11-dimension rubric; corpus adds `docs/ideas/` and documents two finding-dependent branch points for code and long files.
<!-- /ref:ltg-plan-phase-0 -->

<!-- ref:ltg-plan-phase-1 -->
## Phase 1 — Topic Extractor Spike (1 session)

**Goal:** Validate that a local model can extract meaningful, non-contiguous topics from real files.

**Steps:**
1. Write a topic-extraction prompt that asks for 3–10 topics per file, each with a name, a short description, and a list of span ranges. Use the `format` parameter for structured JSON output.
2. Run the extractor against 5 representative files from `docs/research/smart-rag-*.md` plus 2–3 files from `.claude/` and `.memories/`.
3. Manually verify the output: do topic boundaries make sense? Do non-contiguous spans correctly merge related content? Are topics at the right granularity?
4. Record model, tokens in, tokens out, latency per file. Estimate total cost for indexing the full corpus.
5. Commit the prompt, a runner script, and a small results log.

**Acceptance:**
- Extractor produces 3–10 topics per file with non-empty descriptions.
- At least one topic per test file has non-contiguous spans.
- Manual inspection agrees with at least ~70% of topic assignments.
- Total indexing cost for the full llm repo is estimable.

**Deliverables:** `retrieval/extract_topics.py`, `retrieval/prompts/extract.txt`, `retrieval/spike-results.md`.

**Session 52 expansion:** Phase 1 is load-bearing; see `ref:ltg-extractor` for the expanded protocol — 5–6 models × 8 files (7 prose + 1 code) + long-file appendix, 11-dimension rubric, two-stage variant for top 2 models, exit threshold at weighted quality ≥ 2.2, and two finding-dependent branch points that feed into Phase 2.
<!-- /ref:ltg-plan-phase-1 -->

<!-- ref:ltg-plan-phase-2 -->
## Phase 2 — Embedding + Storage (1 session, overlaps with Phase 1)

**Goal:** Store extracted topics as embedded nodes in a local vector store.

**Steps:**
1. Install the chosen embedding model. Verify it runs on the local GPU alongside Ollama.
2. For each topic from Phase 1, embed the topic description and optionally the concatenated span text. Compare: is description-only sufficient, or is span text needed?
3. Set up LanceDB (or chosen store). Define the schema: `{id, file_path, topic_name, description, spans, embedding, extractor_model, extraction_timestamp}`.
4. Write nodes for all Phase 1 files.
5. Test top-K nearest neighbor queries against a handful of probe queries.

**Acceptance:**
- Writing and reading nodes works reliably.
- Top-K queries return sensible neighbors on probe questions ("what do we know about thinking mode", "how do we handle memory across sessions").
- Query latency is acceptable (sub-second for small corpus).

**Deliverables:** `retrieval/embed.py`, `retrieval/store.py`, `retrieval/schema.sql` (if SQLite metadata), populated `retrieval/index/`.

**Session 52 notes:** Embedding model is `bge-m3` via Ollama (1024-dim dense) per `ref:ltg-embedding`. Storage is pure LanceDB per `ref:ltg-storage-layout` — no `schema.sql`; the LanceDB schema includes optional `segment_id` / `segment_start` / `segment_end` fields if Phase 1 long-file findings require chunking. A VRAM co-residence probe (qwen3:14b + bge-m3) is required before locking the embedding choice.
<!-- /ref:ltg-plan-phase-2 -->

<!-- ref:ltg-plan-phase-3 -->
## Phase 3 — Anchor Integration (0.5–1 session)

**Goal:** Ingest the existing `ref:KEY` graph as anchor nodes and merge with extracted topics where appropriate.

**Steps:**
1. Walk `.claude/index.md` and all `<!-- ref:KEY -->` blocks across the repo. Extract key, content, source location.
2. Embed each anchor block.
3. For each extracted topic from Phase 2, compute similarity to all anchors. Above a threshold (suggest 0.85), mark the topic as aliased to the anchor (merged node with anchor-level confidence). Below, keep separate.
4. Record provenance on every node: `extracted` / `anchor` / `merged`.
5. Write an integrity check: every ref key in the repo appears as at least one anchor node.

**Acceptance:**
- All ref keys are represented as anchor nodes.
- At least some extracted topics merge cleanly with anchors (e.g., the topic "thinking mode handling" in session 35 notes should merge with `ref:thinking-mode`).
- Merged nodes preserve both the anchor confidence and the extracted context.

**Deliverables:** `retrieval/anchors.py`, merged node index.
<!-- /ref:ltg-plan-phase-3 -->

<!-- ref:ltg-plan-phase-4 -->
## Phase 4 — Graph Assembly + Community Detection (1 session)

**Goal:** Build the weighted graph and compute multi-resolution communities.

**Steps:**
1. For every pair of topic nodes (or approximate via ANN top-K to avoid O(N²)), compute edge weight from embedding similarity. Keep edges above a threshold; discard noise.
2. Load the edge set into networkx. Add anchor edges with confidence 1.0; add extracted edges with confidence = similarity.
3. Run Leiden community detection at 2 resolutions (coarse + fine). Store cluster assignments as node metadata.
4. Sanity check: do communities roughly match folder structure where expected? Do cross-folder communities reveal unexpected-but-true connections?
5. Export a static visualization (GraphML or JSON for a web viewer) for manual inspection.

**Acceptance:**
- Communities at coarse resolution roughly track semantic domains (e.g., all smart-rag files cluster together).
- Communities at fine resolution reveal distinctions within domains (e.g., LLM-wiki and Obsidian-Mind closer than either to Dify).
- A manual walk-through of the top 20 edges by weight returns mostly defensible matches.

**Deliverables:** `retrieval/graph.py`, `retrieval/communities.py`, `retrieval/viz/` (optional static export).
<!-- /ref:ltg-plan-phase-4 -->

<!-- ref:ltg-plan-phase-5 -->
## Phase 5 — `relate(a, b)` Tool (0.5 session)

**Goal:** Build the pairwise relation query that serves as the primary acceptance test.

**Steps:**
1. Implement `relate(file_a, file_b) -> dict` with the schema from the concept paper's "Testing and Demonstration" section.
2. For the overall explanation, call a local model with the structured topic-overlap data and ask it to synthesize a natural-language summary in 3–5 sentences.
3. Test on pairs drawn from the smart-rag cluster: `(llm-wiki, obsidian-mind)`, `(llm-wiki, dify)`, `(repowise, claude-mem)`, `(mempalace, memory-architecture-design)`.
4. Review outputs manually. If they are specific and verifiable, the system is working. If they are vague or wrong, revisit Phase 1 prompt engineering.

**Acceptance:**
- `relate(llm-wiki, obsidian-mind)` identifies at least one shared topic (pre-compile, graph-first, etc.) and one divergence (typed KG vs routing hook).
- `relate(llm-wiki, dify)` correctly reports low overall similarity with a specific reason.
- `relate(mempalace, memory-architecture-design)` surfaces the per-folder scoping connection even though the two documents never reference each other.

**Deliverables:** `retrieval/relate.py`, `retrieval/relate-test-results.md`.
<!-- /ref:ltg-plan-phase-5 -->

<!-- ref:ltg-plan-phase-6 -->
## Phase 6 — MCP `retrieve_context` Tool (0.5 session)

**Goal:** Expose the substrate as an MCP tool callable from any Claude Code session.

**Steps:**
1. Add `retrieve_context(query: str, scope: str = "repo", mode: str = "hybrid", limit: int = 10)` to ollama-bridge (or a new `retrieval-mcp` sub-server, depending on Phase 0 placement decision).
2. Implementation: embed the query, top-K lookup in the graph, expand along high-confidence edges, rerank by similarity-plus-confidence, return a list of `{topic_name, file_path, spans, confidence, excerpt}`.
3. Add `relate_files(file_a: str, file_b: str)` as a second tool backed by Phase 5.
4. Register the tool in `.mcp.json`. Test from a Claude Code session.

**Acceptance:**
- A Claude Code session can ask "what do we know about thinking mode" without knowing any ref key and receive the correct answer.
- `relate_files` works end-to-end from Claude Code.

**Deliverables:** MCP tool definitions, updated `.mcp.json`, smoke-test transcript.
<!-- /ref:ltg-plan-phase-6 -->

<!-- ref:ltg-plan-phase-7 -->
## Phase 7 — Reranker (optional, 0.5 session)

**Goal:** Add a cross-encoder reranker to lift retrieval quality.

**Steps:**
1. Install `bge-reranker-v2-m3` or equivalent. Verify local inference works.
2. Wire into the retrieval pipeline: top-50 from ANN → rerank → top-10 returned.
3. Measure before/after on a fixed probe set.

**Acceptance:** Measurable quality lift on the probe set, even if modest. If no lift, skip this phase and document why.

**Deliverables:** `retrieval/rerank.py`, measurement notes.
<!-- /ref:ltg-plan-phase-7 -->

<!-- ref:ltg-plan-phase-8 -->
## Phase 8 — Per-Repo Configuration (0.5 session)

**Goal:** Generalize the substrate to multiple repos with scope and permission rules.

**Steps:**
1. Define a config schema: `{corpus_paths, exclude_patterns, scope_tags, permission_class}`.
2. Write configs for llm, web-research, career-chat (public subset), expense.
3. Test the `chatbot-safe` scope: verify that `.claude/local/` and other sensitive paths are never indexed under that scope.

**Acceptance:**
- Each repo has a working config.
- Permission tests pass (sensitive content never leaks under `chatbot-safe`).

**Deliverables:** `retrieval/configs/*.yaml`.
<!-- /ref:ltg-plan-phase-8 -->

<!-- ref:ltg-plan-phase-9 -->
## Phase 9 — Federation Layer (1 session, future)

**Goal:** Cross-repo queries via a thin federator.

**Steps:**
1. Each repo runs its own retrieval endpoint (MCP tool bound to the repo's index).
2. Federator queries all endpoints in parallel, merges with RRF, returns unified results.
3. Test a query that must pull from both llm and web-research (e.g., "how do agent personas relate to multi-agent research").

**Acceptance:** Federated query returns results spanning multiple repos with correct attribution.

**Deliverables:** `retrieval/federate.py`, cross-repo smoke test.
<!-- /ref:ltg-plan-phase-9 -->

<!-- ref:ltg-plan-deferred -->
## Deferred / Out of Scope (Explicitly)

- **SPLADE / learned sparse retrievers.** Diminishing returns at our scale.
- **Multi-vector ColBERT late interaction within topic nodes.** Interesting but adds complexity without solving the cross-document relation problem.
- **Online incremental graph updates.** Initial versions rebuild on demand. Incremental update is a v2 concern once stability is understood.
- **Cross-lingual retrieval.** Out of scope until an actual bilingual use case arrives.
- **Fine-tuned embedding models.** Off-the-shelf first; fine-tune only if retrieval quality proves insufficient.
<!-- /ref:ltg-plan-deferred -->

<!-- ref:ltg-plan-relationship -->
## Relationship to plan-v2 (Existing Roadmap)

LTG is not a new parallel track — it is the **elevated form of several tasks already in `.claude/plan-v2.md`**, pulled forward and merged into a single coherent substrate. Reading the plan-v2 layers through an LTG lens:

| plan-v2 layer/task | LTG relationship |
|---|---|
| **Layer 7 — Memory + Learning System** | **Primary home.** Task 7.11 ("Full RAG with embeddings: nomic-embed-text + cosine similarity retrieval") is the closest existing task; LTG replaces it with a richer substrate. Tasks 7.2 and 7.3 (memory write/read pipelines) become consumers of the LTG substrate instead of custom retrievers. |
| **Layer 7 task 7.10** ("Prompt pre-processor: local model compresses/enriches context before Claude calls") | Becomes a direct LTG consumer: retrieval replaces hand-coded compression. |
| **Layer 7 task 7.7/7.8** (SFT/DPO dataset builders) | LTG's topic extraction produces high-signal training data as a byproduct — topic-labeled spans are a candidate DPO input. |
| **Layer 4 — Evaluator Framework** | Reused in Phase 1 and Phase 4 to score extraction quality and retrieval precision. LTG does not replace the evaluator; it adds new things for the evaluator to score. |
| **Layer 3 — Persona Creator** | May spawn a dedicated `my-topic-extractor-*` persona. The persona creator is the tool; LTG is a new domain for it to serve. |
| **Layer 8 — Project Bootstrapper** | An architect persona gains dramatically from LTG: it can ask "what have we already decided about X" and get substrate answers, making recruitment and decomposition much better-informed. |
| **Layer 9 — Idle-Time Runner** | A natural home for background LTG maintenance: re-run topic extraction on changed files, recompute communities, validate edges. |
| **Cross-cutting: closing-the-gap integration** | LTG uses the same structured-output, few-shot, decomposition techniques that are already standards everywhere else. |
| **Layer 5 — Expense Classifier** | Out of LTG scope (keyword/BM25 few-shot injection is already sufficient), confirmed in `docs/ideas/smart-rag2.md`. |

**Promotion rationale.** Task 7.11 was originally scoped as "basic RAG, embeddings, cosine similarity" — a vanilla implementation. The research cluster (`ref:smart-rag-research`) and the concept note (`ref:concept-latent-topic-graph`) argue that a more ambitious form of 7.11 has enough leverage across Layers 3, 4, 7, 8, and 9 — *and* across the chatbot Phase 3 work happening outside plan-v2 — to justify elevating it from a single Layer 7 task to a cross-cutting substrate delivered ahead of Layer 7 closing.

**Implication for the plan-v2 ordering.** Layer 7 is currently deferred behind Layers 5–6. LTG's Phases 1–6 can execute independently of Layer 5/6 progress because LTG does not depend on expense classification or OpenClaw security. It also does not block them. The two tracks can proceed in parallel.

**What stays in plan-v2 as originally specified:** per-persona MEMORY.md files (task 7.1), summarization agent (7.4), bloat prevention (7.5), fine-tuning pipeline (7.6–7.9). These are not subsumed by LTG and remain on their original timeline.

**What plan-v2 should acquire:** a forward reference from Layer 7 task 7.11 to this plan, marking the task as "promoted to cross-cutting substrate per `ref:plan-latent-topic-graph`." This reference is added as part of executing this plan, not before.
<!-- /ref:ltg-plan-relationship -->

<!-- ref:ltg-plan-integration -->
## Integration Points with Existing Infrastructure

| Component | Role |
|---|---|
| `ollama-bridge` | Hosts topic extractor calls (new `extract_topics` internal helper) and the retrieval MCP tools. |
| `mcp-server` | May host `retrieve_context` and `relate_files` as new tools, or delegate to a separate server. |
| `personas/` | Consider a dedicated `my-topic-extractor-g3-12b` persona with the extraction prompt baked in. |
| `overlays/ollama-scaffolding` | Package the retrieval-convention docs for cross-repo deployment. |
| `evaluator/` | Score extraction quality and retrieval precision in Phase 1 and Phase 4 review. |
| `.memories/` convention | Unchanged. LTG is a complementary access path, not a replacement. |
| `ref:KEY` system | Unchanged. Becomes the anchor node source in Phase 3. |
| `~/.local/share/ollama-bridge/calls.jsonl` | Continues to log every extraction call as part of DPO data collection. |
| `docs/ideas/claude-code-python-port.md` → `autoDream/consolidationPrompt.ts` | Reference for writing the extraction prompt. |
<!-- /ref:ltg-plan-integration -->

<!-- ref:ltg-plan-risks -->
## Risks and Mitigations

- **Topic extraction prompt sensitivity.** Outputs may vary across runs. Mitigate with temperature 0.1, structured output via `format`, and multi-run sampling for stability measurement in Phase 1.
- **Clustering instability as corpus grows.** Leiden is more stable than Louvain but not immune. Mitigate with multi-resolution runs and stability metrics.
- **Embedding model mismatch with domain.** bge-m3 is general-purpose; technical content (model names, config flags) may not embed well. Mitigate by testing on actual corpus early (Phase 2) before committing.
- **Opus token cost for prompt iteration.** Extraction prompt tuning can be expensive if driven by Claude. Mitigate by running iterations through gemma3:12b or qwen3:14b and only escalating to Claude for prompt review.
- **Claim: "27× token reduction" (from repowise) may not replicate.** Measure actual savings against a fixed baseline; don't assume.
- **Integration friction with existing MCP setup.** MCP tool response formats are specific. Mitigate by reading `docs/ideas/claude-code-python-port.md` → `normalization.ts` notes before designing the tool schema.
<!-- /ref:ltg-plan-risks -->

<!-- ref:ltg-plan-estimate -->
## Work Estimate

- Phase 0 + Phase 1 (decisions + spike): 1 session
- Phase 2 + Phase 3 (embedding + anchors): 1 session
- Phase 4 + Phase 5 (graph + relate): 1 session
- Phase 6 (MCP): 0.5 session, can slot into Phase 4–5 session if time permits
- Phase 7–9 (polish + federation): 1–2 sessions

**Total to usable MVP:** ~3 focused sessions for Phases 0–6, plus 1–2 for polish.
<!-- /ref:ltg-plan-estimate -->

<!-- ref:ltg-plan-success -->
## Success Definition

The implementation is a success when `relate(smart-rag-llm-wiki.md, smart-rag-obsidian-mind.md)` returns a specific, verifiable, non-trivial answer that a human reader would agree with, **and** a Claude Code session can retrieve information by natural-language query without knowing the target ref key. Both conditions must hold. If either fails, iterate on Phase 1 extraction quality before declaring success.
<!-- /ref:ltg-plan-success -->

<!-- ref:ltg-plan-handoff -->
## Handoff Notes for the Executing Session

- Start by reading the "Required Reading" section at the top of this file, in order.
- Confirm Phase 0 decisions explicitly. Do not skip this. (As of session 52, Phase 0 is resolved — see `retrieval/DECISIONS.md`.)
- Phase 1 is load-bearing for everything else. If Phase 1 quality is poor, do not proceed to Phase 2; iterate on the extraction prompt instead.
- The `relate()` acceptance test in Phase 5 is the primary success signal. Treat benchmark IR metrics (precision/recall) as secondary.
- If stuck on a design decision, re-read `docs/ideas/smart-rag3.md` — the "files as containers" discussion is the architectural north star.
<!-- /ref:ltg-plan-handoff -->
