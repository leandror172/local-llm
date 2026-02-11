# Plan v2: Local AI Infrastructure

**Status:** Draft — under refinement
**Vision:** See `docs/vision-and-intent.md` for goals, principles, and use cases
**Previous plan:** `plan.md` (Phases 0-6, all complete)

---

## Overview

Build a local AI infrastructure on RTX 3060 12GB that:
- Runs multiple specialized models for different tasks
- Creates, evaluates, and refines its own agent personas
- Integrates with frontier models (Claude) to offload simple tasks locally
- Serves multiple domains: coding, finance, career, writing, research
- Learns from usage through memory and correction logging

---

## Layer 0: Foundation Upgrades

**Goal:** Maximize baseline quality before building anything on top.
**Depends on:** Phases 0-6 complete (they are).

### Tasks

| ID | Task | Effort | Source |
|----|------|--------|--------|
| 0.1 | Pull Qwen3-8B Q5_K_M, create updated my-coder | 10 min | closing-the-gap #1 |
| 0.2 | Benchmark Qwen3-8B vs Qwen2.5-Coder-7B on standard prompts | 30 min | closing-the-gap #1 |
| 0.3 | Rewrite my-coder system prompt in skeleton format (ROLE/CONSTRAINTS/FORMAT) | 30 min | closing-the-gap #2 |
| 0.4 | Create few-shot example library for common coding tasks | 1-2 hrs | closing-the-gap #4 |
| 0.5 | Test Qwen3-14B Q4_K_M for heavy reasoning tasks | 30 min | closing-the-gap #11 |
| 0.6 | Pull additional models per model strategy (see `docs/model-strategy.md`) | 30 min | new |
| 0.7 | Test structured output (JSON schema) with Ollama | 1 hr | closing-the-gap #6 |
| 0.8 | Qwen3 thinking mode management: test `/no_think`, measure overhead, decide default | 1 hr | benchmark 0.2 finding |
| 0.9 | Prompt decomposition for visual tasks: break monolithic prompts into staged calls | 1-2 hrs | benchmark 0.2 finding, closing-the-gap #3 |
| 0.10a | Runtime validation (frontend): headless browser smoke test for generated HTML/JS | 1-2 hrs | benchmark 0.2 finding |
| 0.10b | Runtime validation (backend): compilation + static analysis gate for generated Go/Java | 1-2 hrs | task 0.9 finding |

### Benchmark 0.2 Findings

**Run date:** 2026-02-09 | **Models:** 4 personas × 6 prompts (3 backend, 3 visual)

Key discoveries that informed tasks 0.8–0.10:

1. **Hidden thinking tokens (→ task 0.8):** Qwen3's `<think>` blocks are stripped from `message.content` by Ollama but counted in `eval_count`. Result: 75–88% of generated tokens are invisible reasoning. Effective visible tok/s drops from ~51 to ~8 tok/s equivalent. This caused 2/3 backend prompts to time out at 120s. Fix: either disable thinking with `/no_think` for simple tasks, or budget 5–17× more time. Need a per-task strategy.

2. **Visual quality gap (→ task 0.9):** All 6 visual outputs (both models) were rated poor by frontier review. Common failures: incorrect coordinate transforms for rotation, broken collision math, variable shadowing crashes (`for (let fish of fish)`), ugly procedural shapes. Root cause: monolithic "create complete physics simulation" prompts exceed what 7–8B models handle in a single shot. Closing-the-gap technique #3 (decomposition) applies directly: break into shape drawing → physics math → animation loop → integration.

3. **Silent JS crashes (→ task 0.10a):** Qwen3's aquarium output crashed on frame 1 due to a trivial variable shadowing bug. No way to detect this without opening the file. A headless browser (Puppeteer/Playwright) smoke test catching console errors would flag obvious failures automatically.

4. **Backend code validation (→ task 0.10b):** The same class of bugs (const reassignment, undefined variables, type errors) that crash JS at runtime would be caught at compile time in Go/Java. Since `my-coder`'s primary output is backend code, a compilation + static analysis gate (`go build`, `go vet`, `javac`) provides equivalent safety for generated Go/Java snippets. Requires scaffolding: wrap snippet in compilable unit (package declaration, imports, main if needed).

**Backend quality:** Merge intervals was the only near-passing output (A- from both models). Go LRU cache had a use-after-delete bug (Qwen2.5) and an overcomplicated struct (Qwen3). Java CSV parser from Qwen3 timed out even at 300s.

**Performance comparison (backend, visible output only):**
| Model | Avg tok/s | Avg tokens | Thinking overhead |
|-------|-----------|------------|-------------------|
| Qwen2.5-Coder-7B | 66 tok/s | 500–800 | None |
| Qwen3-8B | 51 tok/s (raw) | 3000–9400 | 75–88% hidden |

### Task 0.8 Findings: Thinking Mode Strategy

**Run date:** 2026-02-09 | **Tool:** `benchmarks/lib/ollama-probe.py`

**Key discovery: `/no_think` in message content does NOT disable thinking.** Only the API-level `think: false` parameter works. `/no_think` is a soft hint the model can (and does) ignore — it still produced 247-1856 chars of hidden reasoning.

**Overhead measurements (my-coder-q3, same prompt, think vs no-think):**
| Prompt complexity | think:true tokens | think:false tokens | Speedup | Thinking % |
|-------------------|-------------------|--------------------|---------|-----------:|
| Simple (add two ints) | 1,152 | 425 | 3.2x | 67% |
| Medium (merge intervals) | 6,867 | 1,201 | 6.0x | 77% |
| Complex (LRU cache) | 12,206 | 2,006 | 6.9x | 84% |

**Default strategy — `think: false` unless reasoning-critical:**
| Task type | Mode | Rationale |
|-----------|------|-----------|
| Simple code gen | `think: false` | 3x faster, near-identical output |
| Medium algorithms | `think: false` | 6x faster, adequate first-pass quality |
| Complex architecture | `think: true` | Correctness-critical; thinking helps plan structure |
| Classification / routing | `think: false` | Speed matters, reasoning overkill |
| Creative / visual | `think: false` | Thinking didn't improve quality in benchmarks |
| Retry after failure | `think: true` | Escalate with reasoning if first attempt has bugs |

**One-line rule:** Default `think: false`, escalate to `think: true` for complex reasoning or retries. This aligns with the cascade pattern (closing-the-gap #14): try fast, escalate on failure.

**Implementation notes:**
- `think` is an API parameter, not a Modelfile setting — callers (MCP server, scripts) must set it
- Two calls with `think: false` is still faster than one call with `think: true` on complex prompts
- Qwen2.5-Coder has no thinking mode — this strategy only applies to Qwen3 models

### Task 0.5 Findings: Qwen3-14B Performance

**Run date:** 2026-02-09 | **Tool:** `benchmarks/lib/ollama-probe.py`

**VRAM:** 10.4 GB / 12 GB with 14B loaded — context limited to ~4K tokens.

**14B vs 8B on complex prompt (LRU cache):**
| Model | Mode | Tokens | Wall time | tok/s | Content chars |
|-------|------|--------|-----------|-------|---------------|
| Qwen3-8B | think:false | 2,006 | 36s | 56 | 6,807 |
| Qwen3-8B | think:true | 12,206 | 252s | 49 | 8,003 |
| Qwen3-14B | think:false | 1,726 | 54s | 32 | 5,614 |
| Qwen3-14B | think:true | 7,616 | 257s | 30 | 5,252 |

**Key findings:**
- 14B is more concise (14% fewer tokens, tighter code)
- 14B reasons more efficiently (26K vs 43K chars of thinking — 40% less)
- Speed: 32 tok/s (1.7x slower than 8B) — manageable for single-question use
- VRAM constraint: ~4K context max, unsuitable for multi-file or long conversations

**Model selection rule:**
| Scenario | Model |
|----------|-------|
| Quick code gen, boilerplate | 8B think:false |
| Medium algorithms | 8B think:false |
| Complex architecture | 14B think:false |
| Multi-file / long context | 8B (14B can't fit) |
| Retry after 8B failure | 14B think:true |
| Classification / routing | 8B or 4B |

### Task 0.7 Findings: Structured Output (JSON Schema)

**Run date:** 2026-02-10 | **Tool:** `benchmarks/lib/ollama-probe.py` + `benchmarks/lib/run-structured-tests.sh`

**Test matrix:** 5 prompts × 2 models × 2 variants (format=on vs format=off) = 20 API calls.
Prompts map to real use cases: expense classification (L5), bug analysis (L4), model routing (L1), function metadata (L3), number describe (baseline).

**Headline: grammar-constrained decoding works flawlessly.**

| | format=on (constrained) | format=off (instructed) |
|--|------------------------|------------------------|
| Valid JSON | **10/10 (100%)** | **0/10 (0%)** |
| Schema-compliant | 10/10 | N/A |
| Enum adherence | 10/10 | N/A |

**Without `format`, coding personas never produce JSON.** In 8/10 free-form runs, both models wrote code (Java classes, Go functions) instead of answering the analytical question. The `format` parameter doesn't just format output — it shifts the model from code-generation mode to analysis/classification mode.

**Speed impact:**
| Model | format=on tok/s | format=off tok/s | Per-token overhead |
|-------|----------------|-----------------|-------------------|
| Qwen3-8B | 56.7 | 57.1 | ~0% (negligible) |
| Qwen2.5-Coder-7B | 63.4 | 65.4 | ~3% |

Per-token speed is unaffected. Qwen2.5 shows a wall-time startup overhead (5-7s on some runs, likely grammar compilation) that Qwen3 does not exhibit.

**Content quality (all format=on responses correct):**
- Both models correctly classified subway fare as "transport", extracted $2.75
- Both identified division-by-zero bug (Qwen3: "critical", Qwen2.5: "high")
- Both selected qwen2.5-coder-7b for Go unit test routing
- Both produced valid Java function signatures
- Both correctly identified 42 as even, not prime, with Hitchhiker's Guide reference
- No hallucinations detected in any constrained response

**Qwen3 vs Qwen2.5 quality difference:** Qwen3 showed slightly better reasoning — more accurate severity ratings, more internally consistent routing decisions (medium complexity + think:false vs Qwen2.5's contradictory simple + think:true).

**Token efficiency:** Constrained responses are compact (43-107 tokens). Free-form responses range 11-232 tokens producing wrong output type.

**Minor quirk:** Constrained decoding occasionally inserts extra whitespace/tabs before JSON commas. Valid JSON but cosmetically unusual.

**Implementation rules for downstream layers:**
1. Always use `format` for structured tasks — it is not optional for coding personas
2. No speed penalty — safe to use in hot paths (MCP server responses, classification)
3. Enum enforcement is reliable — define allowed values in schema, model cannot violate them
4. Combine with `think: false` for fastest structured responses

**Artifacts:** `benchmarks/prompts/structured/` (5 prompt + 5 schema files), `benchmarks/results/structured/` (10 result JSONs, gitignored), `benchmarks/lib/run-structured-tests.sh` (test runner)

### Task 0.9 Findings: Prompt Decomposition for Visual Tasks

**Run date:** 2026-02-10 | **Tool:** `benchmarks/lib/decomposed-run.py` + `benchmarks/lib/run-decomposed.sh`

**Approach:** Incremental build — each stage produces a complete runnable HTML file, adding one feature. Previous stage's output becomes context for the next. Tested two variants: v1 (prose instructions) and v2 (explicit math formulas with step-by-step algorithms).

**Test matrix:** 3 visual prompts (bouncing ball 3 stages, heptagon 3 stages, aquarium 3 stages) × 2 models × v1/v2 variants for bouncing ball.

**Results summary (decomposed grade vs monolithic grade):**

| Prompt | Model | Monolithic | Decomposed | Change |
|--------|-------|-----------|------------|--------|
| Bouncing Ball v2 | Qwen3-8B | C+ | D | ↓ (const crash, sign errors) |
| Bouncing Ball v2 | Qwen2.5-7B | D+ | C- | ↑ (follows 7-step structure) |
| Heptagon | Qwen3-8B | C+ | B+ | ↑↑ (edge-normal works, balls work) |
| Heptagon | Qwen2.5-7B | D | C | ↑ (algorithm correct, const crash) |
| Aquarium | Qwen3-8B | C+ | C | ~ (fish=ellipse, scope bugs) |
| Aquarium | Qwen2.5-7B | D+ | C- | ↑ (fish+tail+eye, bubbles spawn) |

**What decomposition consistently fixes:**
1. Feature completeness — missing elements (heptagon drawing, bubble spawning, ball numbers) now appear
2. Persistent state — pebbles, light rays no longer re-randomized per frame
3. Shape quality — fish upgraded from triangles to ellipse bodies with fins and eyes
4. Algorithm structure — explicit formulas get followed as a sequence

**What decomposition doesn't fix:**
1. `const` vs `let` — systematic pattern: models default to `const` for formula variables, crash when prompt shows mutation (`/=`). Appears in 4/6 formula-heavy runs
2. Coordinate-space confusion — bouncing ball collision response still wrong in both v1 and v2
3. Variable scoping — shadowing, undefined references in complex multi-stage outputs

**Key insight: decomposition reduces bug severity.** Monolithic bugs were fundamental design errors (wrong algorithm, missing features). Decomposed bugs are implementation/transcription errors (const vs let, sign errors, scope). The latter are detectable by runtime validation — strongly motivating task 0.10.

**Model behavior difference with explicit formulas:**
- Qwen3 "optimizes" formulas (creates new variables like `nX = normalX / len` — avoids const crash but may corrupt signs)
- Qwen2.5 copies literally (const + /= = crash, but formulas themselves are correct)
- Neither approach is universally better — depends on whether the formula uses mutation

**Practical rules for prompt decomposition:**
1. 3 stages is the sweet spot for 7-8B models (more stages = more context growth)
2. Explicit formulas help with algorithm structure but use `let` in examples, never show `/=` on declared variables
3. Each stage prompt should say "modify the file above" to prevent rewrites from scratch
4. `--start N --inject file.html` allows retrying individual stages without rerunning the whole pipeline
5. Runtime validation would catch the #1 remaining bug pattern (const crash) instantly — headless browser for JS (0.10a), compiler for Go/Java (0.10b)

**Artifacts:** `benchmarks/prompts/decomposed/` (3 pipelines, 9 stage prompts + v2 variant), `benchmarks/lib/decomposed-run.py` (pipeline runner), `benchmarks/lib/run-decomposed.sh` (wrapper), `benchmarks/results/decomposed/` (6 pipeline runs, gitignored)

### Closing-the-gap integration
- Techniques #1-7 are applied here directly
- Techniques #3 (decomposition), #4 (few-shot), #5 (temperature) become standard practices documented as agent-building guidelines

### Unlocks
- Better baseline for all subsequent layers
- Multiple models available for role-specific assignment
- Structured output enables programmatic agent pipelines

---

## Layer 1: MCP Server — Ollama as ClaudeCode Tool

**Goal:** Let ClaudeCode delegate simple tasks to your local Ollama.
**Depends on:** Layer 0 (models installed and tested)
**Pattern:** Frontier-first, delegates down (Pattern B from routing discussion)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 1.1 | Research MCP server specification and ClaudeCode integration | 2-3 hrs |
| 1.2 | Build MCP server wrapping Ollama /api/chat | 1 day |
| 1.3 | Define tool capabilities: generate_code, classify_text, summarize, translate | 1 day |
| 1.4 | Configure ClaudeCode to use the MCP server | 1 hr |
| 1.5 | Test: ClaudeCode delegates a boilerplate function to local model | 1 hr |
| 1.6 | Document usage patterns and limitations | 2 hrs |

### Closing-the-gap integration
- The MCP server should apply structured prompts (skeleton format) when calling Ollama
- Temperature presets per tool capability (0.1 for code, 0.3 for general, 0.7 for creative)
- Structured output (JSON schema) for classification and structured responses

### Unlocks
- Reduced Claude token consumption for simple tasks
- Foundation for any frontier tool to call local models
- First instance of "routing" in practice — informs design of later routing layers

### Opportunities opened
- Claude Desktop could also use this MCP server
- Other frontier tools with MCP support get local model access for free
- The tool capabilities become reusable building blocks for the persona creator

---

## Layer 2: Local-First CLI Tool

**Goal:** A ClaudeCode-like interface that runs against local Ollama, with optional frontier escalation.
**Depends on:** Layer 0
**Pattern:** Local-first, escalates up (Pattern A)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 2.1 | Evaluate tools: Aider, Open Interpreter, Goose, Continue.dev CLI | 2-3 hrs |
| 2.2 | Install and configure chosen tool with Ollama backend | 1-2 hrs |
| 2.3 | Configure frontier fallback (Anthropic API key for escalation) | 30 min |
| 2.4 | Test on a real coding task: compare output quality vs ClaudeCode | 1 hr |
| 2.5 | Document when to use local-first CLI vs ClaudeCode | 1 hr |

### Closing-the-gap integration
- Cascade pattern (#14 from closing-the-gap): try local, escalate if quality is insufficient
- Best-of-N (#10): some tools support generating multiple candidates

### Unlocks
- Coding continues when Claude quota is depleted
- Unlimited experimentation and iteration
- Persona testing without frontier token cost

---

## Layer 3: Persona Creator

**Goal:** A system (possibly itself a persona) that builds, tests, and refines Modelfile personas through conversation.
**Depends on:** Layer 0 (multiple models available), Layer 1 or 2 (a tool to run it through)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 3.1 | Design persona template: required fields, optional fields, defaults | 2 hrs |
| 3.2 | Build conversational persona creator — asks questions, generates Modelfile | 1-2 days |
| 3.3 | Model selection logic: given a role, recommend base model + quantization | 1 day |
| 3.4 | Auto-detection: analyze a codebase/domain and propose appropriate persona | 1-2 days |
| 3.5 | Registration: `ollama create` integration, add to persona registry | 2 hrs |
| 3.6 | Create initial persona set beyond my-coder | 2-3 hrs |

### Initial personas to create (via the creator once built, or manually before)

| Persona | Base Model | Role |
|---------|-----------|------|
| my-coder | Qwen3-8B | Java/Go backend (existing, upgraded) |
| my-frontend | Qwen3-8B | React/TypeScript frontend |
| my-architect | Qwen3-14B | System design, architecture decisions |
| my-reviewer | Qwen3-8B | Code review, quality evaluation |
| my-classifier | Phi-4-mini / Qwen3-4B | Fast classification, routing decisions |
| my-translator | TBD | PT-BR ↔ EN translation |
| my-writer | Llama-3.1-8B or Mistral | General writing, documentation |

### Closing-the-gap integration
- Every generated persona should embed: skeleton system prompt, appropriate temperature, stop sequences
- Few-shot examples included per persona where applicable
- Personas for tasks that need structured output include JSON schema definitions

### Unlocks
- Rapid creation of new specialists as needs arise
- Foundation for project bootstrapper (Layer 8) to "recruit" personas
- Self-describing system: each persona knows its own capabilities and limitations

### Opportunities opened
- A "meta-persona" specialized in tuning other personas
- Personas that choose their own model version based on task requirements
- Automated A/B testing: create two variants, run same prompts, compare

---

## Layer 4: Evaluator Framework

**Goal:** Standardized way to score and compare model/persona outputs.
**Depends on:** Layer 0, Layer 3 (personas to evaluate)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 4.1 | Define evaluation criteria per domain (code correctness, style, completeness) | 2-3 hrs |
| 4.2 | Build evaluation pipeline: prompt → N personas → score → report | 1-2 days |
| 4.3 | Integrate frontier model as evaluator (strongest available judge) | 1 day |
| 4.4 | Create benchmark prompt sets per domain (coding, writing, classification) | 1 day |
| 4.5 | Output: comparison reports (like model-comparison-hello-world.md, automated) | 1 day |
| 4.6 | Conversation insights pipeline: analyze exported Claude Desktop data (career project + general usage) — classify messages, extract friction patterns, generate insights report. First real-world evaluator use case. Data: `.claude/local/exports/` | 1-2 days |

### Closing-the-gap integration
- Best-of-N sampling (#10) is a direct application
- Self-refinement loops (#14) use the evaluator to score iterations
- Self-consistency / majority voting (#7C from closing-the-gap)

### Unlocks
- Data-driven persona selection ("which persona is best for Go concurrency questions?")
- Quality gates: reject output below threshold, escalate to frontier
- Training data generation: high-scoring outputs become few-shot examples
- Cross-platform usage insights: analyze Claude Desktop + Claude Code interaction patterns together, track improvements over time

---

## Layer 5: Expense Classifier (First Concrete Product)

**Goal:** Local model classifies expenses from text, learns from corrections, calls Go tool.
**Depends on:** Layer 0 (classification model), Layer 4 (evaluation helps but not required)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 5.1 | Define expense categories and classification schema | 1 hr |
| 5.2 | Build Go tool: add expense to spreadsheet via API | 1-2 days |
| 5.3 | Build classification pipeline: text → local model → category + confidence | 1 day |
| 5.4 | Correction logging: store input/predicted/actual for learning | 1 day |
| 5.5 | Few-shot injection: use correction log as examples in prompt | 2 hrs |
| 5.6 | (Later) Telegram integration — direct input, or via OpenClaw | deferred to Layer 6 |

### Closing-the-gap integration
- Structured output (JSON schema) for classification response
- Context injection (fact grounding) with category definitions
- Low temperature (0.1) for deterministic classification
- Correction log → eventual QLoRA fine-tuning data

### Unlocks
- First end-to-end local AI product
- Proves the pattern: model → tool → feedback → improvement
- Classification pipeline reusable for routing decisions

---

## Layer 6: OpenClaw + Security Planning

**Goal:** Chat-based interface (Telegram/WhatsApp) for non-coding tasks, with proper security.
**Depends on:** Layer 5 (expense classifier as first use case), Layer 3 (personas)
**Pattern:** Chat routes both ways (Pattern C)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 6.1 | Security planning: threat model, sandboxing requirements, access controls | 1 day |
| 6.2 | Docker sandbox setup for OpenClaw | 1 day |
| 6.3 | Install OpenClaw in sandboxed environment | 2-3 hrs |
| 6.4 | Configure Ollama integration (local model fallback) | 2 hrs |
| 6.5 | Configure Anthropic API with spending limits | 1 hr |
| 6.6 | Connect expense classifier as first OpenClaw capability | 1 day |
| 6.7 | Security audit: use security-specialist persona to probe the setup | 1 day |

### Closing-the-gap integration
- Multi-model routing: OpenClaw decides local vs frontier per message
- Cascade pattern: try local classification, escalate if confidence is low

### Unlocks
- Non-coding AI assistant via familiar chat interface
- Telegram expense flow complete
- Platform for career coaching, writing assistance, general queries in PT-BR

---

## Layer 7: Memory System

**Goal:** Per-persona persistent memory that enables learning from use.
**Depends on:** Layer 3 (personas), Layer 4 (evaluator), Layer 5 (correction logging pattern)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 7.1 | Design memory schema: per-persona MEMORY.md structure | 2 hrs |
| 7.2 | Build memory write pipeline: after each interaction, extract and store insights | 1 day |
| 7.3 | Build memory read pipeline: inject relevant memory into prompts (simple RAG) | 1 day |
| 7.4 | Summarization agent: compress old memory entries | 1 day |
| 7.5 | Bloat prevention: usage metrics, archival policy, memory size limits | 1 day |
| 7.6 | (Advanced) Full RAG with embeddings + vector store | 2-3 days |
| 7.7 | (Advanced) QLoRA fine-tuning from correction logs | 2-3 days |

### Closing-the-gap integration
- RAG (#8, #12 from closing-the-gap) is the technical foundation
- Few-shot examples evolve: manually curated → auto-extracted from high-scoring outputs
- Fine-tuning (#13) is the "batch learning" step

### Unlocks
- Agents that improve with use
- Organizational knowledge accumulates (not just in the user's head)
- Fine-tuning creates genuinely specialized models

---

## Layer 8: Project Bootstrapper

**Goal:** An "architect" persona that takes a project description, designs the approach, and recruits/creates specialist personas.
**Depends on:** Layer 3 (persona creator), Layer 4 (evaluator), Layer 7 (memory)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 8.1 | Design architect persona with project analysis capabilities | 1 day |
| 8.2 | Build recruitment pipeline: architect identifies needed specialists, creates via Layer 3 | 2-3 days |
| 8.3 | Multi-agent discussion: specialists propose approaches, evaluator scores | 2-3 days |
| 8.4 | Pair programming pattern: two different personas/models review each other's output | 1-2 days |
| 8.5 | Manager coordination: task allocation, progress tracking across agents | 2-3 days |
| 8.6 | PT-BR support via translator-agent pipeline | 1-2 days |

### Closing-the-gap integration
- One-task-per-prompt decomposition (#3) is how the architect breaks down work
- Chain-of-thought (#1D) for the architect's reasoning process
- Best-of-N (#10) when multiple specialists propose solutions
- Different models/temperatures for genuine diversity of perspective

### Unlocks
- The flagship multi-agent use case
- Self-assembling teams for any project type
- Not limited to coding: resume optimization team, research team, writing team

---

## Layer 9: Idle-Time Runner

**Goal:** Use compute downtime for self-improvement, benchmarking, and autonomous research.
**Depends on:** Layer 4 (evaluator), Layer 7 (memory), Layer 8 (project bootstrapper)

### Tasks

| ID | Task | Effort |
|----|------|--------|
| 9.1 | Build idle-time scheduler: detect inactivity, queue tasks | 1 day |
| 9.2 | Persona comparison jobs: run day's prompts through multiple variants | 1-2 days |
| 9.3 | Self-refinement jobs: generate → evaluate → refine → re-evaluate | 1-2 days |
| 9.4 | Research jobs: investigate improvement techniques, summarize findings | 1 day |
| 9.5 | Tool building: agents use coding personas to build tools they need | 2-3 days |
| 9.6 | (Optional) AirLLM or equivalent: offline 70B benchmarking for quality ceiling reference | 1-2 days |

### Closing-the-gap integration
- Self-refinement loops (#14) run at scale during idle time
- Best-of-N (#10) with more N (since time isn't constrained)
- Results feed back into memory system (Layer 7) and persona refinement (Layer 3)

### Unlocks
- Dead time becomes productive
- System self-improves without user intervention
- Quality ceiling benchmarks inform which tasks to keep local vs escalate

---

## Cross-Cutting Concerns

### Closing-the-Gap as Ongoing Discipline

The following techniques from `docs/closing-the-gap.md` are not layer-specific tasks — they are **standards applied everywhere**:

| Technique | How it's applied |
|-----------|-----------------|
| Skeleton system prompts (#2) | Every persona uses ROLE/CONSTRAINTS/FORMAT |
| One-task-per-prompt (#3) | Every agent pipeline decomposes complex requests |
| Few-shot examples (#4) | Every persona includes domain-appropriate examples |
| Temperature tuning (#5) | Per-persona, per-task: 0.1 for code/classification, 0.3 for general, 0.7 for creative |
| Context injection (#1B) | Every agent grounds prompts in provided facts |
| Chain-of-thought scaffolds (#1D) | Numbered step templates for reasoning tasks |

### Techniques that ARE tasks (to be built once and reused)

| Technique | Layer where it's built | Reused in |
|-----------|----------------------|-----------|
| Structured output (JSON schema) | Layer 0.7 | Layers 1, 3, 4, 5 |
| Few-shot example library | Layer 0.4 | All layers |
| Best-of-N pipeline | Layer 4.2 | Layers 8, 9 |
| Self-refinement loop | Layer 4 + 9 | Layers 8, 9 |
| Cascade pattern | Layer 1 + 2 | Layers 5, 6, 8 |
| RAG pipeline | Layer 7.6 | Layers 3, 7, 8 |
| QLoRA fine-tuning pipeline | Layer 7.7 | Layers 5, 7 |

---

## Dependency Graph

```
Layer 0 (Foundation)
  ├── Layer 1 (MCP Server)
  │     └── used by all ClaudeCode interactions
  ├── Layer 2 (Local CLI)
  │     └── independent coding workflow
  ├── Layer 3 (Persona Creator)
  │     ├── Layer 4 (Evaluator)
  │     │     ├── Layer 8 (Project Bootstrapper)
  │     │     └── Layer 9 (Idle-Time Runner)
  │     └── Layer 7 (Memory System)
  │           ├── Layer 8 (Project Bootstrapper)
  │           └── Layer 9 (Idle-Time Runner)
  └── Layer 5 (Expense Classifier)
        └── Layer 6 (OpenClaw + Security)
```

Layers 1, 2, 3, and 5 can proceed in parallel after Layer 0.
Layers 4 and 7 can proceed in parallel after Layer 3.
Layer 8 requires 3, 4, and 7.
Layer 9 requires 4, 7, and 8.
Layer 6 can start after Layer 5 (or independently if other use cases drive it).
