# llm/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status

Layers 0-4 complete (of 10-layer plan). Infrastructure fully operational.
Layer 5+ active: expense classifier, chatbot Phases 1+2 (cross-repo context + LLM routing).
Session 59 (2026-05-04): LTG Phase 1 **fully closed**. All 3 freeze gates cleared:
determinism re-run (Branch C — off-by-one confirmed model property) + MoE eval
(qwen3:30b-a3b unusable TTFT > 9min; qwen3-coder:30b fails adj. 2.06 < 2.2).
**ref:ltg-extractor frozen**: qwen3:14b prose, qwen2.5-coder:14b code.
Phase 2 next: VRAM co-residence probe (qwen3:14b + bge-m3 ≈ 12GB).

## Repo Structure

```
llm/
  mcp-server/    # MCP bridge server (Python/FastMCP) — Claude Code ↔ Ollama
  personas/      # 35+ specialized model configs from 13 base models
  evaluator/     # Two-phase evaluation framework (automated + LLM-as-judge)
  benchmarks/    # Multi-language code validation suite
  overlays/      # Portable scaffolding packages for cross-repo consistency
  modelfiles/    # Ollama Modelfile definitions
  retrieval/     # LTG substrate — Phase 1 reconciled (session 58, Branch C); freeze pending determinism + MoE
  docs/          # Research, patterns, portfolio, findings
```

## Key Rules

- **12GB VRAM budget** shapes every architecture decision (RTX 3060)
- **Bash wrappers over direct python3** — `./script.sh` form, whitelist-safe
- **ref-indexing convention** — `<!-- ref:KEY -->` blocks for runtime lookups
- **Local-first, frontier escalation** — try local models first, Claude for judgment
- **Verdict protocol** — ACCEPTED/IMPROVED/REJECTED on every local model output → DPO data

## Deeper Memory -> KNOWLEDGE.md

- **VRAM Budget Constraints** — model tier limits, context window ceilings
- **Prompt Decomposition** — empirically validated 3-stage sweet spot
- **Cross-Repo Architecture** — 3 repos, one hardware platform, MCP integration layer
- **DPO Data Collection** — passive training data from verdict-labeled inference logs
- **Smart RAG Research** — content-linking retrieval cluster (7 sources, 5 philosophies); hub at `ref:smart-rag-research`. Converges chatbot Phase 3 + Layer 7 RAG into one substrate.
- **Latent Topic Graph (LTG)** — named concept + implementation plan for that substrate. Concept: `ref:concept-latent-topic-graph`. Plan: `ref:plan-latent-topic-graph` (+ 18 narrow phase/section refs `ltg-plan-*`). Phase 0 frozen → `retrieval/DECISIONS.md`. **Phase 1 fully closed (session 59)**: extractor frozen (qwen3:14b prose, qwen2.5-coder:14b code). Findings at `ref:ltg-phase1-results`; MoE eval at `ref:ltg-phase1-moe-eval`; determinism at `ref:ltg-phase1-determinism-smart-rag-index`. Phase 2 next.
