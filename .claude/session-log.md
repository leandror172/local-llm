# Session Log

**Current Layer:** Layer 3 COMPLETE → next: Layer 4 (Evaluator Framework)
**Current Session:** 2026-02-20 — MCP-1/2/3/4 done, housekeeping done, ready for Layer 4
**Previous logs:** `.claude/archive/session-log-layer0.md`

---

## 2026-02-20 - Session 26: MCP-1/2/3/4 — Persona-Aware MCP Tools

### Context
MCP server (Layer 1) had 6 generic tools but predated Layer 3 persona system (30 personas, registry, detector, builder). These 4 tasks bring the MCP server in sync with persona infrastructure. Implementation order: MCP-4 → MCP-1 → MCP-2 → MCP-3.

### What Was Done

**MCP-4: Persona Registry Query Tool**
- New `mcp-server/src/ollama_mcp/registry.py` (~170 lines): load YAML, cache, query, build language routes
- Added `REPO_ROOT` + `REGISTRY_PATH` constants to `config.py`
- Added `LLM_REPO_ROOT` env var export to `run-server.sh`
- Added `pyyaml>=6.0` dependency
- New `query_personas(language?, domain?, tier?, name?)` tool — filters registry, returns JSON

**MCP-1: Persona-Aware Routing**
- Replaced hardcoded `LANGUAGE_ROUTES` with registry-driven `get_language_routes()`
- Added `persona` param to `ask_ollama` with registry validation + suggestions
- Routing now: java→my-java-q3, go→my-go-q3, python→my-python-q3, rust→my-rust-async-q3, etc.
- Fallback dict preserved for when registry isn't loaded
- Language aliases: js→javascript, ts→typescript, golang→go, sh→bash

**MCP-2: Detect Persona Tool**
- New `detect_persona(path)` tool — runs `run-detect-persona.sh --json-compact` via `asyncio.create_subprocess_exec`
- 30s timeout, input validation, structured error returns

**MCP-3: Build Persona Tool**
- New `build_persona(description, codebase_path?)` tool — runs `run-build-persona.sh --describe --json-only --skip-refinement`
- 120s timeout (involves LLM call), optional `--codebase` flag

**Bugfix: build-persona.py forward-reference**
- `VALID_TEMPERATURES` used at line 62 but defined at line 80 — moved definitions above schema

**Verification bugs found and fixed:**
- Dict merge: `routes or fallback` replaced with `{**fallback, **routes}` (registry non-empty = fallback never consulted)
- Qwen3 tiebreaker: when two generalists match same language, prefer `-q3` suffix persona

### Commits
- `f4b6feb` feat: MCP-1/2/3/4 — persona-aware routing and registry tools
- `2e500c1` fix: forward-reference error in build-persona.py

### Decisions Made
- **Subprocess for detect/build:** Clean isolation, no sys.path hacking, reuses existing tested CLI scripts
- **Registry loads once at startup:** Personas change rarely; server restart is trivial (~1s)
- **Merge > replace for routes:** `{**fallback, **registry}` preserves fallback entries (js, css) that can't be detected from role text
- **Qwen3 tiebreaker:** When two generalists tie, prefer `-q3` (newer model) over Qwen2.5 variant

### Housekeeping
- Updated `tasks.md`: MCP-1/2/3/4 marked complete, 3.5-A marked done, persona count 30
- Updated `session-context.md`: current status, branch info
- Updated `session-log.md`: this entry

### Next
- **Merge decision:** Two feature branches still unmerged (`feature/task-3.5-conversational-builder`, `feature/task-3.5-A-comparison`)
- **Layer 4: Evaluator Framework** — define evaluation criteria, build pipeline, benchmark prompt sets

---

## 2026-02-20 - Session 25: Task 3.5-A — Persona Designer Comparison Benchmark

### Context
Resumed with recontextualization after model switch to Sonnet 4.6. Task: build comprehensive benchmark comparing persona designer backends (qwen3:8b, qwen3:14b, Claude Haiku). User requested analysis first (Option 3), then 14B comparison (Option 1), then Claude via sub-agents (Option 2 adapted). Final result: separate branch for 3.5-A work pending merge decision.

### What Was Done

**Phase 1: 8b Analysis (Option 3)**
- Analyzed `persona-designer-compare-20260219-214831.json` (10 test cases, 8b only)
- Identified patterns: strong on domain knowledge, weak on version-implied constraints
- Created `3.5A-ANALYSIS.md` with test-by-test breakdown, strengths/gaps, recommendations

**Phase 2: 8b + 14b Comparison (Option 1)**
- Ran full 10-case benchmark: `./benchmarks/compare-persona-designer.sh --skip-claude`
- Timing: 8b ~12s/case, 14b ~35s/case (3x slower, 4K context limit)
- Quality: 14b avoids explicit errors but doesn't improve over 8b
- Findings: 14b not worth the performance trade-off
- Saved: `persona-designer-compare-8b-14b-FULL.txt`

**Phase 3: Claude via Sub-agents (Option 2 adapted)**
- Spawned Task sub-agents (Haiku, no web search) on 3 key cases
- Test 1 (Axon 4.9): Claude correctly identified Jakarta EE + added eventual consistency, snapshots
- Test 2 (Research agent): Claude took testing-focused approach vs API-focused
- Test 3 (Brainstorm): Claude escalated temp to 0.9 (vs 0.7) + anti-pattern constraints
- Finding: Claude Haiku best-in-class for understanding abstract intent
- Saved: `3.5A-CLAUDE-COMPARISON.md`

**Phase 4: Commit 3.5-A Work**
- Created new branch: `feature/task-3.5-A-comparison` (separate from main task-3.5)
- Added `--designer-model` flag to `build-persona.py` (override backend)
- Added `--verbose` flag to `build-persona.py` (debug output to stderr)
- Created `benchmarks/lib/compare-persona-designer.py` (unified benchmark engine)
- Created `benchmarks/compare-persona-designer.sh` (whitelist-safe wrapper)
- Created `benchmarks/prompts/persona-designer-test-cases.txt` (10 test cases in 3 groups)
- Updated `run-build-persona.sh` usage docs with new flags
- Commit: `8fad0be`

### Decisions Made
- **Designer backend flexibility:** `--designer-model` allows testing any Ollama model (current default: `my-persona-designer-q3`, no change to existing workflows)
- **Separate 3.5-A branch:** Keep benchmark work on dedicated branch, separate from main task-3.5 conversational builder
- **Findings ready, merge pending:** 3.5-A analysis complete; next session decides merge timing
- **Anti-pattern scoring noted:** Claude's success at anti-pattern thinking (avoid disclaimers, avoid caveats) will inform Layer 4 evaluator design

### Key Findings
- **8b:** Production-ready, solid constraint inference, efficient
- **14b:** Not worth 3x performance hit; same quality or avoids constraints instead of solving them
- **Claude Haiku:** Best at understanding abstract intent, escalating temperature appropriately, architectural reasoning
- **Axon test:** Initially thought it failed (8b said jakarta for Axon 4.9), but Claude found Axon 4.9 actually requires Spring Boot 3.x → jakarta is correct. Web search vs pure reasoning trade-off discovered.

### Next
- Decide: merge both `feature/task-3.5-conversational-builder` and `feature/task-3.5-A-comparison` to master (closes Layer 3), or keep separate
- If merged: start Layer 4 (Evaluator Framework) next session
- If kept separate: document merge strategy and resume with next phase

---

## 2026-02-19 - Session 24: Task 3.5 Complete — Layer 3 Done

### Context
Resumed from session 23 (Tasks 1+2 of 3.5 done). Picked up at Task 3 (`build-persona.py`). Also clarified the `bash <script>` vs `./script.sh` pattern — user pointed out `bash` invocations can't be individually whitelisted in Claude Code's permission system.

### What Was Done

**Task 3 — `personas/build-persona.py` (core LLM builder):**
- `build_initial_prompt()`: injects codebase detect results + user description + constraint guidelines
- `build_refinement_prompt()`: passes original spec + feedback for single refinement pass
- `call_designer()`: calls `my-persona-designer-q3` with `PERSONA_SPEC_SCHEMA` structured output
- `validate_spec()`: checks all required fields, domain/temperature enum values, constraint count
- `display_proposal()`: formatted display with temp name resolved from value
- `build_creator_command()` / `handoff_to_creator()`: converts spec dict → `create-persona.py --non-interactive` flags
- **Bug 1 fixed:** `detect-persona.py` has a hyphen → can't `import detect_persona` → used `importlib.util.spec_from_file_location()`
- **Bug 2 fixed:** Embedded commas in LLM constraints ("MUST use X, NOT Y") split incorrectly when passed to `--constraints` → replaced commas within each constraint with semicolons before joining
- Tests: `benchmarks/test-build-persona.sh` (3 cases: describe-only, codebase-seeded, dry-run) — 3/3 passing
- Commit: `c1b6927`

**Task 4 — `personas/run-build-persona.sh` (bash wrapper):**
- Standard wrapper pattern with `PATH` fix for non-interactive WSL shells
- **Bug 3 fixed:** Python stdout fully buffered in pipes → subprocess output appeared before `print()` output → fixed with `python3 -u` (unbuffered mode)
- Commit: `1c8e1d2`

**Task 5 — Integration verification + docs:**
- Full regression: 11/11 tests passing (5 detect + 3 ollama-client + 3 build-persona)
- Live e2e: created `my-rust-async-q3` persona end-to-end (Ollama registered + registry updated)
- Refinement flow tested: "generic backend developer" → Express/TypeScript after feedback
- `personas/BUILD-PERSONA.md`: architecture diagram, usage examples, schema, known limitations
- Tracking files updated, branch ready for PR
- Commit: `01ae817`

**Shell script invocation convention clarified:**
- `./script.sh` instead of `bash script.sh` — the `./` form is whitelistable per-script in Claude Code
- All test scripts confirmed `+x`; going forward always use `./`

### Decisions Made
- **`importlib` for hyphenated modules:** Project uses `kebab-case.py` + bash wrappers; `importlib.util.spec_from_file_location()` is the correct stdlib pattern when you need to import a file whose name isn't a valid identifier.
- **Constraint comma fix in `build-persona.py`:** Replace `,` within constraints with `;` before joining — boundary fix, no change to `create-persona.py` API.
- **`python3 -u` in wrapper:** Unbuffered mode ensures correct output ordering when stdout is a pipe (subprocess output no longer jumps ahead of Python print() output).
- **Keep `my-rust-async-q3`:** Test persona is valid and useful; left in registry + Ollama.

### Next

**Layer 3 complete. Open PR for `feature/task-3.5-conversational-builder` → merge to master → start Layer 4.**

Uncommitted: `personas/registry.yaml` (has `my-rust-async-q3` entry from live test), `modelfiles/rust-async-qwen3.Modelfile` — ask user whether to commit before PR or include in PR.

---

## 2026-02-19 - Session 23: Task 3.5 In Progress — Tasks 1+2 Complete

### Context
Resumed from session 22 (Layer 3 refactoring complete, PR #3 merged to master). Planning on Sonnet → Opus for plan writing → Sonnet for execution. Used subagent-driven-development skill for Tasks 1+2, dropping it for Tasks 3-5 (too token-heavy for Pro plan).

### What Was Done

**Plan written (Opus 4.6):** `docs/plans/2026-02-18-conversational-persona-builder.md`
- 5 tasks: designer persona → sync client → core builder → bash wrapper → integration/docs
- Architecture: single-shot + one refinement pass; `my-persona-designer-q3` on qwen3:8b
- Handoff: LLM spec → `create-persona.py --non-interactive` flags

**Task 1 complete — `my-persona-designer-q3` persona:**
- Created `modelfiles/persona-designer-qwen3.Modelfile`, registered with Ollama
- Appended to `personas/registry.yaml` (now 29 active personas)
- Quality review fix: tier values + constraint count wording improved in system prompt
- Commits: `5efa311`, `e9498c0`

**Task 2 complete — `personas/lib/ollama_client.py`:**
- Synchronous urllib-based Ollama client (no new deps)
- Exports: `ollama_chat(prompt, *, model, system, temperature, think, format_schema, timeout)`
- Returns: `{content, model, eval_count, total_duration_ms}`
- **Bug caught:** dead `except TimeoutError` — urllib wraps socket.timeout inside URLError, must check `isinstance(e.reason, TimeoutError)` inside URLError handler
- **Bug caught:** `HTTPError` must be caught BEFORE `URLError` (it's a subclass)
- Test fixtures committed to `benchmarks/test-fixtures/ollama-client/` (not /tmp/)
- Commits: `9c69c58`, `59e119d`

### Decisions Made
- **Drop subagent framework for Tasks 3-5:** Token cost too high for Pro plan; tasks 3-5 are mechanical.
- **Architecture confirmed:** Two-pass (initial + one refinement), future: multi-round + qwen3:14b test.

### Next

**Task 3 — `personas/build-persona.py` (start here on resume):**
- Full code in plan: `docs/plans/2026-02-18-conversational-persona-builder.md` § Task 3
- Key imports: `ollama_chat`, `detect`, `ask/ask_confirm`, `DOMAIN_CHOICES`, `TEMPERATURES`
- PERSONA_SPEC_SCHEMA has enum for domain, temperature (0.1/0.3/0.7), tier (full/bare)
- Test: `benchmarks/test-build-persona.sh` — 3 cases (describe-only, codebase-seeded, dry-run)
- Then Task 4 (wrapper), Task 5 (integration + BUILD-PERSONA.md)

---

## 2026-02-18 - Session 22 (Continued): Layer 3 Refactoring — PR #1 Deferred Tasks

### Context
Completed Task 3.4 handoff. User flagged three refactoring items from PR #1 review that were deferred. Analyzed cost/benefit and decided to execute all three in same session while context was warm. Used Sonnet for straightforward refactoring.

### What Was Done

**All three PR #1 deferred items completed:**

1. **Refactor 1: MODEL_MATRIX → personas/models.py** (~1 hour)
   - Extracted model selection logic to centralized `personas/models.py`
   - Contains: MODEL_MATRIX, DOMAIN_CHOICES, temperature config, helper functions
   - Updated create-persona.py to import from models.py
   - Reduced create-persona.py by ~80 lines
   - Enables reuse by detect-persona.py, Task 3.5, future tools

2. **Refactor 2: Input helpers → personas/lib/interactive.py** (~50 min)
   - Extracted ask(), ask_choice(), ask_multiline(), ask_confirm() to shared library
   - Created personas/lib/ package structure
   - Updated create-persona.py to import from lib.interactive
   - Reduced create-persona.py by ~75 lines
   - Enables consistent UX across personas package tools

3. **Refactor 3: TEMPERATURE consolidation** (~already done in Refactor 1)
   - Merged TEMPERATURE_MAP + _temp_comment into single TEMPERATURES dict
   - Structure: `{"temp_name": {"value": 0.X, "description": "...", "use_case": "..."}}`
   - Updated _temp_comment() to reference consolidated structure
   - Prevents future drift if new temperatures added
   - Both TEMPERATURE_MAP and TEMP_DESCRIPTIONS available for backward compatibility

**Commits this phase:**
- 11a7152 Refactor 1: Extract MODEL_MATRIX to personas/models.py
- 03923b0 Refactor 2: Extract interactive input helpers to personas/lib/interactive.py
- e9c5c10 Layer 3 refactoring complete: Consolidate persona infrastructure (summary)

**Verification:**
- All refactoring verified via `personas/run-create-persona.sh --help`
- Incremental commits (one per refactor) for clear git history
- Tested via approved wrapper scripts (not direct python3 calls)
- Zero behavior changes; clean refactoring

### Decisions Made

- **Do refactoring now vs defer:** Cost/benefit analysis showed low risk + warm context → immediate benefit for Task 3.5. Avoided premature extraction in Refactor 1 & 2 by deferring secondary consumers (only extracted when 2+ users exist). TEMPERATURE consolidation justified as bug prevention.

- **Incremental commits:** One commit per refactor + summary commit. Improves git history readability and allows reverting individual refactors if needed.

- **Keep backward compatibility:** TEMPERATURE_MAP and TEMP_DESCRIPTIONS still available as properties of TEMPERATURES dict. Prevents breaking existing code.

### Impact

**For Task 3.5:**
- Can now import `from models import MODEL_MATRIX, TEMPERATURES, get_model()`
- Can import `from lib.interactive import ask, ask_choice, ask_multiline, ask_confirm`
- No need to reimplement input logic; consistent UX with create-persona.py
- Foundation is clean, consolidated, reusable

**Code metrics:**
- Reduced create-persona.py by 155 lines (consolidation)
- Created 58 lines in personas/models.py (reusable)
- Created 121 lines in personas/lib/interactive.py (reusable)
- Net: -155 + 58 + 121 = +24 lines (but better organized, reusable)

### Next

**Immediate (next session):**
- Merge `feature/layer3-refactoring-consolidate-personas` to master
- Start Task 3.5 with clean, refactored foundation
- Begin conversational persona builder implementation

**Task 3.5 roadmap:**
- Import and use refactored models.py (model selection)
- Import and use refactored lib/interactive.py (user dialogue)
- Import detect() from detect-persona.py (file-based hints)
- Build LLM-driven constraint elicitation flow
- Integrate with registry for persona lookup

---

## 2026-02-18 - Session 22: Task 3.4 Complete — Codebase Analyzer (3 Phases)

### Context
Resumed from Session 21 (Tasks 3.2/3.3 done, 28 personas registered). Entry point: Task 3.4 (file-based codebase analyzer for persona detection). User requested implementation plan from .claude/plan-v2.md. Completed all three phases in single session. Used Haiku 4.5 for implementation.

### What Was Done

**Task 3.4 Complete: Codebase Analyzer — All 3 Phases**

**Phase 1 — Core Detection** (~550 lines)
- Created `personas/detect-persona.py` with 3-signal detector:
  * File extension heuristics (50% weight): `.java`, `.go`, `.py`, `.tsx`, etc.
  * Import pattern detection (30% weight): Spring, FastAPI, React, gRPC, Angular
  * Config file presence (20% weight): pom.xml, go.mod, package.json, requirements.txt
  * Registry lookup + top-3 ranking by confidence (0.0–1.0)
  * Graceful fallback to `my-codegen-q3` for unknown codebases
- Created `personas/run-detect-persona.sh` — whitelist-safe CLI wrapper
- Built 5 test fixtures: java-backend, go-grpc, react-frontend, python-fastapi, monorepo-mixed
- Created `benchmarks/test-detect.sh` verification script (all 5 tests pass ✓)

**Phase 2 — Advanced Signals** (enhanced parsing)
- Config file *content* parsing (new):
  * `_parse_package_json()` — extracts React/Angular/Vue/Express from dependencies
  * `_parse_pom_xml()` — extracts Spring/Jakarta/Maven from artifactIds
  * `_parse_requirements_txt()` — extracts FastAPI/Django/Flask from packages
  * `_parse_go_mod()` — extracts gRPC/Gin from import paths
- Enhanced IMPORT_PATTERNS with language-specific regex:
  * Python: `(?:import|from)` for fastapi, flask, django, starlette
  * Java: Spring imports, Jakarta EE, gRPC
  * Go: gRPC, Gin, GORM, net/http
  * JavaScript/TypeScript: React, Angular, Vue, Express, Next.js
- Framework keyword bonus scoring (40% of base score for detected frameworks)
- All tests still passing (5/5)

**Phase 3 — Polish & Documentation** (final refinements)
- Created `personas/DETECT-PERSONA.md` — 200+ line comprehensive guide:
  * Algorithm explanation with weight breakdown
  * 12 usage examples (CLI + Python import + edge cases)
  * Supported languages/framework matrix
  * Integration roadmap for Task 3.5
  * Testing instructions
- Improved error handling in main():
  * Path existence and type validation
  * Registry file existence check
  * Better error messages with context (resolved paths in verbose mode)
  * Try/except around detection and JSON serialization
  * Traceback printing in verbose mode
- Enhanced help message with examples
- All tests still passing (5/5)

**Commits this session:**
- 9b86320 Task 3.4 Phase 1: Core codebase analyzer (file-based persona detection)
- 97bbe26 Task 3.4 Phase 2: Advanced import and config parsing
- 9fe21c4 Task 3.4 Phase 3: Polish and documentation
- 844acd0 Mark Task 3.4 as complete (all phases done)

### Decisions Made

- **Use wrapper script instead of direct python3 calls:** User corrected mid-session (correct per project patterns). Updated test-detect.sh to use `personas/run-detect-persona.sh` instead of `python3 personas/detect-persona.py`. Wrapper handles PATH setup for non-interactive shells.

- **Three-signal weighting (50/30/20):** Extensions are strongest signal (files are immutable); imports are good but require parsing; config files are weakest (may be outdated). Per the plan.

- **Config file content parsing as Phase 2 enhancement:** Initially designed as Phase 1 feature, but breaking it out to Phase 2 allowed cleaner separation. Adds ~100 lines but significantly improves detection accuracy (e.g., can distinguish React from Node.js pure apps).

- **Top-3 ranking instead of top-1:** Supports monorepo discovery without decomposition (Phase 2 enhancement deferred). Top-1 is sufficient for single-language codebases; top-3 gives alternatives for edge cases and mixed codebases.

- **Fallback to my-codegen-q3 at 0.5 confidence:** For unknown/empty codebases. Allows CLI to always exit code 0 (no hard failures). Caller decides whether to trust the fallback.

- **Importable detect() function:** Designed for Task 3.5 integration. Returns same JSON structure as CLI for consistency.

- **Registry as single source of truth:** Extract language hints from persona.role string (e.g., "Java 21 backend..." → `['java']`). Avoids maintaining separate metadata file.

### Next

**Immediate (next session):**
- Merge `feature/task-3.4-codebase-analyzer` to master
- Start Task 3.5 (Conversational persona builder) — will import and call `detect()`

**Task 3.5 responsibilities:**
- Import: `from personas.detect_persona import detect`
- Call: `results = detect(user_repo_path)`
- Seed LLM dialogue: "I detected Java. Is this correct?"
- Offer top-1 as suggestion, alternatives (top-2, top-3) as fallback
- Manual constraint entry if user disagrees with detection

**No new gotchas discovered.** Project patterns confirmed stable:
- Bash wrappers for whitelist safety ✓
- Registry as YAML source of truth ✓
- Importable Python modules ✓
- Test fixtures in benchmarks/test-fixtures/ ✓

---

## 2026-02-17 - Session 21: Tasks 3.2 + 3.3 — Persona Creator CLI, 28 Active Personas

### Context
Resumed from Session 20 (Tasks 3.1, 3.5, 3.6 done). Context was compacted before starting. Entry point: Task 3.2 (conversational persona creator). User switched from Opus 4.6 to Sonnet 4.6 mid-session for implementation phase.

### What Was Done

**Task 3.2 + 3.3 Complete: Conversational persona creator with embedded model selection**
- Created `personas/create-persona.py` — standalone Python CLI (~420 lines, no venv needed)
- Created `personas/run-create-persona.sh` — bash wrapper (whitelist-safe; user set auto-approve)
- Features: 8-step interactive flow, `--non-interactive` mode with full flag set, `--dry-run`, collision guard, auto name suggestion
- MODEL_MATRIX embeds Task 3.3 logic: domain → (model, ctx, default_temp); e.g., reasoning → qwen3:14b/4096, classification → qwen3:4b-q8_0/4096
- Domain default constraints per category (code/reasoning/classification/writing/translation/other)
- Registry append uses raw text (not PyYAML round-trip) to preserve comment section headers

**10 remaining planned personas created via the new creator script**

| Persona | Model | Tier | Key role |
|---------|-------|------|---------|
| my-react-q3 | qwen3:8b | full | React 18+ TypeScript frontend |
| my-angular-q3 | qwen3:8b | full | Angular 17+ TypeScript frontend |
| my-architect-q3 | **qwen3:14b** | full | High-level system architect (deeper reasoning) |
| my-be-architect-q3 | qwen3:8b | full | Backend architecture: API design, data modeling, microservices |
| my-fe-architect-q3 | qwen3:8b | full | Frontend architecture: component trees, state management |
| my-aws-q3 | qwen3:8b | full | AWS consultant: services, IAM, cost patterns |
| my-gcp-q3 | qwen3:8b | full | GCP consultant: services, IAM, cost patterns |
| my-java-reviewer-q3 | qwen3:8b | full | Java code reviewer (temp=0.1, deterministic) |
| my-go-reviewer-q3 | qwen3:8b | full | Go code reviewer (temp=0.1, deterministic) |
| my-career-coach-q3 | qwen3:8b | full | Career coach for SW engineers (temp=0.7, PT-BR aware) |

**Registry updated:** 18 → 28 active personas, 0 planned remaining.

### Decisions Made
- **Standalone script (no venv):** PyYAML 5.4.1 already system-wide; avoids uv scaffolding overhead. Follows `ollama-probe.py` pattern.
- **Raw text append for registry:** PyYAML `dump()` strips all comments and section headers. Creator appends raw YAML text block instead. New entries land after the planned comments section (users can reorder manually).
- **`--constraints` splits by comma:** Constraint strings must not contain commas. Documented as design constraint of the tool.
- **`--dry-run` flag:** Safe for Claude Code use (no side effects). Used for verification before committing.
- **Reviewer personas at temp=0.1:** Code review should be deterministic — same code in, same findings out.
- **career-coach at temp=0.7:** Writing/coaching benefits from varied phrasing.
- **my-be-architect-q3 / my-fe-architect-q3 use "other" domain (→ qwen3:8b):** Planned registry specified qwen3:8b. Only my-architect-q3 (top-level) uses qwen3:14b via "reasoning" domain.
- **Auto-approve set for `personas/run-create-persona.sh`:** User will not be prompted for this wrapper again.

### Next
- **Task 3.4:** Auto-detection — analyze a codebase/domain and propose the appropriate persona
- Uncommitted changes from this session (see warning below)

---

## 2026-02-17 - Session 20: Layer 3 Kickoff — Template, Registry, 8 Specialized Personas

### Context
Layer 2 complete. Starting Layer 3 (Persona Creator). Entry point: `.claude/plan-v2.md` Layer 3 definition.

### What Was Done

**Task 3.1 Complete: Persona template specification**
- Created `personas/persona-template.md` — canonical reference for all persona creation
- Codifies the two-tier system (full vs bare personas), ROLE/CONSTRAINTS/FORMAT skeleton
- Temperature guide (0.1/0.3/0.7), model selection decision flow, naming conventions
- Checklist for creating new personas

**Task 3.6 Complete: 8 new specialized personas created and registered**

| Persona | Modelfile | Role | Key Constraints |
|---------|-----------|------|-----------------|
| my-java-q3 | java-qwen3.Modelfile | Java 21, Spring Boot 3.x | jakarta.* not javax.*, constructor injection, records |
| my-go-q3 | go-qwen3.Modelfile | Go 1.22+, Effective Go | Error handling, context.Context, consumer-side interfaces |
| my-python-q3 | python-qwen3.Modelfile | Python 3.11+, FastAPI | Type hints, pathlib, lazy logging, no mutable defaults |
| my-shell-q3 | shell-qwen3.Modelfile | Bash/shell, Linux/WSL2 | set -euo pipefail, quoted vars, [[ ]] over [ ] |
| my-mcp-q3 | mcp-qwen3.Modelfile | MCP server dev (FastMCP) | Async handlers, tool descriptions, structured errors |
| my-prompt-eng-q3 | prompt-eng-qwen3.Modelfile | Prompt engineering (7-14B) | ROLE/CONSTRAINTS/FORMAT, hard language, 120-token limit |
| my-ptbr-q3 | ptbr-translator-qwen3.Modelfile | PT-BR ↔ English | False cognates, tech term preservation, register matching |
| my-tech-writer-q3 | tech-writer-qwen3.Modelfile | Technical docs/READMEs | Active voice, no filler, structure-first, temp=0.7 |

**Task 3.5 Complete: Persona registry**
- Created `personas/registry.yaml` — machine-readable source of truth
- 18 active personas, 10 planned (commented, with metadata)
- Organized by category: specialized coding, LLM infrastructure, NLP/utility, legacy, bare

### Decisions Made
- **Specialization over generalization:** Narrow personas outperform broad ones at 7-8B. Splitting my-coder into my-java-q3 + my-go-q3 (each gets domain-specific constraints).
- **Keep my-coder-q3 as fallback:** Not deleted, marked as polyglot fallback in registry. Prefer specialists for new work.
- **LLM infrastructure personas added:** my-python-q3, my-shell-q3, my-mcp-q3, my-prompt-eng-q3 — the project's own toolstack gets dedicated personas.
- **Constraint design = observed failures:** Each MUST/MUST NOT targets a real failure mode (javax.persistence from Layer 2, unquoted variables in shell, etc.).
- **Deferred 4 personas:** my-react-q3, my-angular-q3, my-ollama-q3, my-career-coach-q3 — no active projects/use cases yet.
- **Taxonomy expanded beyond original plan:** Original plan had 7 generic personas; revised to ~20 specialized ones grouped by domain.

### Next
- **Task 3.2:** Build conversational persona creator (Python CLI — asks questions, generates Modelfile, registers with Ollama)
- **Task 3.3:** Model selection logic (embedded in creator)
- **Task 3.4:** Auto-detection (analyze codebase/domain → propose persona)
- Before starting: commit all uncommitted changes from this session

---

## 2026-02-17 - Session 19: Layer 2 Complete — Testing, Expansion, Findings

### Context
Resumed from Session 18 (Tasks 2.1-2.3 done). Goal: run real coding tests across tools, compare output quality, document decision guide (Tasks 2.4-2.5).

### What Was Done

**Task 2.4 Complete: Five-tool comparison test**

Expanded original Aider + OpenCode plan to 5 tools after discovering OpenCode + local models failed:

| Tool | Model | Result |
|------|-------|--------|
| Aider | qwen2.5-coder:7b (local) | ✅ Executed all 3 tests |
| Claude Code | claude-sonnet | ✅ Executed all 3 tests, higher quality |
| OpenCode | qwen3:8b (local) | ❌ Emitted Python pseudocode instead of JSON tool calls |
| OpenCode | Groq Llama 3.3 70B | ❌ TPM exceeded (tool-definition overhead = 16K tokens, limit = 12K) |
| Qwen Code | qwen3:8b (local) | ❌ No file writes — plan described, tools never invoked |
| Goose | qwen2.5-coder:7b (local) | ❌ Tool calls sent with missing `content` field |

**New tools installed and tested:**
- Goose v1.24.0 (`curl` install, `GOOSE_DISABLE_KEYRING=1` for WSL2, `~/.config/goose/config.yaml`)
- Qwen Code v0.10.3 (`npm install -g @qwen-code/qwen-code`, `~/.qwen/settings.json`)
- Config fix: Qwen Code `id` field must be the actual model name (e.g., `qwen3:8b`), not a display name
- New test worktrees: `test-goose`, `test-qwencode`; all worktrees had `.claude/` stripped to prevent context pollution

**Code quality comparison (Aider vs Claude Code):**

| Test | Aider | Claude Code |
|------|-------|-------------|
| Spring Boot — compiles? | ❌ `javax.persistence` (Boot 3.x needs `jakarta`) | ✅ Correct |
| Spring Boot — runs? | ❌ Wrong web stack (webflux vs web) | ✅ Correct |
| Spring Boot — spec compliance | ❌ `@Autowired` field injection (spec said constructor) | ✅ Constructor injection |
| Visual — physics correct | ❌ Fixed-axis collision in rotated square (ball escapes) | ✅ Coordinate transforms |
| Visual — real trail | ❌ Single fading arc | ✅ 120-position history |
| MCP tool — spec fallback | ❌ Missing char estimate fallback | ✅ Implemented |

**Task 2.5 Complete: Decision guide written**
- Full findings documented in `tests/layer2-comparison/findings.md`
- Decision guide covers: when to use Aider vs Claude Code vs frontier-backed tools
- Failure taxonomy table: 7 failure types with examples and mitigations

### Decisions Made
- **Tool-calling wall is confirmed:** All 3 tool-calling agents failed at 7-8B scale. Not a prompt issue — a model capability threshold. Only text-format (Aider) works reliably locally.
- **Groq incompatible with OpenCode:** Tool-definition overhead exceeds 12K TPM free limit regardless of prompt size. Gemini free tier is the only viable path.
- **`javax` vs `jakarta`** is a hard training cutoff marker — 7-8B models consistently use old namespace for Spring Boot 3.x. Confirmed Aider failure.
- **Spatial reasoning requires scale:** Rotating square physics correct on Claude, broken on qwen2.5-coder:7b. Same pattern as benchmark findings.
- **Aider `no-auto-commits: true` added** — user found auto-commit disruptive.
- **Worktrees must have `.claude/` stripped** — other tools' models read CLAUDE.md and session files, causing context pollution (session-handoff loop in OpenCode was the trigger).
- **Qwen Code `id` field = model name:** OpenAI-compatible provider in Qwen Code uses the provider `id` as the model parameter in API calls, not `model.name`. Must be `qwen3:8b`, not `ollama-local`.
- **Qwen Code revisit deferred:** No viable local model at 7-8B; qwen3-coder smallest local is 30B (19GB). Added to future notes.

### Next
- **Layer 2 is complete (5/5).** Next session should start **Layer 3** — check `.claude/plan-v2.md` for Layer 3 definition.
- Before starting Layer 3: commit all uncommitted changes from this session.
- Optional: Get Gemini API key to give OpenCode a fair test with a working frontier model.

---

## 2026-02-16 - Session 18: Layer 2 Kickoff — Tool Evaluation + Installation

### Context
First session of Layer 2. Layer 1 complete (7/7). Goal: set up a Claude Code-like CLI running against local Ollama with optional frontier escalation (Pattern A: local-first, escalates up).

### What Was Done

**Task 2.1 Complete: Tool landscape evaluation**

Ran 3 parallel research agents surveying the entire local-first CLI tool landscape (Feb 2026):

- **34 tools surveyed** across 5 tiers (major CLIs, niche tools, enterprise, IDE-only, frameworks)
- **Key architectural finding:** Two camps — **text-format agents** (Aider) vs **tool-calling agents** (OpenCode, Goose, Qwen Code, Cline CLI). Tool-calling requires valid JSON from the LLM, which 7-8B models fail at systemically. Text-format is the only reliable path for our Qwen3-8B / RTX 3060 setup.
- **Major new entrants** not in original plan: OpenCode (100K+ stars, Go TUI), Qwen Code (Qwen-optimized, Gemini CLI fork), Codex CLI (OpenAI, `--oss` flag), Kilo CLI (Memory Bank feature), Cline CLI (was IDE-only, now has CLI)
- **Ecosystem shift:** `ollama launch` (v0.15, Jan 2026) = zero-config setup; MCP standardization drove extension ecosystems
- **Goose lead/worker analysis:** Elegant auto-fallback, but failure mode is protocol-level (malformed JSON), not quality-level — with 8B models, would end up running on Claude most of the time
- **Selected:** Aider (primary) + OpenCode (comparison)

**Task 2.2 Complete: Both tools installed and configured**

| Tool | Version | Config | Model | Install |
|------|---------|--------|-------|---------|
| Aider | v0.86.2 | `.aider.conf.yml` | `qwen2.5-coder:7b` (whole format) | `uv tool install aider-chat` |
| OpenCode | v1.2.5 | `opencode.json` | `qwen3:8b` via Ollama | `curl -fsSL https://opencode.ai/install \| bash` |

Both smoke-tested against live Ollama — working.

**Task 2.3 Complete: Frontier fallback pre-wired (dormant)**

- Created `.env` (gitignored) with 7 pre-documented frontier providers, all commented out
- Top free tiers: Google Gemini (frontier-class), Groq (fast 70B), Cerebras (1M tokens/day), OpenRouter (multi-model)
- Aider: frontier via `--architect --model gemini/gemini-2.5-flash` (CLI flag toggle)
- OpenCode: Google + Groq added as providers in `opencode.json` (select from TUI)
- All dormant until an API key is uncommented in `.env`

### Decisions Made
- **Aider primary, OpenCode secondary:** Aider's text-format editing is the only reliable approach for 7-8B models. OpenCode is comparison + future use with larger models.
- **Goose deferred:** Lead/worker is interesting but tool-calling JSON failures make it impractical at 8B.
- **Qwen Code — revisit later:** Optimized for Qwen3-Coder models (MoE, 3B active/80B total). Worth testing when we pull Qwen3-Coder-Next.
- **Frontier = opt-in per session:** Default is always local-only. Frontier activated via CLI flags (Aider) or TUI selection (OpenCode). `.env` is the API key catalog.
- **`.gitignore` refined:** `.aider*` blanket replaced with specific working files — config files (`.aider.conf.yml`, `opencode.json`) are tracked.

### Files Created/Modified
| File | Action |
|------|--------|
| `.aider.conf.yml` | Created — Aider project config (local default, frontier via flags) |
| `opencode.json` | Created — OpenCode project config (3 providers: Ollama, Gemini, Groq) |
| `.env` | Created — API key catalog, 7 providers (gitignored) |
| `.gitignore` | Updated — added `.env`, refined `.aider*` to specific files |
| `.claude/session-context.md` | Updated — Layer 2 decisions added |

### Next
- **Task 2.4:** Test on a real coding task — compare Aider and OpenCode quality vs Claude Code
- **Task 2.5:** Document when to use local-first CLI vs Claude Code

---

## 2026-02-13 - Session 17: Task 1.7 — System-Wide MCP Availability

### Context
Resuming from Session 16 which completed Tasks 1.4-1.6 (MCP wiring, verification, docs). This session makes ollama-bridge available everywhere.

### What Was Done

**Task 1.7 Complete: MCP server available system-wide**

1. **Startup health probe** (`server.py` `_lifespan`):
   - After creating `OllamaClient`, probes `list_models()` in a try/except
   - Success: logs model count to stderr (e.g., "16 model(s) available")
   - Failure: logs warning to stderr — does NOT block server startup
   - Catches both `OllamaConnectionError` and generic `Exception` for robustness

2. **User-level Claude Code config** (`~/.claude.json`):
   - Added top-level `mcpServers` entry with `ollama-bridge`
   - Server is now available in every Claude Code session, not just `/mnt/i/workspaces/llm`
   - Project-level `.mcp.json` kept in place (harmless overlap, serves as documentation)

3. **Claude Desktop config** (`%APPDATA%\Claude\claude_desktop_config.json`):
   - Added `mcpServers` entry using `wsl --` prefix for Windows-to-WSL bridging
   - Claude Desktop (Windows process) can now spawn the server inside WSL2

4. **Documentation updates**:
   - `mcp-server/README.md`: Added "System-Wide Setup" section with user-level + Desktop instructions
   - Updated troubleshooting to reference user-level config
   - `tasks.md`: Task 1.7 marked complete
   - `index.md`: Updated Layer 1 table with new config locations

### Decisions Made
- **Graceful degradation over gating:** Server starts regardless of Ollama status — individual tools handle errors
- **Keep `.mcp.json`:** Harmless overlap with user-level; serves as in-repo documentation for other contributors
- **stderr for diagnostics:** stdout is reserved for JSON-RPC protocol; stderr is the correct channel

### Verification Results
- Claude Code from different directory: **passed** — tools available system-wide
- Claude Desktop initial attempt: **failed** — `uv: not found` (non-interactive shell doesn't source `~/.bashrc`)
- **Fix:** Added `export PATH="$HOME/.local/bin:$PATH"` to `run-server.sh` — makes script self-contained
- Claude Desktop after fix: **passed** — all tools callable from Desktop app

### Gotcha Discovered
Non-interactive shells (spawned by `wsl --`, cron, systemd) skip `~/.bashrc`, so `~/.local/bin` tools like `uv` aren't on `$PATH`. Scripts invoked by external orchestrators must set their own `$PATH`.

### Next
- **Layer 1 is complete (7/7).** All tasks done, verified, documented.
- Next session: Start **Layer 2** (check `.claude/plan-v2.md` for scope and tasks)
- Uncommitted changes from this session need committing first

---

## 2026-02-13 - Session 16: Tasks 1.4 & 1.5 — MCP Wiring + End-to-End Verification

### Context
Resuming from Session 15 which completed Task 1.3 (4 specialized tools). This session wires the MCP server into Claude Code.

### What Was Done

**Task 1.4 Complete: Claude Code configured to use the Ollama MCP server**

Created `.mcp.json` at repo root (project-level scope):
- Server name: `ollama-bridge`
- Command: `/mnt/i/workspaces/llm/mcp-server/run-server.sh` (bash wrapper convention)
- Project-level scope chosen over user-level — system-wide availability deferred to Task 1.7

Added `MCP_TIMEOUT=120000` to `~/.bashrc`:
- Default MCP timeout is 10s — too short for Ollama cold starts (model loading into VRAM)
- Matched to server-side `DEFAULT_TIMEOUT` (120s) in `config.py`
- This is a Claude Code env var (global, affects all MCP servers)

Added Task 1.7 to plan: "Make MCP server available system-wide" — covers user-level config, Claude Desktop, and reliability for always-on use.

### Decisions Made
- **Project-level (`.mcp.json`)** over user-level (`~/.claude.json`) — avoids exposing an unreliable server to all Claude contexts before reliability work
- **Timeout = 120s** — matches server-side timeout, covers cold starts without being excessive
- **Task 1.7 added** — system-wide availability requires reliability work (auto-start Ollama, health checks, graceful degradation)

**Task 1.5 Complete: End-to-end delegation verified**

After restart, Claude Code discovered all 6 tools from `ollama-bridge`. Smoke tests:

| Tool | Test | Result |
|------|------|--------|
| `list_models` | List available models | 16 models returned, all 8 personas visible |
| `generate_code` | Python IPv4 validator | Clean function, routed to `my-codegen-q3` |
| `classify_text` | Expense: "groceries $87.50" | `{"category":"food","confidence":1.0}` — grammar-constrained JSON |
| `summarize` | MCP protocol (3 points) | Exactly 3 bullet points, factually correct |
| `translate` | EN → PT-BR | Natural output, no preamble |
| `ask_ollama` | *(verified in Task 1.3)* | General-purpose Q&A works |

All tools returned within normal latency (no cold start this session).

**Task 1.6 Complete: Documentation written**

Created `mcp-server/README.md` covering:
- Architecture diagram (Claude Code → MCP → Ollama pipeline)
- All 6 tools with signatures and routing logic
- "When to delegate" decision guide (boilerplate/transforms → local; refactoring/architecture → Claude)
- All 8 model personas with roles and temperatures
- Configuration reference (both Claude Code and server-side env vars)
- 6 known limitations (single GPU, context window, quality ceiling, cold starts, no streaming, thinking overhead)
- Troubleshooting guide (connection, model not found, timeout, tools not appearing)

Updated `.claude/index.md` — added README, `.mcp.json`, and `MCP_TIMEOUT` entries to Layer 1 Implementation section.

### Next
- Task 1.7: Make MCP server available system-wide (deferred — future layer work)

---

## 2026-02-13 - Session 15: Task 1.3 — Specialized MCP Tool Capabilities

### Context
Resuming from Session 14 which completed Task 1.2 (MCP server built). This session adds 4 specialized tools with dedicated Ollama personas.

### What Was Done

**Task 1.3 Complete: 4 specialized tools with per-task personas**

Created 4 Modelfiles (all based on `qwen3:8b`, sharing weight layers):

| Modelfile | Persona | Temp | Role |
|-----------|---------|------|------|
| `modelfiles/codegen-qwen3.Modelfile` | `my-codegen-q3` | 0.1 | General-purpose code gen (Python, Rust, C++, etc.) |
| `modelfiles/summarizer-qwen3.Modelfile` | `my-summarizer-q3` | 0.3 | Text summarization (bullet points) |
| `modelfiles/classifier-qwen3.Modelfile` | `my-classifier-q3` | 0.1 | Text classification (JSON output) |
| `modelfiles/translator-qwen3.Modelfile` | `my-translator-q3` | 0.3 | Language translation (100+ languages) |

Added 4 tool functions to `mcp-server/src/ollama_mcp/server.py`:

| Tool | Key Feature |
|------|-------------|
| `generate_code(prompt, language?, model?)` | Smart language routing: Java/Go→my-coder-q3, HTML/JS/CSS→my-creative-coder-q3, else→my-codegen-q3 |
| `summarize(text, max_points?, model?)` | Optional `max_points` constraint, bullet-point output |
| `classify_text(text, categories, model?)` | Grammar-constrained JSON via dynamic schema + `format` param |
| `translate(text, target_language, source_language?, model?)` | Auto-detect source language |

Also added:
- `LANGUAGE_ROUTES` dict for generate_code persona routing
- `_format_error()` shared error handler
- Updated `ask_ollama` docstring with routing guidance to specialized tools
- Updated `config.py` MODELS list (now 8 personas)

**All smoke tests passed against live Ollama:**
- `generate_code("binary search", language="python")` → clean Python function
- `classify_text("Uber ride $45", ["food","transport","housing"])` → `{"category":"transport","confidence":0.95,...}`
- `summarize(python_history, max_points=3)` → 3 bullet points, no meta-commentary
- `translate("Hello world", "Spanish")` → "Hola mundo" (no preamble)
- Language routing: Java→my-coder-q3 (added error handling per its SYSTEM), HTML→my-creative-coder-q3 (used Canvas API per its SYSTEM)

### Decisions Made
- **Temperature split:** 0.1 for deterministic tasks (code, classification), 0.3 for variation tasks (summarization, translation)
- **Per-task personas over API system prompts:** Avoids conflicting instructions between Modelfile SYSTEM and API `system` param
- **`think=False` hardcoded** for all specialized tools (simple tasks per Layer 0 strategy)
- **Language routing dict** (`LANGUAGE_ROUTES`): clean, extensible, explicit model override always wins
- **Grammar-constrained decoding** for classify_text: dynamic JSON schema with enum from categories list, passed via `format` param
- **Shared `_format_error`** helper to DRY error handling across new tools (existing `ask_ollama` kept inline for backwards clarity)

### Next
- Task 1.4: Configure Claude Code to use the MCP server (`claude mcp add`)
- Task 1.5: End-to-end test — Claude Code delegates to local model
- Task 1.6: Document usage patterns and limitations

---

## 2026-02-12 - Session 14: Task 1.2 — MCP Server Built and Verified

### Context
Resuming from Session 13 which completed Task 1.1 (MCP research + language decision). This session implements the MCP server itself.

### What Was Done

**Task 1.2 Complete: Built MCP server wrapping Ollama `/api/chat`**

Created `mcp-server/` directory with full Python project:

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project config — deps: `mcp[cli]>=1.0.0`, `httpx>=0.27.0` |
| `src/ollama_mcp/config.py` | Defaults + env var overrides (URL, model, timeout, think, temps) |
| `src/ollama_mcp/client.py` | Async `OllamaClient` — httpx connection pooling, structured `ChatResponse` dataclass, 3 custom exception types |
| `src/ollama_mcp/server.py` | FastMCP server with `ask_ollama` and `list_models` tools, lifespan for client lifecycle |
| `src/ollama_mcp/__main__.py` | Entry point for `python -m ollama_mcp` (stdio transport) |
| `run-server.sh` | Bash wrapper (project convention) |

**Tooling installed:**
- `uv` 0.10.2 — Python package manager (installed to `~/.local/bin`, no sudo)
- `mcp` SDK 1.26.0 — FastMCP server framework (38 packages total in venv)

**Verification results — all passed:**
- Server starts and responds to MCP `initialize` handshake
- Tool discovery: `ask_ollama` + `list_models` visible via `tools/list`
- Live Ollama integration: "What is 2+2?" → "four" (via my-coder-q3)
- Error handling: clean message when Ollama unreachable (no stack trace)
- Bash wrapper: works correctly, resolves own directory

### Decisions Made
- **Package name:** `ollama-mcp` (pyproject.toml) / `ollama_mcp` (Python package)
- **Architecture:** Module-level client with lifespan management (simple, appropriate for stdio single-process server)
- **Error strategy in tools:** Return error strings instead of raising exceptions — lets Claude read and handle errors gracefully
- **Default model:** `my-coder-q3` (Qwen3-8B) — good all-rounder for delegated tasks

### Next
- Task 1.3: Define specialized tool capabilities (generate_code, classify_text, summarize, translate)
- Task 1.4: Configure Claude Code to use the MCP server (`claude mcp add`)
- Task 1.5: End-to-end test — Claude Code delegates to local model

---

## 2026-02-12 - Session 13: Layer 1 Kickoff + Context Optimization

### What Was Done

**Context optimization housekeeping (before Layer 1 work):**

Problem: Recontextualization was consuming ~9% of session limit. Root causes:
- CLAUDE.md (~8.4 KB) loaded into every API turn, 70% was completed-phase history
- plan-v2.md (~15 KB) read at start, ~175 lines were Layer 0 findings
- tasks.md, session-context.md full of completed checkboxes and Phase 0-6 details

Solution: Archive-and-index strategy — no information deleted, everything findable:

| File | Action | Before | After |
|------|--------|--------|-------|
| `.claude/index.md` | Created | — | Knowledge map: every topic → file location |
| `.claude/archive/layer-0-findings.md` | Created | — | Full benchmark data, thinking mode, decomposition |
| `.claude/archive/phases-0-6.md` | Created | — | All setup phase details, decisions, gotchas, artifacts |
| `.claude/archive/session-log-layer0.md` | Created | — | 717-line Layer 0 session log (rotated) |
| `CLAUDE.md` | Trimmed | ~170 lines | ~50 lines (rules + current state only) |
| `.claude/tasks.md` | Trimmed | ~97 lines | ~40 lines (Layer 1 only + summary) |
| `.claude/session-context.md` | Trimmed | ~190 lines | ~65 lines (prefs + active decisions) |
| `.claude/plan-v2.md` | Trimmed | ~559 lines | ~385 lines (findings → archive) |

Estimated savings: ~38 KB at session start, ~6 KB per turn (CLAUDE.md reduction).

### Decisions Made
- Archive-and-index over delete: all historical content preserved in `.claude/archive/`
- Knowledge index (`.claude/index.md`) as the connection map for all project information
- Session log rotation by layer (was by phase)
- CLAUDE.md principle: rules + current state only; no history

### Research Items Noted
- **Knowledge management tools for AI context:** User has seen news about tools/techniques for indexing and connecting project knowledge. Investigate during Layer 1 research (MCP servers for knowledge management are a growing category) or tie into Layer 7 (Memory System, RAG, knowledge graphs).

### Next
- ~~Task 1.1: Research MCP server specification and Claude Code integration~~
- Task 1.2: Build MCP server (Python / FastMCP)

---

## 2026-02-12 - Session 13 (continued): MCP Research + Language Decision

### Task 1.1 Completed — MCP Research

Full findings archived → `.claude/archive/layer-1-research.md`

**MCP Protocol:**
- JSON-RPC 2.0, spec v2025-06-18, stdio transport for Claude Code
- Tools = primary primitive; declare name + description + inputSchema
- Claude sees all tool descriptions, autonomously decides when to call
- Config: `claude mcp add --transport stdio <name> -- <command>` → stored in `~/.claude.json` (NOT settings.json)
- Limits: 10s timeout (`MCP_TIMEOUT`), 25K token output (`MAX_MCP_OUTPUT_TOKENS`)

**Language Decision: Python (FastMCP)**
- Evaluated: Python, Go, Java, Kotlin, TypeScript
- Python wins on: tool friction (~8 lines/tool), ecosystem (PDF/scraping/NLP), community docs
- Go was strong runner-up (fast startup, single binary) — may use for perf-critical components later
- Java/Kotlin: JVM startup too slow for stdio subprocess
- TypeScript: user preference against JS

**Existing Tools Landscape:**
- No existing project is a drop-in for our "frontier-delegates-to-local" pattern
- Patterns worth borrowing: learned routing (llm-use), cognitive memory (ultimate_mcp_server), cost analysis (locallama-mcp), modular services (MCP-ollama_server)
- Inverse-direction tools (tools FOR Ollama) still valuable for later layers
- Discovery registries catalogued: mcp.so, mcpservers.org, awesome-mcp-servers, mcp-awesome.com, mcpmarket.com

### Decisions Made
- **Language:** Python with FastMCP (official SDK)
- **Scope expanded:** MCP server is general-purpose gateway, not coding-only
- **Licensing rule added:** Always check + honor licenses; track attributions in `docs/ATTRIBUTIONS.md`
- **Reference existing work:** Borrow patterns from llm-use, ultimate_mcp_server, others (with attribution)

### Next
- Task 1.2: Plan and build the MCP server architecture

---

## CRITICAL NOTE: Task 3.4 Refactoring Debt (Deferred from PR #1)

**User flagged at end of Session 22:** Three refactoring improvements from PR #1 review were deferred but **NOT captured in session-log until now**:

1. **MODEL_MATRIX centralization** — Extract to `personas/models.py` when Task 3.5 needs it (currently single consumer in create-persona.py)
2. **Input helpers** — Extract ask()/ask_choice()/etc. to `personas/lib/interactive.py` when Task 3.5 needs them
3. **TEMPERATURE_MAP + _temp_comment consolidation** — **IMPORTANT:** Merge into single dict-of-dicts to prevent drift. Currently hardcoded in _temp_comment (line 307) instead of referencing TEMPERATURE_MAP.

**When to handle:** Start of Task 3.5 session, before building conversational builder. Can be grouped refactoring pass (2-3 hours).

**Reason these matter:**
- Prevents code duplication in Task 3.5
- Consolidates "temperature" metadata to single place (prevents bugs)
- Keeps related concerns together

See memory file for full reasoning and PR #1 discussion.

