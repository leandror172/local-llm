<!-- ref:ddd-agent-decisions -->
# DDD Agent Decisions: Anti-Patterns, Split/Merge, and Worked Examples

*Expansion of `ddd-agent-modeling.md` § "Anti-Patterns" and § "When to Split vs. Merge Agents".*
*Session 44 fork (Angle B continued).*

---

## Anti-Patterns — Expanded

### 1. God Agent (= God Object)

**What it looks like:**
- System prompt exceeds 2000 tokens and covers multiple unrelated concerns
- Agent is asked to "research, extract, evaluate, decide, and store"
- Context window fills up because the agent needs to hold everything
- Prompt has sections like "When doing X... but when doing Y... however if Z..."

**Detection heuristics:**
- The system prompt has more than 3 distinct "modes" or "when" clauses
- The agent needs more than one model tier to do its job well (some tasks need 14B, others only 7B)
- You can't describe what the agent does in one sentence without "and"
- Adding a new capability means modifying the agent's core prompt

**Why it happens in agent systems:**
It's the path of least resistance. One agent, one prompt, one model call. No data translation, no state passing, no model swaps. It works — until the context fills up, the prompt becomes contradictory, or the model can't handle the cognitive load.

**Remediation:**
1. List everything the agent does
2. Group by domain (what concepts does each task use?)
3. If groups share fewer than 30% of their concepts, they're separate bounded contexts
4. Split into agents, one per group
5. Define the data contract between them

**Web research tool example:**
A God Agent prompt: "You are a research assistant. Given a topic, search the web using SearXNG, fetch pages using Crawl4AI, extract key facts from the HTML, identify relevant links, score each link's relevance, decide which to follow, track what you've visited, review whether you have enough information, and produce a final summary with source citations."

That's 9 distinct responsibilities. Split into: search/fetch (tool execution), extract/score (content processing), decide/track (orchestration), review (quality), summarize (synthesis).

---

### 2. Anemic Agents (= Anemic Domain Model)

**What it looks like:**
- Agent receives input, calls a tool, returns the tool's output unchanged
- System prompt is mostly "pass this to X and return the result"
- No judgment, transformation, or domain logic
- Could be replaced by a function call

**Detection heuristics:**
- Remove the agent entirely and call the tool directly — does anything change?
- The agent never says "no" or modifies the request
- The agent's output is identical to its input, just reformatted
- There are no few-shot examples because there's nothing to exemplify

**Why it happens:**
Over-application of the "separate concerns" principle. Not every step needs an agent. An HTTP call to SearXNG doesn't need an LLM to decide how to parse the JSON response — that's deterministic code.

**Remediation:**
Replace with a function/adapter. Save the model call for work that actually requires judgment.

**Web research tool example:**
An "Agent Fetch" that receives a URL, calls `crawl4ai.scrape(url)`, and returns the markdown. This is not an agent — it's a function. Make it a function.

The extraction step DOES need an agent because it requires judgment: what's relevant? what's noise? what links matter? That's where the LLM adds value.

---

### 3. Chatty Agents (= Chatty Services)

**What it looks like:**
- Agent X sends partial result to Agent Y, gets feedback, sends revised version, gets more feedback
- Multiple round-trips between agents for a single logical operation
- Each round-trip incurs: context construction + model inference + response parsing + (possibly) model swap

**Detection heuristics:**
- Two agents exchange more than 2 messages for a single task
- The total latency of the exchange exceeds what one agent could do
- The agents' system prompts heavily reference each other's outputs
- Removing one round-trip doesn't degrade output quality

**Cost calculation (on RTX 3060):**
```
Per message between agents (same model):
  Context construction: ~0.5s
  Model inference: 2-30s (depends on output length)
  Response parsing: ~0.1s
  Total: ~3-30s per message

Per message between agents (different models):
  Model unload: ~1-2s
  Model load: ~2-8s (7B: 2s, 14B: 5-8s)
  Context construction: ~0.5s
  Model inference: 2-30s
  Response parsing: ~0.1s
  Total: ~6-40s per message

3 round-trips, different models: 18-120s overhead
```

If one agent could do it in a single 30s call, the chatty design costs 3-4x in latency for no quality gain.

**Remediation:**
- Batch: send all context in one message, get one response
- Merge: if agents always work in lock-step, they're one agent
- Pipeline: if it's truly sequential, make it a pipeline (A output → B input, one direction, no back-and-forth)

**Web research tool example:**
Conductor asks Auditor: "Is this enough?" Auditor: "No, search more about X." Conductor searches. Conductor asks Auditor again: "Now?" Auditor: "Almost, but clarify Y." This is chatty.

Better: Conductor completes a full research iteration, then Auditor reviews the batch. One round-trip. If Auditor says "more needed," Conductor does another full iteration, not a single refinement.

---

### 4. Shared Database (= Shared Kernel Overuse)

**What it looks like:**
- All agents read and write the same state file/database directly
- Agent X writes half-processed data that Agent Y reads mid-processing
- No clear ownership of which agent manages which data
- Race conditions: Agent X updates a record while Agent Y is reading it

**Detection heuristics:**
- Multiple agents write to the same file/table without coordination
- "Who changed this value?" is unanswerable from the data alone
- Bugs appear intermittently and are hard to reproduce (concurrency)
- Removing one agent breaks another because they share implicit state

**Why this is worse for AI agents than for microservices:**
Microservices at least have transactions and locks. AI agents operating on files have neither. If Agent X writes to `research-state.json` while Agent Y is reading it, the result is undefined.

**Remediation:**
- **Event-based communication:** agents publish events, not shared state
- **Ownership:** each data entity has exactly one agent that writes it
- **Read replicas:** other agents read snapshots, not live state
- **The JSONL pattern:** append-only log means no overwrites, no conflicts

**Web research tool example:**
Bad: Both Conductor (orchestrator) and Dispatcher (executor) write to `session.json` — Conductor updates the research plan while Dispatcher updates the visited URLs list.

Good: Dispatcher emits `URLVisited` events. Conductor reads events to update its view of progress. Each agent owns its own state; they communicate through events.

---

## Split/Merge Decision Framework

### The Flowchart

```
START: You have a task that an agent does.
  │
  ├─ Can the task be done by deterministic code?
  │   YES → Don't use an agent. Write a function.
  │   NO ↓
  │
  ├─ Does the task involve more than one domain?
  │   NO → Keep as one agent. DONE.
  │   YES ↓
  │
  ├─ Would a different model tier significantly improve
  │   part of the task? (e.g., 7B for extraction, 14B for evaluation)
  │   YES → Strong signal to split.
  │   NO ↓
  │
  ├─ Is the context window filling up because the agent
  │   needs too much information from different domains?
  │   YES → Split. Context pressure is the #1 reason on local models.
  │   NO ↓
  │
  ├─ Would splitting produce measurably better output?
  │   (Run both, compare)
  │   YES → Split.
  │   NO → Keep merged. Simpler is better.
  │
  END
```

### Cost/Benefit Calculation Template

For any proposed split, fill in:

```
SPLIT PROPOSAL: [Agent X] into [Agent X1] + [Agent X2]

BENEFITS:
- Context freed: _____ tokens (from removing domain Y's context)
- Model fit: X1 uses ___B, X2 uses ___B (vs current ___B for everything)
- Prompt clarity: X1 prompt is ___ tokens (vs current ___ combined)
- Independent testing: can we test X1 in isolation? [yes/no]

COSTS:
- Model swap: ___s (if different models) or 0s (same model)
- Data translation: [describe what format conversion is needed]
- Lost conversational state: [what context X2 won't have that X1 had]
- Implementation complexity: [new code needed for orchestration]

NET ASSESSMENT:
- Quality improvement: [measured or estimated]
- Latency impact: +___s per research iteration
- Worth it? [yes/no/defer until ___]
```

### Worked Example: Web Research Tool

**Proposal:** Split the MVP's collapsed "Conductor+Dispatcher" into separate Conductor (orchestrator) and Dispatcher (executor).

```
BENEFITS:
- Context freed: ~2000 tokens (API docs, tool signatures, routing logic
  removed from Conductor's prompt)
- Model fit: Dispatcher could be deterministic code (no LLM needed)
  → saves a model call entirely
- Prompt clarity: Conductor focuses on "what to research next" (strategy),
  not "how to call SearXNG" (mechanics)
- Independent testing: yes — Dispatcher is testable with unit tests
  (deterministic inputs/outputs)

COSTS:
- Model swap: 0s (Dispatcher is code, not a model)
- Data translation: Conductor outputs {action: "search", query: "..."} →
  Dispatcher maps to SearXNG API call. Simple JSON contract.
- Lost conversational state: none — Dispatcher doesn't need conversation
  history, just the current command
- Implementation complexity: moderate — need to define the action schema
  and build the executor

NET ASSESSMENT:
- Quality improvement: Conductor's output likely improves (cleaner prompt,
  focused on strategy)
- Latency impact: ~0s (code execution, no model call for Dispatcher)
- Worth it? YES — but only when the MVP proves the core hypothesis.
  In MVP phase, keep collapsed.
```

**Proposal:** Split Conductor into Conductor (manager) and Lens (context proxy).

```
BENEFITS:
- Context freed: significant — Conductor doesn't load raw research content
  (potentially 10K+ tokens per page × multiple pages)
- Model fit: same model, same tier (both 14B) → no swap needed
- Prompt clarity: Conductor asks questions ("what did we find about X?"),
  Lens reads and answers

COSTS:
- Model swap: 0s (same model, but need fresh context construction)
- Data translation: Conductor's question → Lens reads files → formatted answer
- Lost conversational state: Lens doesn't have Conductor's research plan
  context. Must include the question + enough framing.
- Implementation complexity: moderate — need a "query your own research" pattern

NET ASSESSMENT:
- Quality improvement: likely YES on larger research sessions where
  Conductor's context would otherwise overflow
- Latency impact: +3-10s per query (new inference call)
- Worth it? DEFER until context pressure is measured.
  If research sessions stay under 5 pages, Conductor can hold it all.
  If they grow to 20+, this split becomes necessary.
```

---

## Meta: When This Framework Applies

**Use this framework when:**
- Designing a new multi-agent system on constrained hardware
- An existing agent is showing signs of an anti-pattern
- Deciding whether a feature should be a new agent or added to an existing one
- Evaluating an agent framework's architecture (does CrewAI encourage God Agents?)

**Don't use this framework when:**
- You have one agent doing one thing well (no decomposition needed)
- You're on frontier models with 200K context (context pressure barely exists)
- The system is a prototype/spike (optimize later, validate first)
- The overhead of thinking about boundaries exceeds the overhead of just building it

The framework is a tool for **systems that have grown past the "one script" stage** — which the web research tool will, but the MVP hasn't yet.
<!-- /ref:ddd-agent-decisions -->
