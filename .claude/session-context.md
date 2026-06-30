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
- **Session 94** (2026-06-20) — **LTG Phase 3 anchor integration COMPLETE.** `anchors.py` built TDD via contract-pin (main) + 4 sequential subagent slices (SA-1..4) + main-session live acceptance. `store.py` schema 18→22 (+`source_class`/`confidence`/`anchor_key`/`alias_of`). Live rebuild: 212 rows (69 topics + 143 anchors); `concept-latent-topic-graph` merges both `.memories` topics, M:N proven, orphan no-merge, staleness + near-miss diagnostics firing. `plan-latent-topic-graph` non-merge (0.7742, D3 operational-metadata failure on drifted corpus → Phase 2.5/3.5). 2 integration-only bugs caught at live run (sibling-import path, key-name shorthand). **254 tests green.** PR #55.
- **Session 95** (2026-06-23) — **PR #55 merged to master.** LTG Phase 2.5 planned: drafted `docs/plans/ltg-phase2.5-corpus.md` (full-corpus re-extraction + threshold recalibration T-34/T-36; config-driven ignore + group tags; ~45–70 min local GPU). Real corpus measured at 66 files / ~155 K tokens (`.claude/local/` excluded as noise). `.claude/archive/` decided IN, tagged as its own group. Long-file branch point resolved (no chunking). New task T-65 (source-group provenance + query-type-dependent retrieval weighting; cheap half in 2.5, weighting logic Phase 5).
- **Session 94 [pipeline] / 96 [actual]** (2026-06-26) — **LTG Phase 2.5 COMPLETE (PR #56).** Config-driven corpus (`corpus.yaml` → frozen `corpus-manifest.yaml`, 113 files sha256+commit-pinned) + `corpus_groups.py` shared matcher. `source_group` provenance field (T-65 cheap half, store-time derived). `retrieval/` migrated to uv Python 3.12 (T-18 slice; Sonnet subagent + main re-verify). Full rebuild: 875 topics / 113 files + 143 anchors = 1018 rows, 0 failures. T-34: `COSINE_THRESHOLD=0.85` validated-keep (continuous dist); noise threshold measured n=9 (real ≤0.58, pure-noise ≥0.91; recommend L2≈0.70) but documented-not-wired (acceptance_mode record-only) → T-34 left open. Step 5 generic-anchor precision PASS. `plan-latent-topic-graph` healed 0.7742→0.8379. **269 tests green.** Findings: `retrieval/probes/phase2.5-calibration.md`. T-36 closed.
- **Session 96 [pipeline] / 97 [actual]** (2026-06-30) — **Session-97 batch LANDED to master.** Merged #56 (Phase 2.5, `ca1acec`) as its own commit, then #57 (6 tasks + fan-out infra, `245fc95`) — clean SHA-dedup via shared `af3fea4`; #56/#57 closed, review PRs #58–64 closed, all session-97 branches + worktrees deleted (range-diff proved `worktree-agent` fully redundant). T-19/T-26/T-30/T-42/T-58/T-59 now on master (done). **Tooling:** `overlays/Makefile` + `overlays/scripts/` now run all 3 overlay suites (**196 tests**) via one `make test`; **git-add bulk-stage guard** added (`PreToolUse` hook + hookify rule + CLAUDE.md). PR #63 review-fixed: ref-lookup test fully hermetic, shipped in overlay source (manifest v4).
- **Open deferred tasks:** ~~T-57~~ (done), ~~T-32~~ (Phase 3 anchors done), ~~T-36~~ (Phase 2.5 corpus done), ~~T-58~~ (installer `--verify`, merged session 97), ~~T-59~~ (harvest prefix, merged session 97), **T-34** (calibration measured; noise-threshold wiring deferred), **T-55** (MCP migration deferred), **T-56** (add-task CLI tool), **T-60** (overlay distribution G/H evaluation), **T-61** (resume.sh overlay-source vs llm-repo divergence), **T-62** (home-repo run-handoff `--registry` passthrough), **T-63** (Phase 3.5 anchor escalation + near-miss tuning), **T-64** (`nearmiss_report` public stub cleanup), **T-65** (provenance cheap-half DONE; query-type weighting → Phase 5), **T-66** (validate cache-warmed fan-out + protocol-embedding), hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix, **Python 3.10→3.12 via uv** (retrieval slice DONE session 96; benchmarks/scripts/.claude tools pending), Layer 4 stragglers, registry hot-reload, server.py refactor, file-based coordination layer, create-persona.py library, `add_model` MCP tool, prompt-iteration experiment, delete legacy `HTML_TEMPLATE`, LTG cross-ref-index 3rd-arm routing hypothesis, LTG per-topic rubric JSON, containment/post-pass guard, per-language error-handling + logging conventions, M-P0a cleanup (retire DeepCoder personas), **LTG config.yaml two-level registry design** (Phase 3+ trigger), **DeepSeek R2 32B** (watch), **Fara-7B** (watch), **T-67** (verify Option B for `my-go-qcoder` HTTP 500 — root cause is host-RAM ENOMEM, not VRAM: store on 9p `/mnt/i` forces Ollama `UseMmap:false` → reads full 19.3 GiB blob into RAM; WSL2 had 15.5 GiB. Mitigated session 98 by raising WSL `.wslconfig` memory=24GB. **Option B = move the 30B blobs back to native ext4 so mmap re-engages** → host-RAM cost drops to ~0; verify it loads without the 24GB cap and re-check VRAM/RAM footprint. Reverses session-75 store migration; needs vhdx space.)
- **Next:** LTG Phase 4 — graph + communities (`alias_of` lists are proto-edges → edge table; anchor↔anchor edges from index.md cross-refs land here), building on the fresh full-corpus index now on master.
- **Cross-repo:** MVP spike in web-research; expense MCP work in expenses repo; .memories/ PRs merged; all 3 target repos on overlay v6 + latest-only session logs (engine shared user-level; v7 source ready to propagate). Overlay test runner (`make -C overlays test`, 196 tests) now in master.
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
| **LTG Phase 4 — graph + communities** | `ref:ltg-plan-phase-4`, `retrieval/anchors.py` (`alias_of` proto-edges), `retrieval/DECISIONS.md` (`ref:ltg-phase3-decisions` Phase-4 notes), `ref:ltg-graph-lib` (networkx + leidenalg) | **Now the top priority** (Phase 2.5 done session 96). `alias_of` lists relocate to an edge table; anchor↔anchor edges from index.md cross-refs also land here. Build on the fresh 1018-row full-corpus index. |
| **LTG Phase 2.5 — COMPLETE (PR #56)** | `retrieval/probes/phase2.5-calibration.md`, `retrieval/.memories/KNOWLEDGE.md` (`ref:ltg-phase2.5-corpus`) | 875 topics/113 files + 143 anchors. `corpus.yaml`+`corpus-manifest.yaml` (config-driven, sha256-frozen). `source_group` live. retrieval/ on uv Python 3.12. T-34 measured (0.85 validated-keep; noise threshold documented-not-wired); T-36 closed. |
| **LTG Phase 3.5 — anchor escalation (T-63)** | `retrieval/probes/phase2.5-calibration.md` (fresh near-miss data), `docs/plans/ltg-phase3-anchors-implementation.md` §8b, `retrieval/anchors.py` (`describe_*`, `NEARMISS_LOW`, `_nearmiss_with_vectors`) | `plan-latent-topic-graph` now 0.8379 (was 0.7742, healed by re-extraction) — still <0.85. ~26 anchors in 0.80–0.85 near-miss band. Lower `NEARMISS_LOW` and/or LLM one-liner escalation. Plus 2–3 borderline M:N merges above 0.85 to review. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0` |
| **Backfill SOLID + error-handling directives** | `docs/tasks/backfill-persona-constraints.md`, `docs/ideas/persona-error-handling-conventions.md`, `personas/registry.yaml` | grep: `git grep -L "MUST NOT modify"` modelfiles/; pair error-handling session with backfill |
| **M-P0a cleanup — retire DeepCoder personas** | `personas/registry.yaml` (filter `status: benchmark`), `ref:deepcoder-benchmark-decision` | 6 personas to rm + archive Modelfiles; `deepcoder:14b` base (9GB on I:\\) optional |
| **Handoff pipeline — COMPLETE (overlay v7)** | `ref:handoff-pipeline-design` + `ref:handoff-placer-enhancement`, `overlays/session-tracking/files/registry.yaml`, `docs/plans/session-handoff-failure-clarity.md` | B1-B4 + stage/promote + session-29 fixes + session-90 topology/value-only/harvest + session-91 append↔checkoff fix + failure-clarity sweep; **173 tests**; engine shared user-level at `~/.claude/tools/handoff/` (v7); failure messages now name where/whose-fault/what. Register via `manual_if_exists` (Option C). Home-repo run still needs direct `handoff.py --registry` (T-62). |
<!-- /ref:session-reading-guide -->
