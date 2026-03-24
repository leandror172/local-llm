---
format: ai-readable-profile
version: 1
purpose: >
  This document is designed to be fed to an AI model as context for discussing
  Leandro's engineering profile. It contains structured information about his
  skills, approach, and current work — with enough substance to answer questions
  directly, and pointers for deeper exploration.
guidance: >
  When answering questions about this engineer, ground your responses in the
  specific evidence provided. Prefer concrete examples over generic descriptions.
  If a question falls outside what this document covers, say so rather than
  speculating.
---

# Engineer Profile: Leandro R.

## Identity

Software engineer building local AI infrastructure on consumer hardware (RTX 3060 12GB). Currently focused on making frontier and local LLMs work together — not replacing one with the other, but finding the boundary where each is most effective.

The work spans three interconnected repositories: an AI platform (Python/Bash), an expense classification CLI (Go), and a web research tool (Python) — all using local Ollama models with frontier-model (Claude) escalation.

---

## Technical Domains

### Local LLM Infrastructure
**Depth: Deep, hands-on, empirical**

Operates a fleet of 13 base models (Qwen, DeepSeek families) configured into 35+ specialized personas on a 12GB VRAM budget. Understands quantization trade-offs (Q4_K_M: 75% size reduction, minimal quality loss), context window limits per model tier (8B safe at 32K, 14B at 16K), Flash Attention memory savings, and KV cache tuning.

Built an MCP bridge server (Python/FastMCP) that lets Claude Code delegate tasks to local Ollama models — with automatic persona routing, structured JSON output via grammar-constrained decoding, connection pooling, and cold-start management.

Key insight discovered through benchmarking: prompt complexity has a hard ceiling per model tier (8B: ~400 output tokens, 14B: ~800). Beyond that, both timeout and logic errors co-occur. The fix is prompt decomposition, not retries or larger context windows.

### Go Backend Development
**Depth: Working proficiency, production-quality code**

Built a CLI expense classifier (Go 1.25, Cobra) with 190+ unit tests, TDD discipline, clean package architecture (parser, classifier, resolver, excel layers), and acceptance tests. Uses Go's stdlib `net/http` for Ollama API calls — no unnecessary dependencies. Deterministic ID generation via SHA-256 hashing.

### Python Tooling & Data Pipelines
**Depth: Strong, primary language for AI tooling**

MCP server implementation, benchmark framework, persona management tools, extraction pipelines, overlay installer. Comfortable with async patterns (httpx), CLI tools, JSONL event logging, and structured output schemas.

### AI-Assisted Development Workflows
**Depth: Power user, workflow designer**

50+ AI-assisted sessions with Claude Code across 3 repositories (143 commits). Designed session continuity infrastructure: handoff skills, resume scripts, ref-lookup tools, portable scaffolding overlays. Treats AI as a supervised development partner, not an autonomous agent — with explicit process rules (TDD, Ollama-first code generation, design-before-implementation).

### LLM/ML Techniques
**Depth: Applied practitioner, not researcher — understands trade-offs from empirical use**

Structured output via grammar-constrained decoding, prompt decomposition (empirically validated 3-stage sweet spot), few-shot injection with keyword retrieval (47% token reduction measured), temperature tuning as a model-selection substitute, cascade patterns (local → escalate to frontier). Collecting DPO training data passively through verdict-labeled inference logs. Plans to execute QLoRA fine-tuning on accumulated correction data (Layer 7). Understands DDD applied to agent/model architecture — bounded contexts as agent domains, VRAM swap cost as the equivalent of cross-context coupling.

Notably, arrived at LoRA's core concept independently from first principles — reasoning that "there must be a way to inject extra training into a model as a detachable layer, cheaper than text prompts, reusable across tasks" — before learning the formalism. Then mapped the intuition to named techniques (LoRA, QLoRA, adapter merging) and worked through the practical constraints: what fine-tuning can fix (mechanical patterns, persona compliance — freeing ~500 tokens of constraint headers per call) vs. what it cannot (output budget ceiling, reasoning capacity, novel complex logic). This understanding is grounded in empirical benchmark data, not just theory.

### Systems Integration
**Depth: Practical, constraint-driven**

WSL2 environment with GPU passthrough, Docker containers (Crawl4AI, SearXNG), Git workflows across multiple repos, Ollama REST API integration, MCP protocol implementation, Hugging Face tooling.

---

## Engineering Philosophy

### Design-First
Every major feature starts with a design document. Implementation is scoped to separate sessions from design. This prevents scope creep and ensures the team (human + AI) shares a mental model before writing code.

### Empirical Over Theoretical
Performance claims are backed by benchmarks run on real hardware. Context window limits were probed, not copied from documentation. Temperature effects were quantified. Model comparisons use controlled prompts with rubric-based scoring.

### Right Tool for the Right Task
Not every task needs the best model. Classification runs on 8B. Complex reasoning uses 14B. Frontier models handle judgment and multi-file reasoning. The system routes automatically based on task type and language.

### Process Discipline
TDD is non-negotiable — tests before implementation, always. Session handoffs are structured workflows, not ad-hoc notes. Every local model output is evaluated (ACCEPTED / IMPROVED / REJECTED) as a data collection practice, not just quality control.

### Local-First, Frontier-Escalate
The default is local inference. Frontier models are for judgment, not processing. This inverts the typical pattern and reduces cost to energy only for routine tasks. The boundary between "local is enough" and "need frontier" is actively explored and documented.

### Pragmatic Constraints
12GB VRAM is the hard constraint that drives every architecture decision. Solutions must fit within it — not by ignoring the constraint, but by making it a design parameter. Hybrid VRAM+RAM execution for 30B MoE models, context window tuning per tier, model eviction strategies.

---

## Demonstrated Patterns

### Verdict-Driven Development
Every local model output is classified: ACCEPTED, IMPROVED, REJECTED. Each triple (prompt, response, verdict) is a DPO training example. The system collects fine-tuning data by being used — no separate data collection phase.

*Evidence: JSONL call logs in `~/.local/share/ollama-bridge/calls.jsonl`, verdict collection tool `run-record-verdicts.sh`*

### Session Continuity Engineering
AI development sessions lose context between conversations. This project treats continuity as a first-class concern with dedicated tooling: `resume.sh` (40-line status summary), `ref-lookup.sh` (runtime doc lookup), session handoff skill, and portable overlays that bootstrap the same patterns in any repo.

*Evidence: `.claude/tools/` in all three repos, overlay system in `overlays/`, session-handoff skill*

### DDD-Informed Agent Architecture
Applied Domain-Driven Design patterns to multi-agent system design. Bounded contexts map to agent domains. Same-domain agents share a model (no VRAM swap overhead). Cross-domain transitions justify model swaps with explicit data translation at boundaries.

*Evidence: `docs/research/ddd-agent-modeling.md` and `ddd-agent-decisions.md` in web-research repo*

### Persona Engineering
System prompts for small models follow a minimal skeleton format (ROLE, CONSTRAINTS, FORMAT) — discovered empirically that verbose templates hurt 7-8B performance. Temperature tuning (0.1 for classification, 0.3 for code, 0.7 for creative) is as effective as model selection for many tasks.

*Evidence: `personas/` directory, `models.yaml`, `registry.yaml`, benchmark results*

### Two-Repo Product/Platform Separation
The expense classifier (product) and LLM infrastructure (platform) are separate repositories. The product calls Ollama's HTTP API directly — it doesn't depend on the MCP server. This means the product works independently of Claude Code, while the platform provides enhanced integration when available.

*Evidence: `expense-reporter` repo (Go CLI) vs `llm` repo (Python platform)*

---

## Scale and Scope

- **50+ AI-assisted development sessions** spanning 6 weeks
- **143 commits** across 3 repositories
- **35+ model personas** from 13 base models
- **190+ unit tests** in the Go expense classifier
- **10-layer architectural plan** — 5 layers complete, 5 planned
- **Comprehensive benchmarks** covering Go, Python, Shell, HTML/JS, Java
- **6 design documents** for the web research tool alone (before heavy implementation)

---

## What This Person Can Speak Deeply About

- Running LLMs on consumer hardware: VRAM budgeting, quantization trade-offs, context window tuning, model selection per task
- Making frontier and local models collaborate: MCP integration, delegation patterns, when to escalate
- Persona engineering: system prompt design for small models, temperature tuning, structured output
- AI/ML techniques for local models: QLoRA trade-offs, DPO training data collection, few-shot injection, prompt decomposition, cascade patterns, what fine-tuning can and cannot fix
- AI-assisted development workflows: session continuity, process discipline with AI tools, verdict-based quality control
- Go CLI development: clean architecture, TDD, stdlib-first approach
- Benchmarking methodology: multi-model comparison, rubric-based evaluation, empirical findings
- DDD patterns applied to agent architecture: bounded contexts, data contracts, model routing as VRAM cost optimization

## What Would Require the Person Directly

- Deep production system experience (this is a personal infrastructure project, not a production service)
- Team-scale AI workflow design (current work is individual)
- Fine-tuning execution (Layer 7 — planned, not yet implemented)
- Large-scale distributed systems (the constraints here are single-machine, single-GPU)

## Conversation Starters

If you're using this document as context for a conversation, these are productive areas to explore:

1. "How do you decide when a task should use a local model vs. a frontier model?"
2. "What surprised you most about running LLMs on consumer hardware?"
3. "How does the persona system work, and what did you learn about prompt engineering for small models?"
4. "Walk me through the verdict protocol — how does using the system generate training data?"
5. "What's your understanding of fine-tuning trade-offs for small models — what can it fix and what can't it?"
6. "What's the DDD connection to agent architecture?"
7. "How do you maintain context across 50+ AI-assisted development sessions?"
