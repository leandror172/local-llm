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
- **Session 60** (2026-05-16) — Side-track: consolidated 6 Ollama-usage directives from expense/web-research feedback memories into the `ollama-scaffolding` overlay. Converted the reference doc from a `templates:` entry to a `files:` entry (propagates on re-install); renamed `local-model-retry-patterns` → `local-model-conventions`. Fixed 2 installer bugs in `overlays/lib/actions.py` — extension-based chmod (drvfs reports 777) and CRLF preservation in `handle_merge_sections`. Propagated to expense (`4ed7a89`) + web-research (`4bd07d5`). Branch `feature/ollama-scaffolding-directives`, commits `3c0e2f4` + `548ca07`. Did not touch LTG.
- **Session 61** (2026-05-20) — VRAM co-residence probe: bge-m3 + qwen3:14b. WARN verdict (eviction at load time only; 0 query-time evictions, avg infer 3.5s). **bge-m3 locked. Sequential constraint: embed and infer must not run in parallel.** Script: `retrieval/run-vram-probe.sh`. Updated `ref:ltg-embedding` in DECISIONS.md + retrieval/.memories/QUICK.md.
- **Session 62** (2026-05-22) — Side session: designed and wrote 3 MCP server feature plans (refs param, output_file param, patch_file tool). All plans include TDD test specs, ref markers (mcp-refs-param-*, mcp-output-file-*, mcp-patch-file-*), and overlay update steps. Files: `docs/plans/ollama-bridge-refs-param.md`, `docs/plans/ollama-bridge-output-file.md`, `docs/plans/ollama-bridge-patch-file.md`. Ready to execute TDD.
- **Session 63** (2026-05-22) — MCP Plan 1 (refs param): 10 green tests, live-tested. New persona `my-mcp-q25c14`. SOLID + scope constraints added to 3 × 14B coding personas.
- **Session 64** (2026-05-22) — MCP Plan 2 (output_file + output_only): 9 green tests (19 total), live acceptance tested. `_resolve_output_path` + `_write_output_file` helpers extracted. PR #37 created (Plans 1+2).
- **Session 65** (2026-05-22) — Pre-work fixes from Plan 2 advisor review (double resolution, .resolve() ordering, 3 test assertions). Plan 3 (`patch_file` tool): 10 green tests (29 total), atomic write, UTF-8 round-trip, `_strip_code_fences()` for `generate_code`. PR #38 created (base: feature/ollama-bridge-output-file).
- **Session 66** (2026-05-25) — MCP debug logging (`debug_log.py`, env-driven JSONL, per-process `client_id`, reserved-fields filter) wired into `_lifespan` + `patch_file`/`generate_code`/`ask_ollama` + `chat()`. `mcp-server/Makefile` (`make logs/logs-raw/bridges`) + `scripts/{which-bridge,watch-logs}.sh`. Fixed `_resolve_output_path` to `.expanduser()` (surfaced live: `~` was treated literal, writing to `<repo>/~/...`); regression tests for both `patch_file` + `output_file` (21/21 green).
- **Session 67** (2026-05-26) — `patch_file` full acceptance testing: 10/10 scenarios pass (tilde fix live-verified, 6 original cases, 3 complex user scenarios: correction loop, context_files add-functionality, surgical patch). All 5 local model calls verdict 1 — consistent `logging.basicConfig()` antipattern + catch-log-reraise noise. Error-handling analysis written up in `docs/ideas/persona-error-handling-conventions.md` (Python/Java/Go rules + proposed Modelfile directives). Results doc: `docs/plans/ollama-bridge-patch-file-acceptance-results.md`. PR #38 updated. 2 commits ahead of origin (not yet pushed).
- **Session 68** (2026-05-26) — Model update survey: 5 research agents covering Qwen, Microsoft, Llama 4, Mistral, benchmark rankings, and frontier-distilled models. Key findings: (a) `qwen3.6-coder:14b` candidate to supersede `qwen2.5-coder:14b` (claimed SOTA — benchmark numbers from secondary sources, not independently verified; swap gated on M-P0a local benchmark); (b) `qwen3-embedding:8b` candidate to replace `bge-m3` (MTEB 63.0→70.58, on Ollama — VRAM co-residence probe is hard gate before LTG Phase 2 embed.py); (c) `llama4:scout` adds long-context capability (advertised 10M ctx, effective ~200K–1M for RAG, fits 12GB); (d) qwen3.5 tiny models (0.8B/2B) enable simultaneous warm classifier + 14B model in 12GB VRAM; (e) `deepseek-r1:14b` already is a frontier-distilled model (DeepSeek-R1 CoT traces); (f) community Claude-distilled Qwen models exist but ToS gray area + no verified benchmarks — watch only; (g) qwen3:14b still SOTA reasoning ≤14B. Survey doc: `docs/findings/model-updates-2026-05.md`. Tasks: `M-P0a/b` (pull + benchmark + swap if confirmed) + `M-P1a/b` + `M-P2` in tasks.md. Branch: `feature/model-survey-2026-05`.
- **Session 69** (2026-05-27) — Advisor review applied to session 68 output. 8 edits to `docs/findings/model-updates-2026-05.md`: methodology footnote, P0 re-framing (swap → benchmark-first), Verification Status column, Qwen3.7 Max qualified, unverified benchmark numbers footnoted, embedding probe marked hard gate, Llama 4 Scout 10M context qualified, frontier-distilled Independent benchmark Y/N column. Also updated `.memories/QUICK.md`, `.memories/KNOWLEDGE.md`, `.claude/tasks.md` (M-P0a/b), `.claude/session-context.md`. Branch: `feature/model-survey-advisor-review`. PR targets `feature/model-survey-2026-05`.
- **Session 70** (2026-05-27) — LTG Phase 2 design decisions (no implementation). All PRs treated as merged. Key decisions: (a) bge-m3 for Phase 2 (qwen3-embedding:8b probe deferred to after Phase 2); (b) new Phase 2 scope: `model_client.py` isolation layer + `config.yaml` role-keyed config; (c) embed_dim assertion Option B (first embed call, lazy); (d) config.yaml flat/inline for Phase 2 — two-level `models:` + `roles:` design deferred to Phase 3+ trigger. New file: `docs/ideas/ltg-model-registry-design.md`. Updated: `docs/plans/ltg-phase2-implementation.md` (scope + decisions), `tasks.md` (2 new deferred tasks), `index.md`.
- **Session 71** (2026-05-27) — LTG Phase 2 Tasks 3–6 complete. 4 commits on `feature/ltg-phase2-implementation`. Files written: `retrieval/model_client.py` (13 tests), `retrieval/preflight.sh` + `run-preflight.sh`, `retrieval/embed.py` (23 tests) + `run-embed.sh`, `retrieval/store.py` (11 tests) + `run-store.sh`, `retrieval/tests/` (3 test files, 47 total tests green). Remaining: Tasks 7–9 (inspect.py, acceptance run, post-completion docs).
- **Session 72** (2026-05-28) — LTG Phase 2 Tasks 7–9 complete. Branch `feature/ltg-phase2-implementation`. Files: `retrieval/ltg_inspect.py` (14 tests) + `run-inspect.sh`. Key fix: renamed from `inspect.py` — shadows stdlib. Acceptance: 69 topics, 8 files, 7/8 queries pass (R2 borderline), 2.3s total. Probe at `retrieval/probes/acceptance-2026-05-28.md`. qwen2.5-coder:14b timed out 3× on test gen; escalated to qwen3:14b. **Phase 2 fully closed.**
- **All PRs merged** (sessions 63-69): #37 (Plans 1+2), #38 (Plan 3+logging+~fix), #39 (model survey + advisor review). Master is current.
- **Phase 1 status: FULLY CLOSED (session 59, 2026-05-04).** `ref:ltg-extractor` frozen: qwen3:14b (prose), qwen2.5-coder:14b (code). See `retrieval/DECISIONS.md`.
- **Open deferred tasks:** hook-based auto-resume, **Qwen3-Coder-Next feasibility** (superseded — `qwen3.6-coder:14b` is the near-term upgrade; 80B MoE still deferred), expense-reporter runtime.Caller fix (tracked in expenses repo), Python 3.10→3.12 via uv, Layer 4 stragglers (Phase 3 frontier judge, claude-desktop insights tool 4.6), raw temperature values, registry hot-reload, server.py refactor, file-based coordination layer (watch PR #9392), `extract_topics.py` retrofit to model_client.py, extract create-persona.py into importable library, `add_model` MCP tool, prompt-iteration experiment (topic-count floor + containment-only overlap), delete legacy `HTML_TEMPLATE` from viz_sweep.py, **LTG cross-ref-index 3rd-arm routing hypothesis**, **LTG per-topic rubric JSON as Phase 2 input**, **containment/post-pass guard** for qwen3:14b on dense single-line bullet lists, **backfill SOLID+scope constraints to all remaining coding personas**, **per-language error-handling + logging conventions**, **model update tasks M-P0a/b through M-P2** (M-P0b: do VRAM probe for qwen3-embedding:8b *after* Phase 2 completes, not before), **LTG config.yaml two-level registry design** (Phase 3+ trigger), **DeepSeek R2 32B** (watch), **Fara-7B** (watch)
- **Session 73** (2026-05-28) — M-P0b complete. VRAM probe: qwen3-embedding:8b WARN verdict (same as bge-m3 — load-time eviction only, zero query-time, avg infer 4.2s). **Embedding upgraded: bge-m3 (1024-dim) → qwen3-embedding:8b (4096-dim).** `embed.py`/`store.py` now config-driven (no hardcoded dims). Acceptance equivalent (R1/R3/R4 ✅, R2 ⚠️ same gap, relate improved 0.663→0.697). N-criteria threshold recalibration deferred to Phase 3. Branch: `feature/ltg-embedding-upgrade-qwen3`. 2 commits, 61 tests green.
- **Session 75** (2026-05-29) — Infrastructure + model pulls + context-limit audit. Key changes: (a) Ollama model store migrated from WSL2 VHD (C:\\) to I:\\ (`/mnt/i/ollama-models/`, 406GB free); (b) `OLLAMA_KV_CACHE_TYPE=q8_0` enabled system-wide — 8B → 32K ctx, 14B → 16K with headroom; (c) `qwen3.5:0.8b/2b` + `phi4-mini` pulled for classifier benchmark; (d) `llama4:scout` pulled then removed — not viable (67GB, 24GB VRAM floor, poor synthesis quality); M-P1a closed permanently; (e) MCP personas `my-mcp-q25c14` + `my-mcp-q3` fixed (correct FastMCP import canonical example added); (f) Layer 5 adjacent-projects.md created, tasks.md synced; (g) 18-file context-limit doc audit completed — all stale 4K/10240 references updated. `extract_topics.py` num_ctx 8192→16384 (LTG quality impact).
- **Session 76** (2026-05-30) — 14B num_ctx re-probe + LTG architectural note. All 14B models upgraded 16K→32K (deepseek-coder-v2:16b→24K). 11 personas rebuilt. `scripts/run-ctx-probe.sh` added. LTG repo-separation gate note added to Phase 6 plan + tasks.md. Pre-session reading guide added to resume.sh (`ref:session-reading-guide`). Branches: tracking commits on `feature/ollama-monitoring`; probe work on `feature/14b-num-ctx-reprobe`.
- **Session 77** (2026-05-30) — LTG extractor retrofit design. Full design settled in session (two advisor passes). Fork B: `extract_topics.py` → 2-arm production runner; `sweep_extractors.py` new benchmark. New modules: `routing.py`, `schemas.py`. `ModelClient` gains `extract_prose()`, `extract_code()`, `call()`, `_chat()`, `ChatResult`. `config.yaml` → two-level `models:`+`roles:`. Pattern doc: `docs/patterns/code-design-conventions.md` (`ref:patterns-code-named-methods`). Plan: `docs/plans/ltg-extractor-retrofit.md`. Branch: `feature/ltg-extractor-retrofit`. Task 1 TDD tests written (`retrieval/tests/test_routing.py`, 14 tests, confirmed red).
- **Sessions 78–80** (2026-05-31 to 2026-06-01) — LTG extractor retrofit COMPLETE. All 8 tasks implemented on `feature/ltg-extractor-retrofit`. 147 tests green. Parity verified end-to-end (prose→qwen3:14b, code→qwen2.5-coder:14b, 0 failed topics). Commits: routing/schemas/model_client (Tasks 1–3), config+routing-agreement (Task 4), sweep_extractors (Task 5), extract_topics rewrite (Task 6), bash wrappers (Task 7). Branch ready to PR → master.
- **Session 81** (2026-06-01) — Retrofit close-out + **LTG Phase 3 anchor DISCOVERY (not frozen).** Close-out: sonnet sub-agent cleared the advisor punch-list (live sweep verified, stale `bge-m3` refs fixed, `test_config_yaml_contract` added — 148 tests); retrofit PR pushed. num_ctx three-way finding → decision (c) (benchmark 16384 / production 32768 kept divergent; recheck at Phase 2.5). Wrote `.claude/workflows-feature-guide.md`. Started Phase 3 on branch `feature/ltg-phase3-anchors`: discovery doc `docs/plans/ltg-phase3-anchor-discovery.md` — weights generalize anchor stratification; three-confidence concepts; **dual-path RAG** (ref-keys as a parallel retrieval surface, alias-link not physical merge); empirical: only 2 of 138 ref keys in the 8 extracted files. Advisor-reviewed. D1/D3/D4 aligned; **D2/D5/D6/D7 OPEN.** Saved memory: ask permission before `advisor()` in main session.
- **Session 82** (2026-06-02) — **LTG Phase 3 anchor decisions FROZEN.** All decisions settled (5 advisor passes, 2-pass 6-method similarity probe). Key: dual-path=yes, D2=A repo-wide (ingestion via regex grep, not `ref-lookup.sh`), alias-link M:N `alias_of` JSON list, `confidence` 0.7 node-provenance not upgraded on alias, `node_kind` drops `merged`, `mechanical+key` description method (provisional), threshold 0.85/L2 0.547 provisional. Anchor authority = structural (not human-declared); `human_reviewed` deferred. Full spec in `retrieval/DECISIONS.md` (`ref:ltg-phase3-decisions`); discussion in `docs/plans/ltg-phase3-decisions-discussion.md` (`ref:ltg-phase3-discussion`). Probe: `retrieval/probes/anchor-similarity-probe-2026-06-02.py` (6 methods). 5 corrections applied via subagent (anchor row field-population table, D6 distances, grep regex, `node_kind` enum Phase 4 note, integrity-check universe).
- **Next:** **Rebase `feature/ltg-phase3-anchors` onto master** after retrofit PR merges, then **write `retrieval/anchors.py` TDD** — `ref:ltg-phase3-decisions` is the complete spec. See session-reading-guide row below.
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
## Active Decisions

### Cross-cutting principles
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both → `docs/vision-and-intent.md`
- **Licensing (STRONG):** Always check + honor external project licenses; attribute in `docs/ATTRIBUTIONS.md`
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768** (probed 2026-05-30 with `OLLAMA_KV_CACHE_TYPE=q8_0` — all pass); 8B models → 32768; deepseek-coder-v2:16b → 24576 (32K tight at 574 MiB). See `retrieval/probes/ctx-probe-2026-05-30.md`.
- **Multi-model comparison → DPO pairs:** `run-compare-models.sh` + `run-record-verdicts.sh` → Layer 7 pipeline

**Frozen layer decisions (Layers 1/2/3):** `.claude/archive/decisions-layers-1-3.md`
**Historical decisions (Phases 0-6, Layer 0):** `.claude/archive/phases-0-6.md`
**LTG decisions:** `retrieval/DECISIONS.md` (ref keys: `ltg-scope`, `ltg-embedding`, `ltg-extractor`, etc.)
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->
## Pre-Session Reading Guide

*What to read before starting each pending work item. Keeps context sharp without re-reading everything.*

| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| ~~**14B num_ctx re-probe**~~ | ~~DONE session 76~~ | All 4 14B models → 32768 (dsc16 → 24576). Results: `retrieval/probes/ctx-probe-2026-05-30.md` |
| **LTG Phase 3 — write `anchors.py` TDD** | **`ref:ltg-phase3-decisions`** (`retrieval/DECISIONS.md`), `docs/plans/ltg-phase3-decisions-discussion.md` (`ref:ltg-phase3-discussion`), `retrieval/store.py` (schema), `retrieval/model_client.py` (embed_texts) | Decisions FROZEN session 82. Rebase `feature/ltg-phase3-anchors` onto master first (stacked on retrofit PR). Full spec in `ref:ltg-phase3-decisions` — ingestion grep, anchor row field-population table, `mechanical+key` description method, alias-link, threshold, acceptance all specified. |
| ~~**extract_topics.py retrofit**~~ | ~~DONE sessions 78–80~~ | All 8 tasks complete. 147 tests. Branch `feature/ltg-extractor-retrofit` ready to PR. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0` |
| **Backfill SOLID + error-handling directives** | `docs/tasks/backfill-persona-constraints.md`, `docs/ideas/persona-error-handling-conventions.md`, `personas/registry.yaml` | grep: `git grep -L "MUST NOT modify"` modelfiles/; pair error-handling session with backfill |
| **M-P0a cleanup — retire DeepCoder personas** | `personas/registry.yaml` (filter `status: benchmark`), `ref:deepcoder-benchmark-decision` | 6 personas to rm + archive Modelfiles; `deepcoder:14b` base (9GB on I:\\) optional |
<!-- /ref:session-reading-guide -->
