# llm/ — Knowledge (Semantic Memory)

*Repo-wide accumulated decisions. Read on demand by agents and chatbot.*

## VRAM Budget Constraints (2026-02)

All architecture decisions are shaped by 12GB VRAM on an RTX 3060.
7-8B models fit fully in VRAM with generous context (32K tokens).
14B models fit but are limited to ~16K context before quality degrades.
30B MoE models (Qwen3-30B-A3B) run hybrid VRAM+RAM at ~10-20 tok/s.

**Rationale:** Consumer GPU is the constraint, not a limitation — it forces
discipline in prompt design, model selection, and context management that
would be invisible with unlimited compute.
**Implication:** Every feature must answer "does this fit in 12GB?" before
architecture discussion begins.

## Model Tier Findings (2026-02 through 2026-03)

8B models: 63-67 tok/s, reliable up to ~400 output tokens, good for boilerplate.
14B models: 32 tok/s, reliable up to ~800 output tokens, better reasoning.
Key insight: prompt complexity has a hard ceiling per model tier. Beyond that,
both timeout and logic errors co-occur. The fix is prompt decomposition, not
retries or larger context windows.

**Rationale:** Discovered empirically through benchmark runs, not from documentation.
**Implication:** Model selection is task-driven (8B for boilerplate, 14B for reasoning,
frontier for judgment), not "always use the biggest."

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

## Structured Output via Grammar-Constrained Decoding (2026-02)

Always use Ollama's `format` parameter for JSON output — 100% reliable, no speed penalty.
This constrains the model's token generation to valid JSON matching a schema.
Never rely on prompt instructions alone for structured output.

**Rationale:** Prompt-only JSON extraction fails 10-30% of the time at 7-8B tier.
Grammar-constrained decoding makes it deterministic.
**Implication:** Every tool that needs structured output uses `format` param, not
post-processing or retry loops.
