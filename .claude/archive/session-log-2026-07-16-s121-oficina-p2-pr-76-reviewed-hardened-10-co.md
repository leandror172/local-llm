## 2026-07-16 - Session 121: "oficina P2 (PR #76) reviewed + hardened — 10 correctness fixes, test DSL, T-95–T-101 filed"

### Context

Session opened to review PR #76 (the P2 first slice). Composition chosen up front: manual plan-conformance pass + /code-review high (8 finder angles + adversarial verify wave) + a live Opus behavioral verify agent (2 fresh runs) + /security-review, then a Claude-authored fix phase (user directive: no local model for code changes).

### What Was Done

- **PR #76 reviewed via 4 independent passes (14 subagents).** ~23 correctness candidates adversarially verified; heavy convergence on the top bugs (3–4 finders each). Security review: zero findings under the current threat model (author-only submit surface; the `shell=True` `test_cmd` boundary noted for T-86/T-88).
- **Live Opus verify: 2 fresh runs against a scratch repo** — clean Delivered (independently re-tested) + genuine 3-iteration exhaustion exercising P2-D7 (FreshStart on repeated signature); cache reconfirmed on `prompt_eval_duration` (519 tok: 350ms warm vs 772ms cold). Also exposed: `auto_verdict` never reaches `calls.jsonl` (plan overclaim → T-99), plan's `base: HEAD` example rejected by intake, `-`-leading run_ids break `oficina watch`.
- **10 confirmed correctness bugs FIXED + regression-tested (`d0a90df`), suite 223→235:** false-Delivered on unparseable test failure (exit-code + short-summary-scoped parsing); eval subprocess + loop wall-clock timeouts (budgets.wall_clock_s now enforced, `Exhausted(limit_hit=timeout)`); symlink path escape (realpath both sides); kind-scoped intake (worktree/acceptance rejected on non-loop kinds); budgets unknown-key check + `num_predict` field threaded to the coder; `service.result()` surfaces Exhausted best-attempt branch/commit (S11); phase map learned the 6 P2 events; runs-scan hook surfaces Exhausted (verified live on this session's own resume); doubled CONSTRAINTS: header; coder cold-start retry.
- **5 deferred items logged with tasks T-95–T-99** (`docs/findings/oficina-p2-review-deferred-2026-07-16.md`, `ref:oficina-p2-review-deferred`): GenerateFn per-call-wrapper unification, refs `LLM_REPO_ROOT` drop, retention worktree-prune, basename-only scoping, `auto_verdict`→`calls.jsonl` decision.
- **Executable-spec test DSL authored + applied (`9b1c5bc`):** pattern doc `docs/patterns/test-authoring-executable-spec.md` (`ref:test-executable-spec`, 6 rules); `test_loop.py` (temporal) / `test_intake.py` (pure-function collapse) / `test_worker_loop.py` (mixed — taxonomy as triage) converted; non-converted files carry a why-not note. T-100 tracks promotion into code-design-conventions.
- **PR inline comments all resolved (`0622c26` readability: `attributable_failures` rename, `_stable_prompt_parts` + `_record_cheat_and_feedback` extractions, `is_best_so_far`) + 7 threaded replies posted on PR #76 with commit SHAs. T-101 filed (`961c1e9`) for the QUICK.md drift comment.**
- **Memory updates + next-session /simplify orientation (`11fac35`):** coding-delegate QUICK/KNOWLEDGE + mcp-server QUICK; `docs/plans/oficina-p2-simplify-orientation-2026-07-16.md`.

### Decisions Made

- **Review composition:** subagents for verification/finding (fresh eyes, parallel, GPU-vs-cloud isolation), main session for plan-conformance + triage (context asset stays put). Live verify delegated to an Opus agent driving fresh runs — re-deriving, not re-reading, session-120 claims.
- **Fix scope line:** unambiguous confirmed bugs fixed autonomously; anything reshaping frozen decisions (GenerateFn seam), touching P1 spawn code (refs env), or needing a product decision (auto_verdict) deferred with tasks instead of unattended edits.
- **The "loop is a GenerateFn" freeze was imprecise, and the parallel `_run_loop` is a defensible correction** (a run returns a branch, not content); the real T-95 fix is sharing the per-call wrapper, NOT cramming the loop into the one-shot seam.
- **Test DSL:** A+D hybrid (given/when/then bodies + combinator vocabulary); the `given`/`when` split doubles as the triage rule for what to convert.

### Next

- **Run `/simplify` on the PR diff** — briefing ready: `docs/plans/oficina-p2-simplify-orientation-2026-07-16.md` (continues the `0622c26` readability thread; dedup worklist + out-of-scope guard rails).
- **Decide T-99** (`auto_verdict`→`calls.jsonl`: implement the coupling vs correct the plan).
- Then: post-slice widening (P2-D1), merge PR #76, T-86 distribution.

### Gotchas

- **The 223-green suite hid the top bugs because the tests encoded the same assumptions** (well-formed pytest summaries only; no exit-code cases). The review's value came from re-deriving invariants + a live run, not from the suite.
- `git -C` resolves symlinks: `rev-parse --show-toplevel` returns the PHYSICAL path while a spec may carry the `~/workspaces` spelling — always realpath BOTH sides before relpath.
- `.pytest_cache` self-ignores (pytest writes its own `.gitignore`); `__pycache__/*.pyc` does not — that's the junk that lands in deliverable commits via `git add -A`.
- RTK porcelain bug (T-94) bypassed in this handoff's pre-flight via `git diff --quiet` exit codes.
