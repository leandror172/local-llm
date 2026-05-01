# llm/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status

Layers 0-4 complete (of 10-layer plan). Infrastructure fully operational.
Layer 5+ active: expense classifier, chatbot Phases 1+2 (cross-repo context + LLM routing).
Session 58 (2026-04-30): LTG Phase 1 extractor spike **closed via two-rater
reconciliation** (Branch C). 8/8 corpus files scored under both Claude draft +
user HTML-viz tracks; identical 4-model ranking + identical pass/fail. Winner:
**qwen3:14b** (2.44 / 2.61 adj. Claude/User). Production routing: 2-arm
(qwen2.5-coder:14b for code, qwen3:14b for prose); cross-ref-index 3rd-arm
hypothesis deferred to Phase 2. Final freeze still gates on determinism
re-run + MoE eval. Next: PR + determinism re-run on smart-rag-index × qwen3:14b.

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
- **Latent Topic Graph (LTG)** — named concept + implementation plan for that substrate. Concept: `ref:concept-latent-topic-graph`. Plan: `ref:plan-latent-topic-graph` (+ 18 narrow phase/section refs `ltg-plan-*`). Phase 0 frozen → `retrieval/DECISIONS.md`. Phase 1 reconciliation closed (Branch C, session 58); production routing 2-arm + 3rd-arm deferred. Findings at `ref:ltg-phase1-results`; production routing at `ref:ltg-phase1-routing-hypothesis`. Final extractor freeze still gates on determinism re-run + MoE eval.
