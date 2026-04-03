# Session Log

**Current Layer:** Portfolio + HF Space chatbot + cross-repo patterns
**Current Session:** 2026-04-02 — Session 48: Smart chatbot + .memories/ convention
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`

---

## 2026-04-02 - Session 48: Smart chatbot + .memories/ convention

### Context
Started from Arize job application analysis — Claude Desktop asked about observability/instrumentation in the benchmark framework. The answer was so thorough it became the foundation for upgrading the HF Space portfolio chatbot from static context to cross-repo awareness.

### What Was Done
- **Observability/instrumentation analysis** — Mapped evaluator framework to Phoenix/Arize's LLM-as-judge model. Written to `docs/portfolio/hf-space/observability-instrumentation.md`.
- **Established `.memories/` convention across llm repo** — 12 files (QUICK.md + KNOWLEDGE.md) in 6 folders: root, mcp-server, evaluator, personas, benchmarks, overlays. Follows cognitive memory model from `web-research/docs/research/memory-architecture-design.md`.
- **Created cross-repo prompt template** — `docs/portfolio/hf-space/prompt-create-memories.md` for generating .memories/ in other repos. Used in expenses and web-research sessions (PRs open in both).
- **Smart chatbot roadmap** — 4-phase plan in `docs/portfolio/hf-space/ROADMAP-smart-chatbot.md`: Phase 0 (foundation) → Phase 1 (static expansion) → Phase 2 (LLM-as-router) → Phase 3 (source code) → Phase 4 (cross-project intelligence).
- **Phase 1 implemented** — `sync-context.sh` copies `.memories/` + READMEs from all 3 repos into `context/`. `app.py` loads `*-quick.md` files at startup (~4.7K tokens). System prompt precision rules added for tool-matching questions. 4 new example questions.
- **Updated README.md** — Added evaluator, overlays, .memories/, portfolio chatbot to project structure and technical highlights.
- **Updated `.claude/index.md`** — Added .memories/ table, chatbot roadmap files, cross-references to memory architecture docs.
- **HF Space README updated** — Environment vars table, context sync docs.
- **Root `.gitignore` updated** — Synced context files excluded from git but NOT from HF upload (removed nested `.gitignore` that would have blocked `upload_folder`).
- **Tested chatbot locally** — QUICK.md injection works. Llama 3.3 70B handles "what is X" questions well. Complex analytical questions ("which tools match this problem") produce vague associations — Claude backend recommended for those. Added precision rule and Claude-backend nudge to UI.
- **Branch pushed and deployed** — `feature/smart-chatbot` with 3 commits, uploaded to HF Spaces.

### Decisions Made
- **Branch in llm repo, not new repo** — chatbot is still a portfolio piece, not independent enough for its own repo. Extract when it gets own tests/CI.
- **Per-folder .memories/, not just repo root** — follows memory-architecture-design.md convention. Any folder with its own domain gets QUICK.md + KNOWLEDGE.md.
- **QUICK.md always-injected, KNOWLEDGE.md on-demand** — total QUICK files ~4.7K tokens (safe for system prompt). KNOWLEDGE + READMEs ~20K tokens (Phase 2 routing material).
- **Root .gitignore for synced files, not nested** — `upload_folder` respects nested `.gitignore`, which would block the context files from reaching HF.
- **Free tier model sufficient for routing (Phase 2)** — Llama 3.3 70B via Groq handles classification tasks. Phase 2 adds one routing call before the answer call.
- **Sonnet medium effort for cross-repo memory prompts** — quality bottleneck is project context in each session, not model capability.
- **`((copied++))` fails with `set -e` when count is 0** — bash arithmetic expansion returns the old value; 0 is falsy → exit code 1. Fix: `copied=$((copied + 1))`.

### Next
- **Phase 2 implementation** — LLM-as-router for KNOWLEDGE.md sections. ~130-160 lines of code. Build when QUICK.md context proves insufficient for deeper questions. Details in `ROADMAP-smart-chatbot.md`.
- **Review PRs** — expenses and web-research repos have open PRs for their `.memories/` files.
- **Merge this branch** — `feature/smart-chatbot` to master (or PR first for review).
- **Merge PR #21** — persona MCP tools, still open from session 45.
- **Resume expense repo MCP work** — deferred from session 47.
- **READMEs as context** — 8 high-value READMEs identified for Phase 1 sync. Currently synced but only QUICK files loaded. Could load root-level READMEs in always-inject tier.

---

## 2026-03-26 - Session 47: Technology conventions pattern doc

### Context
User was working in the expense repo on MCP work and realized two questions kept surfacing ("which MCP framework?" and "which Python env?") that were already decided in this repo. Identified the gap: decisions are scattered across session-context, MEMORY.md, and findings — no portable reference.

### What Was Done
- **Created `docs/patterns/technology-conventions.md`** — self-indexed pattern doc with 7 sections: Python tooling (uv), MCP development (FastMCP), Ollama API, script conventions, git workflow, persona naming, licensing compliance
- **Self-indexing design** — `ref:patterns-index` lists all patterns in a table; each section is a `ref:patterns-*` block. Two-level lookup: discover via index, drill into details. Split policy documented for when file exceeds ~400 lines.
- **Added "Revisit when" conditions** — each contingent decision includes conditions under which it should be reconsidered. Two patterns marked as invariants (script conventions = security, licensing = hard requirement). Index table has `Revisit?` column for quick scanning.
- **Wired cross-repo discovery** — memory entries added to all 3 project memory directories (llm, expenses, web-research) pointing to `ref_lookup(key="patterns-index", path="/mnt/i/workspaces/llm")`. Leverages existing `ref_lookup` MCP tool with `--root` support.
- **Added CLAUDE.md rule #5** — "Before making technology choices, check `ref:patterns-index`" (this repo trigger)
- **Updated `.claude/index.md`** — registered the new patterns doc

### Decisions Made
- **A+B mechanism for pattern discovery:** CLAUDE.md one-liner (this repo) + memory entries (cross-repo via MCP). Rejected SessionStart hook (high context cost, always-on) and overlay distribution (unnecessary given MCP ref_lookup already works cross-repo).
- **Patterns are not overlays** — unlike scaffolding which copies files, patterns are queried remotely via MCP. No need to duplicate content across repos.
- **"Revisit when" not universal** — some decisions are invariants (security model, legal requirements) and don't get revisit conditions.

### Next
- Resume expense repo MCP work (the questions that triggered this session are now answered)
- Merge PR #21 (persona MCP tools, still open)
- Consider adding patterns as new conventions are established

---

## 2026-03-25 - Session 46: Claude backend for HF Space chatbot

### Context
Compacted fork from an earlier session (same day) that built the portfolio docs, engineer profile, and HF Space chatbot (Level 2). This session focused on adding Claude as an optional backend model and iterating on the chatbot UX.

### What Was Done
- **Added Claude (Haiku) as optional chat backend** — dual-client architecture with HF Inference (free) and Anthropic API. Radio selector auto-appears when `ANTHROPIC_API_KEY` secret is set. Same code deploys with or without Claude.
- **Per-session rate limiting** — in-memory rate limiter (30 calls/hour default, configurable via `CLAUDE_MAX_PER_HOUR`). Real backstop is Anthropic dashboard spend cap.
- **Separate system prompts per backend** — Decomposed prompt into `_PREAMBLE + _RULES + _PROFILE`. HF gets strict grounding rules ("ONLY state facts"); Claude gets relaxed rules ("may synthesize and draw connections"). Fixed `.replace()` bug where backslash-continuation strings didn't match.
- **Self-referential context** — Added NOTE to preamble telling models this chatbot is itself part of Leandro's portfolio work.
- **Updated examples** — Consistent third-person tone ("How does Leandro..." not "How do you..."); added 2 new LLM-focused examples.
- **Increased Claude max_tokens** — 512 → 2048 (Haiku is fast/cheap, no timeout risk).
- **Fixed Gradio `additional_inputs` examples format** — Must be `list[list]` when `additional_inputs` is provided.
- **Added `career_chat_upload_hf` alias** to `~/.bashrc`; fixed missing `cd` in `career_chat_start`; added `--with anthropic` to start alias.
- **HF Space debugging** — Diagnosed stuck "Restarting" state; added startup logging; used factory reboot via API.

### Decisions Made
- **Anthropic API is separate from Claude Pro** — different account, billing, rate limits. API key needed independently.
- **Haiku 4.5 as default** — cheapest Claude model, undated alias (`claude-haiku-4-5`) for auto-upgrades.
- **Composable prompt architecture** — `_PREAMBLE + _RULES + _PROFILE` instead of `.replace()` string surgery. Avoids bugs from Python line continuation semantics.
- **Rate limit HF = no, Claude = yes** — HF is free (their problem); Claude costs money (your problem).
- **Local model used for code gen** — `my-python-q25c14` generated `respond_claude` function structure (IMPROVED verdict, ~400 tokens saved). 3 parallel calls timed out (GPU contention); sequential retry succeeded.

### Next
- Level 3 (local Ollama chatbot) deferred until post-Layer 7 fine-tuning
- Resume main work: merge PR #21, Layer 5 expense classifier, or web research MVP spike

---

## 2026-03-20 - Session 45: Persona MCP tools & infrastructure overhaul

### Context
Another session (web-research project) tried creating Python personas by hand-writing Modelfiles, bypassing the persona pipeline. This triggered a recontextualization: model config was hardcoded in Python, persona creation required CLI access to this repo, and the skill wasn't user-level. Session addressed all three architectural gaps.

### What Was Done
- **Extracted `models.yaml`** — Moved hardcoded model dicts from `models.py` into `personas/models.yaml` (13 base models: display names, suffixes, context sizes, temperatures). `models.py` now loads from YAML.
- **Added `create_persona` / `copy_persona` MCP tools** — New endpoints in ollama-bridge enabling persona creation from any repo via MCP. `copy_persona` parses source Modelfile, extracts ROLE/CONSTRAINTS/FORMAT via regex.
- **Created `create-persona` skill** — User-level skill (`~/.claude/skills/create-persona/`), teaching 3 patterns: copy, create-from-specs, LLM-assisted. Added to `ollama-scaffolding` overlay for distribution.
- **Fixed CLI ergonomics** — `--constraints` (comma-delimited) → repeatable `--constraint` (action=append); fixed double-period in `build_system_prompt()`.
- **Created 5 new Python personas** — `my-python-q35` (qwen3.5:9b), `my-python-q3-14b` (qwen3:14b), `my-python-q25c14` (qwen2.5-coder:14b), `my-python-dsc16` (deepseek-coder-v2:16b), `my-python-dsr14` (deepseek-r1:14b).
- **Audited and upgraded context sizes** — Probed all model tiers: 8B models 8K→32K (6-7GB VRAM free), 14B confirmed at 16K. Updated 35 existing Modelfiles + registry.
- **Added DeepSeek models** — `deepseek-coder-v2:16b` and `deepseek-r1:14b` in `models.yaml` (16K context).
- **Added timeout parameter** — `ask_ollama` and `generate_code` accept optional `timeout` (default 120s) for 30B+ models.
- **Opened PR #21** — All 7 commits on `feature/persona-mcp-tools`.

### Decisions Made
- **Model config is data, not code** — `models.yaml` is the single source of truth; `models.py` loads it
- **Repeatable `--constraint` flag** over comma-delimited string — avoids splitting on commas within constraint text
- **Skill is user-level** — installed to `~/.claude/skills/`, not per-repo; works from any project
- **Always use MCP/skill for persona creation** — never bypass with direct CLI (saved as feedback memory)
- **8B models safe at 32K context** — probed empirically (46-67 tok/s, no degradation, 6-7GB free VRAM)

### Next
- Merge PR #21
- DeepSeek Python personas already created; consider creating personas for other roles on DeepSeek models
- Deferred: extract `create-persona.py` core logic into importable library (avoid subprocess from MCP)
- Deferred: `role_short = role.split(".")[0][:60]` truncates Modelfile comment (cosmetic)
- Resume web-research MVP spike or Layer 5 work

---

