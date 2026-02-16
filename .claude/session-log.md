# Session Log

**Current Layer:** Layer 2 — Local-First CLI Tool
**Previous logs:** `.claude/archive/session-log-layer0.md`

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
