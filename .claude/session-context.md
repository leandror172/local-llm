# Session Context for Future Agents

**Purpose:** User preferences and working context across Claude Code sessions.

---

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

---

## File Management

### Sensitive Data
- **Location:** `.claude/local/` (gitignored)
- **Rule:** System specs, paths, or personal info → write to `local/`

### Log Rotation
- **Policy:** By phase — rename `session-log.md` when a layer completes
- **Archive:** Older logs to `.claude/archive/`
- **Size limit:** Rotate when `session-log.md` exceeds ~500 lines

### Context Optimization
- **System-prompt files** (CLAUDE.md, MEMORY.md): Keep lean — rules + current state only; history in archives
- **Session files** (tasks.md, this file): Only active layer + pointers to archives
- **Knowledge index:** `.claude/index.md` maps every topic to its file location
- **Archives:** `.claude/archive/` — full historical data, read on demand

---

## Current Status

- **Phases 0-6:** Complete → `.claude/archive/phases-0-6.md`
- **Layer 0:** Complete (12/12) → `.claude/archive/layer-0-findings.md`
- **Layer 1:** Complete (7/7) — MCP server built, all tools verified, system-wide availability
- **Layer 2:** Complete (5/5) — Tools installed, tested, findings documented
- **Last completed:** Tasks 3.2, 3.3 (creator CLI + model selection), all 10 planned personas created (28 total)
- **Last checkpoint:** 2026-02-17 (session 21)
- **Next:** Task 3.4 — Auto-detection: analyze codebase/domain → propose persona
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands)

---

## Quick Resume

The tracking files ARE the handoff — no separate handoff files needed.

1. Read this file (preferences + active decisions)
2. Check `.claude/tasks.md` (what's done, what's next)
3. Check `.claude/session-log.md` — the **"Next" pointer** at the bottom tells you where to start
4. See `.claude/index.md` to find anything else (archives, research, references)

---

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
- **Findings + decision guide:** `tests/layer2-comparison/findings.md` — full test results, failure taxonomy, when-to-use guide.

### Layer 3 Decisions (decided 2026-02-17)
- **Creator tool:** `personas/create-persona.py` — standalone Python script (no venv; PyYAML system-wide). Bash wrapper `run-create-persona.sh` is auto-approved for Claude Code.
- **Registry append = raw text:** PyYAML `dump()` strips all comment section headers. Creator appends raw YAML text block to preserve structure.
- **MODEL_MATRIX:** domain → (model, ctx, default_temp). reasoning→qwen3:14b/4096, classification→qwen3:4b/4096, others→qwen3:8b/16384.
- **Reviewer personas at temp=0.1:** deterministic; same code in → same review findings out.
- **`--constraints` splits by comma:** Constraint strings must not contain commas internally (design constraint of the CLI flag).
- **Sonnet preferred for implementation:** Opus for planning/ambiguous decisions; Sonnet for well-defined code generation (saves ~5x quota).
- **28 active personas:** All planned personas from registry.yaml are now created and registered.

### Historical decisions (Phases 0-6, Layer 0)
Archived → `.claude/archive/phases-0-6.md` (setup decisions, gotchas, artifact tables)
