Got the plan. Let me go decision by decision with an actual opinion. I'll flag where I'd push back on defaults vs. agree.

`★ Insight ─────────────────────────────────────`
- Phase 0 is a lock-in point: it freezes runtime substrate choices *before* Phase 1, where the plan says "don't proceed if quality is poor." That means the decisions should minimize *switching cost* later, not just pick the "best" option today.
- Several defaults in the plan lean toward richer tech (bge-m3 multi-vector, SQLite+LanceDB split). The MVP acceptance test is a single-repo `relate()` call — it doesn't exercise that richness yet. There's a real argument for simpler choices and revisiting when Phase 4+ actually needs them.
- Two of these decisions (extractor model, embedding model) are empirically verifiable in hours, not dogmatically. Those shouldn't be frozen — they should be tested inside Phase 1.
`─────────────────────────────────────────────────`

## Decision-by-decision

### 1. Index scope model — **Agree with default** (per-repo + federation later)
The acceptance test is intra-llm-repo. Federation is Phase 9. No reason to over-engineer the interface now — build a single-repo index, no premature "multi-root" abstractions. Matches `.memories/` and permission-class thinking already in the repo.

### 2. Embedding model — **Push back: lean nomic-embed-text via Ollama, not bge-m3**
The default picks bge-m3 for "quality + multilingual + multi-vector headroom." But:
- **Runtime fragmentation:** bge-m3 isn't an Ollama model. You'd run it via `sentence-transformers` or a separate HF runtime — two inference backends sharing GPU with Ollama complicates VRAM accounting and the deployment story.
- **Multi-vector isn't used in Phase 1–4:** dense-only top-K is the whole pipeline. bge-m3's killer feature sits unused.
- **Multilingual need:** no bilingual corpus in scope.
- `nomic-embed-text` is already pullable via Ollama, ~274MB, good English quality, 768-dim. Keeps everything behind one API.

Revisit bge-m3 only if Phase 2 probe queries underperform, or if multilingual/sparse enters scope.

### 3. Vector store — **Agree with default** (LanceDB)
Embedded, no server to manage, file-on-disk indexes are debuggable, aligns with smart-rag2 direction. Only alternative worth considering is sqlite-vss for "literally one file" simplicity, but LanceDB's query API is meaningfully better and the Arrow format is future-proof.

### 4. Graph library — **Agree with default** (networkx + leidenalg)
At MVP scale (hundreds to low thousands of nodes), networkx is plenty; leidenalg pulls igraph as a dependency anyway, so upgrading later is a one-line import change. Leiden is strictly better than Louvain on community-quality guarantees.

### 5. Topic extractor model — **Push back: test both in Phase 1, don't pre-commit**
The plan already hedges ("gemma3:12b for iteration, rerun with qwen3:14b for final"), but I'd go further: Phase 1 is explicitly load-bearing, and *extraction quality dominates everything downstream*. A 30-minute A/B on 3 files between gemma3:12b and qwen3:14b is cheap and informative.
- Pragmatic sub-point: the plan says "gemma3:12b (3–4× faster)" but session 50 benchmark notes have it at ~31 tok/s and qwen3:14b at ~32 tok/s. The speed edge may be overstated for extraction-sized prompts.
- Suggested Phase 1 protocol: run both extractors on the same 3 files, score manually for topic-boundary sanity, pick the winner as the "committed index" model, record the loser as the "iteration" model.

### 6. Placement — **Agree with default** (new `retrieval/` top-level)
Multiple downstream consumers (mcp-server adapter, career chatbot Phase 3, web-research Dispatcher per plan) plus the "extract to standalone package later" option argue for top-level. Sub-package in `mcp-server/` would cause circular-import grief the moment a second consumer shows up.

### 7. Storage split — **Push back: pure LanceDB for Phase 1–5, add SQLite only if needed**
The plan proposes SQLite (nodes/edges metadata) + LanceDB (embeddings). Two sources of truth with write-ordering risk. My read:
- LanceDB already supports scalar columns alongside the vector. `{id, file_path, topic_name, description, spans (list[str]), extractor_model, provenance, community_coarse, community_fine, embedding}` fits fine in a single Lance table.
- Edges can be a second Lance table or a JSON adjacency file — they're written once per rebuild in MVP.
- If SQL joins become genuinely painful in Phase 4 (community detection, aggregate queries), *then* introduce SQLite. Don't pay the two-store complexity tax until forced.

### 8. Corpus scope — **Agree with default, one addition**
Curated subset (`docs/research/` + `.claude/` + `.memories/`) is right. I'd **add `docs/ideas/`** — it's where the LTG concept paper itself lives, where smart-rag1/2/3 conversations live, and where `relate()` has its richest cross-document tests.

---

## Summary table

| # | Decision | Default | My lean |
|---|---|---|---|
| 1 | Index scope | per-repo + federation later | **agree** |
| 2 | Embedding model | bge-m3 | **nomic-embed-text via Ollama** |
| 3 | Vector store | LanceDB | **agree** |
| 4 | Graph library | networkx + leidenalg | **agree** |
| 5 | Extractor model | gemma3:12b (switch later) | **A/B both in Phase 1, decide empirically** |
| 6 | Placement | `retrieval/` top-level | **agree** |
| 7 | Storage | SQLite + LanceDB | **pure LanceDB until Phase 4 proves need** |
| 8 | Corpus | curated subset | **agree + add `docs/ideas/`** |

---

**Where I'd like your input:**
- **#2 (embedding):** do you want to stay inside Ollama for simplicity, or is running a sentence-transformers backend acceptable? This ripples into deployment.
- **#5 (extractor):** OK with Phase 1 starting with a 30-min A/B protocol before locking a model?
- **#7 (storage):** comfortable dropping the SQLite layer for MVP, or do you want the separation from day one?

The rest of the agrees I'll happily lock in as decisions if you nod. Which of these three want deeper discussion first?