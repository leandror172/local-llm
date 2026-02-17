# Task Progress

**Last Updated:** 2026-02-17
**Active Layer:** Layer 3 — (see plan-v2.md for definition)
**Full history:** `.claude/archive/phases-0-6.md`, `.claude/archive/layer-0-findings.md`

---

## Completed (summary)

- **Phases 0-6:** Infrastructure setup complete (Ollama, models, Docker, verification, docs)
- **Layer 0:** Foundation upgrades complete (12/12) — Qwen3 models, benchmarks, structured output, thinking mode strategy, decomposition, runtime validation, few-shot examples
- **Layer 1:** MCP Server complete (7/7) — FastMCP server, 6 tools, system-wide availability

---

## Layer 2: Local-First CLI Tool

**Goal:** A Claude Code-like interface running against local Ollama, with optional frontier escalation (Pattern A: local-first, escalates up).

- [x] 2.1 Evaluate tools: landscape survey of 34 CLI tools → Aider (primary) + OpenCode (comparison)
- [x] 2.2 Install and configure Aider v0.86.2 + OpenCode v1.2.5 with Ollama backend
- [x] 2.3 Configure frontier fallback → `.env` with 7 providers (dormant), CLI-flag toggle
- [x] 2.4 Five-tool comparison test (Aider, OpenCode, Qwen Code, Goose, Claude Code) — see `tests/layer2-comparison/findings.md`
- [x] 2.5 Decision guide written — `tests/layer2-comparison/findings.md` § "Decision Guide"

### Key Findings
- **Tool-calling wall at 7-8B:** All tool-calling agents (OpenCode, Qwen Code, Goose) failed locally. Only Aider's text-format works reliably.
- **Groq free tier incompatible with tool-calling agents:** Tool-definition overhead ≈16K tokens exceeds 12K TPM limit. Gemini free tier needed.
- **Aider quality limits:** `javax.persistence` (wrong namespace for Boot 3.x), broken physics (no coordinate transforms), missed spec requirements. Treat output as draft.
- **Installed tools:** Aider v0.86.2, OpenCode v1.2.5, Qwen Code v0.10.3, Goose v1.24.0
- **Deferred:** Qwen Code with qwen3-coder (smallest = 30B, 19GB — needs hardware upgrade)

### Closing-the-gap integration
- Cascade pattern (#14): frontier fallback via Aider `--architect` mode or `.env` API keys
- Best-of-N (#10): can run same prompt through Aider + OpenCode and compare

### Unlocks
- Coding continues when Claude quota is depleted
- Unlimited experimentation and iteration
- Persona testing without frontier token cost
