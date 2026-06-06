# llm/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status

Layers 0-4 complete (of 10-layer plan). Infrastructure fully operational.
Layer 5+ active: expense classifier, chatbot Phases 1+2 (cross-repo context + LLM routing).
Session 59 (2026-05-04): LTG Phase 1 **fully closed**. All 3 freeze gates cleared.
**ref:ltg-extractor frozen**: qwen3:14b prose, qwen2.5-coder:14b code. ✅ Confirmed — session 74 benchmark closed M-P0a with NO SWAP.
Session 76 (2026-05-30): **14B num_ctx re-probe complete.** All models upgraded 16K→32K with q8_0 KV (dsc16→24K). 11 personas rebuilt. `scripts/run-ctx-probe.sh` added. LTG repo-separation gate note placed at Phase 6. Pre-session reading guide added to resume.sh.
Session 72 (2026-05-28): **LTG Phase 2 complete.** 69 topics, 8 files, 7/8 acceptance pass.
Session 73 (2026-05-28): **M-P0b complete.** Embedding upgraded bge-m3 (1024-dim) → **qwen3-embedding:8b (4096-dim)**. WARN verdict (load-time eviction only). `embed.py`/`store.py` config-driven.
Session 74 (2026-05-29): **M-P0a closed — NO SWAP.** `qwen3.6-coder:14b` phantom tag. Benchmarked DeepCoder-14B: 5/6 timeout at 500s, no think-suppression, intrinsic R1-distill overhead. `qwen2.5-coder:14b` remains primary coder. Side finding: `my-mcp-q25c14` uses wrong FastMCP API (P1 fix pending). Report: `ref:deepcoder-benchmark-decision`. **Next: fix mcp-q25c14 persona OR LTG Phase 3.**
Sessions 63-65 (2026-05-22): MCP Plans 1+2+3 complete — `refs`/`refs_root`, `output_file`/`output_only`,
`patch_file` tool. 29 green tests total. PRs #37 (Plans 1+2) and #38 (Plan 3) open, pending merge.
Session 68 (2026-05-26): Model survey complete. Key findings:
- **qwen3.6-coder:14b** candidate to supersede qwen2.5-coder:14b (claimed SOTA — secondary source; not locally benchmarked; swap gated on M-P0a)
- **qwen3-embedding:8b** — ✅ adopted (session 73, M-P0b complete). Replaced bge-m3; MTEB 63.0→70.58; 1024→4096 dim.
- **llama4:scout** — new long-context capability (~200K–1M effective for RAG, advertised 10M); multimodal, fits 12GB (~10GB Q4)
- qwen3:14b still SOTA reasoning ≤14B; qwen3:4b-q8_0 still best classifier
- Full survey + advisor review: `docs/findings/model-updates-2026-05.md`
Sessions 75-82 (2026-05-29→06-02): infra (Ollama store→I:\, `q8_0` KV cache, tiny models pulled); **all 14B → 32K ctx**; **LTG extractor retrofit complete** (routing.py/schemas.py/ModelClient, 148 tests); **LTG Phase 3 anchor decisions FROZEN** (dual-path + alias-link; next = `anchors.py` TDD).
Session 83 (2026-06-04): **Session-handoff pipeline** side-track — Scope A design frozen (register-driven deterministic, no local model); `registry.yaml` + `(T-NN)` task IDs done.
Session 84 (2026-06-04): handoff pipeline **B2 safety core** — F1/F3/F4, 31 tests.
Session 85 (2026-06-05): handoff pipeline **B3 milestone complete** — F5 Mechanics / F6 Orchestrator+git adapter / per-run logging in `overlays/session-tracking/files/handoff/`, 53 tests green. Scope A spine functionally complete; next = B4 (F7 schema + SKILL rewrite).
Sessions 86–87 (2026-06-05/06): handoff pipeline **B4 complete — Scope A fully done, dog-food-validated.** F7 payload schema + `handoff.py`/`registry_io.py` entrypoint + `run-handoff.sh`; manifest install layout (register via `manual_if_exists` = Option C, propagate-with-flag); `SKILL.md` rewritten (decide content → one payload → one `run-handoff.sh` call). Clone dog-food found+fixed a real append/replace **newline-glue bug** F4 was blind to (`_normalize_block` at the `_collect_edits` seam); **77 tests green.**
Active branch: `feature/session-handoff-pipeline` (stacked on `feature/ltg-phase3-anchors`).

## Repo Structure

```
llm/
  mcp-server/    # MCP bridge server (Python/FastMCP) — Claude Code ↔ Ollama
  personas/      # 35+ specialized model configs from 13 base models
  evaluator/     # Two-phase evaluation framework (automated + LLM-as-judge)
  benchmarks/    # Multi-language code validation suite
  overlays/      # Portable scaffolding packages for cross-repo consistency
  modelfiles/    # Ollama Modelfile definitions
  retrieval/     # LTG substrate — Phases 1+2 complete; Phase 3 next (anchors.py)
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
