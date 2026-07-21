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
- **Session 119** (2026-07-15) — **oficina P2 plan FROZEN (T-92).** Advisor caught the delta-scope masking hole (P2-D12).
- **Session 120** (2026-07-15) — **P2 FIRST SLICE BUILT + ACCEPTED (PR #76).** `kind:function` loop; suite 150→223; cache on `prompt_eval_duration`.
- **Session 121** (2026-07-16) — **PR #76 REVIEWED + HARDENED.** 10 correctness fixes (suite→235); 5 deferred T-95–T-99; executable-spec DSL (T-100).
- **Session 122** (2026-07-16) — **P2 `/simplify` + T-95/T-99 (b)** (suite 241). Shared per-call transport; `auto_verdict` ledger-only.
- **Session 123** (2026-07-17) — **PR #76 MERGED; T-96/T-97/T-98 RESOLVED (PR #77, suite 260).** refs fallback + `RefsDropped`; retention worktree prune; worktree-relative path scoping.
- **Session 124** (2026-07-18) — **Founding problem recovered (T-102) + Go-widening Phase 1 + write-model M2 decided (T-104); PR #79.** (1) T-102: multi-session GPU contention is the *founding* problem. (2) T-92 Axis A Phase 1 shipped (suite 279). (3) T-104: **M2 (edit) = code-anchored**. Filed T-103.
- **Session 125** (2026-07-21) — **VERDICT HARNESS REPAIRED (T-105, PR #80). Coverage 9.6% → 18.7%.** Every durable doc taught an inline phrase while `verdict-capture.py` only ever parsed a `[VERDICT …]` block **taught nowhere durable** — the harness worked, it was never fed. Shipped: `call_id`+`tool` identity (`prompt_hash` is a content address — 1 hash = 24 calls/8 models), content-match provenance with **no positional fallback**, docs converged + **overlay v3** propagated to 3 downstream repos, oficina judged **per-run** via `run_result`, 26 mutation-verified hook tests, 48/49 prose verdicts back-filled, `cleanupPeriodDays: 365`. **Carried caveat: ~81% of calls still hold no judgment in any form** — the format fix addressed the minority; Phase 6 (measure → gate) is deliberately deferred.
- **Open deferred tasks:** **T-105** (verdict harness — only Phase 6 open), **T-106** (stale LTG hook message), **T-107** (verdict hooks: overlay vs machine-global), **T-102** (multi-session contention — M-D4/M-D5 open, gate busy-check G-D8), **T-103** (timeout config mismatch), **T-104** (write-model — M2 decided, edit-kind BUILD open), **T-100** (test-DSL promotion), **T-101** (QUICK.md revision), **T-93** (mermaid-as-context), **T-86** (oficina distribution runbook), **T-88** (model-call gate — G-D4/5/6 + G-D7/G-D8), **T-94** (RTK porcelain), **T-85/T-87/T-83/T-54/T-53/T-55/T-56/T-60/T-65/T-66/T-70/T-76/T-77**, engine tasks **T-34/35/38–41/63/64/72–75** in `latent-topic-graph`, plus standing infra/model watch items.
- **Next:** **PR #80 MERGED (2026-07-21)** — T-105 shipped; only Phase 6 stays open. Optionally push the 3 downstream `v2 → v3` commits (still unpushed). Then resume the pre-empted oficina track: **build the edit kinds on M2** (`LanguagePack.locate_unit` + loop composes `patch_file` + C0 target-present flip), then **Axis A Go read-side** (Phase 3). Standing: T-105 Phase 6 (time-gated), T-102 busy-check (G-D8), T-103, T-93, T-86, **G-D4**.
- **Cross-repo:** `latent-topic-graph` is the 5th tracked repo (S-D7). All 5 on session-tracking v11. **ollama-scaffolding is now v3** — propagated + committed in `expenses/code`, `web-research`, `career-search` (their commits are unpushed). **oficina is machine-global**; T-89 hooks repo-local (llm). **PR #79 merged**; this branch rebased onto it (one `tasks.md` conflict, resolved keep-both-in-order; suites 279 + 26 green). T-93 draft parked at `overlays/ollama-scaffolding/drafts/`. **PR #80 merged 2026-07-21 — T-105 is on master**; the `fix/verdict-capture-repair` branch is spent and can be deleted.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; `:11434` metrics proxy is a systemd peer. Store on ext4 vhdx at `/mnt/ollama-store/models`. `.wslconfig memory=24GB` load-bearing. 14B/32K partial-offload is VRAM contention (T-90) — ~9 GB free of the shared RTX 3060; **this blocked local-model delegation 3× in session 125 (even an 8B with no context files), so treat repeated `TIMEOUT_COLD_START` as a VRAM signal, not a prompt-size one.** `rtk git log` drops merge commits — use plain `git log`. `st-handoff`/`st-resume`/`oficina` need `~/.local/bin` on PATH. oficina storage `~/.local/share/oficina/`. **T-103: declared `OLLAMA_TIMEOUT=120` is NOT operative — effective sync ceiling ~600s.** **`cleanupPeriodDays: 365`** now set in `~/.claude/settings.json` (machine-local, NOT version-controlled) — transcripts are the only audit trail for format/provenance bugs. **`ltg/run-refresh.sh` does not exist**; use `/mnt/i/workspaces/latent-topic-graph/run-refresh.sh --repo-root ..` from `ltg/` (T-106).
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

<!-- ref:quick-pointers -->
## Quick Pointers (Active Work)

| What | Where |
|------|-------|
| Current layer tasks & progress | `.claude/tasks.md` |
| Active execution plan | `.claude/plan-v2.md` |
| Session log (current) | `.claude/session-log.md` |
| Agent preferences & resume checklist | `.claude/session-context.md` |
| Project rules & constraints | `CLAUDE.md` (repo root) |
| Cross-session memory | `~/.claude/projects/.../memory/MEMORY.md` |
<!-- /ref:quick-pointers -->

---

<!-- ref:active-decisions -->
### Cross-cutting principles
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both → `docs/vision-and-intent.md`
- **Licensing (STRONG):** Always check + honor external project licenses; attribute in `docs/ATTRIBUTIONS.md`
- **A format contract must be taught where the producer durably reads (session 125, T-105).** The `[VERDICT …]` block lived only in an ephemeral per-call hook injection while every durable doc taught a different, uncapturable form — so the producer followed the docs and ~90% of judgments were discarded for five months. **Persistent instruction beats ephemeral injection**; anything a model must *produce* has to be specified where the model durably reads. Corollaries: (a) **verify the producer→consumer seam, not the parser** — the 2026-03 test fed a hand-authored fixture to the regex and passed throughout the outage; (b) a **content address is not an identity** — `prompt_hash` collided 24 calls across 8 models, so dedupe-on-hash silenced whole sweeps; (c) **when identity is unknown, stay silent** — a positional fallback names the wrong call, and mislabeled is worse than missing; (d) these failures are all **silent by construction**, so assume anything unverified is failing.
- **oficina composes the ollama-bridge tools; it does not reimplement them (session 124, T-104).** `loop.py:263`'s bespoke `write_text` silently dropped `patch_file` → `kind:function` became file-granular. Sibling of T-95 and the T-102 busy-check. Corollary: **M2 (edit) = code-anchored**; M1 (greenfield) = compose `output_file`.
- **The founding problem is multi-session GPU contention (session 124, T-102).** N concurrent sessions contend for one GPU; a sync call that waits its turn exhausts its own transport deadline. **T-89 is scope-limited, not reopened.** The gate needs a **wait-tolerance axis (G-D7)**, and its MVP is **T-21's busy-check (G-D8)**, not the full scheduler.
- **Code ships as a package; config ships as an overlay (session 111, R-D9).** Corollary: **a deferral whose trigger is guessed will fire on a different trigger**. Second corollary (session 125): **a `merge_sections` edit does not propagate without a manifest `version:` bump** — the installer reports success while half-applying.
- **Three version facts, never conflate (session 111):** installed package `--version`; `registry.yaml: version:`; the per-repo `<!-- overlay:… vN -->` marker.
- **A signal that fires unconditionally carries zero bits (session 111).** Corollary for `--verify`: the **locator contract**. Corollary for warnings: spend silence only on proof of safety.
- **Config over code-patching seams (session 111).** A comment defending why *this* case is special is usually the artifact of an accident.
- **Two scheduling altitudes (session 116, G-D1):** products schedule *runs* (oficina); a layer-0 **gate** schedules *calls*. `ref:model-gate-altitude`.
- **Async routing convention (session 117, T-89):** deliverable-shaped / long / parallelizable → `submit_run` + background watch; small-and-waiting-anyway → sync. `ref:oficina-async-migration-shape`.
- **Verdicts are the session's job, not the user's (session 125).** Judgeable = `generate_code` + `ask_ollama` per-call, **oficina per-run** via `run_result`; NOT summarize/translate/classify_text. Cold-start timeouts are not verdicts.
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768**; 8B → 32768; deepseek-coder-v2:16b → 24576. q8_0 verified active (T-90).
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->
| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **T-105 verdict harness — MERGED (PR #80, 2026-07-21); only Phase 6 open** | `docs/findings/verdict-coverage-collapse-2026-07-21.md` (`ref:verdict-coverage-findings`), `docs/plans/verdict-capture-repair.md` (`ref:verdict-capture-decisions`) | Shipped on master. Findings §9 lists four claims the investigation got **wrong** + corrections — read it before trusting any single claim. Per-phase results are inline in the plan. Downstream `v2 → v3` commits in `expenses/code`/`web-research`/`career-search` are committed but **unpushed**. |
| **T-105 Phase 6 (the only open part) — measure, then decide on a gate** | plan § Phase 6; `.claude/tools/ollama-stats.py` | Needs real working sessions under the fixed docs first. Report coverage **among judgeable calls only** (now possible via the `tool` field in `_log_call`). Gate deferred deliberately: PostToolUse cannot block, and a `Stop` block forces turn continuation → a forced verdict is not a considered one (8-block cap, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). ~81% of calls still hold no judgment — that residue is behavioural. |
| **Recording a verdict (every session, every judgeable call)** | `CLAUDE.md` § Local Model Usage; `.claude/overlays/local-model-conventions.md` | Fill the `[VERDICT call_id=…]` block the hook injects — **prose verdicts are silently discarded**. No template injected = not judgeable, or unidentifiable → write nothing. oficina is judged **per-run** via `run_result`. |
| **Build the edit kinds on M2 (code-anchored)** | `docs/findings/oficina-write-model-benchmark-2026-07-18.md` (`ref:oficina-write-model-report`), `ref:oficina-function-kind-write-model` | M2 = code-anchored DECIDED. Build: `LanguagePack.locate_unit` (Python `ast`; Go `go/parser`); loop **composes `patch_file`** for edit kinds (retire bespoke `write_text`); C0 baseline flips to target-present. Principle: compose, don't reimplement. |
| **Axis A Go read-side (Phase 3 — oficina dogfood)** | `docs/plans/oficina-p2-go-widening.md`, `docs/plans/oficina-language-widening-notes.md` (`ref:oficina-language-widening`) | R1/R3/R4 settled. Duplicate Go beside Python FIRST, extract `LanguagePack` only after (Phase 4 never before Phase 3). `_parse_gotest` is a clean loop-dogfood deliverable. |
| **T-102 multi-session contention (founding problem)** | `docs/ideas/multi-session-contention.md` (`ref:multi-session-contention`, `-failure-mode`, `-transport-requirement`, `-busy-check`) | T-89 scope-limited not reopened. Gate needs wait-tolerance (G-D7); MVP = T-21 busy-check (G-D8). **Session 125 added live evidence:** 3 local-model timeouts incl. an 8B with no context files, `my-python-q25c14` resident at 9.7 GB. |
| **Working on the hooks** | `.claude/hooks/tests/run-tests.sh` (26 tests) | Self-running scripts with a `__main__` PASS/FAIL block — **not pytest**. Mutation-test any new assertion: a test that cannot fail proves nothing (that is exactly how the 2026-03 verdict test passed through a five-month outage). |
| **oficina P2 — review deferral records** | `docs/findings/oficina-p2-review-deferred-2026-07-16.md` (`ref:oficina-p2-review-deferred`) | T-95–T-99 all resolved. Minor items still open there. |
| **mcp-server / benchmark test runs** | `mcp-server/Makefile`; `benchmarks/lib/run-write-model-bench.sh` | `make -C mcp-server test` (270 on master; 279 on the PR #79 branch). |
| **LTG — engine / instance** | Sibling `/mnt/i/workspaces/latent-topic-graph/`; `ltg/.memories/QUICK.md` | Engine sessions run there (S-D7). **Refresh from `ltg/` via `/mnt/i/workspaces/latent-topic-graph/run-refresh.sh --repo-root ..` — `ltg/run-refresh.sh` does NOT exist (T-106).** |
<!-- /ref:session-reading-guide -->
