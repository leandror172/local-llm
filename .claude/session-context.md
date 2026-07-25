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

- **Session 120** (2026-07-15) — **P2 FIRST SLICE BUILT + ACCEPTED (PR #76).** `kind:function` loop; suite 150→223; cache on `prompt_eval_duration`.
- **Session 121** (2026-07-16) — **PR #76 REVIEWED + HARDENED.** 10 correctness fixes (suite→235); 5 deferred T-95–T-99; executable-spec DSL (T-100).
- **Session 122** (2026-07-16) — **P2 `/simplify` + T-95/T-99 (b)** (suite 241). Shared per-call transport; `auto_verdict` ledger-only.
- **Session 123** (2026-07-17) — **PR #76 MERGED; T-96/T-97/T-98 RESOLVED (PR #77, suite 260).** refs fallback + `RefsDropped`; retention worktree prune; worktree-relative path scoping.
- **Session 124** (2026-07-18) — **Founding problem recovered (T-102) + Go-widening Phase 1 + write-model M2 decided (T-104); PR #79.** (1) T-102: multi-session GPU contention is the *founding* problem. (2) T-92 Axis A Phase 1 shipped (suite 279). (3) T-104: **M2 (edit) = code-anchored**. Filed T-103.
- **Session 125** (2026-07-21) — **VERDICT HARNESS REPAIRED (T-105, PR #80). Coverage 9.6% → 18.7%.** Every durable doc taught an inline phrase while `verdict-capture.py` only ever parsed a `[VERDICT …]` block **taught nowhere durable** — the harness worked, it was never fed. Shipped: `call_id`+`tool` identity (`prompt_hash` is a content address — 1 hash = 24 calls/8 models), content-match provenance with **no positional fallback**, docs converged + **overlay v3** propagated to 3 downstream repos, oficina judged **per-run** via `run_result`, 26 mutation-verified hook tests, 48/49 prose verdicts back-filled, `cleanupPeriodDays: 365`. **Carried caveat: ~81% of calls still hold no judgment in any form** — the format fix addressed the minority; Phase 6 (measure → gate) is deliberately deferred.
- **Session 126** (2026-07-22) — **EDIT MODE BUILT + ACCEPTED (T-110, PR #82 open); M2 REVISED to whole-file-with-context.** Pre-clear half: stale-register refresh (T-108 raised). Post-clear: T-106 fixed + full branch cleanup (master-only local+origin); re-grounding caught the code-anchored plan growing an edit language no founding fact needs → T-104 amended (code-anchored = on-file fallback, omission trigger), T-89 routing default revised (**delegated codegen async-first, small edits included**); build by subagent pipeline (impl-opus T1–T5 → impl-opus-med adversarial review, MERGE-READY 10/10 → F1 polish + omission pin); **T6 live acceptance PASSED** (246-line module diff 2+/2−, 24 siblings byte-intact; uncommitted-guard Failed 1.3 s; observed drift additive, not omissive; all runs 1-iteration via tests-as-context). Suite 279→298. NEW `.claude/tools/ollama-cache-report.py` (prefix-reuse tracker; reproduces T8's measurement retroactively). Verdict harness captured all 7 blocks normally — counter-evidence to T-109(1); T-109(2) reproduced live.
- **Session 127** (2026-07-23) — **GO WIDENING COMPLETE (T-92 Axis A, Phases 2–5 in ONE session; suite 298→329; PR #83 OPEN).** Phase 2 prefix threading + Phase 3 duplicated-on-purpose (both Go parsers; imposed `-json` A2; greenfield-C0 stderr fallback pinned empirically — go<1.24 emits build failures unwrapped; loop language axis) + **Phase 4 `LanguagePack`** (4 members vs 5–6 predicted, zero test edits; delta = new `ref:patterns-refactoring-duplicate-first`) + **Phase 5 live acceptance PASSED** (greenfield 1-iter Delivered, auto-routed; stretch: first Go EDIT run — surgical 1-line diff). Build = 5 production edit runs on parser/evaluator incl. one stubs-then-retry recovery; **loop economics: iteration 1 lands 90–95%, retries never see the residual defect — review-fix-inline won 5/5** (→ T-114). **Coder defaults = 16K-ctx personas** via new `create-persona --num-ctx` (32K = 14.2 GiB live, cannot fit the card, 2.5 tok/s offloaded; 16K = 11.1 GiB VRAM-fit, 13–21 tok/s; → T-112 input-fit guard, T-113 re-probe). **T-109(1) mechanism FOUND:** mid-turn text not persisted to Fable transcripts — verdict blocks ride the FINAL message (memorized + recorded). **T-111 filed** (cancel can't interrupt an in-flight generation — 25+ min latency observed). Docstring deleted 4-for-4 by whole-file edit runs (E-D6 systematic; addendum in the edit-mode plan).
- **Session 128** (2026-07-24) — **T-114 + T-115 shipped (PR #84 open); suite 329→332.** T-115: `refactoring-conventions` promoted to a first-class pattern-doc family (graduate-in-place — gateway row in `ref:patterns-index`, taxonomy preserved, zero ref-integrity delta). T-114: oficina **edit runs default to 1 iteration** (greenfield keeps 3, explicit always wins) — mirrors the E-D9 `num_predict` resolve-by-mode contract; core resolver delegated to the 16K coder with convention refs injected (verdict 2). Memory QUICK/KNOWLEDGE de-staled. VRAM datapoint: 16K coder = 11.25 GiB VRAM + 0.64 GiB CPU (95/5); footprint fixed by `num_ctx` KV reservation (does not grow with input) → oversized-input risk is truncation, not VRAM (T-112).
- **Session 129** (2026-07-24 to 2026-07-25) — **T-112 INPUT-FIT GUARD + T-120 PREVIOUS-ATTEMPT-AS-DIFF SHIPPED (PR #84 + PR #85 MERGED); T-118/T-119/T-121 FILED; run-provenance safety net.** T-112: `_context_overflow` weighs `ceil(len(prompt)/4) + resolved num_predict` against the model's live `/api/show` ctx window (injected seam, network-free tests); iteration-1 overflow raises `ContextBudgetError` (payload-blamed triad), later iterations exhaust on `context_budget`, an unresolvable ceiling emits `ContextLimitUnknown` once and runs unguarded rather than guessing. Live-verified: refused in 0.72s with zero GPU calls, chars/4 estimate within 1.3% of the real token count. T-120 (the user's own proposal): an edit run's `previous_attempt` is now a `difflib` diff against the committed baseline (`_previous_attempt_view`), so a repair iteration costs what iteration 1 costs instead of paying for the target file twice. Suite 332→340. Three findings outlived the build: **the feasibility band** (a whole-file edit pays for its target file twice, so files above roughly `(num_ctx − tests)/2` cannot be edited whole at all — recorded in `ref:oficina-ctx-overflow`, a third, previously-unpriced leg of the M2 whole-file-with-context decision); **T-119** (a whole-file edit run pasted ~110 lines of the acceptance tests into the source module and still reported `passed`/`auto_verdict: 2`/Delivered — three candidate detections proposed, undecided); **T-118** (merging is currently the only thing keeping a run's raw commits reachable — R-D1–R-D6 proposed, not frozen). Also filed **T-121** (the `ref:KEY` marker grammar has five implementations and zero written spec; R-D1–R-D5 recorded, not planned). New feedback memory: verdicts must judge pattern adherence, not just functional correctness — two of this session's own verdicts under-reported, corrected in `calls.jsonl` in place (`.bak-2026-07-25` kept). Post-merge safety: `refs/oficina/<run_id>` now pins the three live-acceptance run branches' tips (T-118's R-D2 in isolation — two commands, no convention change) before deleting them; stale `feature/oficina-t114-t115` (already merged, flagged at session start) removed local+origin.
- **Open deferred tasks:** **T-113** (ctx-footprint re-probe — 14.2 GiB live vs 9.5 May probe), **T-118** (run provenance — squash+trailers+ref namespace, R-D2 live, R-D1/R-D3 undecided), **T-119** (whole-file edit runs can leak tests into source, detection mechanism undecided), **T-121** (ref-marker grammar has no owner, decision record written not planned), **T-111** (cancel can't interrupt generation), **T-105** (verdict harness — only Phase 6 open), **T-107** (verdict hooks: overlay vs machine-global), **T-108** (persona catalog strategy), **T-109** (verdict/bridge substrate checks — mechanism for (1) FOUND s127: mid-turn transcript gap; (2)–(5) open), **T-102** (multi-session contention — M-D4/M-D5 open, gate busy-check G-D8), **T-103** (timeout config mismatch), **T-100** (test-DSL promotion), **T-101** (QUICK.md revision), **T-93** (mermaid-as-context), **T-86** (oficina distribution runbook), **T-88** (model-call gate — G-D4/5/6 + G-D7/G-D8), **T-94** (RTK porcelain), **T-116** (ref-integrity baseline note stale), **T-85/T-87/T-83/T-54/T-53/T-55/T-56/T-60/T-65/T-66/T-70/T-76/T-77**, engine tasks **T-34/35/38–41/63/64/72–75** in `latent-topic-graph`, plus standing infra/model watch items.
- **Next:** Decide **T-119**'s detection mechanism. Decide **T-118**'s remaining scope (R-D1/R-D3 squash+trailers, on top of the now-live R-D2). **Axis B kinds reconsideration** (E-D8 rename + dead `acceptance.validators` removal ride the same taxonomy pass) — carried over from session 128, still not started. Triage **T-113** and **T-116**. Standing: T-102 busy-check (G-D8), T-105 Phase 6 (data accumulating), T-103, T-93, T-86, **G-D4**.
- **Cross-repo:** `latent-topic-graph` is the 5th tracked repo (S-D7). All 5 on session-tracking v11. **ollama-scaffolding v3** propagated + committed in `expenses/code`, `web-research`, `career-search`. **oficina is machine-global**; T-89 hooks repo-local (llm). **PR #83, #84, #85 MERGED** (Go widening — Axis A; T-114/T-115; T-112 guard + T-120 diff). Personas: **61 (53 active)** incl. the two 16K-ctx coder variants. T-93 draft parked at `overlays/ollama-scaffolding/drafts/`.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; `:11434` metrics proxy is a systemd peer. Store on ext4 vhdx at `/mnt/ollama-store/models`. `.wslconfig memory=24GB` load-bearing. 14B/32K partial-offload is VRAM contention (T-90) — ~9 GB free of the shared RTX 3060; treat repeated `TIMEOUT_COLD_START` as a VRAM signal, not a prompt-size one. **Ollama's VRAM split is load-time-stale — after freeing VRAM, evict + rewarm to rebalance** (s127). **oficina coder defaults = 16K-ctx personas** (`my-python-q25c14-16k`/`my-go-q25c14-16k`); Go binary seam for detached workers: `OFICINA_GO` env → `which go` → literal (`/usr/local/go/bin` is `.bashrc`-only). `rtk git log` drops merge commits — use plain `git log`; `rtk curl` mangles JSON — use `rtk proxy curl`. `st-handoff`/`st-resume`/`oficina` need `~/.local/bin` on PATH. oficina storage `~/.local/share/oficina/`. **T-103: declared `OLLAMA_TIMEOUT=120` is NOT operative — effective sync ceiling ~600s; a foreground MCP call backgrounds at 120s and then bypasses PostToolUse (T-109(2)).** **`cleanupPeriodDays: 365`** set in `~/.claude/settings.json` (machine-local). **`ltg/run-refresh.sh` is a gitignored verbatim copy of the engine wrapper** (T-106 fixed s126) — re-sync via `cp -p /mnt/i/workspaces/latent-topic-graph/run-refresh.sh ltg/`; never edit in place. **`refs/oficina/<run_id>`** now the pin point for a run's raw commits when its branch is deleted (T-118 R-D2, session 129) — local-only by default refspec, not yet pushed (open question tied to T-86).
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
- **A format contract must be taught where the producer durably reads (session 125, T-105).** The `[VERDICT …]` block lived only in an ephemeral per-call hook injection while every durable doc taught a different, uncapturable form — so the producer followed the docs and ~90% of judgments were discarded for five months. **Persistent instruction beats ephemeral injection**; anything a model must *produce* has to be specified where the model durably reads. Corollaries: (a) **verify the producer→consumer seam, not the parser** — the 2026-03 test fed a hand-authored fixture to the regex and passed throughout the outage; (b) a **content address is not an identity** — `prompt_hash` collided 24 calls across 8 models, so dedupe-on-hash silenced whole sweeps; (c) **when identity is unknown, stay silent** — a positional fallback names the wrong call, and mislabeled is worse than missing; (d) these failures are all **silent by construction**, so assume anything unverified is failing; (e) **the transcript is not the screen (session 127, T-109(1))** — mid-turn assistant text is never persisted to Fable transcripts, so anything machine-captured from the transcript must ride the turn's FINAL message, and capture must be verified (`calls.jsonl` grep), not assumed; (f) **a verdict's reason must name pattern violations, not just functional defects (session 129)** — silently fixing a structural issue while the recorded reason cites only the bug teaches the DPO corpus the structure was fine; check the output against the CONSTRAINTS block and the pattern-doc family it was fed, and re-audit before writing the block.
- **Duplicate before you abstract (session 127, T-92 Phase 4).** Write the second implementation concretely beside the first; extract the abstraction only from two WORKING implementations. Measured delta vs the seam-map prediction: 3 predicted members dead, 1 predicted invariant proved variant (Go's test stage owns its command), 3 unpredicted seams — none pack surface. `ref:patterns-refactoring-duplicate-first`; sibling of characterize-first (both proof-points now recorded, promotion = T-115).
- **A persona's context size must fit the card — measured, not assumed (session 127).** 32K@14B measures 14.2 GiB live (the May probe said ~9.5 — engine drift, re-probe = T-113) → permanent CPU offload at 2.5 tok/s; oficina coder defaults are the 16K variants (11.1 GiB, VRAM-fit, 13–21 tok/s). Ollama's split is **load-time-stale**: freeing VRAM changes nothing until evict + rewarm. **Guard shipped (session 129, T-112):** `_context_overflow` weighs `chars/4 + num_predict` against the model's live `/api/show` ctx before generating — iteration-1 overflow fails loud (never downshifts, since downshifting reopens the E-D9 truncation the `num_predict` resolver was built to prevent); later iterations exhaust on `context_budget`; an undeterminable ceiling emits `ContextLimitUnknown` once and the run proceeds unguarded. **The feasibility band:** a whole-file edit pays for its target file TWICE (once as `current_file`, once as the output), so files above roughly `(num_ctx − tests)/2` cannot be edited whole at all on a given persona — a third, previously-unpriced leg of the M2 whole-file-with-context decision (`ref:oficina-ctx-overflow`).
- **A run's bytes are reachable only through what preserves them — merging is not provenance (session 129, T-118 recorded, not fully built).** `retention.py` never deletes branches, but nothing else keeps them either; squash-merge + branch delete is silent, permanent loss of the model's raw output, discoverable only when a later pass looks for iteration history that isn't there. **R-D2 (pin `refs/oficina/<run_id>` before deleting a run branch) applied ad hoc this session** for 3 live-acceptance runs; R-D1/R-D3 (squash message + trailers) still proposed, not adopted. `ref:oficina-run-provenance-decisions`.
- **oficina composes the ollama-bridge tools; it does not reimplement them (session 124, T-104).** `loop.py`'s bespoke `write_text` silently dropped `patch_file` → `kind:function` became file-granular. Sibling of T-95 and the T-102 busy-check. **Corollary REVISED (session 126, T-110): M2 (edit) = whole-file-with-context** — span confinement forces a constrained edit language whose cost the benchmark never priced; **code-anchored is the recorded fallback** (trigger: a real edit run drops sibling *code* — 4-for-4 docstring deletions are DOC omissions, trigger not fired). M1 (greenfield) = compose `output_file`. Live evidence: whole-file drift is *additive or doc-omissive*, not code-omissive.
- **The founding problem is multi-session GPU contention (session 124, T-102).** N concurrent sessions contend for one GPU; a sync call that waits its turn exhausts its own transport deadline. **T-89 is scope-limited, not reopened.** The gate needs a **wait-tolerance axis (G-D7)**, and its MVP is **T-21's busy-check (G-D8)**, not the full scheduler. **T-111 (s127) is the run-altitude face:** cooperative cancel cannot interrupt an in-flight generation — cancel latency equals the remaining transport window.
- **Async routing convention (session 117, T-89; REVISED session 126):** delegated codegen — **small edits included** — defaults to `submit_run` + harness watch; sync survives as the opportunistic fast path when the GPU is known-free, with the busy-check (G-D8) as its designed admission signal. `ref:oficina-async-migration-shape`.
- **Code ships as a package; config ships as an overlay (session 111, R-D9).** Corollary: **a deferral whose trigger is guessed will fire on a different trigger**. Second corollary (session 125): **a `merge_sections` edit does not propagate without a manifest `version:` bump** — the installer reports success while half-applying.
- **Three version facts, never conflate (session 111):** installed package `--version`; `registry.yaml: version:`; the per-repo `<!-- overlay:… vN -->` marker.
- **A signal that fires unconditionally carries zero bits (session 111).** Corollary for `--verify`: the **locator contract**. Corollary for warnings: spend silence only on proof of safety.
- **Config over code-patching seams (session 111).** A comment defending why *this* case is special is usually the artifact of an accident.
- **Two scheduling altitudes (session 116, G-D1):** products schedule *runs* (oficina); a layer-0 **gate** schedules *calls*. `ref:model-gate-altitude`.
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->

| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **T-119 — whole-file edit test leak (undecided)** | `.claude/tasks.md` T-119; `docs/plans/oficina-p2-edit-mode.md` § RESULTS | Found live during the T-112 control run: ~110 lines of `test_prompt.py` pasted into `prompt.py`, still reported `passed`/Delivered. Three candidate detections proposed, none chosen. |
| **T-118 — run provenance (R-D2 live, R-D1/R-D3 undecided)** | `docs/plans/oficina-run-provenance.md` (`ref:oficina-run-provenance`, `ref:oficina-run-provenance-decisions`) | Merging is currently the only thing keeping a run's raw commits reachable. `refs/oficina/<run_id>` pinning (R-D2) now applied ad hoc; squash-for-message + trailers (R-D1/R-D3) still open, decide alongside T-86 (push worth it?). |
| **T-112 + T-120 — input-fit guard + previous-attempt diff (SHIPPED s129, PR #85 MERGED)** | `mcp-server/src/ollama_mcp/oficina/loop.py` (`_context_overflow`, `_previous_attempt_view`); `docs/findings/oficina-ctx-overflow-2026-07-24.md` (`ref:oficina-ctx-overflow`, `ref:oficina-ctx-overflow-guard`) | Guard fails loud on iteration 1, exhausts on `context_budget` after; ceiling read live via `/api/show`. Diff view keeps a repair iteration at iteration-1 cost. **The feasibility band** (whole-file edits pay for the target file twice) is the one finding that outlives the build. |
| **Axis B kinds reconsideration (NEXT, not started)** | `docs/plans/oficina-p2-edit-mode.md` (`ref:oficina-edit-mode-decisions`, E-D8) | E-D8 `kind` rename + dead `acceptance.validators` removal ride one taxonomy pass. Fed by Axis A (`docs/plans/oficina-p2-go-widening.md` § Amendments A1–A5). Carried over from session 128. |
| **Go widening — AXIS A COMPLETE (T-92, PR #83 MERGED)** | `docs/plans/oficina-p2-go-widening.md` § Amendments (A1–A5) | Phases 2–5 result in **A5**; extraction delta = `ref:patterns-refactoring-duplicate-first`; `LanguagePack` contract in the coding-delegate KNOWLEDGE.md. |
| **oficina edit mode (T-110) + s127–s129 production data** | `docs/plans/oficina-p2-edit-mode.md` (`ref:oficina-edit-mode`, `ref:oficina-edit-mode-decisions`) | § RESULTS addendum s127: docstring deleted 4-for-4 (E-D6 systematic), iteration-1-then-review beat retries 5/5 (→ T-114 SHIPPED s128). s129: T-112 guard + T-120 diff shipped; T-119 test-leak found. Cache tracking: `.claude/tools/ollama-cache-report.py`. |
| **Recording a verdict (every session, every judgeable call)** | `CLAUDE.md` § Local Model Usage; `.claude/overlays/local-model-conventions.md`; `feedback_verdicts_assess_patterns` memory | Fill the injected `[VERDICT …]` block **in the turn's FINAL text message** — mid-turn text is NOT persisted to Fable transcripts (T-109(1) mechanism, s127); then verify with a `calls.jsonl` grep next turn. **Judge pattern adherence, not just functional correctness (s129)** — re-read the output against the CONSTRAINTS block and any pattern refs injected into that prompt before writing the reason. oficina judged **per-run** via `run_result`. A call backgrounded past 120s gets NO template (recover call_id by timestamp). |
| **T-105 verdict harness — only Phase 6 open** | `docs/findings/verdict-coverage-collapse-2026-07-21.md` (`ref:verdict-coverage-findings`), `docs/plans/verdict-capture-repair.md` (`ref:verdict-capture-decisions`) | Findings §9 lists four claims the investigation got **wrong** + corrections. Phase 6: report coverage **among judgeable calls only**; gate deferred deliberately. |
| **T-102 multi-session contention (founding problem)** | `docs/ideas/multi-session-contention.md` (`ref:multi-session-contention`, `-failure-mode`, `-busy-check`) | Live s127 evidence: concurrent session + stale load-time VRAM split. MVP = T-21 busy-check (G-D8); the `/api/ps size_vram < size` offload tell is the natural signal. **T-111** is the run-altitude face (cancel latency = transport window). |
| **Working on the hooks** | `.claude/hooks/tests/run-tests.sh` (26 tests) | Self-running scripts with a `__main__` PASS/FAIL block — **not pytest**. Mutation-test any new assertion. |
| **mcp-server / benchmark test runs** | `mcp-server/Makefile`; `benchmarks/lib/run-write-model-bench.sh` | `make -C mcp-server test`: **340 on master** (post-#85, s129). |
| **LTG — engine / instance** | Sibling `/mnt/i/workspaces/latent-topic-graph/`; `ltg/.memories/QUICK.md` | Engine sessions run there (S-D7). `ltg/run-refresh.sh` is a gitignored verbatim engine-wrapper copy — re-sync via `cp -p`, never edit in place. |
<!-- /ref:session-reading-guide -->
