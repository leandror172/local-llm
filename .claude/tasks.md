# Task Progress

**Last Updated:** 2026-02-27 (session 35)
**Active Layer:** Layer 5 — Expense Classifier
**Full history:** `.claude/archive/phases-0-6.md`, `.claude/archive/layer-0-findings.md`

---

## Completed (summary)

- **Phases 0-6:** Infrastructure setup complete (Ollama, models, Docker, verification, docs)
- **Layer 0:** Foundation upgrades complete (12/12) — Qwen3 models, benchmarks, structured output, thinking mode strategy, decomposition, runtime validation, few-shot examples
- **Layer 1:** MCP Server complete (7/7 + MCP-1/2/3/4) — FastMCP server, 9 tools, persona-aware routing, system-wide availability

---

## Layer 2: Local-First CLI Tool

**Goal:** A Claude Code-like interface running against local Ollama, with optional frontier escalation (Pattern A: local-first, escalates up).

- [x] 2.1 Evaluate tools: landscape survey of 34 CLI tools → Aider (primary) + OpenCode (comparison)
- [x] 2.2 Install and configure Aider v0.86.2 + OpenCode v1.2.5 with Ollama backend
- [x] 2.3 Configure frontier fallback → `.env` with 7 providers (dormant), CLI-flag toggle
- [x] 2.4 Five-tool comparison test (Aider, OpenCode, Qwen Code, Goose, Claude Code) — see `docs/findings/layer2-tool-comparison.md`
- [x] 2.5 Decision guide written — `docs/findings/layer2-tool-comparison.md` § "Decision Guide"

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
  - **Follow-ups:**
    - [x] 3.5-A: Persona designer comparison benchmark — 8b, 14b, Claude Haiku compared. Finding: 8b production-ready, 14b not worth 3x perf hit, Claude Haiku best at abstract intent. Branch: `feature/task-3.5-A-comparison` (unmerged)
    - [ ] 3.5-B: Implement Option 3 multi-round conversation loop — deferred, not blocking Layer 4

<!-- ref:layer3-inventory -->
### Persona Inventory (30 active)
**Specialized coding:** my-java-q3, my-go-q3, my-python-q3, my-react-q3, my-angular-q3, my-creative-coder(-q3), my-codegen-q3
**Code reviewers:** my-java-reviewer-q3, my-go-reviewer-q3
**Architecture:** my-architect-q3 (14B), my-be-architect-q3, my-fe-architect-q3
**Cloud consulting:** my-aws-q3, my-gcp-q3
**LLM infrastructure:** my-shell-q3, my-mcp-q3, my-prompt-eng-q3
**NLP / utility:** my-classifier-q3, my-summarizer-q3, my-translator-q3, my-ptbr-q3, my-tech-writer-q3
**Life / career:** my-career-coach-q3
**Meta:** my-persona-designer-q3
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

<!-- /ref:layer3-inventory -->

### Creator Tool
- Script: `personas/create-persona.py` — interactive 8-step flow or `--non-interactive` flags
- Wrapper: `personas/run-create-persona.sh` — whitelist-safe, auto-approved
- Features: model selection (Task 3.3), domain defaults, name suggestion, collision guard, `--dry-run`

<!-- ref:layer4-status -->
## Layer 4: Evaluator Framework — COMPLETE

- [x] 4.1 Rubrics: 6 YAML rubric files in `evaluator/rubrics/` (code-go, code-java, code-python, code-general, classification, writing)
- [x] 4.2 evaluate.py: two-phase scoring engine + `evaluator/run-evaluate.sh`
  - Phase 1: automated checks (Go compile/vet, JSON schema) → deterministic scores
  - Phase 2: LLM judge via ollama_chat (one criterion per call, temp=0.1, structured output)
- [x] 4.3 benchmark.py: persona×prompt orchestrator + `evaluator/run-benchmark.sh`
  - VRAM optimization: groups personas by base_model, defers judge to end
  - --dry-run mode, --all-coding discovery, results → `evaluator/results/{timestamp}/`
- [x] 4.4 Prompt sets: 40 prompts across 5 domains (go:10, java:10, python:10, cls:5, shell:5)

### Deferred / Future Evaluator Work
- [x] **4.x Shell rubric** — COMPLETE (2026-02-24, session 29). PR #7. Findings: `docs/findings/shell-benchmark-findings.md`
  - `evaluator/rubrics/code-shell.yaml` — new rubric (1 Phase 1 + 5 Phase 2 criteria)
  - `benchmarks/lib/validate-code.py` — added `validate_shell()` + `.sh` dispatch + shellcheck availability check
  - `evaluator/lib/evaluate.py` — added `shellcheck_clean` case (plan was wrong: else path returned null)
  - `modelfiles/shell-qwen3.Modelfile` — 6 new shellcheck-targeted constraints (SC2207/SC2181/SC2012/SC2064/SC2168/SC2030 eliminated)
  - **Key findings:** Specialist hypothesis not confirmed at 8B (both 66.7%); constraints fix mechanical patterns but not logic errors; sh-01/sh-02 exceed 8B generation capacity at any timeout; sh-04 is best differentiator (specialist 95.2% vs baseline 68.6%)
- [x] **4.x Java/Python Phase 1 validators:** COMPLETE (session 31, PR #8)
  - Python: `validate_python()` via built-in `compile()`, `syntax_valid` criterion in `code-python.yaml`, 5 fixtures
  - Java: `validate_java()` via `javac` with class-name scaffolding + two-pass `missing_dependency` classifier, `compiles` criterion in `code-java.yaml`, 5 fixtures
  - `validate-code.py` now covers Go, Shell, Python, Java
- [x] **4.x sh-01/sh-02 prompt decomposition:** COMPLETE (session 31, PR #8)
  - `01a-log-stats.md`, `01b-log-histogram.md`, `02a-backup-create.md`, `02b-backup-rotate.md`
  - Each targets ~150–250 token output — within 8B reliable window
- [x] **4.x Default timeout bump:** COMPLETE (session 31) — `benchmark.py` DEFAULT_TIMEOUT 300s → 600s
- [ ] **4.x Phase 3 frontier judge:** Extension point designed in `docs/plans/2026-02-21-layer4-discussion-context.md` — Claude API call for subjective/ambiguous cases.
- [ ] **4.6 Claude Desktop insights tool:** Standalone `tools/claude-desktop-insights.py` (split out from original Layer 4 scope).

### Session 28 fixes (committed 41a99ba, branch feature/layer4-evaluator-framework)
- [x] evaluate.py: `result = None` before try block (UnboundLocalError on judge failure)
- [x] benchmark.py: Markdown table separator fix in `generate_report()`
- [x] benchmark.py: `--resume RUN_ID` flag — skip cached generations + evals, rerun only missing

### Discussion context: `docs/plans/2026-02-21-layer4-discussion-context.md`
Key decisions: Stance 3 (Unix-style seams), three-phase scoring, tight scope, 4.6 split to standalone utility

### MCP Enhancement Tasks (Layer 1 catch-up — COMPLETE)
Brought the MCP server in sync with Layer 3 persona infrastructure (session 26):
- [x] **MCP-4: Persona registry query** — `query_personas` tool: filters by language/domain/tier/name, returns JSON
- [x] **MCP-1: Persona-aware routing** — `generate_code` uses registry-driven routes (java→my-java-q3, etc.); `ask_ollama` gains `persona` param with registry validation
- [x] **MCP-2: Detect persona tool** — `detect_persona` tool: runs `run-detect-persona.sh --json-compact` via subprocess
- [x] **MCP-3: Build persona tool** — `build_persona` tool: runs `run-build-persona.sh --describe --json-only --skip-refinement` via subprocess
- [x] **Bugfix:** `build-persona.py` forward-reference error (VALID_TEMPERATURES used before definition)
- New file: `mcp-server/src/ollama_mcp/registry.py` (~170 lines)
- Tool count: 6 → 9; dependency added: `pyyaml>=6.0`

---

<!-- ref:deferred-infra -->
## Deferred Infrastructure / Tooling

Items identified but not yet prioritized — evaluate when relevant layer work begins:

- [ ] **Hook-based auto-resume:** `UserPromptSubmit` Claude Code hook that injects `resume.sh` output as context on session start. Eliminates need for CLAUDE.md instruction to run resume manually. Needs investigation: hook fires every message (not just first), so would need a `.claude/local/session-started` flag to gate it.
- [ ] **ref-integrity checker:** Script that validates all `[ref:KEY]` tags in CLAUDE.md and docs have corresponding `<!-- ref:KEY -->` blocks in `*.md` files, and all blocks are properly closed. Maintenance/QA tool — run after large doc restructures.
- [ ] **ref_lookup cross-repo support:** The MCP `ref_lookup` tool currently reads only from this repo's `.claude/index.md`. Extending it to accept an optional `path` parameter (pointing at another repo's `.claude/` directory) would make cross-repo ref lookups explicit and intentional — rather than relying on one repo's `current-status` block containing notes about the other. Triggered by: observed emergent behavior where Claude inferred the MCP tool could provide "the other repo's perspective" — the inference was directionally correct but fragile (it only worked because the LLM repo's `current-status` block happened to document expense repo state).
- [ ] **ollama-bridge: context_files input for generate_code / ask_ollama:** Currently, passing existing file content to a local model requires Claude to read the file (input tokens) and embed it in the prompt string (output tokens) — the content hits Claude's context twice. A `context_files` parameter that the bridge reads server-side and injects into the Ollama prompt would eliminate this overhead entirely. **API design:** `context_files: [{"path": "/abs/path/to/file.go"}, {"path": "/other/file.go", "start_line": 40, "end_line": 80}]` — list of objects, each with a required `path` and optional `start_line`/`end_line` for slice injection. Bridge reads and formats files as a fenced block section prepended to the user prompt before sending to Ollama. Enables "apply this change to this existing file" patterns without doubling token cost through Claude context.
- [x] **ollama-bridge: log prompt/completion token counts + frontier savings estimate:** COMPLETE (session 38, PR #10). `prompt_eval_count`, `prompt_chars`, `response_chars`, and `claude_tokens_est` ((prompt+system+response chars)/4) now logged in every `calls.jsonl` entry. Verdict instruction in CLAUDE.md + scaffolding-template.md updated: ACCEPTED/IMPROVED verdicts include a rough mental chars/4 estimate — no file reads, no code execution.
- [ ] **ollama-bridge: PostToolUse hook for structured verdict capture:** After each `mcp__ollama-bridge__*` tool call, a `PostToolUse` hook could prompt Claude to record the verdict and append `{prompt_hash, verdict, ts, claude_tokens_est}` to `calls.jsonl` using `prompt_hash` as join key. Currently verdicts live only in session narrative text — not queryable. This closes the loop: `calls.jsonl` would hold both metrics AND verdict for every call, enabling DPO pair assembly without manual `run-record-verdicts.sh` runs. Branch: `feature/verdict-capture-hook`.
- [ ] **Qwen3-Coder-Next feasibility study (80B MoE, 3B active):** At 3-bit quantization ~24GB — technically fits 12GB VRAM + ~26GB free RAM = 38GB, but only ~2GB headroom (high OOM risk). Requires Ollama ≥ v0.15.5 (already satisfied after 0.17.5 upgrade). Investigation tracks: (1) profile actual RAM usage of current hybrid models to see real headroom; (2) evaluate native Linux (no WSL2) — WSL2 adds ~4-6GB RAM overhead from virtualization; running Ollama natively in Linux could recover enough margin. If native Linux route: consider dual-boot or moving WSL2 to native Ubuntu on a separate partition. Not a priority until 30B models are benchmarked and proven insufficient.
- [ ] **expense-reporter config reader: replace runtime.Caller with os.Executable:** `internal/config/config.go` uses `runtime.Caller(0)` to locate `config/config.json` relative to the source file. This breaks on deployment (embedded path points to build machine's source tree). Fix: use `os.Executable()` + walk up to find `config/config.json`, matching the pattern already used in `GetWorkbookPath()` in `root.go`. Low priority until the binary is deployed anywhere.
<!-- /ref:deferred-infra -->

---

<!-- /ref:layer4-status -->

### Design Decisions
- **Specialization over generalization:** Narrow personas outperform broad ones at 7-8B. my-java-q3 with `MUST use jakarta.*` beats generic my-coder-q3 that tries to cover both Java and Go.
- **Constraint-driven prompts:** Each MUST/MUST NOT targets an observed failure mode (e.g., javax.persistence from Layer 2, unquoted variables in shell).
- **Two-tier system:** Full personas (SYSTEM + all params) vs bare personas (minimal, for external tools like Aider/OpenCode).
- **Registry as source of truth:** `personas/registry.yaml` — machine-readable, appended by creator tool.
- **Raw text append:** PyYAML strips comments on round-trip; registry uses comment section headers, so creator appends raw YAML text.

---

## Layer 5: Expense Classifier

**Goal:** Local model classifies expenses, auto-inserts into Excel via expense-reporter Go tool.
**Context:** `docs/vision/expense-classifier-vision.md` (full vision + iterative plan)
**Data inventory:** `docs/vision/expense-classifier-data-inventory.md`
**External data:** `I:\workspaces\expenses\` (auto-category analysis + expense-reporter source)
**Two-repo workflow (session 36):** Layer 5 feature work lives in `~/workspaces/expenses/code/` (expense-reporter repo). This repo holds the MCP thin wrapper (5.8) only. Scaffolding template: `docs/scaffolding-template.md`. Expense repo branch: `feature/claude-code-scaffolding`.

> **REPO BOUNDARY:** Tasks 5.1–5.7 are executed in `~/workspaces/expenses/code/` (expense-reporter repo).
> This file tracks their status only — do NOT execute them here.
> Only task **5.8** (MCP thin wrapper) runs in this repo.

### Pre-work — COMPLETE (sessions 32–35)
- [x] **5.0a** ollama-bridge JSONL logging: `config.py` (CALL_LOG_PATH, LOG_FULL_CONTENT) + `client.py` (_log_call method). Logs to `~/.local/share/ollama-bridge/calls.jsonl`.
- [x] **5.0b** CLAUDE.md: Layer 5+ local-model-first instruction (try local, evaluate, record ACCEPTED/IMPROVED/REJECTED verdict)
- [x] **5.0c** Model audit + new pulls (session 34): qwen2.5-coder:14b, qwen3:8b-q8_0, qwen3:30b-a3b; personas my-go-q25c14 (ACCEPTED), my-go-q3-q8 (IMPROVED), my-go-q3-30b (REJECTED)
- [x] **5.0d** Multi-model comparison tooling: `run-compare-models.sh` + `run-record-verdicts.sh`; first DPO pairs in `benchmarks/results/compare-runs.jsonl`
- [x] **5.0e** Fix `think: false` in `ollama_client.py` — moved from `options{}` to top-level payload in both `personas/lib/ollama_client.py` and `mcp-server/src/ollama_mcp/client.py`. Verified: 82% token reduction, 6.4x speedup. (session 35)
- [x] **5.0f** Reduce `num_ctx` in `go-qwen25c14.Modelfile` from 16384 → 10240 (user chose 10240 over 8192). Rebuilt persona, no OOM. (session 35)
- [x] **5.0g** Create `my-java-q25c14` persona (qwen2.5-coder:14b, Java 21 + Spring Boot 3.x, num_ctx=10240). Registered + smoke-tested. (session 35)
- [x] **5.0h** Set up todaytix-test workspace (`/home/leandror/workspaces/todaytix-test/`) with CLAUDE.md + .mcp.json for Spring Boot exercise. (session 35)

### Layer 5 Tasks (next)
- [ ] **5.1** Port training data into expense-reporter: copy `feature_dictionary_enhanced.json` + `training_data_complete.json` to `data/` in expense-reporter; document format
- [ ] **5.2** `classify` command in expense-reporter: 3-field input → Ollama HTTP → structured JSON → top-N subcategories with confidence
- [ ] **5.3** `auto` command: classify + insert if HIGH confidence (≥0.85), else print candidates
- [ ] **5.4** `batch-auto` command: classify a CSV, write classified.csv (HIGH) + review.csv (LOW)
- [ ] **5.5** Correction logging: `corrections.jsonl` — {input, predicted, actual, confidence} on user override
- [ ] **5.6** Expense persistence: hash ID (sha256[:12] of normalized item+date+value), `expenses_log.jsonl` appended on insert
- [ ] **5.7** Few-shot injection: keyword pre-match against training data, inject top-K examples into classify prompt
- [ ] **5.8** MCP thin wrapper in llm repo: `classify_expense` / `add_expense` / `auto_add` tools

### Key decisions (from session 32 design)
- Classification logic in **expense-reporter** (Go) — it's a product feature, not LLM infrastructure
- MCP wrapper in **llm repo** — thin, calls the Go binary as subprocess
- Training data strategy: hybrid (feature dict + correction rules as system + top-K few-shot per request)
- Structured output via Ollama `format` param — already proven reliable
- Model to benchmark: Qwen3-8B (`my-classifier-q3`) vs Qwen2.5-Coder-7B (speed)
