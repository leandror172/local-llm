# llm/ — Knowledge (Semantic Memory)

*Repo-wide accumulated decisions. Read on demand by agents and chatbot.*

## VRAM Budget Constraints (2026-02, updated 2026-04)

All architecture decisions are shaped by 12GB VRAM on an RTX 3060.
7-8B models fit fully in VRAM with generous context (32K tokens).
14B models fit but are limited to ~16K context before quality degrades.
30B MoE models (Qwen3-30B-A3B) run hybrid VRAM+RAM at ~10-20 tok/s.
Dense partial offload: a 27B dense model spilling 5GB to RAM runs at ~3.2 tok/s —
slower than 30B MoE because dense models pay PCIe bandwidth on every layer; MoE
only activates ~3B params per token so fewer layers cross the bus.

**Rationale:** Consumer GPU is the constraint, not a limitation — it forces
discipline in prompt design, model selection, and context management that
would be invisible with unlimited compute.
**Implication:** Every feature must answer "does this fit in 12GB?" before
architecture discussion begins. Hybrid VRAM+RAM is viable only for MoE
architectures; dense models must fit fully in VRAM to be practical.

## Model Tier Findings (2026-02 through 2026-04)

8B models: 63-67 tok/s, reliable up to ~400 output tokens, good for boilerplate.
14B models: 32 tok/s, reliable up to ~800 output tokens, better reasoning.
Key insight: prompt complexity has a hard ceiling per model tier. Beyond that,
both timeout and logic errors co-occur. The fix is prompt decomposition, not
retries or larger context windows.

**gemma3:12b (2026-04-09):** ~31 tok/s, IMPROVED tier on Go + Python — 3-4× faster than
qwen2.5-coder:14b (8 tok/s) with comparable quality. Same IMPROVED verdict on all 3
benchmark prompts. Best use: iterative tasks where speed matters more than one-shot accuracy.
**gemma3:27b (2026-04-09):** 3.2 tok/s, timeouts on all coding tasks (even warm, even
on shorter prompts). Dense 27B at 5GB RAM spillover is slower than 30B-A3B MoE — dense
partial offload costs more PCIe bandwidth per forward pass than MoE sparse routing.

**Rationale:** Discovered empirically through benchmark runs, not from documentation.
**Implication:** Model selection is task-driven (8B for boilerplate, gemma3:12b for speed,
14B for reasoning, frontier for judgment), not "always use the biggest."

## Prompt Decomposition (2026-02)

Multi-stage prompts where each stage's output feeds the next work better than
single large prompts. Empirically validated sweet spot: 3 stages.
Example: Stage 1 generates HTML structure, Stage 2 adds animation, Stage 3 refines.

**Rationale:** Keeps each prompt within the model's reliable output budget.
**Implication:** Complex tasks should be decomposed before attempting, not retried
with bigger context.

## Cross-Repo Architecture (2026-02 through present)

Three interconnected repositories share one hardware platform:
1. **llm** (this repo) — AI platform: MCP server, personas, benchmarks, evaluator, overlays
2. **expenses** — Go CLI for expense classification using local LLM inference
3. **web-research** — Python extraction + search pipeline with DDD agent architecture

The MCP bridge server (this repo) is the integration layer — Claude Code in any repo
can delegate to local models through the same interface. Overlays provide cross-repo
consistency (ref-indexing, session tracking, local model conventions).

**Rationale:** Separation by domain (platform vs. application vs. research tool),
not by technology.
**Implication:** Changes to the MCP server affect all downstream repos. Overlays
must be backward-compatible.

## DPO Data Collection Strategy (2026-03)

Every local model call is logged to JSONL (prompt, response, model, latency, token counts).
Human verdicts (ACCEPTED/IMPROVED/REJECTED) are recorded alongside each generation.
The evaluator framework adds automated quality scores (Phase 1) and LLM judge scores (Phase 2).
Together these form DPO training triples: (prompt, response, quality_signal).

**Rationale:** Fine-tuning requires labeled preference data. Collecting it passively
during normal work avoids the cost of dedicated annotation.
**Implication:** Every coding task that uses local models produces training data as
a byproduct. The verdict protocol is not overhead — it's the data pipeline.

## Local-First with Frontier Escalation (2026-02)

Default to local models for code generation, classification, summarization.
Escalate to Claude (frontier) for architectural decisions, multi-file reasoning,
security-sensitive code, and evaluation judgment.

**Rationale:** Local inference is free after hardware cost. Frontier inference
costs per token. But frontier quality is needed for tasks where errors compound.
**Implication:** The MCP server exists to make this delegation seamless — Claude Code
calls a tool, local model responds, Claude evaluates the result.

## Claude Code Source + Related Repos (2026-04)

Three repos cloned to `~/workspaces/clones/` after Claude Code source leaked via npm sourcemap:
- **claude-code/** — full TS source (785KB main.tsx, 40+ tools, coordinator/, services/)
- **claude-code-sourcemap/** — raw v0.2.8 with maps; community fork → dnakov/anon-kode
- **open-multi-agent/** — MIT TypeScript multi-agent framework (3 runtime deps)

**Key files to read before MCP server refactor:**
- `claude-code/src/services/mcp/normalization.ts` — how Claude Code normalizes MCP tool
  responses before they reach the prompt; informs optimal MCP response format
- `claude-code/src/services/autoDream/consolidationPrompt.ts` — the exact prompt driving
  automated memory consolidation (autoDream = our session-handoff, automated)

**open-multi-agent integration pattern:**
```typescript
const localAgent = { provider: 'openai', baseURL: 'http://localhost:11434/v1', apiKey: 'ollama' }
```
Verified tool-calling: Gemma 4, Llama 3.1, Qwen 3. Falls back to text extraction if model
returns tool calls as text (handles thinking-mode models). Relevant for web-research multi-agent phase.

**Full notes:** `docs/ideas/claude-code-python-port.md`

**Rationale:** Understanding Claude Code internals lets us align MCP tool response formats
with how the host actually consumes them, rather than guessing from observed behavior.
**Implication:** Read `normalization.ts` before any MCP server refactor. Read
`consolidationPrompt.ts` before improving session-handoff memory quality.

## Smart RAG / Content-Linking Research (2026-04-13, session 51)

Investigation into retrieval techniques beyond keyword/vector RAG — triggered by wanting
career chatbot, Claude Code, web-research, and llm repo to note relations across all content
without blowing up context. 7 sources reviewed (see `ref:smart-rag-research`).

**Five philosophies identified:**
1. **Pre-compile into interlinked wiki** (Karpathy llm-wiki v1+v2) — highest relevance; v2
   adds typed knowledge graph + hybrid search (BM25+vector+graph). Maps cleanly to our
   "prepared artifact before HF push" constraint.
2. **Graph-first via wikilinks** (obsidian-mind) — validates exploiting our existing
   `ref:KEY` + `.memories/` graph instead of building a new one.
3. **Code-graph + git co-change** (repowise) — biggest genuinely new idea: files that
   change together without importing each other is an edge type static analysis misses.
4. **Hybrid observation store** (claude-mem) — steal the pattern (FTS over calls.jsonl),
   don't install it (conflicts with session-log + autoDream).
5. **Hierarchical spatial memory** (MemPalace) — 34% recall gain from scoping alone
   validates `.memories/` per-folder convention.

**Cross-cutting patterns (3+ sources):**
- Hybrid = BM25 + vectors + graph (table stakes)
- Pre-compile once, query many
- Exploit existing graph structure (our `ref:KEY` system is the seed)
- Hierarchical scoping beats smarter embeddings
- Filter-before-fetch via IDs (critical for Opus context discipline)
- Supersession / contradiction tracking (addresses stale-memory problem)
- Git co-change edges (scoped to code repos)

**Architectural direction (refined from prior conversation):**
```
raw sources → LLM-authored wiki (pre-compile)
            → indexed wiki (hybrid + graph from refs/links/co-change)
            → retriever (MCP tool + HTTP endpoint)
            → consumers: chatbot, Claude Code, web-research Dispatcher
```
One wiki per domain (profile, llm, web-research, expense), one federating retriever.
Chatbot = static artifact; Claude Code = live MCP service; same artifacts underneath.

**Rationale:** Off-the-shelf RAG (Dify) fails the content-linking problem; we have
infrastructure (`ref:KEY`, `.memories/`, ollama-bridge, evaluator, overlay system) to
build minimum-viable from primitives at <500 lines of Python.
**Implication:** Phase 3 chatbot work and Layer 7 RAG (task 7.11) converge on this
substrate. Build once in llm repo, consume from everywhere via federation layer.
Full file-by-file notes: `docs/research/smart-rag-*.md` (ref keys `rag-*`).

## Structured Output via Grammar-Constrained Decoding (2026-02)

Always use Ollama's `format` parameter for JSON output — 100% reliable, no speed penalty.
This constrains the model's token generation to valid JSON matching a schema.
Never rely on prompt instructions alone for structured output.

**Rationale:** Prompt-only JSON extraction fails 10-30% of the time at 7-8B tier.
Grammar-constrained decoding makes it deterministic.
**Implication:** Every tool that needs structured output uses `format` param, not
post-processing or retry loops.
