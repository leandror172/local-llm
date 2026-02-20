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

- [x] 3.5 Conversational persona builder — **COMPLETE** (session 23-24)
  - Branch: `feature/task-3.5-conversational-builder` (pending PR + merge)
  - Plan: `docs/plans/2026-02-18-conversational-persona-builder.md` (5 tasks)
  - **✅ Task 1:** `my-persona-designer-q3` persona created + registered
  - **✅ Task 2:** `personas/lib/ollama_client.py` — sync urllib client (3 tests passing)
  - **✅ Task 3:** `personas/build-persona.py` — core LLM builder (3 tests passing)
    - importlib used for `detect-persona.py` (hyphenated filename — can't import directly)
    - Constraint sanitization: commas within constraints replaced with semicolons before `--constraints` join
  - **✅ Task 4:** `personas/run-build-persona.sh` — wrapper with `python3 -u` (stdout unbuffering fix)
  - **✅ Task 5:** Integration verified (11/11 tests), live persona created (`my-rust-async-q3`), docs written
  - Tests: `./benchmarks/test-build-persona.sh` (use `./` not `bash` — enables Claude Code whitelist)
  - Docs: `personas/BUILD-PERSONA.md`
  - **Follow-ups (deferred, not blocking Layer 4):**
    - [ ] 3.5-A: Test `my-persona-designer-q3` with `qwen3:14b` backend — 14B would improve nuanced constraint inference (e.g., "Java + Spring Boot + enterprise" → infers Jakarta EE namespace, constructor injection, OpenAPI annotations without being told). Tradeoff: 32 tok/s vs 51 tok/s, and 4K ctx limit on RTX 3060 12GB (vs 16K for 8B). Worth benchmarking quality difference on representative descriptions.
    - [ ] 3.5-B: Implement Option 3 multi-round conversation loop — LLM asks one clarifying question at a time, user responds, N turns before proposing spec. More natural UX but: requires history list management, qwen3:8b degrades past ~4K history tokens, latency compounds (~4s × N turns), terminal UX awkward with thinking delays between questions. Current Option 2 (single-shot + one refinement) chosen as sweet spot; Option 3 is the natural next step if interactive feel becomes a priority.

### Persona Inventory (29 active)
**Specialized coding:** my-java-q3, my-go-q3, my-python-q3, my-react-q3, my-angular-q3, my-creative-coder(-q3), my-codegen-q3
**Code reviewers:** my-java-reviewer-q3, my-go-reviewer-q3
**Architecture:** my-architect-q3 (14B), my-be-architect-q3, my-fe-architect-q3
**Cloud consulting:** my-aws-q3, my-gcp-q3
**LLM infrastructure:** my-shell-q3, my-mcp-q3, my-prompt-eng-q3
**NLP / utility:** my-classifier-q3, my-summarizer-q3, my-translator-q3, my-ptbr-q3, my-tech-writer-q3
**Life / career:** my-career-coach-q3
**Legacy fallback:** my-coder, my-coder-q3 (polyglot Java+Go — prefer specialists)
**Bare (tool wrappers):** my-aider, my-opencode
**Rust async:** my-rust-async-q3 (added during 3.5 live e2e test)

### Future Persona Candidates (not yet built)
Identified during 3.5-A designer comparison test design — abstract personas that proved
interesting to reason about and could be genuinely useful:
- **my-code-archaeologist-q3**: Reads unfamiliar legacy codebases and explains what they
  actually do — not what comments say. MUST NOT trust comments, MUST read before explaining,
  skeptical framing. Good for onboarding onto inherited code.
- **my-socratic-tutor-q3**: Never gives direct answers; leads through questions.
  MUST NOT state answers, MUST ask ≥1 question per response, domain-agnostic.
  Useful for learning sessions where spoon-feeding defeats the purpose.

### Creator Tool
- Script: `personas/create-persona.py` — interactive 8-step flow or `--non-interactive` flags
- Wrapper: `personas/run-create-persona.sh` — whitelist-safe, auto-approved
- Features: model selection (Task 3.3), domain defaults, name suggestion, collision guard, `--dry-run`

### MCP Enhancement Tasks (deferred — Layer 1 catch-up)
Current MCP server (Layer 1) has 6 generic tools but predates Layer 3 persona system.
These tasks bring the MCP in sync with persona infrastructure:
- [ ] **MCP-1: Persona-aware routing** — `generate_code` currently routes by language to generic models. Should use `registry.yaml` to pick the best specialized persona (e.g., Java → `my-java-q3`, Go → `my-go-q3`). `ask_ollama` could also accept an optional persona parameter.
- [ ] **MCP-2: Detect persona tool** — New MCP tool: given a codebase path, call `detect()` and return ranked persona matches. Lets Claude Code auto-suggest the right local model for a repo.
- [ ] **MCP-3: Build persona tool** — New MCP tool: given a free-form description, call `build-persona.py --describe "..." --json-only --skip-refinement` and return the proposed spec. Non-interactive mode fits MCP request/response perfectly.
- [ ] **MCP-4: Persona registry query** — New MCP tool: query `registry.yaml` — "list all personas", "which personas handle Java?", "show constraints for my-java-q3". Gives Claude Code visibility into what local models are available.

### Design Decisions
- **Specialization over generalization:** Narrow personas outperform broad ones at 7-8B. my-java-q3 with `MUST use jakarta.*` beats generic my-coder-q3 that tries to cover both Java and Go.
- **Constraint-driven prompts:** Each MUST/MUST NOT targets an observed failure mode (e.g., javax.persistence from Layer 2, unquoted variables in shell).
- **Two-tier system:** Full personas (SYSTEM + all params) vs bare personas (minimal, for external tools like Aider/OpenCode).
- **Registry as source of truth:** `personas/registry.yaml` — machine-readable, appended by creator tool.
- **Raw text append:** PyYAML strips comments on round-trip; registry uses comment section headers, so creator appends raw YAML text.
