# llm/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status

Layers 0-4 complete (of 10-layer plan). Infrastructure fully operational.
Layer 5+ active: expense classifier, chatbot Phases 1+2 (cross-repo context + LLM routing).
Session 59 (2026-05-04): LTG Phase 1 **fully closed**. All 3 freeze gates cleared.
**ref:ltg-extractor frozen**: qwen3:14b prose, qwen2.5-coder:14b code. ⚠ See session 68 — coder arm superseded.
Session 72 (2026-05-28): **LTG Phase 2 complete.** 69 topics, 8 files, 7/8 acceptance pass.
Session 73 (2026-05-28): **M-P0b complete.** Embedding upgraded bge-m3 (1024-dim) → **qwen3-embedding:8b (4096-dim)**. WARN verdict (load-time eviction only). Acceptance equivalent. `embed.py`/`store.py` now config-driven (no hardcoded dims). **Next: LTG Phase 3 — anchor integration.**
Sessions 63-65 (2026-05-22): MCP Plans 1+2+3 complete — `refs`/`refs_root`, `output_file`/`output_only`,
`patch_file` tool. 29 green tests total. PRs #37 (Plans 1+2) and #38 (Plan 3) open, pending merge.
Session 68 (2026-05-26): Model survey complete. Key findings:
- **qwen3.6-coder:14b** candidate to supersede qwen2.5-coder:14b (claimed SOTA — secondary source; not locally benchmarked; swap gated on M-P0a)
- **qwen3-embedding:8b** — ✅ adopted (session 73, M-P0b complete). Replaced bge-m3; MTEB 63.0→70.58; 1024→4096 dim.
- **llama4:scout** — new long-context capability (~200K–1M effective for RAG, advertised 10M); multimodal, fits 12GB (~10GB Q4)
- qwen3:14b still SOTA reasoning ≤14B; qwen3:4b-q8_0 still best classifier
- Full survey + advisor review: `docs/findings/model-updates-2026-05.md`
Active branch: `feature/model-survey-2026-05`.

## Repo Structure

```
llm/
  mcp-server/    # MCP bridge server (Python/FastMCP) — Claude Code ↔ Ollama
  personas/      # 35+ specialized model configs from 13 base models
  evaluator/     # Two-phase evaluation framework (automated + LLM-as-judge)
  benchmarks/    # Multi-language code validation suite
  overlays/      # Portable scaffolding packages for cross-repo consistency
  modelfiles/    # Ollama Modelfile definitions
  retrieval/     # LTG substrate — Phase 1 fully closed (session 59); Phase 2 next
  docs/          # Research, patterns, portfolio, findings
```

## Key Rules

- **12GB VRAM budget** shapes every architecture decision (RTX 3060)
- **Bash wrappers over direct python3** — `./script.sh` form, whitelist-safe
- **ref-indexing convention** — `<!-- ref:KEY -->` blocks for runtime lookups
- **Local-first, frontier escalation** — try local models first, Claude for judgment
- **Verdict protocol** — 0/1/2 on every local model output → DPO data

## Deeper Memory -> KNOWLEDGE.md

- **VRAM Budget Constraints** — model tier limits, context window ceilings
- **Prompt Decomposition** — empirically validated 3-stage sweet spot
- **Cross-Repo Architecture** — 3 repos, one hardware platform, MCP integration layer
- **DPO Data Collection** — passive training data from verdict-labeled inference logs
- **Smart RAG Research** — content-linking retrieval cluster (7 sources, 5 philosophies); hub at `ref:smart-rag-research`. Converges chatbot Phase 3 + Layer 7 RAG into one substrate.
- **Latent Topic Graph (LTG)** — named concept + implementation plan for that substrate. Concept: `ref:concept-latent-topic-graph`. Plan: `ref:plan-latent-topic-graph` (+ 18 narrow phase/section refs `ltg-plan-*`). Phase 0 frozen → `retrieval/DECISIONS.md`. **Phase 1 fully closed (session 59)**: extractor frozen (qwen3:14b prose, qwen2.5-coder:14b code). Findings at `ref:ltg-phase1-results`; MoE eval at `ref:ltg-phase1-moe-eval`; determinism at `ref:ltg-phase1-determinism-smart-rag-index`. Phase 2 next.
