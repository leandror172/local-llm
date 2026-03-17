<!-- ref:vision-web-research -->
# Vision: AI-Powered Web Research Tool

*Synthesized 2026-03-16, session 44. Distilled from user thinking, research findings, and architectural analysis.*

---

## What This Is

A **local-model-powered web research workbench** that iteratively gathers, processes, and accumulates knowledge from the web — designed to work with limited resources (RTX 3060 12GB), integrate with Claude Code, and progressively become more autonomous over time.

It is **not** a one-shot search tool. It is an ongoing investigation system with persistent memory, iterative deepening, and human-in-the-loop steering that gradually delegates more decisions to local models.

---

## Core Principles

### 1. Context-Efficient by Design
The whole point is that processing happens **outside** the frontier model's context. Scrapers fetch, local models process, files accumulate. Claude Code (or the user) only sees summaries and decision points. The frontier model's value is in **judgment**, not **processing**.

### 2. Local-Model-First
Ollama (7-14B models) handles the heavy lifting: extraction, summarization, query generation, relevance scoring. Frontier models (Claude) are optional — used for complex synthesis, evaluation, or supervision. Every token processed locally is a token not spent on API costs.

### 3. Pluggable Everything
Scraper backends (Crawl4AI, Firecrawl, SearXNG, raw Playwright) are swappable. LLM backends are swappable. Tools are plugins. The architecture defines **interfaces**, not implementations. This minimizes lock-in and allows using the best tool for each job.

### 4. Progressive Autonomy
The tool starts supervised — a human (or Claude) guides decisions at every step. Over time, as the tool proves reliable, it takes on more decisions: which links to follow, when research is sufficient, when to stop. The autonomy level is a dial, not a switch.

### 5. Knowledge Compounds
Research findings persist across sessions. New data is linked to existing knowledge. The system gets smarter over time, not just within a single research session. This is the key differentiator from most existing tools (which are stateless between runs).

### 6. Domain-Driven Agent Modeling
Agents map to bounded contexts (DDD). Each agent has a domain with its own language, rules, and appropriate model. Same-domain agents share a model (no swap overhead). Cross-domain transitions justify model swaps and require explicit data translation at the boundary. Over-engineering is avoided by only splitting into separate agents when the context/domain benefit outweighs the swapping cost.

---

## Use Cases

### Direct Research (MVP)
A human gives the tool a URL, a list of URLs, or a topic. The tool fetches content, extracts relevant information, identifies links worth following, and presents options. The human guides the investigation. Output: organized markdown files with findings.

*Example: "Here are 20 sites about AI tools. Research each one. Tell me what they do, how they compare, and which are relevant to our setup."*

### Claude Code Delegation
Claude Code invokes the tool to research a topic without consuming its own context. The tool runs a local-model pipeline, writes findings to files, and returns a summary. Claude Code reads the summary and acts on it.

*Example: This very research session — instead of Claude spending tokens reading 20 pages, the tool scrapes, extracts, and summarizes locally. Claude only reads the final analysis.*

### Post-Research Conversation
After research is stored, a user (or Claude) asks questions about accumulated knowledge. The knowledge layer provides answers grounded in sources, with links back to the original data.

*Example: "What did we find about event sourcing for AI agents?" → answers drawn from stored research, with source citations.*

---

## Architecture Overview

### Layers

```
┌──────────────────────────────────────────────┐
│  ENTRY POINTS                                 │
│  - Human via CLI                              │
│  - Claude Code via MCP tool / skill           │
│  - Programmatic (script, cron, idle-time)     │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  ORCHESTRATION (Agent A)                      │
│  - Receives query, enriches prompt            │
│  - Determines what tools/pipelines needed     │
│  - Saves context (no auto-conversation like   │
│    Claude Code — must be explicit)            │
│  - Iterates until criteria met                │
│  - Delegates context-heavy sifting to proxy   │
│    (Agent A2) to avoid context pollution      │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  TOOL EXECUTION (Agent Tool)                  │
│  - Knows available tools and how to call them │
│  - Builds execution pipelines                 │
│  - Decides parallelization                    │
│  - Routes data between tools                  │
│  - Tools are plugins (swappable, multi-lang): │
│    SearXNG, Crawl4AI, Firecrawl, Ollama,     │
│    Playwright, Stagehand, etc.                │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  REVIEW (Agent B)                             │
│  - Is the research sufficient?                │
│  - Should more be explored?                   │
│  - "More" signal decreases iteratively        │
│  - Produces notes for orchestrator            │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  KNOWLEDGE (Persistence Layer)                │
│  - Raw content stored (for replay)            │
│  - Extracted facts stored (for queries)       │
│  - Relationships created (graph)              │
│  - New data triggers integration: does this   │
│    connect to existing knowledge?             │
│  - Summarization with source pointers         │
│  - Event log for audit trail and replay       │
└──────────────────────────────────────────────┘
```

### Agent ≠ Model ≠ Process

"Agent" in this architecture means **a role with a bounded context**, not necessarily:
- A separate model (same-domain agents can share a model)
- A separate process (agents can be function calls within one process)
- An AI at all (Agent Tool's integration layer could be deterministic code)

The split into agents happens when the **context benefit** (focused prompt, appropriate model, cleaner reasoning) outweighs the **swapping cost** (VRAM reload, lost conversational state, data translation).

### DDD → Agent Mapping

| DDD Concept | Agent Equivalent |
|-------------|-----------------|
| Bounded context | Agent's domain (research mgmt, tool execution, review) |
| Ubiquitous language | The system prompt defining concepts for this agent |
| Context map | How agents pass data between domains |
| Anti-corruption layer | Adapter between tools with different data formats |
| Aggregate root | Primary entity each agent manages (session, pipeline, knowledge entry) |
| Domain event | Something that happened (URLFetched, FactExtracted) → event sourcing |

---

## Key Technical Decisions (Open)

### Scraping
- **Crawl4AI** is the strongest self-hosted option (Apache 2.0, Docker, Ollama-native extraction)
- **SearXNG** needed for search (self-hosted metasearch, Docker, free, no API keys)
- **Firecrawl** available as cloud fallback (already installed as Claude Code plugin)
- Architecture: pluggable `Scraper` interface; all backends expose REST APIs

### Language
Four viable paths (see `web-research-tool-analysis.md` Part 7):
- **Python**: Richest ecosystem, code reuse, Crawl4AI native
- **TypeScript**: Emmett (event sourcing), Mastra (agent framework), Firecrawl primary SDK
- **Go**: Single binary, best concurrency, long-term maintainability
- **Kotlin**: Best type system + async, Axon if event sourcing is primary
- Agent Tool's plugin architecture reduces language lock-in pressure

### State Management
- **JSONL event log** from day one (audit trail, replay, near-zero cost)
- **SQLite** for indexed state + lightweight knowledge graph (node/edge tables)
- Upgrade path: Python `eventsourcing` lib, or Emmett (TS), or Graphiti/Neo4j for graphs

### Integration with Claude Code
- **MCP tools**: `research_url`, `search_topic`, `query_knowledge` (thin wrappers)
- **Skill**: `/research <url>` for high-level workflow
- **Standalone CLI**: runs independently without Claude Code

---

## MVP → Full Vision Path

| Phase | What | Validates |
|-------|------|-----------|
| **MVP** | Single pipeline: query → search → fetch → extract → store to files | Can local models produce useful web research? |
| **+Review** | Sufficiency check, iteration, decreasing "more" signal | Can the system self-assess quality? |
| **+Pipeline** | Agent Tool layer, pluggable backends, parallelization | Does tool abstraction reduce language lock-in? |
| **+Knowledge** | Graph relationships, cross-session persistence, post-research queries | Does accumulated knowledge compound value? |
| **+Context mgmt** | Agent A2 proxy, model-per-domain routing, DDD boundaries | Does context separation improve output quality? |
| **+Learning** | Historical pipeline data, improved routing, distillation | Does the system get better with use? |

---

## Testing Strategy

| Level | Determinism | Approach |
|-------|-------------|----------|
| **Unit** | Deterministic | Standard tests, mocked HTTP responses, fixed model outputs |
| **Integration** | Semi-deterministic | Known test fixtures, property-based ("output contains X"), snapshot tests |
| **System** | Non-deterministic | Frontier-model judgment as optional evaluator, expected-result fixtures |

**Principles:**
- Extract the deterministic from the non-deterministic
- Accept non-determinism and work around it
- Ignore non-determinism backed by lower-level tests
- Well-tested low levels → trust at higher levels

---

## What Makes This Different

Most existing research tools (GPT-Researcher, STORM, Perplexity, dzhng/deep-research) are:
- API-dependent (frontier models for all processing)
- Single-session (stateless between runs)
- Fully autonomous (no progressive autonomy)
- Single-backend (hardcoded to one search/scrape tool)

This tool would be:
- **Local-model-first** with frontier as optional layer
- **Persistent** across sessions with compounding knowledge
- **Progressively autonomous** (supervised → delegated → autonomous)
- **Pluggable** with swappable tool backends
- **Context-efficient** for frontier model integration (Claude Code delegation)

The closest existing tool is **Local Deep Research** (Ollama + SearXNG, persistent knowledge). Differentiation: progressive autonomy, pluggable scrapers, focus-directed extraction, DDD agent modeling, Claude Code integration.

---

## Related Documents

- `web-research-tool-analysis.md` — Full technical analysis (scrapers, languages, state management, existing tools)
- `web-research-tool-user-notes.md` — Raw user thinking (use cases, agent architecture, testing)
<!-- /ref:vision-web-research -->
