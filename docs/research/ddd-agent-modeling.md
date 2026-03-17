<!-- ref:ddd-agent-modeling -->
# DDD as Agent/Model Modeling

*Session 44 fork (Angle B). Formalizing "domain driven design thought as agent/model modeling."*
*Origin: user insight during web research tool architecture discussion.*

---

## The Core Claim

Domain-Driven Design (DDD) solved a fundamental software architecture problem: **how to decompose complex domains into manageable pieces with clean boundaries, so that each piece can evolve independently while the whole system remains coherent.**

Multi-agent AI systems face the **same structural problem**: where to draw agent boundaries, how to translate data between agents, when to use one agent vs. many, how to avoid context pollution, when model swaps are justified.

The mapping is not metaphorical — it's **structural**. DDD patterns directly inform agent architecture decisions.

---

<!-- ref:ddd-strategic-patterns -->
## Strategic Patterns (System-Level)

### 1. Bounded Context → Agent Domain

**DDD:** A bounded context is a boundary within which a particular model (domain model) is defined and applicable. The same word ("order") means different things in different contexts (sales vs. shipping vs. billing).

**Agent equivalent:** Each agent operates within a **domain** where its system prompt, vocabulary, and rules apply. An "extraction agent" understands web content structure; a "review agent" understands quality criteria; a "tool agent" understands API contracts. The word "result" means different things to each.

**Practical implication:**
- Don't make one agent do everything — it will conflate domain concepts
- Each agent's system prompt IS its domain model — keep it focused
- When an agent needs to reason about two very different domains, that's a signal to split

**Resource implication (local models):**
- Same domain → same model, same prompt session (no swap)
- Different domain → potentially different model, justified swap
- The cost of a swap (2-10s VRAM reload + lost conversational state) must be weighed against the benefit of focused context

### 2. Context Map → Inter-Agent Data Contracts

**DDD:** A context map shows how bounded contexts relate to each other. Key relationship types:
- **Shared Kernel:** Two contexts share a common subset (tightly coupled)
- **Customer-Supplier:** One context provides data that another consumes (one-way dependency)
- **Conformist:** Consumer adopts supplier's model as-is (no translation)
- **Anti-Corruption Layer (ACL):** Consumer translates supplier's model into its own (loose coupling)
- **Published Language:** Shared interchange format both contexts agree on
- **Open Host Service:** Supplier exposes a well-defined protocol

**Agent equivalent:**

| DDD Relationship | Agent Relationship | When to Use |
|-----------------|-------------------|-------------|
| **Shared Kernel** | Two agents share state directly (same DB/file) | Tightly coupled agents in same domain; e.g., Agent A and A2 share the research session state |
| **Customer-Supplier** | Agent B consumes Agent Tool's output | One agent produces, another evaluates. Output format defined by producer. |
| **Conformist** | Agent consumes tool output as-is | When the tool's output format is good enough. E.g., Crawl4AI returns markdown, agent uses it directly. |
| **Anti-Corruption Layer** | Translation layer between agents | When tool output doesn't match agent's domain model. E.g., translating SearXNG JSON into the research pipeline's internal format. |
| **Published Language** | Shared JSON schema / structured output format | When multiple agents need to exchange structured data. The `format` param in Ollama API acts as a published language. |
| **Open Host Service** | REST API / MCP tool interface | When a tool or agent exposes a stable interface. All Docker services (SearXNG, Crawl4AI, Ollama) are Open Host Services. |

**Practical implication:**
- Define the data contracts BEFORE building agents
- Use structured output (JSON schemas) as the "published language" between agents
- Anti-corruption layers are where adapters live — these can be deterministic code, not LLMs
- The more loosely coupled agents are, the easier to swap models/tools

### 3. Subdomain Classification → Agent Criticality

**DDD:** Subdomains are classified by their strategic importance:
- **Core Domain:** What makes your system unique. Invest the most here.
- **Supporting Domain:** Necessary but not differentiating. Build simply.
- **Generic Domain:** Solved problems. Use off-the-shelf.

**Agent equivalent:**

| Subdomain Type | Agent Example | Model Strategy |
|---------------|--------------|----------------|
| **Core** | Research orchestration (Agent A), quality review (Agent B) | Best available model (14B). Custom prompts. Most iteration. |
| **Supporting** | Extraction, summarization, query generation | Adequate model (7-8B). Standardized prompts. |
| **Generic** | Tool calling, data transformation, file I/O | Deterministic code. No LLM needed. |

**Practical implication:**
- Not every agent needs an LLM — generic subdomain agents can be pure code
- Core domain agents deserve the most capable model and the most refined prompts
- Supporting agents are where local models shine (cheap, fast, "good enough")
- This directly maps to the multi-model pipeline pattern: 14B for core, 7B for supporting, code for generic

### 4. Ubiquitous Language → System Prompt as Domain Model

**DDD:** Within a bounded context, everyone (developers, domain experts, code) uses the same language. Terms are precisely defined. Ambiguity is eliminated.

**Agent equivalent:** The system prompt IS the ubiquitous language. It defines:
- What concepts exist in this agent's world
- What each concept means (a "source" is a URL + metadata + reliability score)
- What operations are valid (extract, summarize, score — NOT compare, architect, decide)
- What the agent should NOT do (explicit boundaries)

**Practical implication:**
- A well-crafted system prompt is a domain model, not just instructions
- When the same word means different things to different agents, you NEED separate prompts (separate bounded contexts)
- Prompt engineering IS domain modeling — the same discipline applies
- Few-shot examples in the prompt are like test cases for the domain model

---

<!-- /ref:ddd-strategic-patterns -->

<!-- ref:ddd-tactical-patterns -->
## Tactical Patterns (Agent-Level)

### 5. Aggregate → Agent's Unit of Consistency

**DDD:** An aggregate is a cluster of domain objects treated as a single unit for data changes. Changes to the aggregate go through the aggregate root, which enforces invariants.

**Agent equivalent:** Each agent manages a primary entity:
- Agent A → Research Session (the session is the aggregate root)
- Agent Tool → Pipeline Execution (one execution is atomic)
- Agent B → Review Decision (one review cycle is atomic)
- Knowledge Layer → Knowledge Entry (one fact + its relationships)

**Practical implication:**
- An agent should manage ONE primary entity at a time
- Consistency is maintained within the agent's scope, not across agents
- "Eventual consistency" between agents is natural — Agent B reviews results AFTER Agent Tool finishes, not during
- This maps to event sourcing: each aggregate produces events

### 6. Domain Events → Event Sourcing for Agent Communication

**DDD:** Domain events represent something that happened in the domain. They are facts, immutable, and trigger side effects in other contexts.

**Agent equivalent:** Agent actions produce events:
```
ResearchRequested(query, focus, timestamp)
  → SearchExecuted(query, engine, results_count)
    → PageFetched(url, content_hash, source)
      → FactsExtracted(url, facts[], links[])
        → SufficiencyReviewed(verdict, score, notes)
          → ResearchCompleted(session_id, findings_count)
```

**Practical implication:**
- Events are the communication mechanism between agents
- Events are stored (JSONL) — this gives you audit trail, replay, and debugging for free
- An agent doesn't need to know WHO will handle an event, only that it happened
- This decouples agents — you can add new consumers without modifying producers
- Replay: re-run extraction with better prompts, without re-fetching

### 7. Repository → Knowledge Store

**DDD:** A repository provides the illusion of an in-memory collection of domain objects, hiding the storage mechanism.

**Agent equivalent:** The knowledge store is a repository:
- Agent A asks "what do I know about topic X?" — doesn't care if it's SQLite, files, or Neo4j
- Agent A2 (context proxy) IS a repository accessor — it reads the store and returns relevant items
- The storage mechanism can evolve (files → SQLite → graph DB) without changing agent logic

### 8. Saga / Process Manager → Multi-Step Agent Orchestration

**DDD:** A saga (or process manager) coordinates a long-running business process across multiple aggregates/services, reacting to events and issuing commands.

**Agent equivalent:** Agent A IS a saga/process manager:
- Reacts to events (search completed, extraction done, review verdict)
- Issues commands (search for X, fetch URL Y, review these results)
- Maintains state across steps (what's been searched, what's pending)
- Handles compensation (if a fetch fails, try alternative source)
- Can be interrupted and resumed (progressive autonomy — human takes over mid-saga)

**Practical implication:**
- The orchestration agent doesn't DO the work — it COORDINATES
- Its context should contain the process state, not the content being processed
- This is why Agent A delegates content sifting to Agent A2 — the saga manager shouldn't load raw data
- Saga state should be persisted — enables resume after interruption (model swap, session end, human break)

---

<!-- /ref:ddd-tactical-patterns -->

<!-- ref:ddd-anti-patterns -->
## Anti-Patterns (What NOT to Do)

### 1. God Agent (= God Object)
One agent that does everything. Symptoms: huge system prompt, conflated concerns, needs the most context, makes all decisions. Just like a God Object in code, this defeats the purpose of decomposition.

### 2. Anemic Agents (= Anemic Domain Model)
Agents that are just pass-throughs — they receive data, forward it to a tool, and return the result without any domain logic. If an agent adds no judgment, reasoning, or transformation, it shouldn't be an agent — it should be a function call.

### 3. Chatty Agents (= Chatty Services)
Too many fine-grained agents that constantly exchange messages. Each exchange has overhead (data serialization, potential model swap, context construction). If two agents always communicate in lock-step, they should probably be one agent.

### 4. Shared Database (= Shared Kernel Overuse)
All agents reading/writing the same state directly. This creates tight coupling and race conditions. Better: events as communication, each agent has its own view of the data.

---

<!-- /ref:ddd-anti-patterns -->

<!-- ref:ddd-split-merge -->
## When to Split vs. Merge Agents

The DDD heuristic for bounded contexts also applies to agents:

**Split when:**
- The agent's system prompt tries to cover two unrelated domains
- The context window is too small for all the knowledge this agent needs
- A different model would be significantly better for part of the work
- You want to test/improve one capability independently

**Merge when:**
- Two agents always run sequentially with no other work in between
- The overhead of data translation between them exceeds the benefit
- They share the same model and same domain
- Splitting doesn't improve output quality

**The litmus test:** Does splitting this agent into two produce BETTER output? Not "is it architecturally purer" — does the actual output improve? If not, don't split.

---

<!-- /ref:ddd-split-merge -->

<!-- ref:ddd-web-research-application -->
## Applying to the Web Research Tool

### Bounded Contexts Identified

| Context | Agent(s) | Core Concepts | Model Tier |
|---------|----------|---------------|------------|
| **Research Strategy** | Agent A (manager) | Sessions, queries, goals, progress, criteria | 14B (planning) |
| **Tool Integration** | Agent Tool (executor) | Pipelines, tools, APIs, routing, parallelization | Code (deterministic) or 7-8B |
| **Content Processing** | Extraction agents | Pages, facts, links, summaries, relevance | 7-8B (focused tasks) |
| **Quality Assessment** | Agent B (reviewer) | Sufficiency, coverage, depth, gaps | 14B (evaluation) |
| **Knowledge Management** | Knowledge layer | Entities, relationships, sources, temporal validity | Code + 7-8B for integration |

### Context Map

```
Research Strategy ──[Customer-Supplier]──→ Tool Integration
       │                                        │
       │                                 [Open Host Service]
       │                                        │
       │                                   ┌────┴────┐
       │                                   │ SearXNG │ Crawl4AI │ Ollama │
       │                                   └─────────┘
       │
       ├──[Shared Kernel]──→ Knowledge Management
       │   (session state)
       │
       └──[Customer-Supplier]──→ Quality Assessment
                                        │
                                 [Published Language]
                                 (JSON: verdict, score, notes)
```

### Model Swap Boundaries

Only THREE justified swap points:
1. **Strategy → Content Processing** (14B → 7-8B): Different capability needed
2. **Content Processing → Quality Assessment** (7-8B → 14B): Evaluation needs stronger model
3. **Any → Tool Integration**: Only if Tool Integration uses an LLM (could be pure code)

Within a context, NO swaps. Agent A and Agent A2 share the Research Strategy context → same model.

---

<!-- /ref:ddd-web-research-application -->

<!-- ref:ddd-generalized -->
## Generalizing Beyond Web Research

This pattern applies to ANY multi-agent system on constrained hardware:

1. **Identify your bounded contexts** — what are the distinct domains of reasoning?
2. **Classify by subdomain type** — core (best model), supporting (adequate model), generic (code)
3. **Define context maps** — how do agents exchange data? What's the published language?
4. **Minimize swap points** — each model swap costs 2-10s + lost conversational state
5. **Use events for communication** — decouples agents, enables replay, provides audit trail
6. **Start merged, split when quality improves** — the anti-premature-optimization of agent design

This is particularly relevant for local model setups where:
- VRAM is limited (one model at a time, or constrained multi-model)
- Model swaps have real latency
- Context windows are small (8-32K vs. frontier 200K)
- The "right model for the right task" principle creates real benefit from specialization

---

<!-- /ref:ddd-generalized -->

## Relationship to Existing Work

- **DDD (Evans, 2003):** Original strategic/tactical patterns. Everything here maps back.
- **Microservices (Newman, 2015):** Bounded contexts as service boundaries. Same decomposition problem.
- **Actor Model (Hewitt, 1973):** Agents as actors with message passing. Events as messages.
- **CQRS/Event Sourcing:** Natural fit — agents produce events, consume projections.
- **The Akka blog post** ("Event Sourcing: The Backbone of Agentic AI") makes a similar argument but from the event sourcing side, not the DDD side.

What's novel here is **applying DDD's strategic patterns (context mapping, subdomain classification) specifically to the problem of multi-agent orchestration on constrained hardware**, where the cost of agent boundaries (model swaps, context loss) is concrete and measurable.

---

## Open Questions

1. **Can the "split when quality improves" heuristic be measured automatically?** Run same task merged vs. split, compare output quality. This would be a benchmark.
2. **How does this interact with fine-tuning?** A fine-tuned 7B for extraction might outperform a general 14B — the subdomain classification changes.
3. **Does this pattern hold for frontier models?** With 200K context and fast inference, the "split for context efficiency" argument weakens. The "split for domain clarity" argument may still hold.
4. **How does this relate to CrewAI/AutoGen/LangGraph agent patterns?** Are they implicitly doing DDD, or are they ignoring it?
<\!-- /ref:ddd-agent-modeling -->
