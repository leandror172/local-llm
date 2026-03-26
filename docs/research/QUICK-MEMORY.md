<!-- ref:quick-memory-web-research -->
# Quick Memory: Web Research Tool — Where We Are

*Updated 2026-03-26. Read this first to recontextualize any forked session.*

---

## Current Status

**Phase 1 (extraction spike) complete.** Local 7-14B models can reliably extract structured
information from web pages. Pipeline validated, merged to main.

**Phase 2 (search integration) next.** Not yet started.

**Key decisions made:**
- Build new (not fork LDR) — LDR patterns worth borrowing, not the code
- Language: Python, uv + pyproject.toml
- Task-aware model selection — extraction and codegen need different models
- Protocol-based pipeline — each step independently callable, swappable

**LDR patterns still worth borrowing:**
1. `BaseSearchEngine` + factory (plugin architecture)
2. Two-phase retrieval (metadata preview → full content on demand)
3. ReAct loop (search/read/reason cycle)
4. Library as search source (past research queryable alongside live web)

## Memory Architecture (cross-repo design)

Per-folder `.memories/` with two tiers, modeled on human memory types:
- **QUICK.md** (working + prospective) — injected into agents, ~30 lines max
- **KNOWLEDGE.md** (semantic + consolidated episodic) — read on demand

Procedural lives at repo level (CLAUDE.md/overlays). Episodic lives at repo level
(session logs) and consolidates into folder semantic via "dream" passes.

Full design: `/mnt/i/workspaces/web-research/docs/research/memory-architecture-design.md`
First instance: `web-research/spike/.memories/`

## Remaining Work Size Estimate

| Component | Sessions | Notes |
|-----------|----------|-------|
| Search engine abstraction | 1-2 | Borrow LDR BaseSearchEngine pattern |
| Multi-model config per stage | 1 | Reuse warm_model + OllamaClient |
| JSONL event log | 0.5 | Same as calls.jsonl |
| SQLite knowledge store | 1-2 | Schema + node/edge graph |
| Sufficiency check (Auditor) | 1 | LLM prompt + iteration logic |
| CLI | 1 | argparse or click |
| MCP integration | 1 | Same pattern as task 5.8 |
| SearXNG Docker setup | 0.5 | Straightforward |
| **Total to usable tool:** | **~6-8** | Search + pipeline + knowledge + CLI |
| **Total full vision:** | **~12-15** | + knowledge graph, review, MCP, progressive autonomy |

## Key Documents

See `INDEX.md` in this folder for full catalogue with ref keys.
Web-research repo: `/mnt/i/workspaces/web-research/`
<!-- /ref:quick-memory-web-research -->
