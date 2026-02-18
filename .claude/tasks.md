# Task Progress

**Last Updated:** 2026-02-17 (session 21)
**Active Layer:** Layer 3 — Persona Creator
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

---

## Layer 3: Persona Creator

**Goal:** A system that builds, tests, and refines Modelfile personas through conversation.

- [x] 3.1 Design persona template — `personas/persona-template.md` (fields, defaults, skeleton, model selection guide)
- [x] 3.6 Create specialized persona set — 8 new personas (java, go, python, shell, mcp, prompt-eng, ptbr, tech-writer)
- [x] 3.5 Persona registry — `personas/registry.yaml` (28 active, 0 planned)
- [x] 3.2 Build conversational persona creator — `personas/create-persona.py` + `run-create-persona.sh`
- [x] 3.3 Model selection logic — embedded in creator (MODEL_MATRIX: domain → model + ctx + temp)
- [x] 3.4 Codebase analyzer — file-based persona detection (returns top 3 with confidence scores)
  - **COMPLETE:** Phase 1, 2, 3 all done ✓
  - Phase 1: Core detection, 3-signal scoring, 5 test fixtures (all passing)
  - Phase 2: Advanced import/config parsing (package.json, pom.xml, requirements.txt, go.mod)
  - Phase 3: Polish, documentation (DETECT-PERSONA.md), error handling
  - Merged to master (PR #2)
  - Input: directory path; Output: ranked personas with confidence (0.0–1.0)
  - Callable as Python function + standalone CLI (`personas/run-detect-persona.sh`)
  - Heuristics: file extensions (50%), imports (30%), config files (20%)

- [x] **Layer 3 Refactoring** (bonus work: all PR #1 deferred items)
  - **Refactor 1:** MODEL_MATRIX → personas/models.py (centralized, reusable)
  - **Refactor 2:** Input helpers → personas/lib/interactive.py (ask, ask_choice, ask_multiline, ask_confirm)
  - **Refactor 3:** TEMPERATURES consolidation (dict-of-dicts, prevents drift)
  - Result: create-persona.py reduced by 155 lines; clean foundation for Task 3.5
  - PR #3 created (awaiting merge to master)

- [ ] 3.5 Conversational persona builder — use LLM + detect() to elicit constraints interactively
  - Input: natural language via dialogue
  - Call detect() for file-based hints (seed dialogue with detected language)
  - Use lib.interactive helpers for consistent prompting UX
  - Ask clarifying questions; propose constraints based on LLM reasoning + feedback
  - Fall back to creator CLI if no match found
  - **Status:** Ready to start (foundation refactored, all prep work done)

### Persona Inventory (28 active)
**Specialized coding:** my-java-q3, my-go-q3, my-python-q3, my-react-q3, my-angular-q3, my-creative-coder(-q3), my-codegen-q3
**Code reviewers:** my-java-reviewer-q3, my-go-reviewer-q3
**Architecture:** my-architect-q3 (14B), my-be-architect-q3, my-fe-architect-q3
**Cloud consulting:** my-aws-q3, my-gcp-q3
**LLM infrastructure:** my-shell-q3, my-mcp-q3, my-prompt-eng-q3
**NLP / utility:** my-classifier-q3, my-summarizer-q3, my-translator-q3, my-ptbr-q3, my-tech-writer-q3
**Life / career:** my-career-coach-q3
**Legacy fallback:** my-coder, my-coder-q3 (polyglot Java+Go — prefer specialists)
**Bare (tool wrappers):** my-aider, my-opencode

### Creator Tool
- Script: `personas/create-persona.py` — interactive 8-step flow or `--non-interactive` flags
- Wrapper: `personas/run-create-persona.sh` — whitelist-safe, auto-approved
- Features: model selection (Task 3.3), domain defaults, name suggestion, collision guard, `--dry-run`

### Design Decisions
- **Specialization over generalization:** Narrow personas outperform broad ones at 7-8B. my-java-q3 with `MUST use jakarta.*` beats generic my-coder-q3 that tries to cover both Java and Go.
- **Constraint-driven prompts:** Each MUST/MUST NOT targets an observed failure mode (e.g., javax.persistence from Layer 2, unquoted variables in shell).
- **Two-tier system:** Full personas (SYSTEM + all params) vs bare personas (minimal, for external tools like Aider/OpenCode).
- **Registry as source of truth:** `personas/registry.yaml` — machine-readable, appended by creator tool.
- **Raw text append:** PyYAML strips comments on round-trip; registry uses comment section headers, so creator appends raw YAML text.
