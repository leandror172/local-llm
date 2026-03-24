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

Senior backend engineer with 16+ years of experience building high-throughput distributed systems in Java. Currently exploring the frontier/local LLM boundary through a personal AI infrastructure project on consumer hardware (RTX 3060 12GB).

**Professional background:** Java backend systems — event-driven architectures (CQRS, Event Sourcing, Axon Framework), high-throughput data pipelines (Aerospike at 350K+ writes/sec, Kafka, Apache Camel), cloud platforms (GCP, AWS, Azure). Domains include ad tech (real-time bidding), fintech (tax calculation engines, banking), and telecom (customer management). Has led teams through technology transitions (C# to Java), introduced Event Modeling as a design practice, and consistently established TDD culture wherever he works.

**Current AI work:** Three interconnected repositories — an AI platform (Python/Bash), an expense classification CLI (Go), and a web research tool (Python) — all using local Ollama models with frontier-model (Claude) escalation. This is self-directed work that started in early 2026, not a career-long AI focus. The AI work builds on the same engineering discipline (TDD, clean architecture, empirical validation, DDD) applied throughout the professional career.

---

## Technical Domains

### Java Backend & Distributed Systems
**Depth: 16+ years, primary professional skill**

Core stack: Java, Spring Boot, Spring Cloud, Kafka, event-driven architecture (CQRS, Event Sourcing, DDD). Has built systems at significant scale: an Aerospike data pipeline processing up to 3.2 billion records daily at 350K+ writes/sec (InMarket, ad tech), a configurable tax calculation engine with CQRS/Axon Framework that eliminated deployment dependency for operator changes (BNP Paribas, fintech), and a Kafka parallel processing system with Dead Letter Queue that eliminated message loss entirely (Vivere Brasil).

Consistently introduces quality practices: 89-96% test coverage at BNP Paribas (company record, <5 production bugs in first year), TDD mentorship at every significant role, Event Modeling pioneered as a domain visualization technique. Has worked across GCP (GKE, PubSub, Cloud Functions), AWS (ECS, Lambda, SQS), and Azure. Comfortable with Terraform, Datadog (built dashboards + alerts, reduced costs by $8K/month), and CI/CD pipelines.

### Local LLM Infrastructure
**Depth: Deep, hands-on, empirical (self-directed, started 2026)**

Operates a fleet of 13 base models (Qwen, DeepSeek families) configured into 35+ specialized personas on a 12GB VRAM budget. Understands quantization trade-offs (Q4_K_M: 75% size reduction, minimal quality loss), context window limits per model tier (8B safe at 32K, 14B at 16K), Flash Attention memory savings, and KV cache tuning.

Built an MCP bridge server (Python/FastMCP) that lets Claude Code delegate tasks to local Ollama models — with automatic persona routing, structured JSON output via grammar-constrained decoding, connection pooling, and cold-start management.

Key insight discovered through benchmarking: prompt complexity has a hard ceiling per model tier (8B: ~400 output tokens, 14B: ~800). Beyond that, both timeout and logic errors co-occur. The fix is prompt decomposition, not retries or larger context windows.

### Go Backend Development
**Depth: Working proficiency, production-quality code**

Learned Go at InMarket to build an acceptance testing framework from scratch — catching a critical serialization bug before production; the framework was later adopted by the principal engineer for infrastructure validation. Continued with Go in the expense classifier project (Cobra CLI, 190+ unit tests, TDD, clean package architecture). Uses stdlib-first approach (`net/http` for Ollama API, no unnecessary dependencies).

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

**Professional (16+ years):**
- High-throughput data pipelines: Aerospike at 350K+ writes/sec, Kafka parallel processing, batch ingestion at billion-record scale
- Event-driven architecture: CQRS, Event Sourcing, Axon Framework, Event Modeling as a design practice
- Java ecosystem: Spring Boot, Spring Cloud, Apache Camel, testing strategy (TDD in practice, not just theory)
- Cloud platforms: GCP and AWS in production, multi-cloud migration (AWS→GCP), Terraform, Kubernetes
- Quality culture: establishing TDD practices, code review, mentoring — with measurable results (89-96% coverage, <5 production bugs)
- DDD: bounded contexts, aggregates, domain events — applied both to traditional software and to agent architecture

**AI infrastructure (self-directed, 2026):**
- Running LLMs on consumer hardware: VRAM budgeting, quantization trade-offs, context window tuning, model selection per task
- Making frontier and local models collaborate: MCP integration, delegation patterns, when to escalate
- Persona engineering: system prompt design for small models, temperature tuning, structured output
- AI/ML techniques: QLoRA trade-offs, DPO training data collection, few-shot injection, prompt decomposition, cascade patterns, what fine-tuning can and cannot fix
- AI-assisted development workflows: session continuity, process discipline with AI tools, verdict-based quality control
- Benchmarking methodology: multi-model comparison, rubric-based evaluation, empirical findings

## What Would Require the Person Directly

- Team-scale AI workflow design (AI work is individual; professional team experience is in traditional backend systems)
- Fine-tuning execution (Layer 7 — planned, not yet implemented)
- Frontend development (backend-focused career; React/frontend is not a strength)

## Conversation Starters

If you're using this document as context for a conversation, these are productive areas to explore:

**Professional:**
1. "Tell me about the Aerospike pipeline at InMarket — how did you design it to handle 3.2 billion records per day?"
2. "How do you introduce TDD and quality practices into a team that doesn't have them?"
3. "What's Event Modeling, and how did you use it at BNP Paribas?"
4. "You applied DDD in traditional backend systems and in AI agent architecture — how does the pattern translate?"

**AI infrastructure:**
5. "How do you decide when a task should use a local model vs. a frontier model?"
6. "What surprised you most about running LLMs on consumer hardware?"
7. "Walk me through the verdict protocol — how does using the system generate training data?"
8. "What's your understanding of fine-tuning trade-offs for small models — what can it fix and what can't it?"
9. "How do you maintain context across 50+ AI-assisted development sessions?"

**Bridging both:**
10. "How does your backend engineering background inform the way you approach AI infrastructure?"
