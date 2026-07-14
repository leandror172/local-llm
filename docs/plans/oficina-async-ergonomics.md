# oficina async ergonomics — migration shape + V-D12 (decision record → T-89)

**Status:** Decided (session 117, 2026-07-14). Small build items tracked in T-89; not yet built.
**Origin:** the "migration shape" discussion — should the existing Layer-5 sync
`generate_code`/`ask_ollama` convention migrate onto oficina's `submit_run`?
**Fires:** V-D12 (hook-based monitor injection) — its "when P1 ergonomics are felt in
practice" trigger fired via this design discussion, not felt usage friction (the
guessed-trigger corollary, again).
**Task:** T-89. Convention *text* stays with T-86(a) — this record is cited there, it does
not own the overlay teaching.

<!-- ref:oficina-async-migration-shape -->
## Migration shape (DECIDED): no facade, no cutover — routing convention + harness ergonomics

Three shapes were considered for migrating the sync `generate_code`/`ask_ollama` path onto
the async substrate:

- **(a) Convention-only routing** — ADOPTED (with the harness items below).
- **(b) Sync facade** (`generate_code` internally becomes submit+bounded-wait) — REJECTED.
  Both of its claimed benefits dissolve on inspection, and it breaks a load-bearing property:
  - The "concurrency safety" it would buy does not exist as a gap: P1's single-writer
    discipline protects the *store*; GPU-level collision is already absorbed by Ollama's own
    queue (stance S9: "Ollama's queue is the collision absorber").
  - It **inverts interactive priority**. `ref:delegate-gpu-policy`: interactive calls "simply
    queue behind the active run's *current model call*" — that works only because sync calls
    bypass the run FIFO. A facade would put an interactive call behind every queued run in a
    priority-less FIFO (queue policies are P6, V-D13). The gate's rule 2 ("a Claude session's
    sync `generate_code` should preempt an LTG batch refresh", `ref:model-gate-decisions`)
    *presumes the sync path survives*.
  - **The sync path's directness is the v1 priority mechanism**, implemented purely by
    topology: sync skips the run queue and waits only at Ollama's door; batch work serializes
    in oficina's FIFO. Not legacy debt — do not close this seam.
- **(c) Hard cutover** (deprecate the sync tools) — REJECTED for the same reasons plus the
  recorded finding "sync is right for small calls" (T-81 outcome, folder KNOWLEDGE.md).

Also rejected: a **timeout-redirect hint** in the sync tools' error path ("resubmit via
`submit_run`"). It is model-mediated recovery — it pays the failed sync call *and* another
model turn to resubmit. The convention routes correctly upfront; when routing is wrong, the
existing timeout error is signal enough.

**The routing convention (practice starts immediately; formal teaching is T-86(a), P2-era):**
deliverable-shaped / long / parallelizable work → `submit_run` (`kind: file` ≈
`generate_code`, `kind: answer` ≈ `ask_ollama` — S20/V-D10, nothing to build); small calls
where Claude would wait anyway → sync tools. The async substrate already serves both tool
classes; migration is a routing decision per call, not a code change.
<!-- /ref:oficina-async-migration-shape -->

<!-- ref:oficina-async-ergonomics-scope -->
## Harness-owned ergonomics (T-89 scope)

Goal (user, 2026-07-14): monitoring activation and result collection are done *by the
harness*, not by the model — when the run ends, the fact of completion (or the result
itself) is injected into the conversation that started it, the same way backgrounded
scripts already notify.

Mechanics constraint (verified against Claude Code's hook model): hooks are a
**pull/inject** mechanism — they run at lifecycle points and can add context, but they
cannot register harness-tracked background tasks and have no push channel into a running
session. So the flow decomposes into two halves along the two available channels:

1. **In-session half — V-D12 implemented.** PostToolUse hook on
   `mcp__ollama-bridge__submit_run` auto-instructs backgrounding `watch-run.sh <id>`
   (the `watch_cmd` is already in the submit response, P1-D10). One model-issued background
   Bash call remains the floor; the harness re-invokes the session when the watcher exits on
   a terminal event. The delivery report already rides the `Delivered` payload (folder
   KNOWLEDGE.md: report lives in the ledger, not `artifacts/`), so the injected notification
   carries the result narrative, not just "finished".
2. **Result-in-notification check.** Verify a `kind: answer` run's answer text actually
   appears in the watcher's terminal output (it is returned by `run_result`; whether the
   `Delivered` payload carries it is unverified). If not: add `oficina watch --result`
   (print the result on terminal state) so the answer itself lands in the injection.
3. **Cross-session half — T-14-adjacent store-scan injection.** SessionStart (or
   PreToolUse) hook scans `~/.local/share/oficina/` for runs newly terminal since last
   surfaced and injects "run X delivered" — covers submit-then-end-session and missed
   notifications. (User: "notifying a starting/restarting session that there's work that
   finished".)
4. **`refs` parity in the worker's `_default_generate`** (already a recorded P2 gap in the
   folder KNOWLEDGE.md — supports `context.files` but not `refs`). Without it, any
   `generate_code` call using `refs` cannot route through a run. **Defers to the P2 plan if
   P2 freezes first** — no double-build.
<!-- /ref:oficina-async-ergonomics-scope -->

## Build record (session 117, 2026-07-14) — items 1–3 BUILT, item 4 deferred

Decisions taken at build time:
- **D1 — hook config residency: repo-level first** (llm `.claude/settings.json`);
  user-level promotion is a T-86 runbook line.
- **D2 — scan scope: option 2, global + origin-annotated, never filtered.**
  `service.submit` records `submitted_from: os.getcwd()` in the `RunSubmitted` payload
  (additive; folds tolerate it). **Named possible-next: option 3 (repo-filtered)** — if
  notification volume ever annoys, filtering is a presentation-only change in the scan
  (the origin data is already recorded from day one).
- **Marker semantics:** per-run `surfaced` flag file (cancel-flag pattern — non-workers
  never touch ledgers).

What shipped:
- **(1) V-D12 hook:** `.claude/hooks/oficina-watch-hook.py` + PostToolUse matcher on
  `mcp__ollama-bridge__submit_run` in `.claude/settings.json`. Instructs backgrounding
  with an **absolute** watcher path (`$CLAUDE_PROJECT_DIR`) — a relative path bit during
  this very session when the shell cwd had drifted.
- **(2) Result-in-notification: VERIFIED, no build.** The `Delivered` payload carries the
  answer text / file target; `oficina watch` prints full events; live run confirmed the
  answer arriving in the harness notification. No `--result` flag needed.
- **(3) Store-scan:** `.claude/hooks/oficina-runs-scan.py` + SessionStart wiring.
  Stdlib-only events.jsonl parse (hooks run outside the uv env; the JSONL envelope is a
  frozen P1 contract), torn-tail tolerant, fail-open. Live smoke surfaced the session's
  five real runs.
- **Tests:** `.claude/hooks/tests/` — 11 subprocess-level tests (5 watch-hook, 6 scan),
  runner `run-tests.sh`. mcp-server suite 150 green (149 + origin-annotation test).
- **(4) `refs` parity: NOT built** — stays on the P2 gap list per the sequencing rule.

Build method note: tests and both scripts were local-model generated (tests-first;
scripts via `submit_run` itself — the watch flow validated its own build). Verdicts:
one 2, three 1s, one 0 + retry; the sync test-file attempts truncated twice while the
async run path produced complete files — consistent with the T-81 Part 2 finding that
completion behavior differs across invocation paths.

## Relations

- **T-86(a)** — owns the convention *teaching* (whether/when `ollama-scaffolding` gains
  async-vs-sync guidance; recorded lean: P2-era). This record supplies the decided content.
- **V-D12 / T-14** — V-D12 status updated in `docs/vision/coding-delegate/decisions.md`;
  the cross-session half is the T-14-adjacent mechanism named there.
- **T-88 (gate)** — the gate sits *under* all of this (sync tools and oficina's worker are
  both gate clients); nothing here pre-empts G-D4/G-D5. The facade rejection protects the
  interactive-priority property the gate's rule 2 will later own properly.
- **oficina P2** — item 4 is P2's gap list surfacing early; sequencing note inside T-89.
