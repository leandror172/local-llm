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
- **Session 51** (2026-04-13) — Smart RAG research + Latent Topic Graph concept & plan:
  - 7-source research cluster on content-linking retrieval (`ref:smart-rag-research`); see `docs/research/smart-rag-*.md` (8 files)
  - Named concept: **Latent Topic Graph (LTG)** — topic-level nodes, files-as-containers, anchor stratification, multi-scale. Concept paper at `ref:concept-latent-topic-graph` is publishable-grade
  - Implementation plan: `ref:plan-latent-topic-graph` (10 phases, Phase 0 decisions required at session start, `relate(a,b)` as acceptance test, ~3 sessions to MVP)
  - plan-v2 Layer 7 task 7.11 **promoted** from vanilla RAG to cross-cutting substrate; executes in parallel with Layers 5/6
  - web-research MCP tool tested live (arxiv extraction, 46s via qwen3:14b)
  - Branch: `feature/smart-rag-research` — merged as commit e639b5e
- **Session 52** (2026-04-14) — LTG Phase 0 decisions frozen + plan re-indexed:
  - All 8 Phase 0 decisions resolved and recorded in `retrieval/DECISIONS.md` (new top-level `retrieval/` directory). Each entry: decision / rationale / alternatives / revisit trigger.
  - Notable non-default outcomes: **embedding** flipped to `bge-m3` via Ollama after confirming `ollama pull bge-m3` works (eliminates runtime split); **storage** simplified to pure LanceDB + sidecars (SQLite layer rejected for MVP); **extractor** deferred to empirical A/B in Phase 1 with 11-dim rubric, 5-6 models × 8 files + long-file appendix, exit threshold ≥ 2.2
  - Plan re-indexed: 19 narrow `ref:KEY` blocks replace single file-wide block. `plan-latent-topic-graph` now wraps intro+goal only; per-phase keys `ltg-plan-phase-0..9` + section keys `ltg-plan-{required-reading,deferred,relationship,integration,risks,estimate,success,handoff}`. Phase 0/1/2 annotated with forward references to session 52 resolutions.
  - Decision ref keys (in `retrieval/DECISIONS.md`): `ltg-scope`, `ltg-embedding`, `ltg-vector-store`, `ltg-graph-lib`, `ltg-extractor`, `ltg-placement`, `ltg-storage-layout`, `ltg-corpus`, `ltg-notes`.
  - New feedback memory: batch multiple edits into one Write or parallel calls on Opus (sequential Edits burn cost). Captured mid-session after user flagged it.
  - Chore commits: `.mcp.json` gains web-research MCP entry; 3 `/copy` snapshot files saved under `docs/ideas/smart-rag-phase-0-response-*.md`.
  - Branch: `feature/ltg-phase0` (3 commits: docs + 2x chore)
- **Session 53** (2026-04-15) — ref-lookup prefix search + Phase 1 extractor spike (runner built):
  - `ref-lookup.sh` gains glob mode (`KEY*`) + digit-key fix in `--list`; overlay ref-indexing v2; PR #30
  - Phase 1 corpus: 8 files selected (7 prose + 1 code). `retrieval/prompts/extract.txt` + `retrieval/extract_topics.py` built via local-model workflow (q25c14 + gemma3:12b IMPROVED; Claude version chosen as final)
  - MCP `client.py` fix: `timeout=None` on AsyncClient + fresh client per `chat()` call (fixes stale connection after cancelled requests)
  - Deferred: `ModelCaller` Protocol for `extract_topics.py` (in `ref:deferred-infra`)
  - `cozempic` window bug: reports 1.00M, actual 200K — multiply reported % by 5×
  - Branch: `feature/ltg-phase1-extractor-spike` (commit 80e7ebf)
- **Active branch:** `feature/ltg-phase1-extractor-spike` (PR not yet opened — run sweep first)
- **Prior active branch:** `feature/ref-lookup-prefix-search` (PR #30 open); `feature/ltg-phase0` (PR open, under review); `feature/gemma3-benchmark` (PR still not opened)
- **Open deferred tasks:** hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix (tracked in expenses repo), Python 3.10→3.12 via uv, Layer 4 stragglers (Phase 3 frontier judge, claude-desktop insights tool 4.6), raw temperature values, registry hot-reload, server.py refactor, file-based coordination layer (watch PR #9392), ModelCaller Protocol for extract_topics.py, extract create-persona.py into importable library, `add_model` MCP tool, gemma4 on Ollama (check ~2026-04-23)
- **Next:** **Run the Phase 1 sweep** (`python3 retrieval/extract_topics.py` from repo root) — 4 models × 8 corpus files. Score dims 1-4 auto; fill dims 5-8 manually in `retrieval/runs/*-manual-rubric.md`. Exit threshold: weighted quality ≥ 2.2. Document results in `retrieval/spike-results.md`, then open PR for `feature/ltg-phase1-extractor-spike`. Also: **Phase 2 VRAM co-residence probe** (qwen3:14b + bge-m3 on 12GB card, required before locking embedding). Still open: PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; read `claude-code/src/services/mcp/normalization.ts` before next MCP refactor; Layer 4 stragglers; registry hot-reload; server.py refactor
- **Cross-repo:** MVP spike executing in web-research repo sessions; expense MCP work executing in expenses repo sessions; PR #21 merged (`feature/persona-mcp-tools`); .memories/ PRs merged in expenses + web-research
- **Two-repo workflow:** Feature work in `~/workspaces/expenses/code/`; MCP wrapper in this repo
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands)
<!-- /ref:current-status -->

---

<!-- ref:local-model-retry-patterns -->
## Local Model Retry Patterns

When Ollama output is imperfect, classify by **defect type × fix scope × prompt cost**:

- **Mechanical** (syntax, typo, wrong import) → IMPROVED, inline always
- **Structural, 1–2 isolated sites** → inline (IMPROVED or REJECTED based on effort)
- **Structural, 3+ sites or interdependent** → REJECTED + stubs-then-Ollama if interface definable; scratch if not
- **Conceptual** (correct syntax, wrong behavior) → REJECTED, write from scratch
- **Prompt cost tiebreaker:** if explaining > fixing → inline regardless of scope

Stubs-then-Ollama: write stub signatures, call Ollama with stubs in `context_files`. First call = REJECTED triple; second call gets its own verdict (often ACCEPTED). Both are clean DPO signal.

Cold-start timeouts → `TIMEOUT_COLD_START`, not REJECTED. No DPO triple recorded. Retry immediately. Use `warm_model` MCP tool to eliminate cold starts.

Full decision tree: `docs/scaffolding-template.md` § "Handling Imperfect Output: Decision Tree"
<!-- /ref:local-model-retry-patterns -->

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

### Layer 5 Model Decisions (decided 2026-02-26/27, sessions 34-35)
- **Preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, ACCEPTED quality. Speed tradeoff acceptable ("free tokens" philosophy).
- **qwen3:30b-a3b not recommended for focused tasks:** Dropped `id` field from constructor on first real test. Larger ≠ better for narrow coding prompts.
- **qwen3:8b think:false FIXED (session 35):** Was broken because `think` was inside `options{}` — Ollama silently ignores it there. Fix: top-level payload parameter. Verified: 701→124 tokens, 16.7s→2.6s, chars/token 1.51→3.65.
- **num_ctx doesn't require powers of 2:** Chose 10240 for 14B models (balances context vs VRAM). KV cache formula: `2 × layers × kv_heads × head_dim × ctx × 2bytes`.
- **Multi-model comparison → DPO pairs:** Pattern established. Use `run-compare-models.sh` for each code gen task, collect verdicts with `run-record-verdicts.sh` in terminal. Results feed Layer 7 pipeline.
- **Java persona on 14B:** `my-java-q25c14` created for Spring Boot exercise. Same constraints as `my-java-q3`, different base model.
- **Future candidates deferred:** qwen3.5:35b-a3b (released 2026-02-24, too new + 24GB tight on this system); qwen3-coder:30b (pull after qwen3:30b-a3b validated on more tasks).

### Historical decisions (Phases 0-6, Layer 0)
Archived → `.claude/archive/phases-0-6.md` (setup decisions, gotchas, artifact tables)
<!-- /ref:active-decisions -->
