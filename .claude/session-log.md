# Session Log

**Current Layer:** Layer 3 — Persona Creator (in progress)
**Previous logs:** `.claude/archive/session-log-layer0.md`

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
