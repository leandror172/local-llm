# llm/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status

Layers 0-4 complete (of 10-layer plan). Infrastructure fully operational.
Layer 5+ active: expense classifier using the MCP bridge for local inference.
Session 47 was most recent (2026-03-26): technology conventions pattern doc.

## Repo Structure

```
llm/
  mcp-server/    # MCP bridge server (Python/FastMCP) — Claude Code ↔ Ollama
  personas/      # 35+ specialized model configs from 13 base models
  evaluator/     # Two-phase evaluation framework (automated + LLM-as-judge)
  benchmarks/    # Multi-language code validation suite
  overlays/      # Portable scaffolding packages for cross-repo consistency
  modelfiles/    # Ollama Modelfile definitions
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
