# Session Log

**Current Layer:** Local model benchmarking + persona expansion
**Current Session:** 2026-04-09 — Session 50: Gemma 3 benchmark + Claude Code source research
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`

---

## 2026-04-09 - Session 50: Gemma 3 benchmark + Claude Code source research

### Context
Resumed on master (clean). User brought two news items: Claude Code source leaked via npm
sourcemap, and Google's Gemma 3 / TurboQuant. Session focused on investigating both and
storing findings durably.

### What Was Done
- **Research stored:** `docs/ideas/claude-code-python-port.md` — covers all 3 cloned repos
  (claude-code TS source, claude-code-sourcemap, open-multi-agent); key files to read flagged
- **Gemma models pulled:** `gemma3:12b` (8.1GB) and `gemma3:27b` (17GB) via Ollama
- **models.yaml:** added gemma3:12b + gemma3:27b entries (15 base models now)
- **Personas cloned** via copy_persona from my-go-q25c14 / my-python-q25c14:
  - `my-go-g3-12b`, `my-python-g3-12b` (active)
  - `my-go-g3-27b`, `my-python-g3-27b` (inactive — benchmarked, too slow)
- **Benchmarks (3 prompts, 2 languages):**
  - gemma3:12b: ~31 tok/s, IMPROVED on all; 3-4× faster than qwen2.5-coder:14b
  - gemma3:27b: 3.2 tok/s, timeout on ALL tasks even warmed
- **record-verdicts.py:** added `--verdicts A,I,R --notes "p1|p2|p3"` for non-interactive
  use (Claude Code terminal has no TTY; interactive `input()` hits EOFError)
- **Gemma 4:** not on Ollama as of 2026-04-09; revisit ~2 weeks
- **Deferred:** `add_model` MCP tool (automate models.yaml entry creation)
- **.memories/ updated:** QUICK (root, personas, benchmarks) + KNOWLEDGE (root, benchmarks)
- **Branch:** `feature/gemma3-benchmark`, 3 commits (feat + 2x chore)

### Decisions Made
- gemma3:12b = new speed tier: same IMPROVED quality as 14B, 3-4× faster; best for iterative tasks
- gemma3:27b = not viable on RTX 3060: dense partial offload slower than MoE at same total size
  (dense pays PCIe bandwidth on every layer; MoE only activates ~3B params per token)
- Claude Code `services/mcp/normalization.ts` → read before any MCP server refactor
- Claude Code `services/autoDream/consolidationPrompt.ts` → read before improving session-handoff quality
- open-multi-agent (MIT, 3 deps): defer until web-research multi-agent phase; local model pattern
  via `provider: 'openai', baseURL: 'http://localhost:11434/v1'` verified with Gemma 4 / Qwen 3

### Next
- Open PR for `feature/gemma3-benchmark` → master
- Phase 3 chatbot (source code awareness)
- Explore `claude-code/src/services/mcp/normalization.ts` before next MCP refactor
- Gemma 4 on Ollama: check availability ~2026-04-23
- Layer 4 stragglers (Phase 3 frontier judge, claude-desktop insights 4.6)

---

## 2026-04-03 - Session 49: Chatbot Phase 2 — LLM routing + error handling

### Context
Resumed on `feature/smart-chatbot`; created new branch `feature/chatbot-phase2` for all new work this session.

### What Was Done
- **Phase 2 LLM-as-router**: `_build_section_index()` parses all `*-knowledge.md` into flat sections; `_route_sections()` makes a non-streaming Groq call to select up to 3 relevant sections per question; `_enrich_prompt()` appends them to the system prompt
- **Test suite built**: 48 unit tests with synthetic fixtures (`tests/fixtures/context/`), `conftest.py` mocking HF/Gradio/Anthropic, `_make_hf_exc()` helper matching Groq's real nested `{"error": {...}}` format
- **Error handling overhaul**: `_parse_hf_error()` (structured, via `exc.response.json()`), `_retry_after()` (parses `Xh/Xm/Xs` wait formats, retries short waits only), `_classify_error()` (user-friendly messages with wait time for quota errors), `_with_retry()` wrapper used by both routing and main call
- **Groq rate-limit fixes**: TPD daily limit handling with human-readable wait ("about 2 hours"); Claude backend skips Groq routing entirely
- **Debug logging**: `[routing]` and `[respond_hf]` prints + `career_chat_log` alias for log tailing
- **PR #26** opened: `feature/chatbot-phase2` → master

### Decisions Made
- Routing capped at 3 sections (not 6) to stay under Groq's 12K TPM — routing call ~4K + enriched prompt ~9K would exceed limit
- `_with_retry`: one retry on `rate_limit_exceeded` with wait ≤ 60s; daily/hourly quota (long waits) returns None → user gets specific message instead
- Claude backend skips `_route_sections` — avoids burning Groq TPD quota, Claude doesn't need a separate routing call
- Section content truncated to 600 chars in `_enrich_prompt` to control token cost
- `_make_hf_exc` uses Groq's real nested format `{"error": {...}}` — discovered via production log (`body_keys=['error']`)

### Feedback captured (memory)
- Ollama retry protocol: REJECTED → improve prompt + second model, not straight to Claude
- Ollama workflow: always first; write tests first; send full files not slices
- Don't revisit previously validated decisions without new evidence

### Next
- Merge PR #26 to master
- Deploy to HF Spaces (`career_chat_upload_hf`) to test Phase 2 live
- Review `.memories/` PRs in expenses + web-research repos
- Merge PR #21 (persona MCP tools)
- Phase 3 chatbot: source code awareness (file index + targeted reads)

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

