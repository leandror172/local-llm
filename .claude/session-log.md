# Session Log

**Current Layer:** Web research tool — vision, research, architecture design
**Current Session:** 2026-03-17 — Session 44: Web research tool genesis
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`

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

## 2026-03-15 - Session 43: warm_model testing, bug fix, Ollama eviction research

### Context
Resumed from session 42 (PR #15 pending merge). Switched to Sonnet 4.6. First task: manually test `warm_model` MCP tool that was built last session.

### What Was Done

**warm_model — fully tested, bug found and fixed:**
- Tests 1-4 passed: already-loaded no-op, evict+load, hook fix, cold start
- Test 5 (invalid model): found "evict then 404" bug — `warm_model` evicted loaded model before validating target exists, leaving VRAM empty
- Fix: `_check_model_exists()` helper (generated by local model, IMPROVED — return type annotation fixed) validates via `/api/tags` BEFORE any eviction
- Also added `resp.raise_for_status()` to load call for defensive coverage
- Hook fix: `ollama-post-tool.py` now skips verdict template for non-generation tools (warm_model, list_models, ref_lookup, query_personas); only 7 generation tools get verdict prompt
- Deferred task added: refactor `server.py` separation of concerns

**PR #15 merged to master:**
- Merge conflict in session-context.md and session-log.md (session 41 vs session 42 content)
- Resolved: took incoming for session 42 status; kept HEAD session 39b history; restored missing session 41 entry

**Ollama coordination layer — researched and deferred:**
- Proved in-process `_inflight` dict is per-MCP-server-process (cross-session calls invisible)
- Researched Ollama extensibility: no plugin/hook system; all compiled-in Go
- Discovered PR #9392: adds `ACTIVE` field to `/api/ps` via internal `refCount` — could replace file layer entirely
- Ran empirical eviction-during-generation tests (two models):
  - `keep_alive: 0` during active generation → Ollama **queues** unload, doesn't interrupt
  - Generation ran to completion (300 tokens, 1477 chars) after evict signal
  - Correctness risk is off the table; remaining concern is VRAM thrash (performance only)
- Documented in `docs/findings/ollama-eviction-concurrency-findings.md`
- Updated design doc + deferred task: build trigger = VRAM thrash observed AND PR #9392 not shipped

**New deferred task:** File-based coordination layer (Option 2) — revised rationale, watch PR #9392 first

### Decisions Made
- `_check_model_exists()` extracted as helper (not inlined) — sets precedent for server.py refactor
- Local model (`generate_code`) used for helper; IMPROVED (return type annotation fix)
- File-based coordination layer deferred: correctness not at risk; PR #9392 may eliminate need
- `git reset --hard` preferred over `git revert` for undoing accidental master commits (cleaner merge history)

### Next
- Checkout `feature/session-43-handoff`, open PR, then reset master to pre-accidental-commit state
- Merge PR #8 in expense repo (overlay install)
- Python 3.10 → 3.12 upgrade via `uv` (highest priority before next standalone script)
- Layer 4 stragglers: Phase 3 frontier judge, Claude Desktop insights tool 4.6

---

## 2026-03-14 - Session 42: Verdict retry policy + warm_model + ollama-scaffolding overlay

### Context
Resumed from session 41. All PRs merged, master clean. Chose "IMPROVED verdict workflow codification" from deferred tasks, which expanded into a full architecture session.

### What Was Done

**Verdict retry policy — COMPLETE:**
- Replaced "3 lines" threshold with 3-dimension heuristic (defect type / fix scope / prompt cost)
- Stubs-then-Ollama codified as named retry pattern; conceptual defects named as category
- Cold-start grace period: first-call timeouts → `TIMEOUT_COLD_START`, not REJECTED
- Added to `docs/scaffolding-template.md` and `ref:local-model-retry-patterns`

**warm_model MCP tool — COMPLETE (pending manual test):**
- In-flight tracking wraps `chat()` in try/finally; `list_running()`, `unload_model()` on client
- `warm_model` tool: check loaded → check in-flight → evict if safe → warm with trivial prompt
- Design doc for future directory-based coordination: `docs/ideas/ollama-coordination-layer.md`

**ollama-scaffolding overlay — COMPLETE:**
- `overlays/ollama-scaffolding/` — packages verdict/retry policy for any ollama-bridge project
- Tested 3 AI backends against expense repo; all over-deleted with long section
- Redesigned: short pointer in CLAUDE.md (~6 lines) + full reference file
- Installed in expense repo worktree, PR #8 opened

**New persona:** `my-api-docs-q3` (API doc analyst, deterministic). Found: MCP server caches registry — new personas invisible until restart.

**New deferred tasks:** MCP `create_persona` tool, raw temperature values, registry hot-reload

### Decisions Made
- Defect type / fix scope / prompt cost replaces line-count threshold
- Stubs-then-Ollama is REJECTED retry, not IMPROVED — cleaner DPO signal
- warm_model: bundled Option 1 now; directory-based Option 2 when second consumer emerges
- Overlay CLAUDE.md sections must be short pointers — all AI backends over-delete long sections
- "Do NOT use for security" removed — code is reviewed; "Training Data" removed — implementation detail

### Next
- Merge PR #15 (LLM repo) and PR #8 (expense repo)
- Manual test warm_model after MCP server restart
- Remaining deferred: Python 3.10→3.12, auto-resume hook, registry hot-reload
- Layer 4 stragglers: Phase 3 frontier judge, Claude Desktop insights tool

---

## 2026-03-13 - Session 41: All PRs merged; dotfiles backup system

### Context
All pending PRs (#10, #11, #12, #13, #14) were merged to master by the user before the session.
Entry point: recontextualize + discuss next steps from remaining deferred infra tasks.

### What Was Done

**All open PRs merged to master** (by user, pre-session):
- #10 token logging, #11 verdict hooks, #12 context-files, #13 ref-integrity, #14 overlay-system

**Dotfiles backup system — COMPLETE:**
- Created private GitHub repo `leandror172/dotfiles` at `~/workspaces/dotfiles/`
- Three-way folder structure: `claude-code/` (user-level `~/.claude/`), `claude-projects/` (memory only), `claude-desktop/` (Windows AppData config)
- `backup.sh`: OS-aware (WSL2 vs Linux via `/proc/version`), copies all three areas, `git commit` if changed
- `install.sh`: restore script with top-of-file variables (`WINDOWS_USER`, `LLM_PROJECT_PATH`) for machine-specific paths; derives `~/.claude/projects/` slug from project path
- `SessionStart` hook added to `~/.claude/settings.json` — auto-runs `backup.sh` on every Claude Code session start
- First backup committed + pushed: 10 files (settings.json, .mcp.json, keybindings.json, installed_plugins.json, MEMORY.md, debugging.md, claude_desktop_config.json)
- Deferred infra task "Claude Code user-config backup/tracking" marked complete in tasks.md

### Decisions Made
- Dotfiles repo location: `~/workspaces/dotfiles/` (consistent with workspace convention)
- Scope: Claude files only (not full dotfiles — can expand later)
- `claude-projects/` backs up `memory/` subdirs only — transcript UUIDs excluded (ephemeral)
- OS detection via `/proc/version` grep — reliable in non-interactive shells (hooks, cron)
- `install.sh` uses explicit top-of-file variables for machine-specific paths (not convention/manifest) — honest about what needs human attention on a new machine
- No `SessionFinish` hook (doesn't exist in Claude Code); `SessionStart` + manual `backup.sh` on demand
- Conversations NOT backed up — ephemeral, large, Claude already maintains `~/.claude/backups/`

### Next
- Remaining deferred infra tasks: hook-based auto-resume, IMPROVED verdict workflow codification, Python 3.10→3.12 upgrade (do before next standalone script)
- Layer 4 stragglers: Phase 3 frontier judge (4.x), Claude Desktop insights tool (4.6)
- Layer 5 continues in `~/workspaces/expenses/code/` (separate sessions, tasks 5.1–5.7)

---

