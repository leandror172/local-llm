`★ Insight ─────────────────────────────────────`
- You're not describing one feature — you're describing a **shared substrate**. The same "content-linking retrieval layer" needs to serve four distinct consumers (profile chatbot, Claude Code, web-research knowledge domain, llm project itself), each with different query shapes but the same underlying index. That's a strong architectural signal: build it as a **library + service**, not as a chatbot component.
- TF-IDF not appearing in my first answer was deliberate — BM25 is TF-IDF's direct descendant and strictly better for retrieval (length normalization, term saturation). If the expense project folks are reaching for TF-IDF, they're either doing classification (where TF-IDF as features still makes sense) or they haven't discovered BM25 yet. Worth naming the distinction.
- Your memory tier design (Tier 0–3) and the proposed retrieval layer are the **same problem at different scales**. Tier 0 QUICK.md is a hand-curated working set; a retrieval layer is an automatically-maintained working set. They should share infrastructure, not compete.
`─────────────────────────────────────────────────`

This reframing changes everything about how to think about it. Let me restructure around the four consumers, then find the shared shape.

## Four consumers, one substrate

**1. Profile chatbot (HF Space)**
- Query shape: natural-language questions from strangers ("does Leandro know Kubernetes?", "what's his experience with AI?")
- Corpus: profile data + llm repo docs + expense repo docs + web-research docs + chatbot source
- Constraint: remote, stateless, cheap. Must run without local GPU.
- Sensitivity: **some corpus must NOT leak** (e.g., session logs with internal context, `.claude/local/`)

**2. Claude Code itself (across all repos)**
- Query shape: "where is X?", "what did we decide about Y?", "has this been tried before?"
- Corpus: whatever repo is open + cross-repo references + memory system
- Constraint: local, fast, cache-warm. Must not replace the existing `ref_lookup` workflow but augment it.
- Sensitivity: none locally — same trust boundary as the filesystem

**3. Web-research knowledge domain**
- Query shape: "what do we know about event sourcing?", "which scrapers support JS rendering?"
- Corpus: accumulated research artifacts (scraped pages, extracted facts, notes)
- Constraint: corpus grows continuously, relationships matter more than documents
- Sensitivity: none (research output)

**4. LLM project as the experimental platform**
- Query shape: all of the above, plus meta-queries ("which personas handle Python best?", "which benchmarks ran on gemma3?")
- Corpus: code + configs + benchmarks + session logs + DPO data
- Constraint: this is where you *build* the retrieval layer, so it doubles as the first user
- Sensitivity: same as Claude Code

**The common shape:** a content-indexed, relation-aware retrieval service that answers `(query, scope, permissions) → [(chunk, source, score, edges)]`. Each consumer differs in *scope* and *permissions*, not in the retrieval mechanism.

## Why this maps onto your memory-tier design cleanly

Your existing tiers (from `memory-layer-design.md`):

| Tier | What it is now | What retrieval adds |
|------|----------------|---------------------|
| Tier 0 (`QUICK.md`) | Hand-curated, always-injected | *Could be auto-generated* from a retrieval pass over the folder, then manually pruned. Or stay manual but backstopped by retrieval for everything QUICK.md doesn't cover. |
| Tier 1 (session-context) | Hand-curated at handoff | Unchanged — too dense/deliberate to auto-generate. |
| Tier 2 (`ref:KEY` blocks) | Hand-tagged semantic blocks | **This is already a knowledge graph.** The ref keys are nodes, the cross-references (`ref:patterns-index` → `ref:patterns-*`) are edges. You've been hand-curating a graph for a year. Retrieval turns it from "look up by key" into "find related by query." |
| Tier 3 (user memories) | Small, always-loaded index | Unchanged — different purpose (stable preferences, not documents). |

The retrieval layer isn't a *replacement* for any tier — it's a **new access path** across Tiers 0–2 that answers "what's relevant to *this query*" instead of "what's in *this specific location.*"

## The substrate: what to actually build

The minimum useful thing is a local indexing service with three layers:

**Layer A — Indexer (runs offline / on commit)**
- Walks configured corpora (llm repo, web-research repo, profile data, expense repo docs)
- Respects include/exclude rules per corpus (critical for profile chatbot — `.claude/local/` never indexed, session logs optionally excluded)
- Chunks with **contextual prefixes** (Anthropic Sept 2024 technique): one small local LLM pass per doc adds a summary-style prefix to each chunk before embedding. Your RTX 3060 + qwen3:8b can do this overnight.
- Emits: vector embeddings, BM25 index, metadata, and a **relation table** that harvests your existing structure (`ref:KEY` tags, `[ref:...]` references, markdown links, file imports, `.memories/` pointers) as edges.

**Layer B — Retriever (stateless query service)**
- `retrieve(query, scope, limit, mode) → ranked chunks`
- `scope` = permission boundary ("chatbot-safe" / "all-local" / "web-research-only")
- `mode` = strategy knob — at minimum: `hybrid` (BM25 + dense + RRF), `rerank` (add BGE/Jina reranker), `graph` (expand top hits along the relation edges, then rerank)
- Runs locally as an HTTP service or as an MCP tool (`retrieve_context`)
- Called by the chatbot (via HTTP, with `scope=chatbot-safe`), by Claude Code (via MCP), by web-research Dispatcher, and by you directly

**Layer C — Consumer adapters (thin)**
- Chatbot: call retriever with `scope=chatbot-safe`, stuff top-K chunks into the system prompt alongside the existing `.memories/QUICK.md` working set
- Claude Code: new MCP tool `retrieve_context(query, scope="repo")` that complements `ref_lookup` (exact key) with semantic search (fuzzy query)
- Web-research: Knowledge Domain's persistence layer writes into the same index; queries go through the same retriever
- Each adapter is ~50 lines — the intelligence lives in the substrate

## Why this is the llm project's job

You said "surely the place where this would be prepared to be applied everywhere else" — and this is exactly right, for three reasons:

1. **You already have the infrastructure.** Local models for contextual chunking (free), ollama-bridge for orchestration, `.memories/` convention for what to prioritize, `ref:KEY` system as a graph prior. No other repo has these pieces.

2. **The llm project is the first user.** Before deploying to the chatbot (where bugs affect strangers) or to web-research (where it's a core dependency), you dogfood it here: replace or augment `ref_lookup` with a retriever that can answer "which decisions mention `think: false`" without you remembering the ref key.

3. **It becomes a Layer 7 deliverable.** Your plan-v2 Layer 7 already lists "Full RAG with embeddings (task 7.11)" as the advanced step after memory. This would be 7.11 promoted to a cross-cutting substrate rather than an internal feature — it unblocks Layer 7 memory, Layer 8 project bootstrapper, and the chatbot Phase 3 all at once.

## Specific techniques that *didn't* appear in my first answer but fit your case

- **TF-IDF per se:** only useful as a feature pipeline in the expense project's classifier (where the output is a category label, not a document). For retrieval, use BM25 instead — same intuition, strictly better math.
- **Propositional indexing** (Chen et al., "Dense X Retrieval"): instead of chunking by size, have a local LLM extract atomic facts ("Qwen3 uses `think: false` via options block, set in session 35") and embed *those*. Dramatically better recall for relational queries; costs one LLM pass per doc. Candidate for your stable content (profile data, architectural decisions). Not worth it for fast-changing code.
- **CRAG / Self-RAG**: after retrieving, a small LLM critiques the retrieved set ("does this actually answer the query?") and triggers re-retrieval or broader search. Fits your "Auditor" agent pattern in web-research.
- **SPLADE**: sparse neural retrieval — learned term expansion on top of BM25. Worth mentioning because it's the "middle path" between BM25 and dense vectors. Probably overkill for your scale (better ROI on reranker + contextual chunking).
- **Fusion-in-Decoder (FiD) vs naive RAG**: if the final answer model is Claude, naive RAG (stuff chunks into prompt) is fine. If you ever run a local model as the answer model, FiD-style per-chunk encoding outperforms naive stuffing.
- **Multi-vector per document** (BGE-M3, ColBERT late interaction): you get dense + sparse + multi-vector from a single model. Practical because you only run one embedder.

## What to do with the expense project

You're right that it applies less. The one place it *could* apply:
- **Classification via retrieval instead of prompting.** Your few-shot injection pattern (5.7) already does this manually: keyword pre-match training data → inject top-K examples. That *is* retrieval-augmented classification, just using BM25-style matching. Upgrading it to hybrid retrieval + reranker would improve few-shot quality at classification time without changing the model. Possibly a 5–10% accuracy lift on ambiguous expenses. Low priority compared to the other consumers.

TF-IDF as a classifier feature input is a different thing — that's building a statistical classifier on top of term frequencies, and it's fine if that's what the expenses discussion is about. For *retrieval*, skip it.

## The architectural question to answer first

Before building, one decision shapes everything: **is the index one-per-repo or one-global?**

- **One-per-repo:** simpler permissions (chatbot only connects to "public-llm" + "public-profile"), more failure isolation, each repo owns its corpus. Matches your existing .memories/ + ref:KEY pattern (per-repo).
- **One-global (with tagged scopes):** cross-repo queries become trivial (chatbot can ask "how does smart-chatbot relate to web-research?"), harder to reason about permissions, one index to maintain.

I lean toward **one-per-repo with a federation layer**: each repo exposes a local retriever endpoint (MCP tool, for example), and a thin federator queries multiple and merges with RRF. It preserves ownership, makes the chatbot's permission boundary crisp (it talks to curated endpoints), and aligns with how you already think about cross-repo work (`ref_lookup` with explicit `path=` argument).

---

Now post your links and the technique names you had in mind — I want to see where the existing tools you've been looking at draw their boundaries, because that will help decide whether to wrap an existing thing (LlamaIndex, txtai, Haystack) or build the minimum from primitives (sentence-transformers + rank_bm25 + LanceDB + a reranker — probably <500 lines of Python). My current intuition is "build minimum, borrow chunking from Anthropic's paper, use your existing ref graph as the relation layer" — but seeing what you've been reading will sharpen that.