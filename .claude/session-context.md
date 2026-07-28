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

- **Session 125** (2026-07-21) — **VERDICT HARNESS REPAIRED (T-105, PR #80). Coverage 9.6% → 18.7%.** Every durable doc taught an inline phrase while `verdict-capture.py` only ever parsed a `[VERDICT …]` block **taught nowhere durable** — the harness worked, it was never fed. Shipped: `call_id`+`tool` identity (`prompt_hash` is a content address — 1 hash = 24 calls/8 models), content-match provenance with **no positional fallback**, docs converged + **overlay v3** propagated to 3 downstream repos, oficina judged **per-run** via `run_result`, 26 mutation-verified hook tests, 48/49 prose verdicts back-filled, `cleanupPeriodDays: 365`. **Carried caveat: ~81% of calls still hold no judgment in any form.**
- **Session 126** (2026-07-22) — **EDIT MODE BUILT + ACCEPTED (T-110); M2 REVISED to whole-file-with-context.** Re-grounding caught the code-anchored plan growing an edit language no founding fact needs → T-104 amended, T-89 routing default revised (**delegated codegen async-first, small edits included**); **T6 live acceptance PASSED** (246-line module diff 2+/2−, 24 siblings byte-intact). Suite 279→298. NEW `.claude/tools/ollama-cache-report.py`.
- **Session 127** (2026-07-23) — **GO WIDENING COMPLETE (T-92 Axis A, Phases 2–5 in ONE session; suite 298→329).** Phase 4 **`LanguagePack`** (4 members vs 5–6 predicted, zero test edits; delta = `ref:patterns-refactoring-duplicate-first`). **Loop economics: iteration 1 lands 90–95%, retries never see the residual defect — review-fix-inline won 5/5** (→ T-114). **Coder defaults = 16K-ctx personas** (32K = 14.2 GiB live, cannot fit the card). **T-109(1) mechanism FOUND:** mid-turn text is not persisted to Fable transcripts — verdict blocks ride the FINAL message. **T-111 filed.**
- **Session 128** (2026-07-24) — **T-114 + T-115 shipped (PR #84); suite 329→332.** T-115: `refactoring-conventions` promoted to a first-class pattern-doc family. T-114: oficina **edit runs default to 1 iteration** (greenfield keeps 3, explicit always wins). VRAM datapoint: 16K coder = 11.25 GiB VRAM + 0.64 GiB CPU; footprint fixed by `num_ctx` KV reservation → oversized-input risk is truncation, not VRAM (T-112).
- **Session 129** (2026-07-24 to 2026-07-25) — **T-112 INPUT-FIT GUARD + T-120 PREVIOUS-ATTEMPT-AS-DIFF SHIPPED (PR #84 + PR #85 MERGED); T-118/T-119/T-121 FILED.** `_context_overflow` weighs `ceil(len(prompt)/4) + resolved num_predict` against the model's live `/api/show` window; iteration-1 overflow fails loud, an unresolvable ceiling emits `ContextLimitUnknown` once and runs unguarded rather than guessing. T-120: an edit run's `previous_attempt` is a `difflib` diff, so a repair iteration costs what iteration 1 costs. Suite 332→340. **The feasibility band** discovered (a whole-file edit pays for its target twice). `refs/oficina/<run_id>` now pins a run's commits before its branch is deleted (T-118 R-D2).
- **Session 130** (2026-07-25) — **T-119 RECAST — the defect is the confident report, not a missing detector.** Measured the leak rather than reasoning about it (78 verbatim lines vs a max-4 legitimate baseline across all 14 source↔test pairs). Corrected two claims: option (b) is not expensive plumbing, and there is **no DPO-corpus poisoning** (`auto_verdict` is ledger-only). **Reframe:** a per-instance detector is a ratchet; T-119 and E-D6 are one family, so **the mechanical layer surfaces drift and the judge/H1 classifies it** — owner **P4**. Filed T-122 and T-124.
- **Session 131** (2026-07-27/28) — **P3-vs-P4 DECIDED (P4 first) and P4 BUILT + ACCEPTED — T-119 RESOLVED; PR #86 open; suite 340→369.** Plan authored and register frozen (P4-D1–D7), then T1–T9 built on `feature/oficina-p4-judge-gate`: `oficina/drift.py` (mechanical metrics, gating nothing), `oficina/judge.py` (Phase-2 rubric judge at packaging emitting `Judged`), `call_id` threaded `chat`→`GenerationResult`→`IterationEvaluated` (closing T-99's deferred join revisit — the join was order-based, the fallback T-105 banned), the delivery report's iteration trail, exhaustion attribution, and `approval_gate` recognized-but-refused. **Acceptance A1–A6 all pass against the REAL T-119 leak** (the pinned ref *and* its run dir survived, so the actual objective was replayed): the leak scores `scope_adherence` **2**/`passed False`, a real accepted edit **5**/True — the signal discriminates rather than firing on size; A3–A6 explicitly 20/20, A5 on live model calls. **Two findings changed the design mid-build:** the unmodified `code-python` rubric scored the leak **5/5**, its `completeness` criterion calling the pasted tests *"a usage example"* (a greenfield rubric has no vocabulary for *unrequested* content → separate `evaluator/rubrics/oficina-edit.yaml`); and **a reviewing model must be shown the CHANGE, not the RESULT** — with the delivered file *plus* drift metrics it still said "contains only the requested change", with the unified diff it caught it at 33% fewer tokens (`ref:judge-sees-the-change`). **Two freeze-time decisions reversed by reading upstream** (P4-D2 judge persona → same-base on the zero-swap preference; P4-D5 keep `auto_verdict` — it is *deliberately* the gameable signal S17 gates), and **P4-D6 corrected against the as-built code** (the report is `Delivered`-payload-resident, not an artifact — three docs had it wrong, the folder's KNOWLEDGE.md had it right). **T-122 MEASURED:** the delegate can edit **21/27** files on the 16K coder (optimistic — 13 have no paired test), and the blocked set is oficina's own core, so the envelope had been silently *selecting* the work. Also: first llm-side **LTG usage guide**; T-125/126/127/128 filed.
- **Open deferred tasks:** **T-125** (LTG index broader than its declared corpus — those files sit outside `--check`), **T-126** (audit health-reporting tools for corpus divergence — 4 instances), **T-127** (`create_persona` MCP tool lacks `num_ctx`, so every 14B persona it makes is born unusable), **T-128** (a hand-written VERDICT block can name a nonexistent `call_id`), **T-122** (feasibility band — now MEASURED at 21/27; remedy still unchosen), **T-124** (ref-integrity validates the working tree, not git — tool decision still open), **T-123** (bracketed `[ref:KEY]` citation rollout), **T-113** (ctx-footprint re-probe — 14.2 GiB live vs 9.5 May probe), **T-118** (run provenance — R-D2 live, R-D1/R-D3 undecided), **T-121** (ref-marker grammar has no owner), **T-111** (cancel can't interrupt generation), **T-105** (verdict harness — only Phase 6 open), **T-107** (verdict hooks: overlay vs machine-global), **T-108** (persona catalog strategy), **T-109** (verdict/bridge substrate checks — (2)–(5) open), **T-102** (multi-session contention — M-D4/M-D5 open, gate busy-check G-D8), **T-103** (timeout config mismatch), **T-100** (test-DSL promotion), **T-101** (QUICK.md revision), **T-93** (mermaid-as-context), **T-86** (oficina distribution runbook), **T-88** (model-call gate), **T-94** (RTK porcelain), **T-116** (ref-integrity baseline note stale), **T-85/T-87/T-83/T-54/T-53/T-55/T-56/T-60/T-65/T-66/T-70/T-76/T-77**, engine tasks **T-34/35/38–41/63/64/72–75** in `latent-topic-graph`, plus standing infra/model watch items.
- **Next:** **Review/merge PR #86** (P4; consider `/simplify` over the branch first). Then **P3 — context & prompt assembly**, now the phase in front and the one that makes the approval gate's payload worth defaulting on. Also: decide **T-118**'s remaining scope (R-D1/R-D3); **Axis B kinds reconsideration** (E-D8 rename + dead `acceptance.validators` removal — carried since s128, still not started); triage the four new tasks, of which **T-125** (widen `corpus.yaml` vs rebuild the index) and **T-128** (validate verdict ids at capture) are cheapest. Standing: T-102 busy-check (G-D8), T-105 Phase 6, T-103, T-93, T-86, **G-D4**.
- **Cross-repo:** `latent-topic-graph` is the 5th tracked repo (S-D7). All 5 on session-tracking v11. **ollama-scaffolding v3** propagated + committed in `expenses/code`, `web-research`, `career-search`. **oficina is machine-global**; T-89 hooks repo-local (llm). **PR #83/#84/#85 MERGED**; **PR #86 OPEN** (P4 judge gate). Personas: **62 (54 active)** incl. the new `my-judge-q25c14-16k`. LTG usage guidance now exists on both sides — career-search's `.claude/ltg-usage-guide.md` is the battle-tested original, `.claude/ltg-usage-guide.md` here is the llm-side derivation (anchor-dense corpus → the pointer loop). T-93 draft parked at `overlays/ollama-scaffolding/drafts/`.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; `:11434` metrics proxy is a systemd peer. Store on ext4 vhdx at `/mnt/ollama-store/models`. `.wslconfig memory=24GB` load-bearing. 14B/32K partial-offload is VRAM contention (T-90) — ~9 GB free of the shared RTX 3060; treat repeated `TIMEOUT_COLD_START` as a VRAM signal, not a prompt-size one. **Ollama's VRAM split is load-time-stale — after freeing VRAM, evict + rewarm to rebalance** (s127). **oficina coder defaults = 16K-ctx personas**; the judge is `my-judge-q25c14-16k`, **same base as the coder so packaging costs no swap** (a full accepted run incl. both model calls measured **7.2 s**). Go binary seam: `OFICINA_GO` env → `which go` → literal. `rtk git log` drops merge commits — use plain `git log`; `rtk curl` mangles JSON — use `rtk proxy curl`. **`rtk git add <path>` printing `ok (nothing to add)` means someone else already committed that change.** `st-handoff`/`st-resume`/`oficina` need `~/.local/bin` on PATH. oficina storage `~/.local/share/oficina/`. **T-103: declared `OLLAMA_TIMEOUT=120` is NOT operative — effective sync ceiling ~600s; a foreground MCP call backgrounds at 120s and then bypasses PostToolUse (T-109(2)), so its verdict needs a `call_id` recovered by TIMESTAMP — never invented (T-128).** **`cleanupPeriodDays: 365`** set in `~/.claude/settings.json`. **`ltg/run-refresh.sh` is a gitignored verbatim copy of the engine wrapper** — re-sync via `cp -p`; never edit in place. **`refs/oficina/<run_id>`** pins a run's commits when its branch is deleted (T-118 R-D2) — **it has now paid for itself three times**, most recently as the only surviving copy of the T-119 evidence the P4 acceptance replayed.
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
- **A checker validates the corpus it can see, not the one its consumers use (session 131, T-126).** Four measured instances in four unrelated subsystems, three found in one session: the ref-marker grammar (T-121, checker tolerant where the LTG engine is strict), ref-integrity's file corpus (T-124, working tree vs `git ls-files`), the `.gitignore` `.claude` rules (a slash-bearing pattern binds to its own directory, so nested copies escaped a rule written to exclude exactly them), and LTG `--check` (T-125, a manifest 4 `docs/` subtrees narrower than the queryable index). **Silent by construction:** the tool's answer is *true about its own set* and read as true about the consumers' set, so nothing inside scope is broken and no error can fire — there is no bug, only a boundary nobody compared. **Heuristic:** for any tool reporting health/coverage/validity/freshness, name the set it enumerates and the set its consumers use, out loud; if they come from different definitions (a glob vs `git ls-files`, a manifest vs an index, one regex vs another) they *will* drift, because nothing holds them together. **Silent-and-narrow is the dangerous direction** — a checker scoped narrower than its consumers yields false health, while the reverse yields self-announcing false alarms. Sibling class kept deliberately separate: **knowledge divergence**, where a rule in one doc is violated by a design in another (P2's order-based ledger↔calls join vs T-105's ban on positional fallbacks) — same silence, different cause, not caught by this heuristic. `ref:corpus-divergence-pattern`.
- **Duplicate before you abstract (session 127, T-92 Phase 4).** Write the second implementation concretely beside the first; extract the abstraction only from two WORKING implementations. Measured delta vs the seam-map prediction: 3 predicted members dead, 1 predicted invariant proved variant (Go's test stage owns its command), 3 unpredicted seams — none pack surface. `ref:patterns-refactoring-duplicate-first`; sibling of characterize-first (both proof-points now recorded, promotion = T-115).
- **A persona's context size must fit the card — measured, not assumed (session 127).** 32K@14B measures 14.2 GiB live (the May probe said ~9.5 — engine drift, re-probe = T-113) → permanent CPU offload at 2.5 tok/s; oficina coder defaults are the 16K variants (11.1 GiB, VRAM-fit, 13–21 tok/s). Ollama's split is **load-time-stale**: freeing VRAM changes nothing until evict + rewarm. **Guard shipped (session 129, T-112):** `_context_overflow` weighs `chars/4 + num_predict` against the model's live `/api/show` ctx before generating — iteration-1 overflow fails loud (never downshifts, since downshifting reopens the E-D9 truncation the `num_predict` resolver was built to prevent); later iterations exhaust on `context_budget`; an undeterminable ceiling emits `ContextLimitUnknown` once and the run proceeds unguarded. **The feasibility band:** a whole-file edit pays for its target file TWICE (once as `current_file`, once as the output), so files above roughly `(num_ctx − tests)/2` cannot be edited whole at all on a given persona — a third, previously-unpriced leg of the M2 whole-file-with-context decision (`ref:oficina-ctx-overflow`). **Owner filed session 130 as T-122** — the guard refuses such targets loudly but does not make them editable, and the editable fraction of the estate has never been measured.
- **A run's bytes are reachable only through what preserves them — merging is not provenance (session 129, T-118 recorded, not fully built).** `retention.py` never deletes branches, but nothing else keeps them either; squash-merge + branch delete is silent, permanent loss of the model's raw output, discoverable only when a later pass looks for iteration history that isn't there. **R-D2 (pin `refs/oficina/<run_id>` before deleting a run branch) applied ad hoc this session** for 3 live-acceptance runs; R-D1/R-D3 (squash message + trailers) still proposed, not adopted. `ref:oficina-run-provenance-decisions`. **Justified inside one session (130):** the pinned commit was the only surviving copy of the T-119 leak, and it is what made that defect measurable rather than anecdotal.
- **The free layer surfaces; the judging layer classifies (session 130, T-119).** Tests-green ≠ deliverable-good: a whole-file edit run pasted ~110 lines of its acceptance tests into the source module and reported `passed` / `auto_verdict: 2` / Delivered, because adding test functions to a module breaks nothing. The reflex — add a mechanical detector for that shape — is a **ratchet**: T-119 (content added) and E-D6 (docstring deleted) are one family, *unrequested change*, and one detector per observed face accumulates special cases each justified by a single anecdote. Split along the evaluator framework's own line (`evaluator/README.md`: Phase 1 = deterministic, free, no model required): **the mechanical layer SURFACES drift** (magnitude is reference-checkable and costs nothing) **and the judge/H1 CLASSIFIES it** (whether a diff is in scope has no reference and is genuinely a judgment). Owner is **P4**, whose delivery report already promises a diff summary and whose S17 already names the `auto_verdict` seam. Corollaries: (a) **a detector fired by one incident is deferred, not built — and its trigger must be countable** ("a second leak in any run"), since a guessed trigger fires on a different trigger; (b) **the judge is not the default answer either** — for a reference-checkable comparison it is the wrong instrument (7–8B tier, and it needs both artifacts in a context that is already the binding constraint); (c) **check what a report actually feeds before believing a data-corruption story** — `auto_verdict` is ledger-only, so the DPO corpus was never poisoned and H1 caught this unaided.
- **oficina composes the ollama-bridge tools; it does not reimplement them (session 124, T-104).** `loop.py`'s bespoke `write_text` silently dropped `patch_file` → `kind:function` became file-granular. Sibling of T-95 and the T-102 busy-check. **Corollary REVISED (session 126, T-110): M2 (edit) = whole-file-with-context** — span confinement forces a constrained edit language whose cost the benchmark never priced; **code-anchored is the recorded fallback** (trigger: a real edit run drops sibling *code* — 4-for-4 docstring deletions are DOC omissions, trigger not fired). M1 (greenfield) = compose `output_file`. Live evidence: whole-file drift is *additive or doc-omissive*, not code-omissive.
- **The founding problem is multi-session GPU contention (session 124, T-102).** N concurrent sessions contend for one GPU; a sync call that waits its turn exhausts its own transport deadline. **T-89 is scope-limited, not reopened.** The gate needs a **wait-tolerance axis (G-D7)**, and its MVP is **T-21's busy-check (G-D8)**, not the full scheduler. **T-111 (s127) is the run-altitude face:** cooperative cancel cannot interrupt an in-flight generation — cancel latency equals the remaining transport window. **The GPU is not the only shared resource (session 130):** two live sessions on one working tree collided on commit boundaries — a concurrent session's *explicit-path* `git add` swept this session's in-flight edits into its commit, which `guard-git-add-all.py` cannot catch and the handoff pipeline's clean-tree guard would have repeated.
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
| **PR #86 review / merge (NEXT)** | `docs/plans/oficina-p4-judge-gate.md` § RESULTS ([ref:delegate-p4-results]) | P4 built T1–T9, suite 340→369, acceptance A1–A6 all pass. Nothing mechanical gates — the demoted detectors stay demoted and their trigger never fired. Consider `/simplify` over the branch before merging. |
| **P3 — context & prompt assembly (the phase in front)** | `ref:delegate-phasing` § P3; `docs/plans/oficina-p4-judge-gate.md` P4-D4 | P3 delivers the prompt compiler + typed context fetchers. **It is what makes the approval gate worth defaulting on** — the gate's payload is thin precisely because context is *declared*, not derived. P4 already recorded the park-and-release shape to build then. |
| **A reviewing model must be shown the CHANGE, not the RESULT** | `docs/findings/judge-must-see-the-change-2026-07-28.md` ([ref:judge-sees-the-change]) | Three conditions on the real leak: delivered file → 5/5; file + scope criterion + drift metrics → still 5; unified diff → 2, at 33% fewer tokens. Measured numbers do NOT substitute for the artifact. Applies to any model asked to review work, not just oficina. |
| **T-122 — the feasibility band, now MEASURED** | `ref:oficina-feasibility-band-measured`; `.claude/tools/judge-window-sweep.py` | 21/27 editable on the 16K coder, and optimistic (13 files have no paired test). Blocked set = oficina's own core, so the envelope was silently *selecting* the work. Remedy still unchosen; re-run the sweep after T-113 (it reads ceilings live). |
| **T-126 — a checker validates the set it can see** | `docs/findings/corpus-divergence-pattern-2026-07-27.md` ([ref:corpus-divergence-pattern]) | Four instances in four subsystems, three found in one session. Silent by construction: the tool's answer is true about ITS set and read as true about the consumers'. Scope is **audit, not fix**. |
| **Using LTG in this repo** | `.claude/ltg-usage-guide.md` ([ref:ltg-usage-pointer-loop]) | Corpus is anchor-dense, so hits come back as bare `ref:KEY` markers — the hit is an instruction to `ref-lookup.sh` that key, then widen for phase-level questions (parked watch-items live *outside* blocks). **Ignore `query_confident`.** Scope must be read from `run-inspect.sh --list`, not `corpus.yaml` (T-125). |
| **Recording a verdict (every session, every judgeable call)** | `CLAUDE.md` § Local Model Usage; `.claude/overlays/local-model-conventions.md` | Fill the injected `[VERDICT …]` block in the turn's **FINAL** text message (T-109(1)); verify with a `calls.jsonl` grep next turn. A call backgrounded past 120s gets NO template — **recover the `call_id` by timestamp, never invent one** (T-128, learned the hard way s131). Judge pattern adherence, not just correctness. |
| **oficina — the built system** | `docs/vision/coding-delegate/.memories/KNOWLEDGE.md` § P4 judge gate | As-built invariants live in the folder memories, and they outrank the plan docs — s131 found three documents wrong about the report's location while KNOWLEDGE.md had it right. Read QUICK/KNOWLEDGE before editing any folder. |
| **mcp-server / benchmark test runs** | `mcp-server/Makefile` | `make -C mcp-server test`: **369** on `feature/oficina-p4-judge-gate`, 340 on master. |
| **LTG — engine / instance** | Sibling `/mnt/i/workspaces/latent-topic-graph/`; `ltg/.memories/QUICK.md` | Engine sessions run there (S-D7). `ltg/run-refresh.sh` is a gitignored verbatim engine-wrapper copy — re-sync via `cp -p`, never edit in place. |
<!-- /ref:session-reading-guide -->
