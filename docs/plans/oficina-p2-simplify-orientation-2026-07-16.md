# `/simplify` orientation — oficina P2 (PR #76), next session

**Purpose:** run `/simplify` on the PR #76 diff with full context already loaded — this is a briefing,
not a plan. Read it, then run `/simplify` (it reviews the changed diff and *applies* quality fixes:
reuse / simplification / efficiency / altitude — **not** bug-hunting). Everything below is the context
`/simplify` cold-starts without.

## State to run against

- Branch `feature/oficina-p2-loop`, PR #76 (oficina P2 evaluated-loop first slice, T-92).
- Session-121 review already landed the correctness fixes + a **readability pass** (see next section).
  Suite **235 green** (`cd mcp-server && uv run pytest`). Commits this session:
  `d0a90df` (correctness fixes) · `9b1c5bc` (test DSL) · `0622c26` (readability) · `961c1e9` (T-101 task).
- **`/simplify` is quality-only** — it must NOT change behavior. The correctness guards added in
  `d0a90df` (exit-code check, subprocess/wall-clock timeouts, path canonicalization, kind-scoped intake,
  Exhausted surfacing) are load-bearing invariants; preserve them exactly.

## Continue the readability thread from `0622c26`

`0622c26` addressed the four PR-review inline comments on `loop.py` by *extracting named helpers*:
- renamed `evaluator.attribute` → `attributable_failures`;
- extracted `EvaluatedLoop._stable_prompt_parts` (the refs-fold);
- extracted `EvaluatedLoop._record_cheat_and_feedback` (the anti-cheat block);
- named the best-attempt condition `is_best_so_far`.

That was scoped to exactly what the comments named. **`/simplify` should carry the same extract-method
/ dedup treatment across the REST of the diff** — the reviewer only annotated a few spots; the same
smells recur elsewhere. In particular `EvaluatedLoop.run()` is still a ~140-line method: after the two
extractions it still inlines the cancel block, the wall-clock-timeout block, the fresh-start/signature
bookkeeping, and three near-identical `LoopResult` constructions. Finish the decomposition.

## The dedup / simplification targets the review finders already surfaced

These are confirmed by the session-121 finder pass — hand them to `/simplify` as the worklist (it will
re-derive, but this is where to look):

1. **Duplicate `LoopResult` constructions** (`loop.py` — cancelled / exhausted / timeout paths each
   repeat the `best.X if best else <default>` four-field chain). → one `_result_from_best(outcome, …)`
   helper (or a `LoopResult.from_best` classmethod). Also: `LoopResult.outcome` docstring says
   `"delivered" | "exhausted"` but `"cancelled"`/`"timeout"` are also produced — fix the comment.
2. **`EvaluatedLoop.run()` length** — extract the cancel and wall-clock-timeout early-returns and the
   fresh-start/signature bookkeeping into named helpers, leaving `run()` a ~20-line skeleton.
3. **Four copies of the unknown-keys checker** in `intake.py` (`_check_*_unknown_keys` for top /
   deliverable / context / acceptance / budgets) → one `_unknown_keys(section, allowed, label)` helper
   + a table.
4. **`EvaluationError` (evaluator.py) and `AssemblyError` (workspace.py) are the same triad class** →
   one shared `TriadError`; then `worker._run_loop`'s `isinstance(exc, AssemblyError)` special-case
   collapses (and stops discarding `EvaluationError`'s `where=` attribution).
5. **Budget defaults duplicated** — `intake.Budgets` (`iterations=3`, `fresh_starts=1`) vs the loop's
   own literals in `__init__`. → construct `intake.Budgets(**budgets)` in the loop and read the fields.
6. **`workspace._build_stable_parts` re-implements `server._build_context_block`** (context-file
   reading) → reuse the server helper (also unifies the missing-file behavior).
7. **`scope_of` rebuilds basename sets per call** inside `attributable_failures`' loop → precompute the
   target/test basename sets once and pass them in.

## What `/simplify` must NOT touch (out of scope — deferred tasks)

- **The `GenerateFn` seam unification (T-95).** Sharing the per-call wrapper between the single-shot
  path and the loop's coder call is an architectural change (reshapes the frozen worker) — NOT a
  mechanical simplify. *Caveat:* target #? — the `default_coder` (loop) vs `_default_generate` (worker)
  duplication IS partly mechanical, but merging them fully touches T-95; extract only the obviously-safe
  shared chat helper and leave the seam decision to T-95.
- **The path-scoping change (T-98, basename→relpath)** — behavior change, not simplification.
- **The DSL test style** — already applied deliberately; don't "simplify" the given/when/then verbs.
- **Anything in `docs/findings/oficina-p2-review-deferred-2026-07-16.md`** (`ref:oficina-p2-review-deferred`)
  — those are decisions/reshapes, tracked as T-95–T-99.

## After running

- Re-run `cd mcp-server && uv run pytest` — must stay **235 green** (quality-only = no test changes
  expected beyond mechanical ones the extractions require).
- Commit as a `refactor(oficina):` commit continuing the `0622c26` thread.
- Then the other open items: **T-99** (`auto_verdict`→`calls.jsonl` decision) and post-slice widening.
