# Session Context for Future Agents

**Purpose:** User preferences and working context across Claude Code sessions.

---

<!-- ref:user-prefs -->
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
<!-- /ref:user-prefs -->

---

## File Management

### Sensitive Data
- **Location:** `.claude/local/` (gitignored)
- **Rule:** System specs, paths, or personal info → write to `local/`

### Log Rotation
- **Tool:** `.claude/tools/rotate-session-log.sh` — run at session end via session-handoff skill
- **Policy:** Keep 3 most recent sessions in `session-log.md`; archive the rest
- **Archive:** `.claude/archive/session-log-YYYY-MM-DD-to-YYYY-MM-DD.md`

### Context Optimization
- **System-prompt files** (CLAUDE.md, MEMORY.md): Keep lean — rules + current state only; history in archives
- **Session files** (tasks.md, this file): Only active layer + pointers to archives
- **Knowledge index:** `.claude/index.md` maps every topic to its file location
- **Archives:** `.claude/archive/` — full historical data, read on demand

---

<!-- ref:current-status -->
## Current Status

- **Phases 0-6:** Complete → `.claude/archive/phases-0-6.md`
- **Sessions 51-53** (2026-04-13 to 15) — Smart RAG research → LTG concept + plan + Phase 0 decisions frozen + Phase 1 extractor spike runner built. See session log archive.
- **Sessions 54-57** (2026-04-16 to 25) — Phase 1 sweep (32/32 ok), HTML scorer built, 8/8 corpus files scored (Claude draft track), rater notes captured. See session log archive.
- **Session 58** (2026-04-30) — LTG Phase 1 two-rater reconciliation closes Phase 1 (Branch C):
  - Reconciled user HTML-viz scoring track (32/32 cells in `retrieval/runs/manual-rubric.md` + 648 per-topic scores in `retrieval/runs/ltg-rater-20260416-181839-20260430-215756Z.json`) with Claude draft. **Both rater tracks produce identical 4-model ranking + identical pass/fail verdicts**, with user track systematically +0.18–0.40 lenient (does not flip any verdict). Pre-registered decision tree (`ref:ltg-phase1-pending-revisions`) resolved to **Branch C (mixed)**: agree on `smart-rag3` flip but disagree on `smart-rag-index` flip → keep 2-arm production routing, defer 3rd arm.
  - **Final 8/8 adjusted scores (Claude / User):** qwen3:14b 2.44 / 2.61 ✅ winner, qwen3:8b 2.27 / 2.63 ✅ backup, qwen2.5-coder:14b 1.76 / 2.16 ❌ (borderline under user — 0.04 below threshold), gemma3:12b 1.61 / 1.82 ❌.
  - **Production routing decision (Branch C):** 2-arm — `qwen2.5-coder:14b` for code files, `qwen3:14b` for prose. Cross-ref-index 3rd-arm (qwen3:8b candidate) **deferred to Phase 2** pending determinism re-run + MoE eval. The qwen3:8b > qwen3:14b flip on `smart-rag-index.md` survived only in the Claude draft, not in user track.
  - **Largest single-cell disagreement:** `.memories/QUICK.md` × `gemma3:12b` (Δ=−0.93). The only cell of 32 where user is harsher than Claude (d5=0 + semantic-hallucination note). Sharpens gemma `❌` rather than weakening it.
  - **Methodological insight for Layer 7 / DPO scoring:** rubric is fit-for-purpose for **binary** decisions (ranking + pass/fail robust across raters); absolute scores diverge by ~0.2–0.4 weighted-quality points. Continuous reuse (DPO scoring) would need inter-rater calibration.
  - Edits: `retrieval/spike-results.md` (filled user table 32 cells; added Two-rater reconciliation section; insight #9; rewrote `ref:ltg-phase1-routing-hypothesis` per Branch C); `.memories/KNOWLEDGE.md` (final 8/8 reconciled, Claude+User columns); `.claude/tasks.md` (marked scoring complete; added 2 deferred items: 3rd-arm hypothesis + per-topic JSON Phase 2 input); `.memories/QUICK.md` (root) + `retrieval/.memories/QUICK.md` (status block refresh).
  - **Final extractor freeze gates cleared in session 59:** (a) determinism re-run → Branch C (model property confirmed), (b) MoE eval → qwen3:30b-a3b unusable (TTFT > 9 min), qwen3-coder:30b fails adjusted threshold (2.06). `ref:ltg-extractor` formally frozen in session 59.
  - Branch: `feature/ltg-phase1-reconciliation-session-58` (off `feature/ltg-phase1-scoring-and-notes`); 2 commits (`c3fdcdd` reconciliation core + `34cfaa8` QUICK.md memory updates).
- **Active branch:** `feature/ltg-phase1-reconciliation-session-58` (PR open; 2 commits this session — determinism + MoE eval + extractor freeze)
- **Phase 1 status: FULLY CLOSED (session 59, 2026-05-04).** All three freeze gates cleared. `ref:ltg-extractor` formally frozen: qwen3:14b (prose), qwen2.5-coder:14b (code). See `retrieval/DECISIONS.md`.
- **Prior active branches:** `feature/ltg-phase1-scoring-and-notes` (parent of current; session 57 work — PR still queued); `feature/ltg-rater-redesign` (further upstream; session 56 work); `feature/ltg-phase1-extractor-spike` (runner + sweep); `feature/ref-lookup-prefix-search` (PR #30 open); `feature/ltg-phase0` (PR open, under review); `feature/gemma3-benchmark` (PR still not opened)
- **Open deferred tasks:** hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix (tracked in expenses repo), Python 3.10→3.12 via uv, Layer 4 stragglers (Phase 3 frontier judge, claude-desktop insights tool 4.6), raw temperature values, registry hot-reload, server.py refactor, file-based coordination layer (watch PR #9392), ModelCaller Protocol for extract_topics.py, extract create-persona.py into importable library, `add_model` MCP tool, prompt-iteration experiment (topic-count floor + containment-only overlap), delete legacy `HTML_TEMPLATE` from viz_sweep.py, **LTG cross-ref-index 3rd-arm routing hypothesis** (defer-to-Phase-2), **LTG per-topic rubric JSON as Phase 2 input** (648 scores in 29/32 cells), **containment/post-pass guard** for qwen3:14b on dense single-line bullet lists (Branch C action from determinism re-run), **qwen3:30b-a3b deferred** pending Ollama MoE offload improvement
- **Next:** **(1) Phase 2 entry — VRAM co-residence probe** (qwen3:14b + bge-m3 ≈ 12 GB on 12 GB card; must confirm simultaneous load before embedding is locked). **(2) Prompt-iteration experiment** (still deferred from sessions 55/57) — topic-count floor `max(5, major_section_count)` + containment-only overlap, cheap re-sweep on existing 8 files. **(3) Phase 2 work** — LanceDB integration, bge-m3 embedding, graph construction (networkx + leidenalg), `relate(a,b)` acceptance test. Still open: session 57 PR for `feature/ltg-phase1-scoring-and-notes`; PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers.
- **Cross-repo:** MVP spike executing in web-research repo sessions; expense MCP work executing in expenses repo sessions; PR #21 merged (`feature/persona-mcp-tools`); .memories/ PRs merged in expenses + web-research
- **Two-repo workflow:** Feature work in `~/workspaces/expenses/code/`; MCP wrapper in this repo
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands)
<!-- /ref:current-status -->

---

<!-- ref:local-model-conventions -->
## Local Model Conventions

When Ollama output is imperfect, classify by **defect type × fix scope × prompt cost**:

Verdict scale: 2 = accepted · 1 = improved · 0 = rejected

- **Mechanical** (syntax, typo, wrong import) → 1 (improved), inline always
- **Structural, 1–2 isolated sites** → inline (1 or 0 based on effort)
- **Structural, 3+ sites or interdependent** → 0 (rejected) + stubs-then-Ollama if interface definable; scratch if not
- **Conceptual** (correct syntax, wrong behavior) → 0 (rejected), write from scratch
- **Prompt cost tiebreaker:** if explaining > fixing → inline regardless of scope

Stubs-then-Ollama: write stub signatures, call Ollama with stubs in `context_files`. First call = 0 (rejected) triple; second call gets its own verdict (often 2 (accepted)). Both are clean DPO signal.

Cold-start timeouts → `TIMEOUT_COLD_START`, not 0 (rejected). No DPO triple recorded. Retry immediately. Use `warm_model` MCP tool to eliminate cold starts.

Full decision tree: `docs/scaffolding-template.md` § "Handling Imperfect Output: Decision Tree"
<!-- /ref:local-model-conventions -->

<!-- ref:resume-steps -->
## Quick Resume

Run `.claude/tools/resume.sh` for a compact session-start summary (replaces reading multiple files).

Or manually:
1. `ref-lookup.sh current-status` — current layer, next task, branch state
2. Tail of `.claude/session-log.md` — "Next" pointer from most recent session
3. `git log --oneline -3` — recent commits
4. `.claude/index.md` — find any specific file/topic on demand
<!-- /ref:resume-steps -->

---

<!-- ref:active-decisions -->
## Active Decisions

### Cross-cutting principles
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both → `docs/vision-and-intent.md`
- **Licensing (STRONG):** Always check + honor external project licenses; attribute in `docs/ATTRIBUTIONS.md`
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx 10240 for 14B:** Balances context vs VRAM. KV cache formula: `2 × layers × kv_heads × head_dim × ctx × 2bytes`
- **Multi-model comparison → DPO pairs:** `run-compare-models.sh` + `run-record-verdicts.sh` → Layer 7 pipeline

**Frozen layer decisions (Layers 1/2/3):** `.claude/archive/decisions-layers-1-3.md`
**Historical decisions (Phases 0-6, Layer 0):** `.claude/archive/phases-0-6.md`
**LTG decisions:** `retrieval/DECISIONS.md` (ref keys: `ltg-scope`, `ltg-embedding`, `ltg-extractor`, etc.)
<!-- /ref:active-decisions -->
