<!-- ref:smart-rag-research -->
# Smart RAG / Content-Linking Research — Index

**Created:** 2026-04-13 (session 51)
**Context:** Investigation into content-linking retrieval techniques beyond keyword/vector RAG, triggered by the question of how to let the career chatbot, Claude Code, web-research, and the llm repo itself "note relations between any part of the content" without blowing up context.
**Prior conversation:** `docs/ideas/smart-rag.md`, `docs/ideas/smart-rag2.md`

## The five philosophies identified

| # | File | Philosophy | Relevance |
|---|------|-----------|-----------|
| 1 | `smart-rag-llm-wiki.md` | Pre-compile sources into a persistent interlinked wiki; query the wiki, not raw sources. v2 adds typed KG + hybrid (BM25+vector+graph). | **Highest** — directly fits "prepared artifact before HF push" constraint. |
| 2 | `smart-rag-obsidian-mind.md` | Graph-first via wikilinks; classification hooks route lookups; "a note without links is a bug." | **High** — validates exploiting the `ref:KEY` + `.memories/` graph we already have. |
| 3 | `smart-rag-repowise.md` | Code-graph (tree-sitter) + git co-change signals + LLM-generated wiki + decision records. Claims 27× token reduction. | **High** — clearest match for "make Claude Code smarter about where to look." |
| 4 | `smart-rag-claude-mem.md` | SQLite + FTS5 + Chroma, lifecycle hooks capture tool use, 3-layer retrieval (search → timeline → details). | **Medium** — observation capture, already solved by session logs. |
| 5 | `smart-rag-mempalace.md` | Hierarchical spatial memory (wings/rooms/halls); scoped retrieval beats flat search; verbatim storage. | **Medium** — validates per-folder `.memories/` scoping. |
| 6 | `smart-rag-hera.md` | Adaptive multi-agent RAG orchestration (arxiv paper). Tangential — not a retrieval layer. | **Low** — future Auditor self-improvement signal. |
| 7 | `smart-rag-dify.md` | Off-the-shelf LLM app platform with generic RAG. | **Baseline only** — what *not* to build. |

## Cross-cutting patterns (appearing in 3+ sources)

1. **Hybrid = BM25 + vectors + graph** (llm-wiki v2, repowise, claude-mem) — confirms the direction from prior conversation.
2. **Pre-compile once, query many** (llm-wiki v1+v2, repowise wiki) — the "prepared artifact" pattern.
3. **Exploit existing graph structure** (obsidian-mind wikilinks, llm-wiki schema, repowise imports, our `ref:KEY`) — don't run generic extraction if you already have hand-curated edges.
4. **Hierarchical scoping beats flat search** (MemPalace rooms, obsidian-mind purpose folders, our `.memories/` per-folder) — architectural, not algorithmic.
5. **Filter-before-fetch via IDs/summaries** (claude-mem 3-layer, repowise) — essential for keeping Opus context clean.
6. **Supersession / contradiction tracking** (llm-wiki v2, MemPalace) — new to our model; directly addresses stale memory problem from `memory-layer-design.md`.
7. **Behavioral edges (git co-change)** (repowise) — new edge type the `ref:KEY` graph doesn't capture.

## Refined architecture (from prior conversation + these findings)

```
raw sources → LLM-authored wiki (pre-compile step, once per domain)
            → indexed wiki (hybrid: BM25 + vectors + graph from refs/links/co-change)
            → retriever service (MCP tool + HTTP endpoint)
            → consumers: Claude Code, career chatbot, web-research Dispatcher
```

Three amendments to the earlier architecture:
1. **Wiki layer is first-class**, not optional — makes the chatbot "prepared artifact" trivial.
2. **Typed supersession edges** (`supersedes:` / `superseded-by:`) — addresses stale-decision drift.
3. **Git co-change edges** scoped to code repos — for llm, expenses, web-research but not profile/chatbot data.

## Architectural decision (open)

One wiki per **domain** (profile, llm, web-research, expense), one federating retriever. Chatbot = static artifact; Claude Code = live MCP service; same wiki artifacts underneath. See `docs/ideas/smart-rag2.md` for the full argument.

## Related infrastructure we already own

| Existing | Relation to smart-rag work |
|---|---|
| `ref:KEY` indexing convention (`.claude/index.md`) | Already a hand-curated knowledge graph. Becomes the edge source for indexing. |
| `.memories/QUICK.md` + `KNOWLEDGE.md` convention | Already hierarchical scoped memory. Tier 0 of retrieval layer. |
| `ref_lookup` MCP tool | Exact-key retrieval; smart-rag adds fuzzy/semantic access path alongside. |
| `ollama-scaffolding` overlay | Deploys the retrieval conventions + MCP tool wiring to new repos. |
| ollama-bridge (local models) | Powers contextual chunking, wiki pre-compile, HyDE queries — all free. |
| web-research repo (`research_url`, `query_knowledge`) | Already a retrieval layer for scraped content. Smart-rag is the substrate it would plug into. |
| `docs/research/memory-architecture-design.md` | Defines memory types; smart-rag is the semantic + structural layer. |
| `docs/research/memory-layer-design.md` | Defines 4 tiers; smart-rag adds a new access path across Tiers 0-2. |
| `docs/ideas/claude-code-python-port.md` → `autoDream/consolidationPrompt.ts` | The consolidation prompt pattern; directly reusable for wiki pre-compile step. |
| `evaluator/` framework | Reusable for scoring wiki quality (contradiction detection, staleness). |

<!-- /ref:smart-rag-research -->
