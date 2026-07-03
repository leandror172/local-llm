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
- **Session 97 [pipeline] / 98 [actual]** (2026-06-30) — **`my-go-qcoder` HTTP 500 fixed + Ollama store moved to ext4 (infra side-track).** Root-caused the recurring 500 as **host-RAM ENOMEM, NOT VRAM** (the label ~6 expense sessions inherited): the 30B partial-offload reads ~10–15 GiB of weights into host RAM > WSL2's old 15.5 GiB. **Fix = WSL `.wslconfig memory=24GB` (load-bearing).** Then executed T-67 store move to a dedicated ext4 vhdx (`/dev/sde` → `/mnt/ollama-store/models`, 162 GB rsync'd byte-verified, 81 models) — but ext4 did **NOT** re-enable mmap (Ollama forces `UseMmap:false` for partial-offload, any fs; `use_mmap:true` ignored) → RAM unchanged; real win = cold load **33 s → 15.6 s** + clean store + guard/checker against silent empty-store. Logon task (Option A) registered for reboot persistence. mmap premise corrected across QUICK/KNOWLEDGE/plan/both repos' session-context. Artifacts: `scripts/ollama-ext4/`, `make -C ~/workspaces ollama-store-check`. Plan: `docs/plans/ollama-store-ext4-move.md`.
- **Session 98 [pipeline] / 99 [actual]** (2026-07-01) — **T-68 CLOSED: ext4 store reboot-persistence now self-heals + 162 GB reclaimed.** A real reboot since session 98 exposed the store detached — the logon task fired but returned `LastTaskResult=1` (its chained in-WSL `systemctl restart` raced the cold WSL/systemd boot; vhd left unattached; ollama correctly refused to start via the loud-fail guard). **Fix (Option A, `a64f211`):** thin the logon task to attach-only; a udev rule `99-ollama-store.rules` (matched by `ID_FS_UUID` → `SYSTEMD_WANTS`) pulls a oneshot `ollama-store-recover.service` (`reset-failed` + `start ollama` → mount → now-present device). Event-driven, no boot-timing race. Live-verified non-destructively (`udevadm trigger --action=add`: FAIL→PASS), then a real reboot cold **PASS** with zero manual steps (device shifted **sde→sdd**; UUID matching held). Reclaimed old `/mnt/i/ollama-models` (162 GB; I: 233→394 GB free); live store verified unaffected. Close-out `717c9ae`. Artifacts + verified runbook: `~/workspaces/ollama-infra/` (moved out of the repo session 100).
- **Session 99 [pipeline] / 100 [actual]** (2026-07-01) — **Career chatbot (HF Space) Groq free-tier fix side-track.** Free backend 413'd on every question: all 19 synced quick files were statically concatenated into SYSTEM_PROMPT (~23.8K tokens/request vs Groq's 12K TPM). Three budget caps (Sonnet subagent + main): 16 non-root quick files demoted into the routed section index (baseline ~20K→~4.2K tok, routing cap 3→5, index switched headings-only after the merged index alone would have hit ~11K tok), `CONTEXT_CHAR_BUDGET` guard (drop whole files largest-first, loud warning), `HISTORY_CHAR_BUDGET=3000` window on replayed history. Expenses repo consolidated its QUICK.md files 46.3K→16.2K chars in parallel (audit: `~/workspaces/expenses/code/.claude/quick-memory-audit-2026-07-01.md`; root cause = handoff episodic append → T-67 here). Retrieval-miss found post-deploy ("work on RAG?" missed LTG entirely): headings-only routing needs query vocabulary in headings → `retrieval/.memories/` headings renamed with LTG/RAG/embedding/vector-store terms (`docs(retrieval)` commit); re-test routed 4/4 LTG sections. Also fixed `_retry_after` to parse Groq's `NNms` wait format (was misclassified non-retriable). Worst-case usage ~11.9K vs 12K ceiling (measured 12,017 — 17 over → now retried). 68 hf-space tests green. Deployed + verified live on both probe questions.
- **Session 100 [pipeline] / 101 [actual]** (2026-07-02) — **Ollama outage fixed + two systemd-coupling gaps closed + all machine config moved out of the repo (PR #65).** Expenses repo reported ollama down. Root cause: `wsl --mount` binds the vhd to a **single WSL2 VM lifetime** — any VM restart (idle, `wsl --shutdown`, Docker) silently drops the attach and the logon-only task never re-fires (`LastTaskResult=0`, attach succeeds then evaporates). Recovered live via `schtasks.exe /run` (device back in 1 s → udev→recover → 81 models on `:11435`). Durable fix: `ollama-store-attach.service` (oneshot, fires on every VM boot, triggers the elevated attach task via interop, `Before=` the mount). Separately `:11434` was dead — the Session-76 metrics proxy (native Go binary, **no Docker in the data path**) was only ever hand-started; made it a systemd peer of ollama (`ollama-metrics-proxy.service`, `WantedBy=ollama.service`+`PartOf`+`BindsTo`) so `:11434` is now as reliable as ollama, clients unchanged. Consolidated all machine-specific ollama config (T-68 ext4 set + both new units + docs) out of the repo to un-versioned `~/workspaces/ollama-infra/`. Both units installed+enabled; VM-restart gate deferred to **T-70** (needs a real `wsl --shutdown`, which kills the session).
- **Session 101 [pipeline] / 102 [actual]** (2026-07-02) — **LTG Phase 4 design locked + implementation plan authored.** PR #65 merge landed. T-63 cleared as a Phase-4 blocker (session-96 calibration: sub-0.85 near-misses are coincidental adjacency, not missed aliases; the one real miss `plan-latent-topic-graph` @ 0.8379 will surface as a ~0.84 similarity edge). Decisions **P4-D1–D7 frozen**: exact similarity (one matmul, no ANN), τ-floor + union top-K retention (new `graph:` config section; values frozen by a Step-0 degree probe), mention-based anchor↔anchor `references` edges, LanceDB `edges` table, nullable `community_coarse`/`community_fine` columns (anchors rebuild nulls them → regenerate; order extract→embed→store→anchors→graph→communities), `alias_of` **projected** to `same_as` edges (not migrated), Leiden RBConfiguration 2 seeded resolutions. Plan: `docs/plans/ltg-phase4-graph-communities.md` (`ref:ltg-phase4-plan`) + index.md entry. Phase 4 = **zero model calls** — pure derivation, regenerates in seconds.
- **Session 102 [pipeline] / 103 [actual]** (2026-07-02) — **LTG Phase 4 EXECUTED (T1–T7, PR #66) + anchors-rebuild idempotency fix.** `graph.py` (exact-matmul similarity, `--degree-probe`, edges build + run report) + `communities.py` (Leiden 2-res seeded) + `run-graph.sh`/`run-communities.sh`. Step-0 probe froze **τ=0.70/K=10** (`ref:ltg-phase4-degree-probe`): archive hairball debunked (24.4% edge share vs 18.3% random), isolation is τ-only. Schema 23→25 (nullable community columns, writers default null). Live: 3367 edges (3222 similarity + 28 same_as exact-M:N + 117 references), Leiden 207 coarse / 214 fine, 1022/1022 assigned. **All acceptance PASS** (`ref:ltg-phase4-acceptance`): top-20 edges 20/20 defensible, T-63 near-miss visible at 0.8379, rebuild ≈11 s zero model calls. **Live bug found+fixed:** `rebuild_index` re-read prior anchor rows as topics (non-idempotent; same_as 28→229) → `_topic_rows_only` filter + regression test; index rebuilt clean via store→anchors→graph→communities (875+147=1022 nodes, zero dupes/phantoms). Reports ref-anchored; QUICK memories de-episodized (retrieval QUICK current-state-only, ledger → KNOWLEDGE; T-67 pattern). **304 tests green.**
- **Open deferred tasks:** ~~T-57~~ (done), ~~T-32~~ (Phase 3 anchors done), ~~T-36~~ (Phase 2.5 corpus done), ~~T-58~~ (installer `--verify`, merged session 97), ~~T-59~~ (harvest prefix, merged session 97), **T-34** (calibration measured; noise-threshold wiring deferred), **T-55** (MCP migration deferred), **T-56** (add-task CLI tool), **T-60** (overlay distribution G/H evaluation), **T-61** (resume.sh overlay-source vs llm-repo divergence), **T-62** (home-repo run-handoff `--registry` passthrough), **T-63** (Phase 3.5 anchor escalation + near-miss tuning — **unblocked, Phase 4 edge evidence in hand**), **T-64** (`nearmiss_report` public stub cleanup), **T-65** (provenance cheap-half DONE; query-type weighting → Phase 5), **T-66** (validate cache-warmed fan-out + protocol-embedding), **T-70** (VM-restart store-attach gate), **T-71** (run-rebuild-all wrapper + backup-chain hardening — single-slot `.bak` clobbered across pipeline stages, session 102), hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix, **Python 3.10→3.12 via uv** (retrieval slice DONE session 96; benchmarks/scripts/.claude tools pending), Layer 4 stragglers, registry hot-reload, server.py refactor, file-based coordination layer, create-persona.py library, `add_model` MCP tool, prompt-iteration experiment, delete legacy `HTML_TEMPLATE`, LTG cross-ref-index 3rd-arm routing hypothesis, LTG per-topic rubric JSON, containment/post-pass guard, per-language error-handling + logging conventions, M-P0a cleanup (retire DeepCoder personas), **LTG config.yaml two-level registry design** (Phase 3+ trigger), **DeepSeek R2 32B** (watch), **Fara-7B** (watch), ~~T-67~~ (DONE session 98), ~~T-68~~ (DONE session 99), **T-69** (mmap revisit — can Ollama ever mmap a *partially-offloaded* model? Would free ~10–15 GiB host RAM + let us drop `.wslconfig memory=24GB`. Currently NO: `UseMmap:false` forced on any fs, `use_mmap:true` ignored [verified session 98]. Re-check on Ollama releases mentioning mmap/partial-offload; test = load `my-go-qcoder`, `journalctl -u ollama | grep UseMmap`; if true + RAM drops, lower the cap.)
- **Next:** LTG Phase 5 — `relate(a,b)` tool (`ref:ltg-plan-phase-5`). Consumers read the `edges` table, never `alias_of` (P4-D6). Phase 4 reports: `ref:ltg-phase4-degree-probe`, `ref:ltg-phase4-acceptance`, `ref:ltg-phase4-findings`. T-63 escalation now has fresh edge evidence.
- **Cross-repo:** MVP spike in web-research; expense MCP work in expenses repo; .memories/ PRs merged; all 3 target repos on overlay v6 + latest-only session logs (engine shared user-level; v7 source ready to propagate). Overlay test runner (`make -C overlays test`, 196 tests) now in master.
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands). Ollama serves `:11435`; the `:11434` metrics proxy is now a systemd peer of ollama (`ollama-metrics-proxy.service`, up whenever ollama is). Store on dedicated ext4 vhdx at `/mnt/ollama-store/models` (session 98); reboot-persistence self-heals via udev (T-68) and now re-attaches on every VM restart via `ollama-store-attach.service` (session 100). All machine-specific ollama config lives in `~/workspaces/ollama-infra/`, NOT the repo. WSL `.wslconfig memory=24GB` is load-bearing for 30B partial-offload.

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
- **Ollama host-RAM + store location (session 98):** 30B partial-offload models read weights into **host RAM** (Ollama forces `UseMmap:false` on partial offload, any filesystem) → `.wslconfig memory=24GB` is the load-bearing fix for the `my-go-qcoder` HTTP 500 (host-RAM ENOMEM, NOT VRAM). Store on a dedicated ext4 vhdx at `/mnt/ollama-store/models` (faster loads + clean store, not a RAM fix). Health: `make -C ~/workspaces ollama-store-check` (systemd+API, namespace-robust). Plan: `docs/plans/ollama-store-ext4-move.md`.
- **Ollama store reboot-persistence (T-68, session 99):** self-healing. The Windows logon task (`WSL-Ollama-ext4-store`, `-AtLogOn`) ONLY attaches the vhd (`wsl --mount --vhd … --bare`); recovery lives in WSL, not Windows-side timing. A udev rule (`99-ollama-store.rules`, matched by `ID_FS_UUID`) `SYSTEMD_WANTS` a oneshot `ollama-store-recover.service` (`reset-failed` + `start ollama` → pulls mount → pulls now-present device) — event-driven, survives `/dev/sdX` letter changes (proven sde→sdd). Do NOT chain the in-WSL `systemctl restart` into the logon task: it races the cold WSL/systemd boot (`LastTaskResult=1`). Artifacts + verified runbook: `~/workspaces/ollama-infra/` (machine-local; moved out of the llm repo 2026-07-02 — the repo carries no machine config).
- **Ollama store attach — VM-restart gap (T-68 follow-up, session 100):** `wsl --mount` binds the vhd to a **single WSL2 VM lifetime**; any VM restart (idle timeout, `wsl --shutdown`, Docker bouncing WSL) silently drops the bare-disk attach and nothing re-attaches — `LastTaskResult=0` is misleading (the attach succeeds then evaporates). The logon task covers cold boot but not mid-session restarts. Fix: `ollama-store-attach.service` (oneshot, `WantedBy=multi-user.target`, `Before=` the mount) fires on **every** VM boot and triggers the elevated Windows attach task via `schtasks.exe /run` (interop; no UAC needed to trigger an already-elevated task). The udev→recover chain completes it. Machine-local at `~/workspaces/ollama-infra/`. Gate = T-70.
- **`:11434` metrics proxy coupling (session 100):** the Session-76 transparent proxy (native Go binary, `:11434`→`:11435`, **no Docker in the data path** — only Grafana/Prometheus `make stack` is Docker) is now a systemd peer of ollama: `ollama-metrics-proxy.service` with `WantedBy=ollama.service` + `PartOf` + `BindsTo`, so `:11434` is up exactly when ollama is. Clients (expenses, MCP bridge, benchmarks) stay on the canonical `:11434`; no per-repo port changes. Install/unit: `~/workspaces/ollama-infra/`.
- **Machine config lives outside the repo (session 100):** all machine-specific ollama systemd/config (ports, `/usr/local/bin`, WSL/UNC paths) lives in un-versioned `~/workspaces/ollama-infra/`, NOT the llm repo (portable platform code only). Boundary established by `~/workspaces/scripts/`; PR #65. Only live pointers repoint on a move; historical session logs keep old paths as history.
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
| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **LTG Phase 5 — `relate(a,b)` tool (NEXT)** | Master-plan section: `ref:ltg-plan-phase-5`. Dataflow model: `ref:ltg-phase4-dataflow` (pipeline diagram + stage×state matrix). Graph state: `ref:ltg-phase4-findings` (gotchas + rebuild order), `ref:ltg-phase4-acceptance` (edge/community shape), `retrieval/graph.py` (Edge, edges table), `retrieval/communities.py`. Decisions: P4-D6 in `ref:ltg-phase4-decisions` — consumers read the `edges` table, never `alias_of`. T-65 weighting rationale for Phase 5 retrieval. | Index live: 1022 nodes + 3367 edges + communities 207/214. Rebuild order extract→embed→store→anchors→graph→communities; graph+communities regenerate in ~11 s, zero model calls. Fine resolution barely splits (207→214) — raise `graph.resolutions.fine` if relate() needs sharper intra-domain splits. |
| **LTG Phase 4 — COMPLETE (PR #66 incl. review round)** | `ref:ltg-phase4-plan` (EXECUTED banner + decisions), reports `ref:ltg-phase4-degree-probe` (τ=0.70/K=10 freeze) + `ref:ltg-phase4-acceptance` (all PASS + idempotency-fix addendum) | 3367 edges (3222/28/117); schema 25 fields; anchors rebuild idempotent since `_topic_rows_only` fix. Review round 2026-07-03: 8 findings fixed (copy-based backups — edges survives anchors rebuild; top-k probe↔build unified; `--table` fix); leftovers = T-72; leidenalg GPL-3 → `docs/ATTRIBUTIONS.md`. T-71 (backup-chain hardening) still open. |
| **LTG Phase 3.5 — anchor escalation (T-63, UNBLOCKED)** | `retrieval/probes/phase2.5-calibration.md` (near-miss bands), `docs/plans/ltg-phase3-anchors-implementation.md` §8b, `retrieval/anchors.py` (`describe_*`, `NEARMISS_LOW`, `_nearmiss_with_vectors`) | Phase 4 evidence in hand: near-miss visible as 0.8379 similarity edge; ~26 anchors in 0.80–0.85 band; 2–3 borderline M:N merges above 0.85 to review. Pair with T-34 wiring. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0` |
| **Backfill SOLID + error-handling directives** | `docs/tasks/backfill-persona-constraints.md`, `docs/ideas/persona-error-handling-conventions.md`, `personas/registry.yaml` | grep: `git grep -L "MUST NOT modify"` modelfiles/; pair error-handling session with backfill |
| **M-P0a cleanup — retire DeepCoder personas** | `personas/registry.yaml` (filter `status: benchmark`), `ref:deepcoder-benchmark-decision` | 6 personas to rm + archive Modelfiles; `deepcoder:14b` base (9GB) optional |
| **Handoff pipeline — COMPLETE (overlay v7)** | `ref:handoff-pipeline-design` + `ref:handoff-placer-enhancement`, `overlays/session-tracking/files/registry.yaml`, `docs/plans/session-handoff-failure-clarity.md` | B1-B4 + stage/promote + session-29 fixes + session-90 topology/value-only/harvest + session-91 append↔checkoff fix + failure-clarity sweep; **173 tests**; engine shared user-level at `~/.claude/tools/handoff/` (v7); failure messages name where/whose-fault/what. Register via `manual_if_exists` (Option C). Home-repo run still needs direct `handoff.py --registry` (T-62). |
<!-- /ref:session-reading-guide -->
