# Session Log

**Current Layer:** "Layer 5 — Expense Classifier (side-track: oficina P2 simplified + T-95/T-99 resolved (b) session 122, suite 241, PR #76 pushed w/ addendum; next = merge decision + post-slice widening P2-D1)"
**Current Session:** 2026-07-16 — Session 122: "oficina P2 /simplify + T-95/T-99 resolved (b) — suite 241, PR #76 pushed"

---
## 2026-07-16 - Session 122: "oficina P2 /simplify + T-95/T-99 resolved (b) — suite 241, PR #76 pushed"

### Context

Resumed from the session-121 handoff with the `/simplify` orientation briefing (`docs/plans/oficina-p2-simplify-orientation-2026-07-16.md`) as the entry point; full P2 context re-read (plans, refs, review-deferred findings, test DSL, 0622c26 diff) before running.

### What Was Done

- `refactor(oficina): /simplify pass over the P2 diff — dedup + decompose (no behavior change)` (`5b35301`) — 4 parallel review agents (reuse/simplification/efficiency/altitude) → 13 applied fixes: `run()` decomposed to ~45 lines, new shared `errors.TriadError` base (evaluation failures keep `where=compile/test` attribution on Failed), `workspace.target_relpath` single-sources the symlink guard, table-driven intake unknown-keys, `Budgets`-from-schema, context files via `server._build_context_block`, `ledger.RUN_EVENTS` derived from the state fold, `scope_of`/anti-cheat efficiency fixes
- `docs(oficina): T-99 DECIDED (b) — auto_verdict is ledger-only; P4 joins on run_id` (`21172f0`) — plan corrected in place (Goal/T6/event-note + result-report delta), findings decision record, tasks.md checkoff
- `refactor(oficina): T-95 RESOLVED (b) — one per-call generation transport; Generation events single-shot-only by design` (`164de8a`) — `worker._chat_generation` + `_cold_start_grace` shared by single-shot and `loop.default_coder`; `spec.timeout_s` now reaches the loop coder (was hardcoded 1800); 6 new tests incl. the `EvaluationError.where`-attribution pin; suite 235→241
- `docs(oficina): mcp-server memories — session-122 state` (`b38d7c9`)
- Branch pushed (`6192eb3..b38d7c9`); PR #76 body gained a session-122 addendum (same layered-addendum pattern as session 121), superseding its stale "next session runs /simplify" line

### Decisions Made

- **T-99 (b), user call:** `auto_verdict` lives in the LEDGER only; `calls.jsonl` stays verdict-free; the P4 DPO pass joins ledger↔calls on `run_id`. Rationale: the call record is appended at generation time, before the verdict exists — the coupling would back-write an append-only log for a consumer that only arrives at P4. Revisit-at-P4 note attached (join is per-run; per-iteration call matching is order-based; anti-cheat iterations record a verdict without an evaluation call).
- **T-95 (b), user call:** the "which seam owns the wrapper" question dissolves on decomposition — grace+timeout are per-call TRANSPORT (now one spelling in worker.py), Generation events are the single-shot run's phase NARRATIVE and stay out of loop runs BY DESIGN (loop narrates via Iteration events; per-call telemetry = calls.jsonl per T-99(b); `GenerationFinished`→phase `packaging` would break `fold_phase` mid-loop). Rejected worker-side-wrapper alternative recorded in the findings file.
- `/simplify` skips recorded in `5b35301`: intake `_git_root` vs workspace `rev-parse` oracle unification and fail-loud `_git` adoption in anti-cheat (behavior changes), stable-prefix pre-fold + per-run client reuse (micro vs model-call cost, T-95-adjacent).
- `Budgets.wall_clock_s` became `Optional[int]` — schema aligned with the loop's documented "0/None disables" behavior.

### Next

- **PR #76 merge decision** — lean: merge as-is, run post-slice widening on a fresh branch (the PR is 40+ files, three review layers deep). User to confirm.
- Post-slice widening (P2-D1): more kinds/validators, escalation ladder (P2-D9), tiny-model classifier (P2-D4 — batch OUTSIDE the coder loop).
- Review deferrals still open: T-96 (worker refs env), T-97 (retention worktree-prune), T-98 (basename→relpath scoping).

### Gotchas

- The suite had already pinned T-95 option (b) before the decision existed: `test_worker_loop` asserts `GenerationStarted not in names` for loop runs ("loop, not single-shot") — the Generation-events-in-loop alternative would have broken a green test.
- Loop prompt rendering for `context.files` changed deliberately with the `server._build_context_block` reuse: fenced `<context>` blocks (same as single-shot), missing file → `Error:` text in the prompt instead of silent skip, relative paths absolutized before the call. Invisible to tests (none pinned the old format) but visible to the model.
