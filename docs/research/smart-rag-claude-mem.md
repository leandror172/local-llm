<!-- ref:rag-claude-mem -->
# Claude-Mem: Hybrid Observation Store with Lifecycle Hooks

**Source:** https://github.com/thedotmack/claude-mem
**Philosophy:** Automatically capture tool usage observations during Claude Code sessions, AI-generate semantic summaries, make them searchable across sessions.
**Relevance:** **Medium** — validates the hook-capture pattern; overlaps with our existing session-log + MEMORY.md flow.

## Summary

**Storage:** SQLite for verbatim observations + AI-generated semantic summaries.
**Indexing:** FTS5 (full-text) + Chroma (vector) — true hybrid keyword + semantic.
**Retrieval:** 3-layer workflow designed for token efficiency:
1. `search` returns compact indices (~50-100 tokens) — "here are IDs matching"
2. `timeline` shows chronological context
3. `get_observations` fetches full details only for filtered IDs

**Claim:** ~10× token savings from filtering-before-fetching.

**Automation:** 5 lifecycle hooks capture data without user intervention — SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd. Plus a worker service for async processing.

**Linking:** "Citations" feature lets the user reference past observations by ID via `http://localhost:37777/api/observation/{id}`.

## Relation to Our Projects

### web-research
Partial match. The hook-capture pattern doesn't apply (no "sessions" in web-research). But the 3-layer retrieval workflow (ID-first, details-on-demand) is directly relevant to the Knowledge Domain: `query_knowledge` should return compact IDs + summaries, not full extracted facts, and a follow-up call fetches details. Current `query_knowledge` tool already does something like this; claude-mem's claim suggests we could push it further.

### Local LLMs (llm repo)
Lifecycle-hook capture is *already in place*: ollama-bridge logs every Ollama call to `~/.local/share/ollama-bridge/calls.jsonl` (prompt, response, model, latency). That's the "observation store." The gap is the retrieval layer — we have no equivalent of `search` over the call log. Adding a small SQLite+FTS index over calls.jsonl is a ~1-day addition with immediate payoff: "which prompts produced ACCEPTED verdicts for gemma3:12b in the last week?"

### Augmenting Claude Code
The hook inventory is interesting. We only have SessionStart (dotfiles backup) and UserPromptSubmit (via hookify). claude-mem uses PostToolUse and Stop — which is how they capture tool observations automatically without needing the user to write session logs by hand.

Competing vs complementary: claude-mem solves "remember what tools did last session." We already solve that via `.claude/session-log.md` + handoff flow. The *difference* is that session-log is hand-curated at handoff time and captures intent; claude-mem captures raw tool output. Complementary, not competing. A PostToolUse hook that appends selective tool observations to a machine-readable log would give us both.

### Career chat (HF Space)
Not applicable directly — the chatbot doesn't invoke tools in the claude-mem sense. But the 3-layer retrieval pattern *is* applicable to how the chatbot consumes its static context: phase 2 already does LLM routing to pick sections; adding an "IDs first, details on demand" layer would reduce the per-question context budget further.

## Existing Infrastructure Connections

- **`~/.local/share/ollama-bridge/calls.jsonl`** — already the observation-store substrate; needs only an index.
- **`.claude/session-log.md`** — hand-curated equivalent of what claude-mem automates.
- **hookify plugin** — precedent for Claude Code hook-based automation.
- **Claude Code SessionStart hook** (dotfiles) — precedent for lifecycle hooks.
- **`docs/ideas/claude-code-python-port.md` → `services/autoDream/`** — Claude Code's own built-in memory consolidation (same pattern). Reading its source before building a competing system is the right move.
- **MCP `ref_lookup`** — conceptual cousin of claude-mem's `get_observations(id)`.

## Takeaway

The hook-capture pattern and the filter-before-fetch retrieval discipline are both patterns worth stealing. But we shouldn't install claude-mem — it would conflict with session-log + autoDream. Instead, steal the two patterns: (1) add an FTS index over ollama-bridge calls.jsonl, (2) consider a PostToolUse hook for selective observation logging if/when we hit a gap in hand-written session logs.
<!-- /ref:rag-claude-mem -->
