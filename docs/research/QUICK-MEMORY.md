<!-- ref:quick-memory-web-research -->
# Quick Memory: Web Research Tool — Where We Are

*Session 44 (genesis). Read this first to recontextualize any forked session.*

---

## Current Status

**Decision: Build new, informed by Local Deep Research.** LDR is MIT-licensed, genuinely modular, extremely active — but its LangChain coupling, 2-3GB deps, multi-user web app design, and lack of structured output / multi-model / progressive autonomy mean the patterns are more valuable than the code. Language question is reopened.

**LDR patterns worth borrowing:**
1. `BaseSearchEngine` + factory (plugin architecture)
2. Two-phase retrieval (metadata preview → full content on demand)
3. Strategy registry (named strategies, configurable)
4. ReAct loop (search/read/reason cycle)
5. Library as search source (past research queryable alongside live web)

## Work Size Estimate (Build New)

| Component | Sessions | Notes |
|-----------|----------|-------|
| **MVP Core** (search→fetch→extract→save) | 2-3 | Validates core hypothesis |
| Structured output + Pydantic models | 1 | Layer 0 patterns transfer |
| Multi-model (config per stage) | 1 | Reuse warm_model + OllamaClient |
| Search engine abstraction | 1-2 | Borrow LDR pattern, simpler |
| JSONL event log | 0.5 | Same as calls.jsonl |
| SQLite knowledge store | 1-2 | Schema + node/edge graph |
| Sufficiency check (Agent B) | 1 | LLM prompt + iteration logic |
| CLI | 1 | Language-dependent |
| MCP integration | 1 | Same pattern as task 5.8 |
| SearXNG Docker setup | 0.5 | Straightforward |
| **Total MVP:** | **~4-5** | Core loop + files + CLI |
| **Total usable tool:** | **~8-10** | + structured output, multi-model, search abstraction, events |
| **Total full vision:** | **~15-18** | + knowledge graph, review, MCP, progressive autonomy |

## Fork Angles (for separate sessions)

1. **MVP spike** — Wire SearXNG + Crawl4AI + Ollama, test with 14B on 5 URLs (~2 hours)
2. **DDD agent modeling** — Formalize "DDD as agent/model modeling" as reusable pattern
3. **Mastra deep-dive** — Suspend/resume + workflow engine for progressive autonomy
4. **Tool calling benchmarks** — Retest current models for Agent Tool feasibility
5. **SearXNG setup** — Docker deploy, test search quality (prerequisite)

## Key Documents

See `INDEX.md` in this folder for full catalogue with ref keys.
<!-- /ref:quick-memory-web-research -->
