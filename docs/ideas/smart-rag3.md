`★ Insight ─────────────────────────────────────`
- Eight sources, five distinct philosophies. The split that matters most: **"retrieve-and-assemble" vs "pre-compile-and-query"** (both Karpathy gists fall cleanly on the second side). That's a deeper architectural fork than hybrid-vs-graph, and it directly maps to your "prepared artifact before HF push" constraint.
- The web-research MCP worked end-to-end on the arxiv fetch — 46s, qwen3:14b extraction, cached in the knowledge store. Worth noting the arxiv ID 2604.00901 resolved to a real (or recently-indexed) paper called *"Experience as a Compass: Multi-agent RAG with Evolving Orchestration and Agent Prompts"*. It's adjacent to your topic but not the retrieval-layer paper I was expecting from the ID.
`─────────────────────────────────────────────────`

Here's the map, organized by the architectural stance each source takes. I'll keep it tight and save the synthesis for the bottom.

## The five philosophies these sources represent

**1. Pre-compiled wiki (both Karpathy-style gists)**
The core move: instead of chunking + retrieving at query time, an LLM *pre-compiles* sources into a persistent interlinked markdown wiki. Queries hit the wiki, not the raw corpus. The v2 gist (rohitg00) adds a **typed knowledge graph layer on top** — entities extracted as nodes, typed relations ("uses" / "contradicts" / "supersedes"), and **hybrid search = BM25 + vectors + graph traversal**. Also includes confidence scoring, supersession links, and a 4-tier consolidation ladder (raw → episodes → semantic → procedures). This is the single closest match to what you already have (`ref:KEY` blocks + `.memories/` + session logs) but formalized.

**2. Graph-as-first-class (obsidian-mind)**
Explicitly *not* vector retrieval. Treats wikilinks as the primary retrieval signal; a note without links is "a bug." Uses lightweight classification hooks (~100 tokens) to route which part of the vault to look at. Storage = git-tracked Obsidian vault. Relevant because it validates the approach of **exploiting the graph you already have** instead of building a new one.

**3. Code-graph + git-signal (repowise)**
Four layers: tree-sitter dependency graph (symbols + files), git hotspot/co-change analysis, generated wiki with RAG, decision records linked to graph nodes. Uses Leiden community detection + PageRank. Stores in NetworkX + LanceDB. Claims 27× token reduction. Relevant *specifically* to your Claude Code consumer — it's the clearest example of what "making Claude Code smarter about where to look" looks like in practice. The git-signal angle (co-changed files as an edge type) is something I didn't mention in my first answer and is genuinely useful for code.

**4. Hybrid observation store (claude-mem)**
SQLite + FTS5 + Chroma vectors, 3-layer workflow (search returns IDs → timeline → get_observations for detail), lifecycle hooks capture tool usage automatically. Token savings come from **filtering before fetching**, not from smarter retrieval. Relevant as an existence proof that the hook-capture pattern works inside Claude Code today.

**5. Verbatim spatial memory (MemPalace)**
Stores raw text (no chunking, no summarization), organizes into wings/rooms/halls/tunnels. Search-within-room achieves 94.8% recall vs 60.9% flat. Cost argument: $10/yr local vs $507/yr summarization. Relevant for the *philosophical* point: **hierarchical scoping before retrieval** is a bigger win than smarter retrieval inside a flat space. Your `.memories/` per-folder convention is already doing this on a simpler axis.

**6. Platform (dify)**
Sets the low bar. RAG capabilities exist but no content-linking or graph features. Useful only as a baseline — "this is what off-the-shelf RAG looks like, and it's not enough for what you want."

**7. Adaptive orchestration (HERA arxiv)**
Not a retrieval layer — it's a multi-agent RAG orchestration framework with reward-guided adaptation. Tangential to your core question. Worth noting the paper exists if you later want to make the Auditor agent in web-research self-improving, but it's not on the critical path.

## Patterns that cut across multiple sources

| Pattern | Sources | Relevance to your setup |
|---|---|---|
| **Hybrid = BM25 + vectors + graph** | Karpathy v2, repowise | Strongest convergence in my first answer too. Confirms the direction. |
| **Pre-compile once, query many** | Both Karpathy gists | **Directly answers your "before HF push" constraint.** |
| **Exploit existing graph structure** | obsidian-mind (wikilinks), Karpathy v2 (schema), repowise (imports) | You already have `ref:KEY` + `.memories/` — same trick. |
| **Hierarchical scoping beats flat search** | MemPalace (rooms), obsidian-mind (purpose folders) | Validates per-folder `.memories/` pattern. |
| **Filter-before-fetch via IDs/summaries** | claude-mem (3-layer), repowise | Keeps Opus-tier context clean. Critical for your Claude Code consumer. |
| **Supersession / contradiction tracking** | Karpathy v2, MemPalace | New to my mental model. Directly relevant to session logs & decision records that go stale. |
| **Behavioral signals as edges** | repowise (git co-change) | New angle: "files that change together" is an edge type the `ref:KEY` system doesn't have. |

## How this refines the earlier architecture

My first answer had: indexer → retriever → consumer adapters, with contextual chunking + hybrid + reranker + graph-expand modes. The sources strongly *confirm* that shape, but they suggest three concrete amendments:

**Amendment 1: Make the wiki/pre-compile step first-class, not optional.**
Both Karpathy gists + repowise's generated wiki all argue the same thing: the LLM-authored intermediate artifact (whether you call it a "wiki," a "knowledge base," or a "structural map") is more valuable than the retrieval layer on top of raw files. This *perfectly* fits your "build before HF push" constraint — the wiki is the prepared artifact the chatbot consumes.

So the pipeline becomes:
```
raw sources → LLM-authored wiki (pre-compile step)
            → index the wiki (hybrid + graph)
            → retrieve from the index (consumer adapters)
```

The wiki layer is the part that makes the chatbot *smart* without infrastructure-per-repo. The wiki gets built in the llm repo, committed (or deployed), and the chatbot points at it.

**Amendment 2: Typed supersession links are worth adding.**
Your session logs accumulate decisions. Some supersede earlier ones (e.g., "verdict policy: 3-dimension heuristic *replaces* 3-lines"). Right now there's no machine-readable edge for that — a reader has to notice. Adding a `supersedes:` / `superseded-by:` edge type to the graph costs very little and directly fixes the "stale memory is worse than no memory" problem in `memory-layer-design.md`.

**Amendment 3: Git co-change as an edge type, scoped to code.**
repowise's strongest idea is that *files changing together without importing each other* is a signal no static analysis captures. For your llm repo specifically (where decisions ripple across Modelfiles + registry.yaml + benchmarks + session logs), this would expose edges the ref graph misses. Not worth it for profile/chatbot (not code); very worth it for llm + expense + web-research.

## What I'd drop from consideration

- **Dify**: too high-level, doesn't solve what you're asking about
- **HERA**: orthogonal (orchestration, not retrieval)
- **MemPalace's verbatim-everything**: elegant but doesn't fit your existing consolidated `.memories/` pattern; also doesn't solve cross-document linking, just within-room navigation
- **claude-mem's hook-capture**: useful pattern but it's observation-capture, not document retrieval — you already have session logs doing the same job

## The remaining decision point

From my first answer I posed: *one-per-repo or one-global?* The sources don't really answer this, but the **pre-compiled-wiki framing changes the shape of the question**. You probably want:

- **One wiki per "domain"** (profile+career, llm, web-research, expense) — because the pre-compile rules differ per domain
- **One federating retriever** that queries across wikis with scope rules
- **The wiki is the deploy artifact**: `llm/wiki/` gets built in the llm repo, committed, and the chatbot clones or copies it pre-push alongside the profile wiki. No live service for the chatbot; live service for Claude Code (which runs where the wikis live).

That gives you both: simple static-asset deployment for the chatbot, and a live MCP endpoint for Claude Code — with the same wiki artifacts underneath.

---

Now: what did *you* have in mind from these links? Is there one of the five philosophies you were most drawn to, or a technique name I haven't mentioned yet? I want to make sure I'm responding to what pulled you toward each link, not just what I extracted from the READMEs.