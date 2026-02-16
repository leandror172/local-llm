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
- **Layer 2:** In progress (3/5) — Aider + OpenCode installed, frontier pre-wired
- **Last completed:** Task 2.3 (frontier fallback configured, dormant)
- **Last checkpoint:** 2026-02-16
- **Next:** Task 2.4 (real coding test: Aider vs OpenCode vs Claude Code)
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

### Layer 2 Decisions (decided 2026-02-16)
- **Tool selection:** Aider (primary) + OpenCode (comparison). Aider chosen for text-format editing (no JSON tool-calling required — critical for 7-8B models). OpenCode for comparison + future use with larger models.
- **Architecture insight:** Two camps — text-format agents (Aider) vs tool-calling agents (OpenCode, Goose, Qwen Code). Tool-calling fails systemically at 7-8B; text-format is reliable.
- **Goose deferred:** Lead/worker auto-fallback is elegant but the failure mode is protocol-level (malformed JSON), not quality-level — auto-escalation would just run Claude most of the time.
- **Qwen Code — revisit later:** QwenLM/qwen-code is optimized for Qwen3-Coder models (MoE, 3B active/80B total). Worth testing when we pull Qwen3-Coder-Next. Also interesting as the Gemini CLI fork with Qwen-specific tuning.
- **Research archive:** `.claude/archive/layer-2-research.md` (to be created)

### Historical decisions (Phases 0-6, Layer 0)
Archived → `.claude/archive/phases-0-6.md` (setup decisions, gotchas, artifact tables)
