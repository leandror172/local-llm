# Session Log

**Current Layer:** Portfolio + HF Space chatbot + cross-repo patterns
**Current Session:** 2026-03-26 — Session 47: Technology conventions pattern doc
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`

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

## 2026-03-17 - Session 44: Web research tool genesis

### Context
User wanted to build an AI-powered web research tool that uses local models for processing. Had saved many URLs of tools/techniques to evaluate. Started from a broad idea and iterated through research, architecture design, and existing tool assessment.

### What Was Done
- **4 parallel research agents** launched: self-hosted scrapers, event sourcing for AI agents, language/framework comparison, existing research architectures
- **Comprehensive analysis** produced (10-part document): scrapers (Crawl4AI standout), languages (Python/Go/TS viable, Java+Axon overkill), state management (JSONL+SQLite sweet spot), existing tools (12 compared)
- **Key discoveries:** Local Deep Research (Ollama+SearXNG, MIT, 4.5K commits), SearXNG as consensus search backend, Crawl4AI as best self-hosted scraper, Jina DeepResearch's token budget pattern
- **User architecture vision** captured: Agent A/B/Tool/A2 multi-agent design, DDD-as-agent-modeling insight, progressive autonomy, testing strategy
- **Vision document** synthesized from user notes + research
- **Deep assessment of Local Deep Research:** Sonnet agent examined repo — verdict: build new, borrow patterns (LangChain coupling, 2-3GB deps, no structured output, no multi-model, no progressive autonomy)
- **Research folder organization:** INDEX.md, QUICK-MEMORY.md, ref blocks on all docs, exploration agenda with fork angles
- **MCP subagent integration** gap analysis (separate finding)
- **Work size estimated:** MVP ~4-5 sessions, usable tool ~8-10, full vision ~15-18

### Decisions Made
- **Build new, informed by LDR** — patterns (BaseSearchEngine, two-phase retrieval, strategy registry, ReAct loop) more valuable than code
- **Language question reopened** — not inheriting Python from LDR; Python/Go/TS all viable
- **Session named "genesis"** — serves as root for forked exploration sessions
- **Research folder convention:** `*-MEMORY.md` files, `INDEX.md` per folder, ref blocks for machine lookup, folder-per-topic scaffolding (future)
- **Deferred:** ref-lookup.sh prefix search enhancement

### Next
- Fork sessions for angles A-E (see `docs/research/exploration-agenda.md`)
- Most impactful next: **MVP spike** (Angle A) — wire SearXNG + Crawl4AI + Ollama, test 14B on 5 URLs
- Or **SearXNG setup** (Angle E) — prerequisite for any pipeline
- Language decision needed before significant coding starts
- Merge this branch's PR, then branch per angle

### Fork: Session 44a — MVP Spike Plan
- **Branch:** `feature/mvp-spike-plan`
- Wrote concrete spike plan (`docs/research/mvp-spike-plan.md`): httpx + trafilatura + Ollama HTTP
- Environment audit: Ollama running, no SearXNG/Firecrawl/Crawl4AI setup needed for spike
- Simplified approach: validate extraction hypothesis before setting up infra
- Updated INDEX.md, exploration-agenda.md
- Established **forked session pattern:** append fork notes, don't rotate logs

### Fork: Session 44b — DDD Agent Modeling
- **Branch:** `feature/mvp-spike-plan` (continued)
- Formalized "DDD as agent/model modeling" as reusable design pattern (`docs/research/ddd-agent-modeling.md`)
- Strategic patterns: bounded contexts → agent domains, context maps → data contracts, subdomain classification → model tier selection
- Tactical patterns: aggregates → agent consistency units, domain events → event sourcing, sagas → orchestration
- Expanded companion doc (`docs/research/ddd-agent-decisions.md`): anti-pattern detection heuristics with RTX 3060 cost calculations, split/merge decision flowchart, cost/benefit template, two worked examples for the web research tool
- Key actionable output: only 3 justified model swap points in the web research architecture; Agent Tool should be code not LLM; Agent A2 deferred until context pressure measured
- Updated INDEX.md with Design Patterns section

---

