<!-- ref:rag-repowise -->
# Repowise: Code-Graph + Git-Signal Intelligence

**Source:** https://github.com/repowise-dev/repowise
**Philosophy:** AI agents lack *institutional* knowledge about codebases — ownership, co-change, dead code, architectural rationale. Static source reading isn't enough.
**Relevance:** **High** — clearest match for "make Claude Code smarter about where to look" across code repos.

## Summary

Builds four intelligence layers locally over a code repository and exposes them to agents:

1. **Graph Intelligence** — tree-sitter parses 14 languages into a two-tier dependency graph (files + symbols). A 3-tier call resolver with confidence scoring handles imports/aliases. Leiden community detection identifies logical modules; PageRank + betweenness centrality rank central code.
2. **Git Intelligence** — analyzes 500 recent commits for hotspots (high churn × complexity), ownership percentages, and **co-change pairs** (files that change together *without* import links — an edge type static analysis misses).
3. **Documentation** — LLM-generated wiki with RAG via semantic search + freshness scoring.
4. **Decision Intelligence** — architectural decisions linked to graph nodes, tracked for staleness.

**Storage:** NetworkX (graphs), LanceDB (embeddings), generated wiki pages, git metadata — all local.
**Claim:** 27× fewer tokens per query vs naive context loading.

## Relation to Our Projects

### web-research
Partial match. The Python code of the web-research pipeline would benefit from a dependency graph + hotspot analysis during active development, but the *research output* (scraped knowledge) is not code — so only the infrastructure side matters here. Decision Intelligence + LLM-wiki layers are more portable across domains.

### Local LLMs (llm repo)
Very high match. The llm repo has heavy cross-file coupling that static analysis *misses*: a decision in `benchmarks/lib/record-verdicts.py` ripples into `models.yaml`, `personas/registry.yaml`, Modelfiles, and session logs — none of which import each other. Git co-change is the edge type that captures this. A nightly job computing co-change edges over the last 500 commits would surface:
- Which session logs correlate with which Modelfile updates
- Which benchmark files co-evolve with which personas
- Dead personas (not touched in N commits, not referenced)

This is a feature the `ref:KEY` graph can never capture because nobody writes `[ref:...]` for "these files just happen to change together."

### Augmenting Claude Code
The biggest concrete win. When Claude Code is about to edit `personas/create-persona.py`, the repowise view would say "these 4 files typically change with it: registry.yaml, models.yaml, persona-template.md, ollama-scaffolding/README.md — budget 5 files of context, not 1." That's a directly actionable signal Claude Code doesn't have today, and it specifically addresses the "what could break?" question.

The decision-records-linked-to-graph-nodes feature matches our `ref:` blocks exactly. Making those blocks queryable *by graph proximity* ("what decisions touched files near this one?") is a new access path we don't currently have.

### Career chat (HF Space)
Minimal applicability. The chatbot's corpus is documentation + profile data, not code; the git-signal layer doesn't help there. However, the generated-wiki layer with freshness scoring is a pattern we could reuse: annotate chatbot context chunks with "how recently was this mentioned" for staleness gating.

## Existing Infrastructure Connections

- **`ref:KEY` system** — already a manual version of Decision Intelligence linked to content. Repowise's "linked to graph nodes" is the automation we don't have.
- **Git history** — we already have rich commit messages (see `git log --oneline -5` discipline). The co-change edges computation would work out of the box.
- **`benchmarks/` results + `~/.local/share/ollama-bridge/calls.jsonl`** — already a "behavioral signal" layer like git-intelligence but for LLM calls. Co-use pairs (which personas get invoked together in a session) is the LLM-call analog of git co-change.
- **tree-sitter** — not currently used; would be a new dependency. But Python binding is tiny and only needs to run at index time.
- **LanceDB** — matches the lightweight-embedded vector store direction mentioned in `docs/ideas/smart-rag.md`.
- **`evaluator/` framework** — can score which co-change edges are meaningful (noise filter).

## Takeaway

The three genuinely new ideas from this research cluster come from repowise: **git co-change as an edge type**, **tree-sitter dependency graphs as structural retrieval**, and **27× token-reduction claim as a concrete target**. For the llm repo specifically, git co-change edges are a ~2-day addition that would measurably improve cross-file awareness without building anything as heavy as a full RAG pipeline.
<!-- /ref:rag-repowise -->
