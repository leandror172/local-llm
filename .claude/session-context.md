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
- **Session 58** (2026-04-30) — LTG Phase 1 two-rater reconciliation closes Phase 1 (Branch C): 2-arm production routing (qwen2.5-coder:14b code, qwen3:14b prose). See session log archive.
- **Session 60** (2026-05-16) — Side-track: consolidated Ollama-usage directives into `ollama-scaffolding` overlay. Propagated to expense + web-research.
- **Session 61** (2026-05-20) — VRAM co-residence probe: bge-m3 + qwen3:14b WARN. bge-m3 locked; sequential constraint.
- **Session 62** (2026-05-22) — MCP server feature plans (refs param, output_file, patch_file). Plans in `docs/plans/`.
- **Sessions 63-67** (2026-05-22 to 26) — MCP Plans 1-3 + logging + acceptance testing. PRs #37, #38. `patch_file` live-verified. Error-handling conventions doc.
- **Session 68-69** (2026-05-26 to 27) — Model update survey + advisor review. `qwen3.5:0.8b/2b` + `phi4-mini` pulled. M-P0/1/2 tasks added. PR #39 merged.
- **Session 70** (2026-05-27) — LTG Phase 2 design decisions frozen. `model_client.py` isolation + `config.yaml` role-keyed. bge-m3 for Phase 2.
- **Sessions 71-72** (2026-05-27 to 28) — LTG Phase 2 COMPLETE. 7 modules, 69-topic acceptance (7/8 pass). `ltg_inspect.py` + all bash wrappers.
- **Session 73** (2026-05-28) — M-P0b: embedding upgraded bge-m3 → qwen3-embedding:8b (4096-dim). Acceptance equivalent. Branch `feature/ltg-embedding-upgrade-qwen3`.
- **Session 75** (2026-05-29) — Ollama model store migrated to I:\\. `OLLAMA_KV_CACHE_TYPE=q8_0` system-wide. 14B→32K ctx. llama4:scout removed. M-P1a closed permanently. Personas fixed.
- **Session 76** (2026-05-30) — All 14B personas rebuilt at 32K (dsc16→24K). `run-ctx-probe.sh`. Pre-session reading guide added to `resume.sh`.
- **Sessions 77-80** (2026-05-30 to 06-01) — LTG extractor retrofit COMPLETE. `routing.py`/`schemas.py`/`model_client.py`/`config.yaml`/`sweep_extractors.py`/`extract_topics.py` rewrite. 147 tests. Parity verified. `docs/patterns/code-design-conventions.md`.
- **Session 81** (2026-06-01) — Retrofit close-out + LTG Phase 3 anchor DISCOVERY. Phase 3 branch started. `docs/plans/ltg-phase3-anchor-discovery.md`. D2/D5/D6/D7 open.
- **Session 82** (2026-06-02) — LTG Phase 3 anchor decisions FROZEN. Dual-path=yes, D2=A repo-wide, alias-link M:N `alias_of`. Full spec: `retrieval/DECISIONS.md` (`ref:ltg-phase3-decisions`).
- **Session 83** (2026-06-04) — Session-handoff pipeline side-track. Design frozen: Scope A = register-driven deterministic spine, no local model. B1.1 done: `overlays/session-tracking/registry.yaml`.
- **Session 84** (2026-06-04) — Handoff-pipeline B1.2 + B2 safety core: F1 Locator, F3 Applier, F4 Verifier. 31 tests.
- **Sessions 85-87** (2026-06-05 to 06) — Handoff pipeline (Scope A) COMPLETE. B3 (mechanics/orchestrator/logging) + B4 (payload schema, `handoff.py`, `run-handoff.sh`, manifest, SKILL.md). 77→88 tests. Dog-food newline-glue bug fixed. PR #50. Project-level skill active.
- **Session 88** (2026-06-09) — Flexible task ID checkoff: locator rewritten (checkbox-first, word-boundary). Payload ID validation broadened. Overlay bumped v2→v3, synced to 3 repos. 88 tests.
- **Session 89** (2026-06-11) — Handoff stage/promote redesign design+plan. Diagnosed collision problem on well-known path. Designed stage/promote flow, two advisor reviews, 7 design issues resolved. New tasks T-55/T-56/T-57. Bug report + implementation plan.
- **Session 88 [pipeline] / 90 [actual]** (2026-06-11) — **Handoff stage/promote redesign IMPLEMENTATION COMPLETE.** T1-T7 all done: runlog lifecycle helpers, orchestrator IoC, handoff.py `--payload`/`--id` two-phase CLI with JSON stdout, gitio `log_messages`, manifest v3→v4 overlay propagated, verifier `_effective_range` overlap fix. 44 tests green. PR #52 opened. Key fix: idempotency check uses commit title suffix (not session number) to survive header-update N+1 false-miss.
- **Session 89 [pipeline] / 91 [actual]** (2026-06-12) — **Session-29 feedback round COMPLETE (P1–P5 all closed).** Expenses field report analyzed: T5 SKILL.md rewrite had never actually landed (commit 75886bb touched only manifest.yaml) and v4 propagation was partial (stale verifier.py in expenses → their P2). Fixes via Sonnet subagents + main-session review: error messages name regions `role(target)@file:line`; `--amend` (additive-only follow-up to last committed session) + `--abort <handle>`; copy-don't-move payload on failed stage; SKILL.md genuinely rewritten (3 copies byte-identical); overlay v5 propagated to 3 repos byte-verified with `cmp`. **126 tests green.** PR #52 body updated. Review caught 2 bugs behind green tests (amend N+1 mismatch, prepend allowlist hole).
- **Session 90 [pipeline] / 92 [actual]** (2026-06-16) — **Handoff topology/value-only/harvest redesign COMPLETE (P1–P5).** `session-log.md` now latest-only (slugged per-entry archives, no `Previous logs:` line); `log-entry` payload is value-only structured slots (pipeline renders all scaffold incl. heading); `handoff-harvest.sh` seeds `what_was_done` from git log. Overlay v5→v6 byte-verified in 3 repos; `session-log.md` migrated to latest-only in all 4 repos (career-search duplicate Session 56 healed). Advisor-gated end-to-end smoke test passed (`stage_ok`); this entry written by the new pipeline for real. **166 tests green.** PR #52 retitled + body extended.
- **Session 91 [pipeline] / 93 [actual]** (2026-06-17) — **Handoff append↔checkoff correctness fix + failure-clarity sweep COMPLETE.** Fixed `verifier.verify()` to treat append/prepend as true insertions (preserving nested checkoff flips) — the reconstruction half of the T-57 bug, surfaced by an expenses bug report. Full failure-clarity sweep: `kind` attribute on all pipeline exceptions (payload vs internal fault), `Region.role/file/target` populated, verifier messages name file+roles+diff with a TOOL BUG marker, locator messages name role+file+target, CLI routes `payload_error` vs `internal_tool_bug` (internal case cites `input.md`). Two-agent dispatch (Sonnet spine + Haiku mechanical). Overlay v6→v7; user-level engine reinstalled (`~/.claude/tools/handoff/`); two unintended installer side effects in llm repo reverted. **173 tests green** (166→173). Plan: `docs/plans/session-handoff-failure-clarity.md`.
- **Open deferred tasks:** ~~T-57~~ (done), **T-55** (MCP migration deferred), **T-56** (add-task CLI tool), **T-58** (overlay installer `--verify` mode), **T-59** (harvest commit-prefix specificity), **T-60** (overlay distribution G/H evaluation), hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix, Python 3.10→3.12 via uv, Layer 4 stragglers, raw temperature values, registry hot-reload, server.py refactor, file-based coordination layer, `extract_topics.py` retrofit to model_client.py, create-persona.py library, `add_model` MCP tool, prompt-iteration experiment, delete legacy `HTML_TEMPLATE`, LTG cross-ref-index 3rd-arm routing hypothesis, LTG per-topic rubric JSON, containment/post-pass guard, backfill SOLID+scope constraints, per-language error-handling + logging conventions, M-P0a cleanup (retire DeepCoder personas), **LTG config.yaml two-level registry design** (Phase 3+ trigger), **DeepSeek R2 32B** (watch), **Fara-7B** (watch)
- **Next:** LTG Phase 3 `anchors.py` TDD. (PR #52 merging — `feature/ltg-phase3-anchors` already in master, no rebase needed.)
- **Cross-repo:** MVP spike in web-research; expense MCP work in expenses repo; .memories/ PRs merged; all 3 target repos on overlay v6 + latest-only session logs (engine shared user-level; v7 source ready to propagate)
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands)

---
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

**Prompt anti-patterns (confirmed session 71):**
- Do NOT send code stubs to Ollama — describe behavior, not implementation. Stubs = you wrote the code and the model transcribed it.
- Do delegate test-writing to Ollama when tests contain non-trivial logic - you may pass test names.
- Large prompts (>2000 chars + 3 large context files) time out on 14B even when model is warm. Split into helper-first + main()-second calls.

**LanceDB API gotcha (session 71):** `LanceTable` has no `.column()` method. Use `.to_arrow().column("field_name").to_pylist()` to read a column. `table.count_rows()` is available directly.

**httpx async slip (session 71):** qwen2.5-coder generates `async def`/`await httpx.post()` even in sync contexts. Fix: explicitly write "use `httpx.post(url, json=payload, timeout=120.0)` — NOT async, NOT httpx.Client" in the prompt.

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

### Cross-cutting principles
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both → `docs/vision-and-intent.md`
- **Licensing (STRONG):** Always check + honor external project licenses; attribute in `docs/ATTRIBUTIONS.md`
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768** (probed 2026-05-30 with `OLLAMA_KV_CACHE_TYPE=q8_0` — all pass); 8B models → 32768; deepseek-coder-v2:16b → 24576 (32K tight at 574 MiB). See `retrieval/probes/ctx-probe-2026-05-30.md`.
- **Multi-model comparison → DPO pairs:** `run-compare-models.sh` + `run-record-verdicts.sh` → Layer 7 pipeline
- **Session-handoff pipeline (session 83):** register-driven deterministic rewrite of the session-handoff flow — reuse existing handoff `ref:` blocks (no new in-file markers), home = `session-tracking` overlay, local-model layer deferred to enhancement. Load-bearing contracts (the register, the F7 schema) are Claude-authored, not local-model. See `ref:handoff-pipeline-design`. **B2 safety core (session 84):** F1/F3/F4 are pure functions over `(role, text)`; the `Region(start,end,interior)` is the single boundary source of truth; F4 verifies by recompute-and-compare (re-derive expected text byte-exact), not hash-outside.
- **Handoff stage/promote redesign (session 89):** `--payload` = stage (rename-on-ingest via `shutil.move` + locate+apply+verify in memory + emit JSON handle); `--id` = promote (recompute from current files + idempotency git-log check + apply + commit + rename dir suffix). `--dry-run` flag dropped. Run dir status suffix (`-pending`/`-success`/`-failed`) replaces "writes nothing" invariant. JSON stdout. MCP migration deferred (T-55). Plan: `~/.claude/plans/handoff-redesign-rename-on-ingest.md`.
- **Handoff topology/value-only/harvest (session 90):** D1 = value-only **2-full** (`log-entry` is structured snake_case slots — `context`/`what_was_done`/`decisions`/`next`/`gotchas`; the pipeline renders ALL scaffold incl. the `## <date> - Session N: <title>` heading). D2 = **clean break** (manifest v5→v6, all repos migrate in lockstep, no dual-accept). Latest-only `session-log.md` — rotation archives each prior entry to a slugged `session-log-<date>-s<N>-<slug>.md`; the `Previous logs:` line is dropped (archive dir + filenames are the index). `handoff-harvest.sh` seeds `what_was_done`. Target registries left untouched (`manual_if_exists`) — the orphaned `header-previous-logs` role is inert (pipeline only walks payload→register). Plan: `docs/plans/session-handoff-topology-valueonly-harvest.md`.

**Frozen layer decisions (Layers 1/2/3):** `.claude/archive/decisions-layers-1-3.md`
**Historical decisions (Phases 0-6, Layer 0):** `.claude/archive/phases-0-6.md`
**LTG decisions:** `retrieval/DECISIONS.md` (ref keys: `ltg-scope`, `ltg-embedding`, `ltg-extractor`, etc.)
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->

*What to read before starting each pending work item. Keeps context sharp without re-reading everything.*

| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **LTG Phase 3 — write `anchors.py` TDD** | **`ref:ltg-phase3-decisions`** (`retrieval/DECISIONS.md`), `docs/plans/ltg-phase3-decisions-discussion.md` (`ref:ltg-phase3-discussion`), `retrieval/store.py` (schema), `retrieval/model_client.py` (embed_texts) | Decisions FROZEN session 82. `feature/ltg-phase3-anchors` already merged to master — no rebase needed. |
| **Merge PR #52 — handoff redesign (full)** | PR #52 on `feature/handoff-redesign-stage-promote`, base=master | 166 tests; stage/promote + session-29 fixes + session-90 topology/value-only/harvest + 4-repo migration. Carries 3 unrelated commits (app.py SSR, sync-context.sh pair) — confirmed acceptable. ltg-phase3-anchors already in master; ready to merge. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0` |
| **Backfill SOLID + error-handling directives** | `docs/tasks/backfill-persona-constraints.md`, `docs/ideas/persona-error-handling-conventions.md`, `personas/registry.yaml` | grep: `git grep -L "MUST NOT modify"` modelfiles/; pair error-handling session with backfill |
| **M-P0a cleanup — retire DeepCoder personas** | `personas/registry.yaml` (filter `status: benchmark`), `ref:deepcoder-benchmark-decision` | 6 personas to rm + archive Modelfiles; `deepcoder:14b` base (9GB on I:\\) optional |
| **Handoff pipeline — COMPLETE (overlay v7)** | `ref:handoff-pipeline-design` + `ref:handoff-placer-enhancement`, `overlays/session-tracking/files/registry.yaml`, `docs/plans/session-handoff-failure-clarity.md` | B1-B4 + stage/promote + session-29 fixes + session-90 topology/value-only/harvest + session-91 append↔checkoff fix + failure-clarity sweep; **173 tests**; engine shared user-level at `~/.claude/tools/handoff/` (v7); failure messages now name where/whose-fault/what (`kind` on exceptions, `payload_error`/`internal_tool_bug` statuses). Register via `manual_if_exists` (Option C). Feedback report: expenses `.claude/local/handoff-pipeline-feedback-session29.md`. |
<!-- /ref:session-reading-guide -->
