<!-- ref:rag-mempalace -->
# MemPalace: Hierarchical Spatial Memory for Conversations

**Source:** https://github.com/MemPalace/mempalace
**Philosophy:** Store verbatim conversation history and retrieve via spatial-memory-inspired hierarchy. Structured navigation beats smarter embeddings on recall.
**Relevance:** **Medium** — validates the per-folder `.memories/` scoping pattern; otherwise less applicable.

## Summary

**Storage:** Raw conversation text in ChromaDB (no chunking, no summarization). Optional SQLite knowledge graph tracks temporal entity relationships. Entirely local, no cloud.

**Architecture:** Mirrors the "memory palace" mnemonic technique:
- **Wings** = people/projects (top-level partitioning)
- **Rooms** = topics
- **Halls** = memory types (decisions, events)
- **Drawers** = verbatim content
- **Tunnels** = cross-wing connections (the graph edges)

**Retrieval claim:** Scoped search (within wing+room) achieves 94.8% recall vs 60.9% for flat search — a 34% absolute gain attributed to structured navigation, not smarter vectors.

**Cost framing:** $10/yr self-hosted vs ~$507/yr for summarization-based alternatives (Mem0, Zep). No lossy compression.

## Relation to Our Projects

### web-research
The verbatim-storage philosophy is already how the Knowledge Domain works (raw extracted data + source pointers). MemPalace confirms that verbatim is a valid design choice — we don't need aggressive summarization to keep corpus size manageable. The wing/room/hall taxonomy doesn't map cleanly to research topics (which are more fluid), but the *principle* — scoped search within a topic partition first — maps onto our focus-directed extraction.

### Local LLMs (llm repo)
The scoping-beats-smarts finding is the most important takeaway: a 34% recall gain from structure alone. This validates the `.memories/` per-folder convention: we already partition by folder purpose, so queries hitting the right folder first should outperform a flat repo-wide search. What we don't have is a mechanism to *route* a query to the right folder before searching. The obsidian-mind classification hook would fill that gap.

### Augmenting Claude Code
Already partially implemented: session-context tells Claude Code "check `.memories/` for the folder you're working in." The formal hierarchy MemPalace names explicitly (wing → room → hall → drawer) maps onto our implicit (repo → folder → topic → file). No architectural change needed — just validation of the existing pattern.

### Career chat (HF Space)
Interesting for the "tunnels" concept — cross-wing connections tracked explicitly. The chatbot's hardest questions are cross-project ("does Leandro's LLM work relate to his Java background?"), which is a tunnel between the career wing and the llm wing. Today that connection lives only in the unified `portfolio.md` file. A more formal edge ("career-wing.java-experience ↔ llm-wing.layer5-expenses") would let the chatbot answer cross-project questions with specific evidence rather than a handwoven narrative.

## Existing Infrastructure Connections

- **`.memories/` per-folder convention** — already wings/rooms, without the name. The 34% recall finding justifies keeping and extending it.
- **`docs/portfolio/portfolio.md`** — already a "tunnels" document (cross-repo connections). Could be formalized with typed edges (`relates-to`, `applies-to`).
- **ChromaDB** — not currently used; would be a new dependency if adopted (LanceDB was the preferred embedded option in prior conversation).
- **`evaluator/`** — could be used to validate the claimed recall gain in our own corpus before committing to a vector store.

## Takeaway

Not a system to adopt, but the empirical finding — **hierarchical partitioning gives 34% absolute recall over flat search** — is a strong argument for investing more in `.memories/` scoping and a classification-based routing hook rather than assuming "better embeddings" would solve the problem. The tunnels concept hints at an underexplored feature for the chatbot's cross-project question handling.
<!-- /ref:rag-mempalace -->
