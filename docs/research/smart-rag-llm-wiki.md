<!-- ref:rag-llm-wiki -->
# LLM Wiki: Pre-Compiled Knowledge Over Live Retrieval

**Sources (deduplicated):**
- https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (v1 — core concept)
- https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2 (v2 — adds typed knowledge graph)

**Philosophy:** Stop re-deriving, start compiling. Build and maintain a persistent interlinked markdown wiki; query the wiki, not the raw corpus.

**Relevance to this work:** **Highest.** This is the single closest match for how the career chatbot should consume repo knowledge pre-push.

## Summary

Traditional RAG retrieves and reassembles fragments on every query — the corpus is re-read repeatedly, contradictions are never resolved, and cross-references are reconstructed on the fly. LLM Wiki inverts this: an LLM *pre-compiles* sources once into a persistent interlinked markdown wiki. Subsequent queries draw from the enriched synthesis, not the raw sources.

**V1 (Karpathy) techniques:**
- **Three-layer architecture:** immutable raw sources → LLM-generated wiki → schema rules
- **Schema document:** configuration file defining wiki structure and LLM ingestion rules
- **Index file:** content-oriented catalog of all pages with summaries (efficient discovery)
- **Log file:** append-only chronological record of ingests and operations (unix-parseable)
- **Health-checking / lint passes:** periodic scans for orphaned pages, contradictions, data gaps
- **Answer filing:** valuable query results stored back into the wiki as new pages

**V2 (rohitg00) adds:**
- **Typed knowledge graph layer** on top of wiki pages — entities (people, projects, libraries) as nodes, typed relations (`uses`, `contradicts`, `supersedes`) as edges
- **Hybrid search:** BM25 (keyword) + vector embeddings (semantic) + graph traversal (relationship-aware)
- **Confidence scoring:** tracks source count, recency, contradictions
- **Supersession links:** explicit versioning of outdated claims rather than conflicting statements
- **4-tier consolidation ladder:** raw observations → episodes → semantic facts → procedures; LLM promotes information as evidence accumulates

## Relation to Our Projects

### web-research
The Knowledge Domain in `docs/research/web-research-tool-vision.md` describes accumulated research findings + post-research conversation. This is exactly the "pre-compile then query" pattern. The Auditor agent already hints at consolidation ("is research sufficient, should we explore more?"). Adopting the v2 schema + supersession links gives web-research a structured way to track what's confirmed vs what's still speculative, and the typed graph layer directly implements "note relations between any part of the content" at the research-output level.

### Local LLMs (llm repo)
The pre-compile step is *free* for us — qwen3:8b or gemma3:12b can run wiki ingestion passes overnight. The schema document pattern is a natural home for things like `ref:model-selection` rules and decision records. The 4-tier consolidation ladder maps cleanly onto our existing session-log → KNOWLEDGE.md → ref-block flow, which is already episodic → semantic → procedural but without machine-readable edges.

### Augmenting Claude Code
This is where the win is biggest. Today Claude Code runs `ref-lookup.sh KEY` (exact-key) and reads files on demand. A pre-compiled wiki lets Claude Code ask "what do we know about thinking mode" and get a synthesized answer that cites session 35, the benchmark file, and the current `ref:thinking-mode` block — without Claude having to read all three separately. Supersession links would prevent Claude from re-suggesting `/no_think` after session 35's fix, which is exactly the "stale memory" problem in `memory-layer-design.md`.

### Career chat (HF Space)
Deploy target. The wiki is **the** prepared artifact: build it in the llm repo pre-push, copy the public-safe subset into the chatbot's `context/` alongside `sync-context.sh`, and the chatbot serves hybrid-search queries against it. No live infrastructure in any consumer repo — the wiki is a static asset, same shape as the current `.memories/` sync pattern but deeper.

## Existing Infrastructure Connections

- **`ref:KEY` blocks in `.claude/index.md`** — already half of v1's schema/index pattern. Formalizing as wiki pages with `ref:` = page IDs is a ~1-day migration.
- **`.memories/QUICK.md` + `KNOWLEDGE.md`** — already implement the 4-tier consolidation ladder manually (working → semantic). Wiki automation can run on top.
- **`ollama-scaffolding` overlay** — perfect place to deploy a "wiki compile" convention across repos.
- **`evaluator/` framework** — can score wiki lint passes (contradiction detection, orphan detection).
- **`docs/ideas/claude-code-python-port.md` → `autoDream/consolidationPrompt.ts`** — Claude Code's own memory consolidation prompt; directly reusable as a starting point for wiki ingest prompts.
- **`sync-context.sh` (HF Space)** — already copies `.memories/` cross-repo; wiki compile output slots into the same flow.

## Takeaway

This is the architectural frame to adopt. The v2 KG extension is where the actual "content-linking" lives; the v1 wiki is the storage substrate. Both are implementable with what we already have (local models for ingest, `ref:` system as seed edges, markdown as storage).
<!-- /ref:rag-llm-wiki -->
