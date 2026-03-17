<!-- ref:analysis-web-research -->
## Comprehensive Analysis: Web Research Tool

### Part 1: The Decision Dimensions

There are four interconnected decisions to make. They constrain each other.

| Decision | Options | What it affects |
|----------|---------|-----------------|
| **A. Scraping backend** | Firecrawl cloud, Firecrawl self-hosted, Crawl4AI, pluggable | Cost, self-hosting, capabilities |
| **B. Language/framework** | Python, Java+Axon, Kotlin, Go, TypeScript, hybrid | Dev speed, type safety, ecosystem |
| **C. State management** | Flat files, JSONL event log, SQLite, full event sourcing, graph DB | Complexity, replay, knowledge queries |
| **D. Autonomy model** | CLI-only, MCP tools, skill, full agent framework | Integration with Claude Code, standalone use |

---

### Part 2: Scraping Backend Analysis

| Backend | Cost | Self-hosted | LLM extraction | JS rendering | Anti-bot | License | Any-language API |
|---------|------|-------------|-----------------|-------------|----------|---------|-----------------|
| **Firecrawl cloud** | $16+/mo (500 free credits) | No | Via agent mode | Yes | Strong (cloud) | N/A (SaaS) | REST API |
| **Firecrawl self-hosted** | Free | Docker Compose + Postgres + Redis | Limited | Yes | Weak | AGPL-3.0 | REST API |
| **Crawl4AI** | Free | Docker (single container) | Yes (Ollama-native!) | Yes (Playwright) | Magic Mode + proxy | Apache 2.0 | REST API at :11235 |
| **firecrawl-simple** | Free | Docker | No | Yes | Hero browser | AGPL-3.0 | Firecrawl-compatible API |
| **Spider (Rust)** | Free | Yes | Via agent | Yes | Proxy + fingerprint | MIT | REST API |
| **ScrapeGraphAI** | Free + LLM tokens | Python lib | Core feature | Yes | Limited | MIT | Python only |

**Key insight:** Your pluggability requirement is the right call. All major options expose REST APIs, so the tool can define a `Scraper` interface and swap backends. Crawl4AI is the strongest default (free, self-hosted, Ollama-native, Apache 2.0, single Docker container), but the architecture shouldn't be locked to it.

**Crawl4AI's Ollama-native extraction** is notable — it can fetch a page AND extract structured data using your local models in a single call. This partially collapses the "fetch → process" pipeline into one step. But you'd still want the option to do extraction separately (different prompts, different models, re-extraction from cached content).

For **browser interaction** (future "AI interacting with pages"):
- **Stagehand** (MIT, 50k stars) — the only one with Java SDK, self-healing, multi-language
- **Browser-Use** (MIT, 78k stars) — most autonomous, Python-native
- **Playwright MCP** (Apache 2.0, Microsoft) — direct Claude Code integration via accessibility tree

---

### Part 3: Language/Framework Analysis

Since all scrapers and Ollama expose REST APIs, **no language is technically blocked**. The question is where the ecosystem advantages and architectural patterns best serve the tool's nature.

#### What the tool actually does at runtime:

1. Makes HTTP calls (scraper API: ~1s, Ollama: 2-30s) — **I/O bound**
2. Processes JSON/markdown responses — **string/struct manipulation**
3. Makes navigation decisions — **state machine logic**
4. Writes to files/database — **I/O bound**
5. Presents options to user or acts autonomously — **CLI/UI**

The bottleneck is always Ollama inference (2-30s per call). Language performance is irrelevant. What matters: **ecosystem, type safety, async model, state management, and maintainability.**

#### Honest comparison:

| Criterion | Python | Go | TypeScript | Kotlin | Java+Axon |
|-----------|--------|----|-----------:|--------|-----------|
| **Time to MVP** | 1-2 weeks | 2-3 weeks | 1-2 weeks | 2-4 weeks | 4-8 weeks |
| **Type safety** | Moderate (Pydantic+mypy) | Good | Good (Zod) | Excellent | Excellent |
| **Async model** | Good (asyncio) | Excellent (goroutines) | Good (promises) | Excellent (coroutines) | Adequate |
| **Scraper SDKs** | Best (Crawl4AI native) | Good (Colly, Firecrawl Go) | Strong (Firecrawl primary) | Moderate (via REST) | Weak (via REST) |
| **Ollama client** | Existing code to reuse | Official Go client | Via HTTP | nirmato-ollama | Spring AI / Ollama4j |
| **Event sourcing** | `eventsourcing` lib | Weak (build your own) | Emmett | Axon works | Axon (excellent) |
| **CLI framework** | Typer/Click | Cobra (gold standard) | Commander.js/oclif | Clikt | Spring Shell / Picocli |
| **Agent frameworks** | PydanticAI, LangGraph | None mature | Mastra | None | None |
| **Deployment** | Needs Python runtime | Single binary | Needs Node | Needs JVM | Needs JVM + Axon Server |
| **Code reuse** | High (OllamaClient) | Partial (Go experience) | None | None | None |
| **Single-dev maintainability** | Good | Excellent | Moderate | Good | Moderate |

#### Per-language narrative:

**Python** — The richest ecosystem by far. Crawl4AI is Python-native (also REST API, but native gives you more control). Existing OllamaClient handles connection pooling, error classification, in-flight tracking, call logging. Pydantic v2 + mypy strict mode close much of the type safety gap. The weakness: refactoring is harder than in compiled languages, and async has sharp edges (colored functions, forgetting `await`). The `eventsourcing` library (v9.5.3) gives you proper aggregates, snapshots, and process managers on SQLite.

**Go** — The strongest "systems" choice. Single-binary deployment, goroutines for concurrency (no colored functions problem), official Ollama Go client. Colly is a mature scraper. Cobra is the gold standard CLI framework. The weakness: no event sourcing frameworks, less expressive types (no sum types/sealed classes), the LLM-agent ecosystem is Python/TS-centric. Would need to build more from scratch.

**TypeScript** — The dark horse. Firecrawl's primary SDK is TypeScript. Emmett is a genuine event sourcing library (composition-over-magic, PostgreSQL). **Mastra** is a purpose-built AI agent framework with workflows, memory, streaming, and tracing. An open-source deep-research implementation already exists in TypeScript (Nutlope/deep-research). Claude Code itself is TypeScript. The weakness: npm dependency churn, Node isn't traditional for system tools, no existing code to reuse from the project.

**Kotlin** — Best type system + async model combination (sealed classes + coroutines). Axon works natively. The weakness: third language in the project (Python + Go already), no scraper SDKs, smallest community for niche problems.

**Java + Axon** — Axon is architecturally impressive but solves distributed microservice coordination problems that don't exist here. A single-developer CLI tool doesn't need Axon Server, sagas with Quartz scheduling, or DDD aggregates. The research found consensus: "If your app is a glorified Excel sheet, Axon is not the superhero you need." The patterns Axon teaches (events, commands, projections) are valuable regardless of whether you adopt the framework. The weakness: 10-20x boilerplate, JVM startup latency, no scraper SDKs, 4-8 weeks to MVP.

**Rust** — Solves performance/memory problems that don't exist here. 6-10 weeks to MVP. Not recommended.

#### The Crawl4AI factor:

The language research noted that if you choose Crawl4AI as the primary scraper, Python becomes more natural. But this is softer than it sounds: Crawl4AI exposes a Docker REST API, so any language can call it. The advantage of Python-native Crawl4AI is finer-grained control (custom extraction strategies, hook into the pipeline, use advanced features like adaptive selectors). Via REST API, you get scrape/crawl/search but lose the deeper integration.

---

### Part 4: State Management Analysis

Research found a clear spectrum from simple to complex:

| Approach | Implementation cost | Replay | Knowledge queries | Graph relationships | Upgrade path |
|----------|-------------------|--------|------------------|--------------------|----|
| **Flat markdown files** | Near zero | Manual | grep/ripgrep | None | Add JSONL log |
| **JSONL event log** | Trivial | Yes (replay full log) | grep + jq | None | Add SQLite |
| **SQLite (events + state)** | Low | Yes | SQL queries | Via node/edge tables | Add `eventsourcing` lib |
| **Python `eventsourcing` lib** | Moderate | Yes + snapshots | Via projections | Build on top | Add graph DB |
| **Axon Framework** | High | Excellent | Via projections | Build on top | Already at ceiling |
| **Neo4j / Graphiti** | Moderate-High | Via event source | Graph queries | Native | Production-grade |

**The research consensus:** Start with JSONL event log + SQLite from day one. JSONL gives you an audit trail and replay capability at near-zero cost (the project already uses this pattern for `calls.jsonl`). SQLite gives you indexed queries and a lightweight graph (node/edge tables with recursive CTEs for traversal).

**The graph question:** Research findings link to each other — page A links to page B, topic X appears on pages A and C, tool Y is recommended by sources B and E. Flat files lose these connections. But Neo4j is heavy. The sweet spot: SQLite with `nodes(id, type, data)`, `edges(source, target, type, data)`, and recursive CTEs for graph traversal. Adequate for hundreds to thousands of nodes. Graduate to Graphiti/Neo4j if needed.

**Temporal knowledge (Graphiti/Zep):** Every fact has a validity window — "Page X claimed Y on date Z." This is interesting for a research tool where information changes over time, but it's a Layer 2 concern, not MVP.

---

### Part 5: Existing Research Tool Architectures

#### Tool Comparison

| Tool | Language | Architecture | Local Model Support | Key Innovation |
|------|----------|-------------|-------------------|----------------|
| **GPT-Researcher** | Python | Multi-agent (7 agents: Chief Editor, Researcher, Editor, Reviewer, Revisor, Writer, Publisher) | Limited | Parallel per-section research with reviewer-revisor loops |
| **STORM (Stanford)** | Python/DSPy | Two-stage (Pre-writing + Writing). Perspective-guided question asking | Via litellm | Simulated conversation between writer and topic expert; multi-perspective synthesis |
| **Co-STORM** | Python/DSPy | STORM + human-in-the-loop via discourse protocol | Via litellm | Dynamic mind map; moderator agent + human observation/steering |
| **dzhng/deep-research** | TypeScript | Minimalist recursive loop (~500 lines) | Local LLM endpoints | Inverted pyramid: breadth halves at each depth level |
| **LangChain open_deep_research** | Python | LangGraph state machine, multi-model composition | Configurable | Different LLMs for different roles (summarize vs research vs compress) |
| **Jina DeepResearch** | TypeScript | Agentic loop with token budget control | **Ollama/LMStudio** | Most sophisticated stopping: token budget + quality eval + anti-rabbit-hole |
| **Local Deep Research** | Python | Ollama + SearXNG, persistent knowledge library | **Primary design (Ollama)** | Encrypted cross-session knowledge compounding; 20+ search sources |
| **Mastra** | TypeScript | Agent framework with graph-based workflows | Via providers | Suspend/resume for human-in-the-loop; 22K stars, YC W25 |
| **CrewAI** | Python | Role-based agents + tasks + crews | Via providers | Sequential/Hierarchical/Flow execution models |
| **Farfalle** | Python+Next.js | Perplexity alternative | **Ollama** | Full local stack possible with SearXNG |
| **Khoj** | Python | Personal AI with research automation | **Local (llama3, qwen, gemma, mistral)** | Full local deployment |
| **Morphic** | Next.js | Perplexity-like with generative UI | **Ollama** | Three modes: Quick, Planning, Adaptive |

#### Architecture Patterns

**Stopping criteria** — Three dominant patterns:
1. **Depth counter** (dzhng, GPT-Researcher): Predetermined recursion depth. Simple, predictable, blind to quality.
2. **Token/time budget** (Jina): Continue until budget exhausted, then force synthesis. Adaptive.
3. **Quality evaluation** (Jina, STORM): Answer evaluated against criteria. Only stops when it passes. Most sophisticated but needs capable evaluator.
Most production systems combine depth/budget as hard ceiling + quality eval as early exit.

**Depth control:**
- **Inverted pyramid** (dzhng): Start broad, breadth halves each level. Elegant and simple.
- **Tree expansion** (GPT-Researcher): Outline → sections → independent parallel research per section.
- **Sub-question decomposition** (Jina): Reflect generates sub-questions; each becomes its own thread.

**Anti-rabbit-hole mechanisms:**
- Jina: Validates new content/URLs actually emerge; disables unproductive action types; hostname constraints.
- STORM: Perspective diversity enforced by surveying existing articles first.
- Budget-based: Token/time budgets inherently limit exploration.
- Simple tools (dzhng, Nutlope): **No anti-rabbit-hole** — rely entirely on depth counters.

**Deduplication:**
- URL dedup: Tracked visited URLs (Set or normalized URL map) — universal.
- Content dedup: Ranking scores (Jina), outline-based organization (STORM).
- **No tool does semantic deduplication** (recognizing differently-worded facts say the same thing). This is a gap.

**Conflict handling:**
- STORM: Multi-perspective synthesis naturally accommodates conflicts.
- GPT-Researcher: Reviewer-revisor cycle implicitly resolves.
- Most tools: Left to final synthesis LLM call. **No explicit conflict detection.**

#### State Management Across Tools

| Tool | Visited URLs | Pending Work | Knowledge Store | Persistence |
|------|-------------|--------------|-----------------|-------------|
| dzhng | Array (Set) | Recursion stack | Array of learning strings | In-memory only |
| Jina | Normalized URL map with scores | Gaps queue (sub-questions) | Q&A pairs (allKnowledge) | In-memory + diary |
| STORM | StormInformationTable | Perspective queue | Conversation logs (JSON) | Files on disk |
| GPT-Researcher | Per-agent tracking | Section outline | Per-section summaries | In-memory |
| Local Deep Research | Database | Strategy-driven | SQLCipher encrypted DB + vectors | **Persistent, cross-session** |

#### Local-Model-First Research Tools

**Local Deep Research** (`github.com/LearningCircuit/local-deep-research`) is the standout:
- Specifically designed for local-first operation with Ollama + SearXNG (both in Docker)
- ~95% accuracy on SimpleQA benchmark (with GPT-4.1-mini)
- 20+ search sources (arXiv, PubMed, Semantic Scholar, Wikipedia, SearXNG, GitHub)
- **Personal encrypted knowledge library:** SQLCipher AES-256. Auto-collects valuable sources, indexes and embeds them, enables compounding research across sessions
- Supports CPU-only execution

**Minimum model capability for research tasks:**
- **Structured output** is table stakes for agent loops (Jina explicitly requires it)
- 7-8B: Viable for extraction, summarization, query generation. Likely fails at complex synthesis
- 14B: Viable for most pipeline stages. Sweet spot for 12GB VRAM
- **Multi-model pipeline is standard:** cheap model for extraction, capable model for synthesis

#### Progressive Autonomy / Human-in-the-Loop

**Existing patterns:**
1. **Approval gates** (Mastra, Plandex): Run one step → show results → ask human → proceed
2. **Observation mode** (Co-STORM): Human watches AI discourse in real time, intervenes when needed
3. **Configurable depth** (most tools): Human sets parameters upfront
4. **Review-revise loops** (GPT-Researcher): AI proposes, reviewer evaluates, could be human-gated
5. **Suspend/resume** (Mastra, Agno): Workflow pauses indefinitely awaiting human input

**Gap: No existing tool does progressive autonomy well.** The "show candidate links, let user choose" pattern is an open design space. Co-STORM and Mastra are closest but not there.

#### Knowledge Accumulation Patterns

- **Most tools are single-session** — knowledge generated, report produced, state discarded
- **Local Deep Research** is the exception: persistent encrypted knowledge library that compounds across sessions
- **Incremental** (Jina, dzhng): Knowledge grows during research
- **Batch** (STORM, GPT-Researcher): Collect everything, synthesize at end
- **Hybrid** (Co-STORM): Incremental mind map during research, batch article at end

#### Search Infrastructure Layer

| Tool | Type | Self-hosted | Cost | Notes |
|------|------|-------------|------|-------|
| **SearXNG** | Metasearch engine | Docker | Free | Consensus local-first search backend. Aggregates multiple engines. No API keys. |
| **Tavily** | Search API for AI | No | Free tier: 1K/mo | Returns RAG-ready context, not just links |
| **Exa** | Neural search | No | Paid | Structured output, deep reasoning mode |
| **Jina Reader** | URL→Markdown | Partial | Free tier: 1M tokens | r.jina.ai/{url} prefix |
| **Firecrawl** | Scraping + search | Partial (AGPL) | Free tier: 500 credits | JS rendering, structured extraction |

**SearXNG** is particularly relevant — it's the search layer that Local Deep Research, Farfalle, and others use for local-first operation. Docker-deployable, no API keys, privacy-preserving.

#### Key Takeaways for This Project

1. **Local Deep Research** is the closest existing tool to the vision. Study it as a reference.
2. **Jina's token budget + quality eval + anti-rabbit-hole** is the most robust research loop pattern.
3. **dzhng's inverted pyramid** (broad→narrow) is elegant for depth control.
4. **Multi-model pipeline is standard** — cheap 7B for extraction, 14B for synthesis. Matches existing tier strategy.
5. **SearXNG** is the consensus local-first search backend (Docker, free, no API keys).
6. **Progressive autonomy is an open design space** — no tool does it well. Differentiator opportunity.
7. **Knowledge persistence across sessions is rare** — most tools are stateless. Another differentiator.
8. **Structured output is table stakes** — Qwen models support this via Ollama's `format` parameter.

---

### Part 6: How Decisions Interact

```
Scraping Backend ──────────────────────┐
  All expose REST APIs                 │
  Crawl4AI strongest self-hosted       │
  Pluggable by design                  │
                                       ▼
Language ◄────── Ecosystem matters ─── but not blocked
  │              Crawl4AI native: Python
  │              Firecrawl primary: TypeScript
  │              Ollama official: Go, Python
  │              Event sourcing: Java (Axon), TS (Emmett), Python (eventsourcing)
  │              Agent framework: TS (Mastra), Python (LangGraph/PydanticAI)
  │
  ▼
State Management ←── Language shapes options
  JSONL + SQLite works in any language
  Python eventsourcing lib → Python
  Emmett → TypeScript
  Axon → Java/Kotlin
  │
  ▼
Autonomy Model ←── Depends on integration needs
  MCP tools → Python (existing MCP server) or separate server
  Skill → Claude Code plugin system
  Standalone CLI → any language
```

**The key dependency:** If you want Crawl4AI native integration (not just REST API), that pulls toward Python. If you want Emmett event sourcing + Mastra agent framework, that pulls toward TypeScript. If you want the simplest deployment and best concurrency model, that pulls toward Go. Java+Axon doesn't have a strong pull from any direction.

---

### Part 7: Viable Paths Forward

Rather than recommending one path, here are the three strongest combinations:

#### Path A: Python-native
- **Language:** Python (uv, Pydantic, Typer)
- **Scraper:** Crawl4AI native + Firecrawl as pluggable alt
- **State:** JSONL event log + SQLite (upgrade to `eventsourcing` lib if needed)
- **Ollama:** Reuse/adapt existing OllamaClient
- **Agent framework:** PydanticAI or LangGraph
- **Pros:** Fastest to MVP, richest ecosystem, code reuse, Crawl4AI native integration
- **Cons:** Weaker type safety, async has sharp edges, deployment needs runtime
- **Time to MVP:** ~1-2 weeks

#### Path B: TypeScript ecosystem
- **Language:** TypeScript (Node, Zod, Commander.js or oclif)
- **Scraper:** Firecrawl TS SDK (primary) + Crawl4AI via REST
- **State:** Emmett event sourcing (PostgreSQL) or JSONL + SQLite
- **Ollama:** HTTP client (simple, Ollama API is straightforward)
- **Agent framework:** Mastra (purpose-built for this kind of tool)
- **Pros:** Strongest event sourcing lib (Emmett), AI agent framework (Mastra), existing deep-research reference impl, Firecrawl's primary SDK
- **Cons:** No existing code to reuse, npm churn, Node not traditional for systems tools
- **Time to MVP:** ~1-2 weeks

#### Path C: Go systems approach
- **Language:** Go (Cobra, official Ollama client)
- **Scraper:** Firecrawl Go SDK + Crawl4AI via REST + Colly for direct scraping
- **State:** JSONL event log + SQLite (build event patterns manually)
- **Ollama:** Official Go client
- **Agent framework:** None (build orchestration from scratch)
- **Pros:** Single binary, best concurrency (goroutines), excellent long-term maintainability, no dependency churn
- **Cons:** No event sourcing framework, no agent framework, more to build from scratch, LLM ecosystem is Python/TS-centric
- **Time to MVP:** ~2-3 weeks

#### Path D: Kotlin (if event sourcing is primary concern)
- **Language:** Kotlin (coroutines, Clikt, Axon or manual ES)
- **Scraper:** All via REST APIs
- **State:** Axon or manual event sourcing with coroutines
- **Pros:** Best type system + async combination, event sourcing if Axon is used
- **Cons:** Third language, smallest ecosystem, no scraper SDKs, 2-4 weeks to MVP

#### What I'd deprioritize:
- **Java + Axon:** Solves distributed problems that don't exist. 4-8 week MVP. The patterns are valuable but the framework is overkill.
- **Rust:** No ecosystem advantage, 6-10 week MVP. Performance doesn't matter here.
- **Hybrid:** Maintenance overhead of multi-language outweighs "best of each" for a single developer.

---

### Part 8: The Naming Question

You noted "research-agent" might not stay an agent, "web-research" feels incomplete, "ai-web-research" is missing something. What's missing is the **accumulation and iteration** aspect — this isn't a one-shot search, it's an ongoing investigation.

Some options that capture different aspects:

| Name | What it evokes | Concern |
|------|---------------|---------|
| **forager** | Iteratively finds, selects, gathers useful things | Might be too metaphorical |
| **recon** | Reconnaissance — systematic investigation | Military connotation |
| **probe** | Systematic investigation, sends out probes | Could work |
| **atlas** | Maps knowledge, reference compilation | Static-sounding |
| **inquiry** | Systematic investigation | Generic |
| **web-scout** | Scouts the web, brings back findings | "scout" is overused in tech |
| **deep-fetch** | Iterative deepening + fetching | Too similar to deep-research |
| **curator** | Curates and organizes knowledge | Passive-sounding |
| **surveyor** | Surveys a landscape systematically | Maps well to the function |

No need to decide now — the name can evolve as the tool's identity solidifies.

---

### Part 9: What Changes With the Full Picture

The existing architecture research (Part 5) significantly reshapes the analysis:

**1. Local Deep Research already exists and is close to the vision.**
It's Ollama + SearXNG, persistent knowledge library, 20+ sources. The question shifts from "build from scratch" to "build on top of / differentiate from Local Deep Research." Key gaps in Local Deep Research that the new tool could fill: progressive autonomy (HITL steering), pluggable scrapers, focus-directed extraction, and knowledge graph relationships.

**2. SearXNG is a critical missing piece.**
The initial analysis focused on scrapers (Crawl4AI, Firecrawl) but missed that *search* is equally important. SearXNG (self-hosted metasearch, Docker, free, no API keys) is the consensus local-first search backend. This adds another Docker service but fills a real need.

**3. The architecture pattern is clearer.**
Combining the best of existing tools:
- **Jina's token budget + quality eval** for stopping criteria (not just depth counters)
- **dzhng's inverted pyramid** for depth/breadth control
- **Local Deep Research's persistent knowledge library** for cross-session compounding
- **Mastra's suspend/resume** for progressive autonomy
- **STORM's multi-perspective approach** for avoiding narrow focus
- **Anti-rabbit-hole mechanisms** (validate new content emerges, hostname constraints)

**4. Multi-model pipeline is validated.**
Using 7B for extraction/queries and 14B for synthesis/evaluation is standard practice. This directly maps to existing persona tiers.

**5. The differentiators for the new tool would be:**
- Progressive autonomy (no existing tool does this well)
- Pluggable scraper backends (most tools hardcode one search/scrape backend)
- Focus-directed extraction (extract content, optionally guided by focus — not hardcoded comparison)
- Local-model-first with frontier model as optional escalation
- Knowledge graph relationships (not just flat storage)

### Part 10: Multi-Agent Architecture Analysis

*(See `web-research-tool-user-notes.md` for raw user thinking; `web-research-tool-vision.md` for synthesized vision.)*

#### Use Cases → Requirements

| Use Case | Entry Point | Processing | Output | Persistence Need |
|----------|-------------|-----------|--------|-----------------|
| **1. Direct research** | Human gives URL(s)/topic | Iterative fetch→extract→deepen | Report/findings | Session state |
| **2. Claude Code delegate** | Claude Code invokes tool | Autonomous pipeline, results to files | Structured findings Claude can consume | Cross-session knowledge |
| **3. Conversational post-research** | Human or Claude queries past research | Query accumulated knowledge | Answers grounded in sources | Knowledge graph + memory |

Use case 2 inverts the typical pattern — Claude Code is the *caller*, delegating research to a local-model pipeline to save its own context/tokens. Pattern B (frontier-first, delegates down) applied to research.

#### Agent Roles (not necessarily separate models/processes)

| Agent | Role | Domain (DDD bounded context) | Model Tier |
|-------|------|-----|------------|
| **Conductor** | Research manager — decides what tools needed, iterates until done | Research strategy | 14B (needs planning ability) |
| **Dispatcher** | Pipeline builder + executor — knows how to call tools, routes data | Tool integration | Could be deterministic code, or 7-8B |
| **Auditor** | Sufficiency reviewer — is the research enough? | Quality assessment | 14B (needs evaluation ability) |
| **Lens** | Context proxy — sifts through results for Conductor | Knowledge retrieval | 7-8B (focused extraction) |

#### Strengths of the Design

1. **Dispatcher as language-flexibility layer** — tools behind REST APIs can be in any language. Language decision applies only to orchestration layer.
2. **Context proxy (Lens)** — practical pattern for local models with limited context. Avoids loading full research output into the manager's context.
3. **Decreasing "more" signal** — formalizes Jina's token budget approach. Configurable, prevents loops.
4. **Pipeline from historical data** — log which patterns worked → improve selection over time.
5. **DDD agent modeling** — same-domain agents share model (no swap), cross-domain justifies swap + data translation.

#### Concerns and Trade-offs

1. **Context swapping cost** — model unload/load is 2-10s. Must be net-positive vs. focused context advantage.
2. **Tool calling by local models** — benchmarks showed this is hard for 7-8B. Options: structured routing (if-else), template pipelines, hybrid (Claude decides pipeline, local executes).
3. **Over-engineering risk** — MVP should collapse Conductor + Dispatcher into one pipeline. Auditor as a simple prompt. No Lens until context pressure is real.

#### MVP Path

| Phase | Agents Active | What Changes |
|-------|--------------|-------------|
| MVP | Conductor+Dispatcher collapsed | Single pipeline script |
| +Review | +Auditor | Sufficiency check prompt added |
| +Pipeline | Conductor, Dispatcher split out | Plugin architecture, parallelization |
| +Knowledge | All + persistence | SQLite graph, cross-session |
| +Context mgmt | +Lens | Model-per-domain, DDD boundaries |
| +Learning | All + feedback loop | Historical pipeline data, distillation |

#### Testing Strategy

| Level | Determinism | Strategy |
|-------|-------------|----------|
| **Unit** | Deterministic | Mocked HTTP, fixed model outputs |
| **Integration** | Semi-deterministic | Known fixtures, property-based ("contains X") |
| **System** | Non-deterministic | Frontier judgment as optional evaluator |

**Principles:** Extract deterministic from non-deterministic. Accept non-determinism backed by lower tests. Well-tested units → trust at integration level.

### Remaining Open Questions

- Should this build on Local Deep Research (fork/extend) or be a new implementation informed by it?
- Is Mastra (TypeScript) worth adopting for its suspend/resume + workflow engine, or can the same pattern be built simply?
- How does the tool integrate with Claude Code? (MCP tool? Skill? Standalone CLI that Claude calls?)
- Naming still unresolved — identity depends on how it differentiates from existing tools
- Firecrawl cloud credits vs self-hosted Crawl4AI vs SearXNG — which combination for the default stack?
- Can 7-8B models do reliable tool calling / pipeline routing? Or must that be deterministic code?
- Where does prompt enrichment (Agent A enriching user query before pipeline) sit?
- How does model swapping latency affect real-world usability?
<!-- /ref:analysis-web-research -->
