# Local AI Infrastructure: Portfolio

**Author:** Leandro R.
**Date:** 2026-03-24
**Hardware:** NVIDIA RTX 3060 12GB, WSL2 (Ubuntu 22.04)

---

## What This Is

A personal AI infrastructure built on consumer GPU hardware. Three interconnected repositories that explore a single question: **how far can you push local LLM capabilities on a $300 GPU, and where does frontier-model delegation become necessary?**

The answer is an evolving system of specialized model personas, an MCP bridge that lets Claude Code delegate to local models, a Go CLI that classifies expenses using local inference, and a research tool that processes web content through local extraction pipelines.

This isn't a demo or a weekend project. It's 50+ AI-assisted development sessions, 143 commits, and a 10-layer architectural plan — five layers complete, five in progress or planned.

### The Grand Vision

The infrastructure isn't limited to coding. The same local stack serves multiple domains — personal finance (expense classification via Telegram), web research, career coaching, writing, project management. Each domain has its own personas, preferred models, and evaluation criteria, but they all run on the same hardware.

The system is designed to improve itself: agents can create other agents (analyzing a codebase and proposing appropriate personas), correction logs feed 
back as few-shot examples and eventually fine-tuning data, and an idle-time runner (Layer 9) will benchmark and refine personas/agents autonomously during GPU 
downtime.

Key design principles from the vision document:

- **Quality compounds across everything** — a better system prompt improves coding, classification, translation, and evaluation simultaneously
- **Memory is prosthetic, not intrinsic** — every invocation starts from zero unless you build explicit memory (files, correction logs, RAG). This architectural awareness shapes every component.
- **Same-model "diversity" is shallow** — two personas on the same base model share blind spots. Real diversity comes from different models, temperatures, or prompting strategies.
- **Compounding hallucination** — when agents build on each other's output, errors amplify. The evaluator must be the strongest available model.

---

## 1. Local AI Platform (`llm` repository)

**Tech:** Python, Ollama, FastMCP, Bash | **Purpose:** Infrastructure layer for everything else

### Problem

Claude Code is powerful but has usage limits. Local models are unlimited but weaker. Most developers pick one or the other. The interesting space is **making them work together** — frontier quality for judgment, local speed for volume.

### What It Does

**MCP Bridge Server** — A Python/FastMCP server that Claude Code spawns as a subprocess. It exposes local Ollama models as callable tools inside Claude's context:

- `generate_code(prompt, language)` — automatically routes to the right persona (Java/Go → backend specialist, HTML/CSS → creative coder)
- `classify_text(text, categories)` — structured output via Ollama's grammar-constrained decoding (100% valid JSON, no retries)
- `ask_ollama()`, `summarize()`, `translate()` — general-purpose delegation
- `warm_model()` — pre-loads models into VRAM to eliminate cold-start latency
- `create_persona()`, `copy_persona()` — runtime persona creation

Every call is logged to JSONL with model, prompt, response, latency, and token counts. This log is the raw material for future fine-tuning (Layer 7).

**Persona System** — 35+ specialized model configurations built from 13 base models. Each persona is a lightweight Modelfile (few KB) that shares base model weights but customizes system prompt, temperature, and context window. A registry (`registry.yaml`) makes them machine-queryable.

The system prompt format is intentionally minimal — a skeleton of ROLE, CONSTRAINTS, FORMAT. Verbose templates actually hurt 7-8B model performance.

**Benchmark Framework** — Multi-language evaluation harness with validators per language:

| Language | Validation |
|----------|-----------|
| Go | `go build` + `go vet` |
| Python | `compile()` |
| Shell | `shellcheck` |
| HTML/JS | Puppeteer headless browser (runtime error detection) |
| Java | `javac` + Spring Boot scaffold |

Includes multi-model comparison tools (`run-compare-models.sh`) and verdict collection (`run-record-verdicts.sh`). Every local model output is classified: ACCEPTED (used as-is), IMPROVED (used with fixes), or REJECTED (not usable). These verdicts are DPO training triples by design — each (prompt, local_response, verdict) is a training example.

**Overlay System** — Portable scaffolding packages that can be installed into any repo. Each overlay is a folder with a manifest, file templates, and CLAUDE.md sections. An installer handles dry-runs, backups, and AI-assisted merges. The expense and web-research repos both use overlays from this repo.

### Key Findings

These emerged from empirical benchmarking, not assumptions:

- **Qwen3 hidden thinking:** 75-88% of tokens are invisible reasoning, even with `think: false`. Discovered by measuring chars-per-token ratios (Qwen2.5: ~3.5, Qwen3: 0.4-1.8). The `think` parameter must be a top-level API field — Ollama silently ignores it inside `options{}`.

- **Prompt complexity ceiling:** 8B models reliably produce ~400 output tokens. Beyond that, both timeout AND logic errors occur simultaneously. The fix is prompt decomposition, not retries.

- **14B sweet spot:** 32 tok/s, handles single-question architectural reasoning. 8B is faster (63-67 tok/s) but fails on multi-step logic. 14B quality at 30s beats 8B speed at 6s when correctness matters.

- **Structured output via `format` param:** 100% valid JSON through grammar-constrained decoding. No speed penalty. Without it, small models write code instead of answering analytical questions.

- **Temperature tuning:** As effective as choosing a different model for many classification tasks. 0.1 for classification, 0.3 for code, 0.7 for creative work.

### Architecture

```
Claude Code (frontier)
    │
    ├── delegates simple tasks via MCP ──→ Ollama (local)
    │                                        ├── 8B models (fast, boilerplate)
    │                                        ├── 14B models (reasoning, quality)
    │                                        └── 30B MoE (complex, hybrid VRAM+RAM)
    │
    ├── persona routing ──→ language → persona mapping
    │
    └── verdict logging ──→ JSONL (future fine-tuning data)
```

---

## 2. Expense Classifier (`expense-reporter` repository)

**Tech:** Go 1.25, Cobra CLI, excelize | **Purpose:** First real application of the platform

### Problem & Vision

Brazilian personal finance tracking: categorize daily expenses into 68 subcategories across 16 top-level categories, then insert into a structured Excel workbook. Manual classification is tedious. LLM classification should handle it — but frontier model API calls for every coffee purchase is wasteful.

**End-to-end vision:** An expense is posted in a Telegram chat ("Uber Centro;15/04;35,50"). A local model classifies it, posts the top options as clickable inline buttons (in PT-BR), the user selects one, and the expense is inserted into the workbook. Corrections feed back into classification. The system handles offline periods with queue behavior — processing the oldest unhandled message first when it comes back online.

**Status lifecycle (full vision):** `pending → classifying → classified → confirmed → inserting → inserted`, with error branches for `failed_classify`, `failed_insert`, and `rejected`.

**Storage evolution:** JSON Lines (current) → SQLite (status tracking + audit) → Redis (queue, when Docker deployment happens).

### What It Does Today

A Go CLI that parses expense strings (`"Uber;15/03;32.50"`), classifies them using local Ollama models, and inserts them into Excel.

**Commands:**
- `add` — parse and insert a single expense
- `batch` — CSV import with progress bar
- `classify` — LLM classification (top-3 subcategories with confidence scores)
- `auto` — classify + insert if high confidence, prompt user otherwise
- `batch-auto` — classify CSV, split into classified.csv + review.csv

**Classification approach:** Hybrid — pattern rules for known merchants (80% of expenses), LLM for ambiguous items. Structured JSON output via Ollama's `format` parameter guarantees parseable responses.

**Deterministic expense IDs:** `sha256(normalize(item) + "|" + date + "|" + value)[:12]` — collision-resistant, reproducible across runs.

### Design Decisions

**Two-repo separation:** The classifier is a *product* that uses LLM as an implementation detail. The LLM infrastructure is a *platform*. Keeping them separate means the expense tool doesn't depend on Claude Code's MCP server — it calls Ollama's HTTP API directly.

**TDD discipline:** 190+ unit tests. Tests written before implementation, every time. Acceptance tests validate the full classify → insert pipeline.

**No external dependencies for Ollama:** Uses Go's stdlib `net/http` for Ollama API calls. No SDK, no framework. The HTTP contract is simple enough that a thin client is better than a dependency.

**Few-shot learning (Phase 2):** Correction logs feed back into prompts. When a user corrects a classification, the correction is stored and injected as a few-shot example for similar future items. Accuracy improves without retraining.

### Architecture

```
CLI (Cobra)
    │
    ├── parser ──→ "item;DD/MM;value" → structured expense
    │
    ├── classifier ──→ Ollama /api/chat (structured JSON output)
    │                    ├── pattern rules (known merchants)
    │                    └── LLM fallback (ambiguous items)
    │
    ├── resolver ──→ subcategory → Excel sheet/row mapping
    │
    └── excel ──→ read reference sheet, write expenses (excelize)
```

---

## 3. Web Research Tool (`web-research` repository)

**Tech:** Python, Ollama, Crawl4AI, SearXNG | **Purpose:** Local-model-powered web research

### Problem

Web research with frontier models is expensive and wasteful. Fetching a page, extracting relevant information, scoring relevance, generating follow-up queries — these are all tasks a 7-14B model can handle. But most research tools either use frontier models for everything or don't use LLMs at all.

### What It Does

A **local-model-powered research workbench** that iteratively gathers, processes, and accumulates knowledge from the web. Currently in spike phase with a working extraction pipeline.

**Core principles:**

1. **Context-efficient** — Processing happens outside the frontier model's context. Local models do the heavy lifting; Claude only sees summaries and decision points.
2. **Local-model-first** — Ollama (7-14B) handles extraction, summarization, query generation, relevance scoring.
3. **Pluggable** — Scraper backends (Crawl4AI, Firecrawl, SearXNG, Playwright) are swappable interfaces.
4. **Progressive autonomy** — A dial, not a switch. Starts supervised, gradually delegates more decisions to local models as they prove reliable.
5. **Knowledge compounds** — Research persists across sessions. New data links to existing knowledge.

### Architecture (DDD-Informed)

The most architecturally interesting aspect: agents map to DDD bounded contexts.

```
Conductor (orchestration)
    │
    ├── Dispatcher (pipeline builder + executor)
    │     ├── SearXNG (search)
    │     ├── Crawl4AI (fetch + extract)
    │     └── Ollama (process)
    │
    ├── Lens (context proxy — sifts results so Conductor stays focused)
    │
    ├── Auditor (sufficiency reviewer — "is research enough?")
    │     └── decreasing "more" signal (prevents infinite loops)
    │
    └── Knowledge Store
          ├── JSONL event log (audit trail, replay)
          └── SQLite graph (nodes/edges, recursive CTEs)
```

**Same-domain agents share a model** (no swap overhead). Cross-domain transitions justify model swaps. The cost of a VRAM reload (2-10s) is weighed against the benefit of focused context. This is DDD's bounded context pattern applied to GPU resource management.

### Key Design Decision: Stop Criteria

Research tools that don't know when to stop are useless. Three mechanisms combined:

1. **Quality evaluation** — only stops when research passes quality criteria
2. **Token/time budget** — hard ceiling prevents runaway
3. **Decreasing "more" signal** — iteratively reduces exploration pressure

### Current State

Working spike with extraction benchmarks across multiple models (Qwen2.5-Coder-14B, Qwen3-8B/14B, DeepSeek-R1-14B, Qwen3-30B-A3B). MVP pipeline: fetch → extract → process → store. Comprehensive design documentation completed before heavy implementation.

---

## Cross-Cutting Patterns

These patterns appear across all three repositories and reflect engineering discipline, not one-off decisions.

### Design-First, Implement Second

Every major feature starts with a design document, not code. The expense classifier has a vision document, phase plan, and category taxonomy — all written before the first `go test`. The web research tool has six design documents covering vision, architecture, DDD modeling, and agent naming. Implementation follows design; sessions are scoped to either design or implementation, not both.

### Empirical Validation Over Assumptions

Claims about model performance are backed by benchmarks. Context window limits were probed on real hardware, not copied from spec sheets. Prompt complexity ceilings were discovered by measuring where timeout and logic errors co-occur. Temperature effects were quantified across classification tasks.

### Session Continuity as Engineering Practice

AI-assisted development sessions lose context between conversations. This project treats continuity as a first-class concern:

- `resume.sh` — prints current status + recent commits in ~40 lines
- `ref-lookup.sh KEY` — runtime documentation lookup via `[ref:KEY]` tags
- Session handoff skill — structured end-of-session workflow
- Overlays — portable scaffolding that can bootstrap the same patterns in any repo

### Verdict Protocol

Every local model output is evaluated: ACCEPTED, IMPROVED, or REJECTED. This isn't just quality control — it's a **data collection pipeline**. Each (prompt, local_response, verdict) triple is a training example for future DPO fine-tuning (Layer 7). The system improves by using it.

### Local-First with Frontier Escalation

The default is local. Frontier models (Claude) are used for judgment, complex multi-file reasoning, and supervision — not for processing. This inverts the typical pattern where developers use frontier models for everything and consider local models as an afterthought.

---

## AI/ML Techniques: Applied and Planned

This section captures the LLM and agent techniques being used, explored, or planned — showing both current practice and the direction of the work.

### Currently Applied

**Structured output via grammar-constrained decoding** — Ollama's `format` parameter enforces valid JSON at inference time through grammar constraints, not post-processing. 100% reliable, no speed penalty. This is what makes programmatic agent pipelines possible with small models — without it, 7-8B models frequently generate code instead of answering analytical questions.

**Prompt decomposition** — Breaking complex prompts into smaller, model-appropriate units. Empirically validated: reduces bug *severity* (not frequency) at a 3-stage sweet spot. Beyond that, coordination overhead cancels the benefit. This is a practical alternative to larger models when the task can be factored.

**Few-shot injection** — Per-request retrieval of relevant historical examples by keyword matching. Used in expense classification: when classifying "Uber Centro", the system finds similar past expenses and injects them as examples in the prompt. 47% token reduction measured vs. including the full training data.

**Temperature tuning as model selection** — Discovered empirically that adjusting temperature (0.1 for classification, 0.3 for code, 0.7 for creative) is as effective as choosing a different model for many tasks. This is cheaper than maintaining more model variants.

**Persona engineering for small models** — System prompts use a minimal skeleton format (ROLE, CONSTRAINTS, FORMAT). Verbose templates hurt 7-8B performance. MUST/NEVER constraint headers reliably fix mechanical patterns (quoting, array syntax) but not logic errors — the boundary was established through shell benchmarks.

**Cascade pattern** — Try local model first → detect low confidence or failure → escalate to 14B or frontier. Gets local speed/cost for the ~70-80% of tasks that fit the 8B window, frontier quality on the rest. More impactful than any single model improvement.

### Explored and Documented

**DPO (Direct Preference Optimization) training data collection** — Every local model call logged with (prompt, response, verdict). ACCEPTED outputs are positive examples; REJECTED outputs are negative examples for the same prompt. This is DPO training data collected passively during normal use — no separate data collection phase. Target: 500+ triples for Layer 7.

**QLoRA (Quantized Low-Rank Adaptation)** — Researched in depth. The key insight: QLoRA loads the base model in 4-bit quantization (~4-5GB), trains small adapter matrices in float16. A 7-8B model fits in 12GB VRAM during training with room to spare. Training time on the expense dataset (~700 examples): ~5-20 minutes.

What QLoRA can fix: mechanical patterns (formatting, syntax, constraint compliance), persona behavior baked into weights (freeing ~500 tokens of constraint headers per call). What it cannot fix: output budget ceiling (~400 tokens for 8B), multi-file reasoning, novel complex logic. The correction log is the reusable asset — adapters are model-specific, but the training data transfers across model upgrades.

**RAG with embeddings** — Planned for expense classification if accuracy needs improvement beyond few-shot. Would embed the 694 historical expenses and retrieve semantically similar ones, rather than relying on keyword matching. More relevant for the web research tool's knowledge layer (querying accumulated research).

### Planned (Layers 7-9)

**SFT/DPO fine-tuning pipeline (Layer 7)** — Periodically fine-tune local models on accumulated verdict data. Expected gain: ~5-15% on affected tasks, primarily mechanical pattern compliance. The real win is freeing context tokens currently used for constraint headers.

**Multi-agent orchestration (Layer 8)** — An architect persona that decomposes tasks and recruits specialist personas. Agents create agents: analyzing a codebase/domain and proposing appropriate personas, testing them against sample tasks, archiving unused ones ("agent bloat" prevention).

**Idle-time autonomous improvement (Layer 9)** — During GPU downtime, an autonomous runner benchmarks persona variants, identifies regressions, and suggests refinements. Local-only, runs unattended, produces data for the next human review session.

---

## Technology Summary

| Component | Technology | Role |
|-----------|-----------|------|
| Inference engine | Ollama | Local model serving (REST API) |
| GPU | RTX 3060 12GB | VRAM-constrained inference |
| MCP bridge | Python / FastMCP | Claude Code ↔ Ollama integration |
| Expense CLI | Go / Cobra | Product application |
| Web research | Python / Crawl4AI / SearXNG | Extraction + research pipeline |
| Benchmarking | Python + Bash + Puppeteer | Multi-language validation |
| Persona management | YAML + Modelfiles | 35+ specialized configurations |
| Session continuity | Bash + Markdown + Overlays | Cross-session context preservation |
| Models | Qwen2.5-Coder (7B/14B), Qwen3 (8B/14B/30B), DeepSeek (R1-14B, Coder-V2-16B) | Multi-tier local inference |

---

## What's Next

| Layer | Focus | Status |
|-------|-------|--------|
| 5 | Expense classifier: few-shot learning, MCP exposure | In progress |
| 6 | Chat interface: Telegram routing to local classifier | Planned |
| 7 | Fine-tuning pipeline: DPO/SFT from accumulated verdicts | Planned |
| 8 | Multi-agent orchestration: architect persona recruits specialists | Planned |
| 9 | Idle-time runner: autonomous self-improvement during GPU downtime | Planned |

The 10-layer plan is designed so each layer produces a working artifact, not scaffolding. Every layer unlocks capabilities for the next while remaining useful on its own.
