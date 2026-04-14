<!-- ref:rag-obsidian-mind -->
# Obsidian Mind: Graph-First Memory for Coding Agents

**Source:** https://github.com/breferrari/obsidian-mind
**Philosophy:** Treat wikilinks as the primary retrieval signal. A note without links is a bug.
**Relevance:** **High** — directly validates exploiting the `ref:KEY` + `.memories/` graph we already have.

## Summary

A git-tracked Obsidian vault acts as a persistent brain for coding agents (Claude Code specifically). It explicitly rejects vector-based retrieval in favor of **graph-based semantic querying**: wikilinks form edges, indexes aggregate related content, and a lightweight classification hook (~100 tokens per message) routes which part of the vault to look at.

**Key techniques:**
- **Purpose-based folder structure** (work/, org/, perf/, brain/) — hierarchical scoping before retrieval
- **QMD semantic search** — find notes by meaning, not full-text
- **Classification hooks** inject ~100-token routing hints per message (which folder/topic to inspect)
- **Auto-loaded `MEMORY.md` index** in `~/.claude/` — points to vault locations, does not store durable knowledge itself
- **Session hooks** inject only lightweight context (~2K tokens: North Star, git summary, task list, file listing); full reads triggered only when explicitly needed
- **Enforced linking discipline** — unlinked notes are treated as bugs

## Relation to Our Projects

### web-research
Less directly applicable — the corpus there is scraped content, not hand-authored notes. But the classification-hook pattern (lightweight routing before retrieval) maps onto the web-research Dispatcher: classify a query into "needs search / needs existing knowledge / needs both" before firing scrapers. Saves wasted calls.

### Local LLMs (llm repo)
The `~/.claude/` auto-loaded `MEMORY.md` pattern is basically what we already do with the auto-memory system (user/feedback/project/reference files + MEMORY.md index). Obsidian Mind validates this as a working pattern for a *different* agent (Claude Code on a coding project), not just for cross-session preferences. Worth noting: they keep durable knowledge in the vault, not in MEMORY.md — MEMORY.md is a pointer layer only. We're already doing this implicitly with `ref:KEY` pointing at files.

### Augmenting Claude Code
Direct match. The classification hook idea is notably absent from our setup: right now every session gets the same session-context.md injected, regardless of task. A routing hook that reads the user's first message and picks which `.memories/` folders to preload would cut session-start context by 50%+ and make the per-folder `.memories/` investment pay off harder.

### Career chat (HF Space)
The lightweight-context pattern is exactly what the chatbot needs. Today `sync-context.sh` copies *all* `.memories/` files into the static context. A classification pass ("is this a career question, a coding question, or a platform question?") before retrieval would let the chatbot load only the relevant slice per query. Works well at chat scale since a small local classifier runs in milliseconds.

## Existing Infrastructure Connections

- **`ref:KEY` cross-references** — already hand-curated wikilinks. The graph exists, we just don't traverse it.
- **`.memories/QUICK.md` per folder** — already purpose-based scoping (like work/, org/, perf/).
- **User-level `MEMORY.md` (auto-memory)** — already a pointer-layer index. Same pattern.
- **`ollama-bridge` classify_text tool** — ready-made classifier for the routing-hook pattern. Model: `my-classifier-q3`.
- **Claude Code SessionStart hook** (backup.sh) — precedent for hook-based injection. Adding a classification hook is an incremental change, not new infrastructure.

## Takeaway

Confirms the graph-first direction and gives us the "classification hook before retrieval" pattern — a ~1-day addition that reduces context waste without touching the underlying indices. The routing hook is the cheapest single win from this research cluster.
<!-- /ref:rag-obsidian-mind -->
