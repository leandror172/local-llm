# Task Progress

**Last Updated:** 2026-02-27 (session 35)
**Active Layer:** Layer 5 — Expense Classifier
**Full history:** `.claude/archive/phases-0-6.md`, `.claude/archive/layer-0-findings.md`

---

## Completed (summary)

- **Phases 0-6:** Infrastructure setup complete (Ollama, models, Docker, verification, docs)
- **Layer 0:** Foundation upgrades complete (12/12) — Qwen3 models, benchmarks, structured output, thinking mode strategy, decomposition, runtime validation, few-shot examples
- **Layer 1:** MCP Server complete (7/7 + MCP-1/2/3/4) — FastMCP server, 9 tools, persona-aware routing, system-wide availability
- **Layer 2:** Local-first CLI complete — Aider (primary) + OpenCode (comparison); decisions → `.claude/archive/decisions-layers-1-3.md`; findings → `docs/findings/layer2-tool-comparison.md`

---

## Layer 3: Persona Creator — COMPLETE

All tasks (3.1–3.6 + refactoring + 3.5-A) complete. Decisions → `.claude/archive/decisions-layers-1-3.md`. Full catalog → `personas/personas-reference.md`. Future candidates → `personas/ideas.md`.

- [ ] **3.5-B:** Implement Option 3 multi-round conversation loop — deferred, not blocking Layer 4

<!-- ref:layer4-status -->
## Layer 4: Evaluator Framework — COMPLETE

Core tasks (4.1–4.4) + shell rubric + Java/Python validators + prompt decomposition all complete. Key design decisions → `docs/plans/2026-02-21-layer4-discussion-context.md`.

### Open stragglers
- [ ] **4.x Phase 3 frontier judge:** Extension point designed in `docs/plans/2026-02-21-layer4-discussion-context.md` — Claude API call for subjective/ambiguous cases.
- [ ] **4.6 Claude Desktop insights tool:** Standalone `tools/claude-desktop-insights.py` (split out from original Layer 4 scope).

---

<!-- /ref:layer4-status -->

<!-- ref:deferred-infra -->
## Deferred Infrastructure / Tooling

Completed items → `.claude/archive/deferred-completed.md`

- [ ] **Hook-based auto-resume:** `UserPromptSubmit` hook injects `resume.sh` output on session start. Needs `.claude/local/session-started` flag to gate (fires every message, not just first).
- [ ] **Qwen3-Coder-Next feasibility study (80B MoE, 3B active):** ~24GB at 3-bit quant. Needs VRAM headroom profiling + native Linux eval. Not priority until 30B models proven insufficient.
- [ ] **expense-reporter config reader: replace runtime.Caller with os.Executable:** `internal/config/config.go` uses `runtime.Caller(0)` — breaks on deployment. Fix: `os.Executable()` + walk up. Low priority until binary deployed.
- [ ] **Overlay wizard — interactive install inside an AI CLI:** Context: `docs/ideas/overlay-wizard.md`. Three steps: `/install-overlay` skill → wizard pattern generalization → portable TUI.
- [ ] **Upgrade WSL2 Python from 3.10 to 3.12:** `uv python install 3.12` alongside 3.10. Do before writing new standalone Python scripts.
- [ ] **`create-persona.py`: accept raw temperature values:** Currently named choices only. Should also accept numeric (e.g., `0.1`, `0.7`).
- [ ] **Refactor `server.py` — separation of concerns:** Extract `_is_model_loaded`, `_check_busy_models`, `_evict_all`, `_load_model` helpers. Split into logical modules.
- [ ] **File-based Ollama coordination layer (Option 2):** Watch Ollama PR #9392 first (`ACTIVE` field in `/api/ps`). Build trigger: VRAM thrash observed AND #9392 hasn't shipped. Design: `docs/ideas/ollama-coordination-layer.md`.
- [ ] **Extract `create-persona.py` into importable library:** MCP tools currently shell out via subprocess. Extract to `personas/lib/persona_builder.py`.
- [ ] **MCP server: hot-reload persona registry:** New personas invisible until restart. Add `reload_registry` tool or file-watcher.
- [x] **ollama-scaffolding overlay: repo-file-as-context guidance:** Include existing repo files as few-shot context. Add to overlay source for downstream repos. Done — D5 (caller inclusion) + D6 (few-shot-before-delete) added to `local-model-conventions.md`.
- [ ] **ollama-scaffolding overlay — review for improvements:** Audit the overlay now that directives are consolidated. Candidate improvements: (1) re-sync directive content against the source feedback memories in the expense / web-research repos as they evolve — the overlay is a point-in-time snapshot and those memories drift; (2) add a ref-block integrity check for `local-model-conventions.md` (balanced `<!-- ref: -->` markers), reusing `ref-indexing`'s `check-ref-integrity.py`; (3) stamp the producing overlay version into the installed doc so downstream repos can tell which version they have (the `files:` mechanism is hash-based, with no version trace); (4) consider a standalone marked-file install mode if any overlay doc ever needs per-repo customization — `files:` currently overwrites wholesale.
- [ ] **install-overlay: preserve line endings in the AI-merge path:** `handle_merge_sections`' deterministic v1→v2 update now preserves CRLF (`_read_text_eol`/`_write_text_eol` in `overlays/lib/actions.py`), but the AI-merge branch (`ai_merge` in `overlays/lib/planner.py`) still round-trips through `read_text`/`write_text` and will normalize a CRLF target to LF. Thread the EOL flag through `ai_merge` / `apply_plan`.
- [ ] **`extract_topics.py`: pluggable ModelCaller Protocol:** Extract `ModelCaller` Protocol; thread through `run_single` / `run_sweep`. Upgrade before Phase 3+ integration.
- [ ] **Subagent MCP server integration discoverability:** See `docs/findings/mcp-subagent-integration.md`. Short-term: `~/.claude/agents/ollama-worker.md` template.
- [ ] **LTG Phase 1 — specialized-extractor routing study:** Add 3-5 more code files to corpus; test routing (coder on code, qwen3:14b on prose) vs single-model. See `ref:ltg-phase1-insights` + `ref:ltg-phase1-routing-hypothesis`.
- [ ] **LTG Phase 1 — prompt iteration: topic-count floor + containment-only overlap:** (1) `max(5, major_section_count)` floor; (2) containment-only overlap (no crossed partial spans). See `ref:ltg-phase1-insights` findings #4 and #5.
- [ ] **LTG Phase 1 — cross-reference-index 3rd-arm routing hypothesis:** Deferred from Branch C reconciliation. Re-evaluate when: determinism re-run on `smart-rag-index.md` × qwen3:14b, or corpus n≥3 cross-ref files, or MoE evaluated. See `ref:ltg-phase1-routing-hypothesis`.
- [ ] **LTG Phase 1 — per-topic rubric JSON as Phase 2 input:** 648 per-topic scores in `ltg-rater-20260416-181839-20260430-215756Z.json`. Could disambiguate 3rd-arm hypothesis without new sweep.
- [ ] **`retrieval/viz_sweep.py` — bash wrapper:** Add `retrieval/run-viz-sweep.sh` + `retrieval/run-extract-topics.sh`. Low priority (one-off tools).
- [ ] **resume.sh — ref tag audit + structural fixes:** Add `ref:quick-pointers` (high priority) and `ref:active-decisions` (medium, now compact); add open-deferred count one-liner. Fix 3 bugs: `head -20` truncation on current-status, user-prefs flattened to unreadable single line, key list unreadable. Full plan: `docs/plans/resume-sh-ref-audit.md`.
<!-- /ref:deferred-infra -->

---

## Layer 5: Expense Classifier

**Goal:** Local model classifies expenses, auto-inserts into Excel via expense-reporter Go tool.
**Context:** `docs/vision/expense-classifier-vision.md` (full vision + iterative plan)
**Data inventory:** `docs/vision/expense-classifier-data-inventory.md`
**External data:** `I:\workspaces\expenses\` (auto-category analysis + expense-reporter source)
**Two-repo workflow (session 36):** Layer 5 feature work lives in `~/workspaces/expenses/code/` (expense-reporter repo). This repo holds the MCP thin wrapper (5.8) only. Scaffolding template: `docs/scaffolding-template.md`. Expense repo branch: `feature/claude-code-scaffolding`.

> **REPO BOUNDARY:** Tasks 5.1–5.7 are executed in `~/workspaces/expenses/code/` (expense-reporter repo).
> This file tracks their status only — do NOT execute them here.
> Only task **5.8** (MCP thin wrapper) runs in this repo.

### Pre-work — COMPLETE (sessions 32–35)
JSONL logging, local-model-first CLAUDE.md instruction, model audit (qwen2.5-coder:14b + 14B personas), multi-model comparison tooling, `think: false` fix, num_ctx tuning. All done.

### Layer 5 Tasks (next)
- [ ] **5.1** Port training data into expense-reporter: copy `feature_dictionary_enhanced.json` + `training_data_complete.json` to `data/` in expense-reporter; document format
- [ ] **5.2** `classify` command in expense-reporter: 3-field input → Ollama HTTP → structured JSON → top-N subcategories with confidence
- [ ] **5.3** `auto` command: classify + insert if HIGH confidence (≥0.85), else print candidates
- [ ] **5.4** `batch-auto` command: classify a CSV, write classified.csv (HIGH) + review.csv (LOW)
- [ ] **5.5** Correction logging: `corrections.jsonl` — {input, predicted, actual, confidence} on user override
- [ ] **5.6** Expense persistence: hash ID (sha256[:12] of normalized item+date+value), `expenses_log.jsonl` appended on insert
- [ ] **5.7** Few-shot injection: keyword pre-match against training data, inject top-K examples into classify prompt
- [ ] **5.8** MCP thin wrapper in llm repo: `classify_expense` / `add_expense` / `auto_add` tools

### Key decisions (from session 32 design)
- Classification logic in **expense-reporter** (Go) — it's a product feature, not LLM infrastructure
- MCP wrapper in **llm repo** — thin, calls the Go binary as subprocess
- Training data strategy: hybrid (feature dict + correction rules as system + top-K few-shot per request)
- Structured output via Ollama `format` param — already proven reliable
- Model to benchmark: Qwen3-8B (`my-classifier-q3`) vs Qwen2.5-Coder-7B (speed)
