# Session Context for Future Agents

**Purpose:** User preferences and working context across Claude Code sessions.

---

<!-- ref:user-prefs -->
## User Preferences

### Interaction Style
- **Output style:** Explanatory (educational insights with task completion)
- **Pacing:** Interactive — pause after each phase for user input
- **Explanations:** Explain the "why" for each step, like a practical tutorial

### Configuration Files
- **Build incrementally:** Never dump full config files at once
- **Explain each setting:** Add a setting, explain what it does, then add the next
- **Ask before proceeding:** Give user options before making non-obvious choices

### Persona Naming
- Pattern: `my-<role>` (my-coder, my-creative-coder)
- Qwen3 variants get `-q3` suffix (my-coder-q3, my-creative-coder-q3)
<!-- /ref:user-prefs -->

---

## File Management

### Sensitive Data
- **Location:** `.claude/local/` (gitignored)
- **Rule:** System specs, paths, or personal info → write to `local/`

### Log Rotation
- **Tool:** `.claude/tools/rotate-session-log.sh` — run at session end via session-handoff skill
- **Policy:** Keep 3 most recent sessions in `session-log.md`; archive the rest
- **Archive:** `.claude/archive/session-log-YYYY-MM-DD-to-YYYY-MM-DD.md`

### Context Optimization
- **System-prompt files** (CLAUDE.md, MEMORY.md): Keep lean — rules + current state only; history in archives
- **Session files** (tasks.md, this file): Only active layer + pointers to archives
- **Knowledge index:** `.claude/index.md` maps every topic to its file location
- **Archives:** `.claude/archive/` — full historical data, read on demand

---

<!-- ref:current-status -->
## Current Status

- **Phases 0-6:** Complete → `.claude/archive/phases-0-6.md`
- **Layer 0:** Complete (12/12) → `.claude/archive/layer-0-findings.md`
- **Layer 1:** Complete (7/7) — MCP server built, all tools verified, system-wide availability
- **Layer 2:** Complete (5/5) — Tools installed, tested, findings documented
- **Layer 3:** Complete (5/5 + refactoring + 3.5-A comparison) — 30 active personas
- **Layer 4:** Complete — evaluator framework, shell rubric, Phase 1 validators (Python + Java), prompt decomposition, all merged to master (PR #6, #7, #8)
- **Last checkpoint:** Sessions 32+33 (2026-02-26, forked) — Layer 5 design + pre-work complete:
  - Pre-work 5.0a: ollama-bridge JSONL call logging active (`~/.local/share/ollama-bridge/calls.jsonl`)
  - Pre-work 5.0b: CLAUDE.md updated with local-model-first instruction for Layer 5+
  - Layer 7 expanded: SFT/DPO/QLoRA pipeline (7.6–7.11) + prompt pre-processor (7.10) planned; DPO caveat documented (personal use vs ToS); see `plan-v2.md`
  - Vision docs: `docs/vision/expense-classifier-vision.md`, `docs/vision/expense-classifier-data-inventory.md`
  - Educational ref: `docs/findings/LoRA.md` — LoRA/RAG/distillation concepts from session Q&A
  - (Session 33 handoff was done in a fork; Session 32 log has distillation details)
- **Branch:** `master` (clean — commits 8666c0e, 532c862, f6d2d7c)
- **Next:** Layer 5 implementation — task 5.1: port `feature_dictionary_enhanced.json` + `training_data_complete.json` into expense-reporter `data/`; then 5.2: `classify` command in Go
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands)
<!-- /ref:current-status -->

---

<!-- ref:resume-steps -->
## Quick Resume

Run `.claude/tools/resume.sh` for a compact session-start summary (replaces reading multiple files).

Or manually:
1. `ref-lookup.sh current-status` — current layer, next task, branch state
2. Tail of `.claude/session-log.md` — "Next" pointer from most recent session
3. `git log --oneline -3` — recent commits
4. `.claude/index.md` — find any specific file/topic on demand
<!-- /ref:resume-steps -->

---

<!-- ref:active-decisions -->
## Active Decisions

### Plan v2 Architecture (decided 2026-02-07)
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both
- **MCP server** is highest-priority routing implementation (Pattern B — enhances Claude Code)
- **Multiple models:** Right model per role, not just best coder → `docs/model-strategy.md`
- **Closing-the-gap:** Ongoing principles + one-time tasks, integrated into every layer
- **OpenClaw:** Deferred until security planning (Layer 6)
- **Full vision:** `docs/vision-and-intent.md`

### Layer 1 Decisions (decided 2026-02-12)
- **MCP server language:** Python (FastMCP) — lowest tool friction, best ecosystem for general-purpose
- **Scope:** General-purpose LLM gateway (coding, scraping, PDF, research, conversation)
- **Licensing rule (STRONG):** Always check + honor external project licenses. If attribution required, add to `docs/ATTRIBUTIONS.md`. Never skip this.
- **Reference existing work:** Borrow architectural patterns with attribution from llm-use, ultimate_mcp_server, locallama-mcp, MCP-ollama_server
- **Research archive:** `.claude/archive/layer-1-research.md`

### Layer 2 Decisions (decided 2026-02-16/17)
- **Tool selection:** Aider (primary) + OpenCode (comparison). Aider chosen for text-format editing (no JSON tool-calling required — critical for 7-8B models). OpenCode for comparison + future use with larger models.
- **Architecture insight:** Two camps — text-format agents (Aider) vs tool-calling agents (OpenCode, Goose, Qwen Code). Tool-calling fails systemically at 7-8B; text-format is reliable.
- **Goose and Qwen Code installed but confirmed broken at 7-8B:** Same root cause as OpenCode local. All tool-calling agents require either 30B+ local model or frontier API.
- **Groq free tier incompatible with tool-calling agents:** Tool-definition overhead ≈16K tokens, exceeds 12K TPM limit. Use Gemini free tier instead.
- **Worktrees must strip `.claude/`:** Other tools' models read CLAUDE.md and skill files, causing context pollution. Strip before using any non-Claude-Code tool.
- **Qwen Code config gotcha:** Provider `id` field must be the actual Ollama model name (e.g., `qwen3:8b`), not a human-readable label — it is sent directly as the model parameter in API calls.
- **Aider quality limits at 7-8B:** `javax.persistence` (old namespace for Spring Boot 3.x), wrong web stack (webflux), `@Autowired` field injection (spec violation), broken physics (coordinate transforms). Treat Aider output as a draft requiring review.
- **`no-auto-commits: true` in Aider:** User found auto-commit disruptive. Enabled by default now.
- **Qwen Code — revisit later:** QwenLM/qwen-code needs qwen3-coder (smallest = 30B, 19GB). Defer until hardware upgrade or cloud option.
- **Findings + decision guide:** `docs/findings/layer2-tool-comparison.md` — full test results, failure taxonomy, when-to-use guide.

### Layer 3 Decisions (decided 2026-02-17 + 2026-02-18)

**Tasks 3.1-3.3, 3.6 (2026-02-17):**
- **Creator tool:** `personas/create-persona.py` — standalone Python script (no venv; PyYAML system-wide). Bash wrapper `run-create-persona.sh` is auto-approved for Claude Code.
- **Registry append = raw text:** PyYAML `dump()` strips all comment section headers. Creator appends raw YAML text block to preserve structure.
- **MODEL_MATRIX:** domain → (model, ctx, default_temp). reasoning→qwen3:14b/4096, classification→qwen3:4b/4096, others→qwen3:8b/16384.
- **Reviewer personas at temp=0.1:** deterministic; same code in → same review findings out.
- **`--constraints` splits by comma:** Constraint strings must not contain commas internally (design constraint of the CLI flag).
- **28 active personas:** All planned personas from registry.yaml are now created and registered.

**Task 3.4 (2026-02-18):**
- **Codebase analyzer as pure heuristics:** No LLM calls, deterministic output. Three-signal weighting: extensions (50%) > imports (30%) > config files (20%).
- **Config file content parsing:** Parse package.json, pom.xml, requirements.txt, go.mod to extract framework keywords. Adds significant accuracy over presence-only detection.
- **Top-3 ranking instead of top-1:** Supports monorepo discovery without decomposition. Top-1 sufficient for single-language codebases; top-3 provides alternatives.
- **Importable detect() function:** Designed for Task 3.5 integration (conversational builder will call `detect(repo_path)` to seed dialogue).
- **Fallback to my-codegen-q3 at 0.5 confidence:** Unknown codebases always return valid result (no errors); caller decides whether to trust fallback.
- **Wrapper script pattern:** `personas/run-detect-persona.sh` is whitelist-safe. Test script updated to use wrapper (not direct python3).
- **Test-driven development:** 5 fixtures (java, go, react, python, monorepo), all passing 100% (5/5).

**Layer 3 Refactoring (2026-02-18, Session 22 extended):**
- **Do refactoring now vs defer:** User caught deferred refactoring items from PR #1. Analyzed cost/benefit: low risk + warm context + immediate benefit for Task 3.5 → decided to execute immediately instead of deferring to Task 3.5.
- **Incremental extraction:** Only extracted when 2+ consumers existed (avoided premature abstraction). MODEL_MATRIX and input helpers extracted because Task 3.5 will also need them.
- **TEMPERATURES consolidation:** Merged TEMPERATURE_MAP + _temp_comment into single dict-of-dicts structure to prevent future drift if new temperatures added. Bug prevention priority.
- **Backward compatibility:** TEMPERATURE_MAP and TEMP_DESCRIPTIONS remain available as properties of TEMPERATURES dict. No breaking changes to existing code.
- **Test via approved wrappers:** All refactoring verified using `personas/run-create-persona.sh` (already approved wrapper script, not direct python3 calls).
- **Incremental commits:** One commit per refactor + summary commit. Improves git traceability and allows reverting individual refactors if needed.
- **Task 3.5 foundation:** Can now import both personas/models.py and personas/lib/interactive.py without reimplementation. No prep work needed; foundation clean and consolidated.

**Task 3.5 (2026-02-19, Session 24):**
- **`importlib` for hyphenated modules:** `detect-persona.py` can't be imported as `detect_persona` (hyphen invalid in identifiers). Use `importlib.util.spec_from_file_location("detect_persona", path)` — stdlib pattern for loading files with non-identifier names.
- **Constraint comma sanitization:** LLM generates "MUST use X, NOT Y" with embedded commas. `build-persona.py` replaces `,` within each constraint with `;` before joining for `--constraints`. Boundary fix; no change to `create-persona.py` API.
- **`python3 -u` in wrapper:** When stdout is a pipe, Python uses full buffering. Subprocess output (raw fd) appears before Python's buffered `print()`. Fix: `-u` flag in wrapper makes stdout unbuffered.
- **`./script.sh` not `bash script.sh`:** Claude Code can whitelist `./specific-script.sh` per-script. `bash script.sh` shows as a generic `bash` invocation — no per-script whitelist option. Convention: always use `./`.
- **29 active personas:** `my-rust-async-q3` added during live e2e test (kept as valid persona).

### Historical decisions (Phases 0-6, Layer 0)
Archived → `.claude/archive/phases-0-6.md` (setup decisions, gotchas, artifact tables)
<!-- /ref:active-decisions -->
