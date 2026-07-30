# Session Log

**Current Layer:** "Layer 5 — Expense Classifier (oficina P4 merged; judge payload closed, PR #87 open; P3 next)"
**Current Session:** 2026-07-29 — Session 133: "T-129 + T-130 CLOSED — the judge's payload made prefix-cacheable and mode-aware; three QUICK files compacted"

---
## 2026-07-29 - Session 133: "T-129 + T-130 CLOSED — the judge's payload made prefix-cacheable and mode-aware; three QUICK files compacted"

### Context

Opened on a merged PR #86 and a clean master, with the session-132 handoff naming three
candidates: P3, the deferred T-129/T-130 judge-payload pair, and the cheap carried tasks. Chose
**B — T-129 + T-130 first**, on the argument that both are defects in *what the judge is sent*,
which is P3's own subject matter: building the prompt compiler first and then discovering them
would have encoded the defects into the mechanism. Mid-session the user redirected twice, and
both corrections changed how the work was done rather than what it produced — read the
test/code/refactor/local-model conventions and delegate through them, and read the QUICK/KNOWLEDGE
memories of every folder being touched.

### What Was Done

- **T-129 closed** — `judge.py`'s system prompt is now criterion-INVARIANT and forward-references a tail-appended criterion block, making the run-constant objective+diff+drift a reusable KV prefix. Second-criterion prompt eval fell **2398→513 ms** (A1) and **3105→459 ms** (A2), 79–85% cold and ~88% session-warm. `_scoring_scale` extracted so the scale has one owner.
- **T-130 closed** — `LoopResult.mode` + `_change_view` (a greenfield `change` is the delivered CONTENT, not a 100%-additions diff); `judge_deliverable(..., mode)` honouring a rubric's `applies_to` precondition through the existing `unavailable_verdict` shape; `_change_heading` naming the artifact per mode; `worker._judge_delivered` handing the mode over.
- **New rubric `evaluator/rubrics/oficina-greenfield.yaml`** (9 rubrics now), and `applies_to` added to `oficina-edit.yaml`.
- **`make accept-p4` made stricter** — A5 runs on the greenfield rubric and asserts `passed is True` rather than that a verdict field merely exists, and now prints the judge's per-criterion reasoning.
- **PR #87 opened**; suite 393 → 408; live acceptance green.
- **T-131 and T-132 filed.**
- **Three QUICK.md files compacted** after user correction: coding-delegate 201→73, mcp-server 167→72 (with one orphaned rationale migrated into its KNOWLEDGE.md), and the s133 entries in all three rewritten from ~25 lines to ~6.
- **Memory/README convergence** across seven documents plus `.claude/index.md`.

### Decisions Made

- **`applies_to` is rubric-level, not criterion-level.** Per-criterion filtering was designed and rejected: excluding criteria from the `passed`/`judge_verdict` reductions is structurally the same operation as the filtered-subset bug **P4-D8** exists to prevent, and it would need a third per-criterion state ("not applicable") beside scored and unscoreable. Rubric granularity needs no change to either reduction.
- **A rubric ships for each mode in the same change.** Deferring `oficina-greenfield.yaml` was considered and reversed on the user's challenge — leaving greenfield (the *original* run mode) unjudged is worse than the incoherent scale, because incoherence is at least visible.
- **`scope_adherence` keeps its name in both rubrics** — the judged question is identical ("only what was asked?") and only the rungs differ, so verdicts stay comparable across modes.
- **`mode` is required, never defaulted**, for the reason `default_judge` requires `run_id`: a default would be a value that looks like one, and it would silently decide which question a rubric is allowed to ask.
- **The applicability check lives in `judge.py`, not the worker** — that module already owns `unavailable_verdict` because it owns the invariant that `passed` and `judge_verdict` agree, and a refusal has to satisfy it too.
- **`loop.py` was hand-edited and the failed delegation recorded** rather than retried at ~1 h per attempt.
- **Compacting `.memories/QUICK.md` (root) deferred to its own session (T-132)** — it spans every workstream, so the unit is one line per *workstream*, and the blocking question (where cross-cutting infra facts live) is a judgement call, not a mechanical pass.

### Next

- **Merge PR #87** — 408 green, `make accept-p4` passing, description current.
- **P3 — context & prompt assembly**, the phase in front. T-129/T-130 handed it two constraints worth encoding in the compiler from the start: prompt ORDER is worth 79–85% of a call's prefix evaluation, and a payload must name the artifact it carries.
- **T-131** (`timeout_s` is per-attempt; `_cold_start_grace` doubles it) — weigh together with T-111, since both come from threading `spec.timeout_s` through as a per-call value.
- **T-132** (root QUICK.md compaction) — its own session, per this session's decision.
- Still carried: **T-118** R-D1/R-D3; **Axis B kinds reconsideration** (untouched since s128); T-125/126/127/128, of which T-125 and T-128 remain cheapest.

### Gotchas

- **A check that can only pass teaches nothing.** Tightening A5 from "`judge_verdict` is a present field distinct from `auto_verdict`" to "`passed is True`" failed on the **first** run — and the fault was in A5's OWN fixture: its objective read *"One line, with a docstring"*, two requirements that cannot both hold, so `objective_met` could never reach its cut of 4. Latent since A5 was authored in s132, invisible because the old assertion passes on any number.
- **`judge-window-sweep.py` measures ONE of two walls.** `loop.py` was refused by the T-112 guard in **0.48 s** on the 16K coder (window) and then produced **nothing in 7,066 s** on the 32K one (throughput — 9.4 GiB resident of a 14.2 GiB config at ~49% utilisation is partial offload). A file can fit the window and still be practically uneditable, so T-122's "21/27" is optimistic on a second axis beyond the 13 files lacking paired tests.
- **`spec.timeout_s` is a PER-ATTEMPT deadline.** `_cold_start_grace` retries once on `OllamaTimeoutError`, so a declared 3600 cost 7,066 s of wall clock. Its premise — a first-call timeout means the model is loading — is false exactly when the model is simply too slow, making the retry a guaranteed second full waste (T-131).
- **A correction can be APPENDED instead of APPLIED, and then the stale claim wins.** `mcp-server/.memories/QUICK.md` § Key Patterns asserted the pre-T-105 call-logging shape for eight sessions while s125's entry, 35 lines below it, said in so many words "supersedes … above". A reader hits the top of the file first. That is the append-log's real cost, not its length.
- **A delegated model can invert a case the brief states explicitly.** `judge.py` attempt 1 wrote `rubric.get("applies_to") != mode`, which refuses when the key is ABSENT — it would have stopped every benchmark rubric from judging anything. The negative-control test caught it, which is the argument for writing that test *before* delegating.
- **Two prior records of my own were wrong in opposite directions and are now corrected in place:** T-129's cost estimate was 35% optimistic (only the shared prefix is free — the criterion block still evaluates), while its pre-change measurement was *understated* (ms/token was FLAT across calls, so reuse was zero, not weak).
- **oficina's worktree checks out HEAD**, so red tests must be COMMITTED before a run can see them. Corollary proved live: a `PYTHONPATH=mcp-server/src` + repo-venv `test_cmd` resolves against the worktree (`baseline_failure_count: 3` matched the committed red tests), which unblocks delegating any oficina file that fits.
