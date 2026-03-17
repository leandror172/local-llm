# Session 44 Discussion: Web Research Tool Architecture

*Raw conversation flow, 2026-03-16. Claude's analysis in response to user's architecture vision.*
*For user's raw thinking, see `web-research-tool-user-notes.md`. For synthesized vision, see `web-research-tool-vision.md`.*

---

## Claude's Response to User Vision

### Use Cases → Architectural Requirements

You identified three increasingly sophisticated use cases:

| Use Case | Entry Point | Processing | Output | Persistence Need |
|----------|-------------|-----------|--------|-----------------|
| **1. Direct research** | Human gives URL(s)/topic | Iterative fetch→extract→deepen | Report/findings | Session state |
| **2. Claude Code delegate** | Claude Code invokes tool | Autonomous pipeline, results to files | Structured findings Claude can consume | Cross-session knowledge |
| **3. Conversational post-research** | Human or Claude asks questions about past research | Query accumulated knowledge | Answers grounded in sources | Knowledge graph + memory |

Use case 1 is the MVP. Use case 2 is the first real differentiator (no existing tool does this well). Use case 3 is the payoff of persistent knowledge accumulation.

**Insight: Use case 2 is particularly interesting because it inverts the typical pattern.** Most research tools have a human at the keyboard. Here, Claude Code is the caller — it delegates research to a local-model-powered pipeline to avoid burning its own context and tokens. This is the project's Pattern B (frontier-first, delegates down) applied to research. The tool becomes another "local specialist" like the coding personas, but for web research.

---

### The Multi-Agent Architecture — User's Thinking Organized

The user's agent breakdown maps to distinct **roles**, not necessarily distinct processes or models:

```
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                     │
│                                                          │
│  Conductor (Research Manager)                            │
│  - Receives initial query                                │
│  - Decides what tools/pipelines needed                   │
│  - Iterates until criteria met                           │
│  - Can optionally enrich the initial prompt              │
│  - Delegates sifting to Lens (context proxy)             │
│    to avoid polluting own context                        │
└─────────┬───────────────────────────────────────────────┘
          │ delegates to
          ▼
┌─────────────────────────────────────────────────────────┐
│  TOOL LAYER                                              │
│                                                          │
│  Dispatcher (Pipeline Builder + Executor)                │
│  - Knows available tools and how to call them            │
│  - Builds pipelines: what to call, in what order         │
│  - Decides parallelization (from config + history)       │
│  - Routes data between tools                             │
│  - Can be layered:                                       │
│    - Integration layer: how to call specific tools       │
│    - Pipeline layer: what sequence/parallel strategy     │
│                                                          │
│  Tools (plugins, swappable, potentially multi-language): │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ SearXNG  │ │ Crawl4AI │ │Firecrawl │ │ Ollama    │  │
│  │ (search) │ │ (scrape) │ │ (scrape) │ │(extract)  │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└─────────┬───────────────────────────────────────────────┘
          │ results flow to
          ▼
┌─────────────────────────────────────────────────────────┐
│  REVIEW LAYER                                            │
│                                                          │
│  Auditor (Sufficiency Reviewer)                          │
│  - First pass: is the research enough?                   │
│  - Should more be explored? Different tools?             │
│  - "More" signal decreases iteratively (avoid loops)     │
│  - Configurable thresholds                               │
│  - Produces notes alongside results                      │
└─────────┬───────────────────────────────────────────────┘
          │ approved results
          ▼
┌─────────────────────────────────────────────────────────┐
│  KNOWLEDGE LAYER                                         │
│                                                          │
│  Storage + Integration                                   │
│  - Results stored (raw + extracted)                      │
│  - Knowledge integration queued: does new data           │
│    connect to existing knowledge?                        │
│  - Graph relationships created                           │
│  - Summarization with source pointers                    │
│  - Available for post-research queries                   │
└─────────────────────────────────────────────────────────┘
```

### What's Strong in This Design

**1. Dispatcher as language-flexibility layer.** This is a key insight. If Dispatcher knows how to call tools via their APIs (REST, CLI, MCP), then tools can be in any language. The decision about "what language do we build in" applies only to the orchestration/agent layer, not to the tools themselves. A SearXNG Docker container, a Crawl4AI Docker container, and Ollama are all just HTTP endpoints. You don't need them in the same language.

**2. Context proxy (Lens).** Avoiding context pollution is a real problem with local models. A 7B model with 8K context can't hold a research session's worth of findings AND reason about them. Having a separate "sifter" that reads results and answers specific questions from Conductor is a practical pattern. It's essentially RAG without the R — you're querying your own research output.

**3. Decreasing "more" signal.** This is Jina's approach formalized. Their token budget naturally decreases the "explore more" pressure. The user's framing as a configurable, iteratively-decreasing signal is more explicit and tunable.

**4. Pipeline decisions from historical data.** If the system logs which pipeline patterns worked for which types of queries (this relates to the calls.jsonl verdict pattern from the main project), it can improve pipeline selection over time.

### Concerns and Trade-offs

**1. Context swapping cost.** The user flagged this themselves. Every agent swap means:
- Unload current model from VRAM (if different model)
- Load new model (~2-5s for 7B, ~5-10s for 14B on the hardware)
- Construct new prompt with relevant context
- The new agent has NO memory of what the previous one did (except what's explicitly passed)

For this to be net-positive, the focused context advantage must outweigh the swapping overhead. The DDD insight applies here — same-domain agents should share a model (no swap), cross-domain transitions justify swaps.

**2. Tool calling by local models.** The user correctly identified this as a known weakness. Benchmarks showed tool calling is hard for local models. This means Dispatcher might need to be the most capable model (14B?), or the tool-calling logic might need to be more structured than "LLM decides what to call." Options:
- **Structured routing**: if-else/match on query type rather than LLM tool selection
- **Template pipelines**: predefined sequences for common research patterns, LLM only decides parameters
- **Hybrid**: Claude (frontier) decides the pipeline, local models execute the steps

**3. Over-engineering risk.** The user flagged this too. The 4-agent architecture is the long-term vision. The MVP might be:
- Conductor + Dispatcher collapsed into one pipeline script
- Auditor as a simple quality check prompt
- No Lens (context proxy) until context pressure is real
- Knowledge layer as JSONL + markdown files

---

### The DDD Insight

> "domain driven design thought as agent/model modeling" just occurred to me, and makes sense

This is genuinely significant. Making it explicit:

In DDD, you have **bounded contexts** — each domain has its own model, language, and rules. The same entity (e.g., "Customer") means different things in different contexts (billing vs. support vs. shipping).

Map this to agents:

| DDD Concept | Agent Equivalent |
|-------------|-----------------|
| Bounded context | Agent's domain (research management, tool execution, review) |
| Ubiquitous language | The prompt/system message that defines what concepts mean to this agent |
| Context map | How agents pass data between domains (what's translated, what's shared) |
| Anti-corruption layer | The adapter between tools with different data formats |
| Aggregate root | The primary entity each agent manages (research session, pipeline execution, knowledge entry) |
| Domain event | Something that happened (URLFetched, FactExtracted, ReviewCompleted) → event sourcing connection |

**The practical implication:** When two agents are in the same bounded context (same domain), use the same model — no swap. When crossing context boundaries, that's where model swaps are justified and where explicit data translation (anti-corruption layer) is needed.

**This DDD-as-agent-modeling framing also clarifies the language question.** In DDD, different bounded contexts can use different technologies (polyglot persistence, different services). The same applies here: Dispatcher's "integration layer" could call tools written in any language, as long as the context boundary (REST API, MCP, CLI) is clean. You don't need one language to rule them all — you need clean interfaces between domains.

---

### Testing Strategy

The user's three-tier approach:

| Level | What | Determinism | Strategy |
|-------|------|-------------|----------|
| **Unit** | Individual tool calls, parsers, data transformations | Deterministic | Standard unit tests, mocked HTTP responses |
| **Integration** | Tool chains, agent handoffs, pipeline execution | Semi-deterministic | Known test fixtures (specific URL → expected extraction), snapshot testing |
| **System** | Full research session end-to-end | Non-deterministic | Frontier-model judgment as optional evaluator, property-based testing ("output mentions X", "found at least N sources") |

The principle of **extracting the deterministic from the non-deterministic** applies at every boundary:
- **Deterministic:** "Given this HTML, extract these facts" (with fixed model + temperature 0)
- **Semi-deterministic:** "Given this page, the extraction should contain these keywords" (property-based)
- **Non-deterministic:** "Research topic X and produce a useful report" (frontier evaluation)

Using frontier judgment for high-level test evaluation is a good match — it's the same "evaluator should be the strongest model" principle from Layer 4.

---

### What This Means for the MVP Path

The "longshot" architecture has clear layers that map to an iterative build:

| Phase | What | Agents Involved |
|-------|------|----------------|
| **MVP** | Single pipeline: query → search → fetch → extract → store | Conductor + Dispatcher collapsed. No Auditor. Files as storage. |
| **+Review** | Add sufficiency check and iteration | Auditor as a prompt. Decreasing "more" signal. |
| **+Pipeline flexibility** | Dispatcher layer, multiple tool backends, parallelization | Dispatcher split out. Plugin architecture for scrapers. |
| **+Knowledge** | Graph relationships, cross-session persistence, post-research queries | Knowledge layer. SQLite graph. |
| **+Context management** | Lens proxy, model-per-domain routing | DDD context boundaries. Model swapping. |
| **+Learning** | Historical pipeline data, improved routing, distillation | Feeds back into Layer 7 (memory/learning) of the main project. |

The MVP tests the core hypothesis: **can a local-model-powered pipeline produce useful web research output?** Everything else layers on top once that's validated.
