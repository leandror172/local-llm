# Session Log

**Current Layer:** Persona infrastructure + web research tool
**Current Session:** 2026-03-20 — Session 45: Persona MCP tools & infrastructure overhaul
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`

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

