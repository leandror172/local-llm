# oficina P1 — Async substrate (plan)

**Status: FROZEN 2026-07-11** (P1-D1–D11 all reviewed; open items resolved below). Task: **T-84**.
Vision: `docs/vision/coding-delegate/` (folder index there; system name **oficina**, V-D1).
Event vocabulary: `ref:delegate-event-model`. Phase contract: `ref:delegate-phasing` § P1.

<!-- ref:delegate-p1-goal -->
## Goal & scope

Deliver the async run substrate around **today's** `generate_code` + `ask_ollama` semantics:
`submit_run` / `run_status(since_offset)` / `run_result` / `cancel_run`, a detached worker
with a disk FIFO, an event-sourced JSONL ledger, retention with observability, and a watch
path that works with zero new harness features.

**What P1 kills:** the 120s MCP-timeout class (T-81's 9–20-min merges become legal);
Claude-works-while-GPU-works parallelism. Side effect: `MCP_TIMEOUT=120000` is demoted from
load-bearing to cosmetic for generation calls.

**Explicitly NOT in P1** (hold this line): no evaluator loop, no iteration budgets, no
worktrees/deliverable-as-branch, no judge, no approval gate, no `answer_run`, no new model
roles, no prompt compiler. A P1 run is: intake → one generation (today's semantics) →
package → terminal event.

**First client candidate:** T-81 (`install-overlay --mode ai` preview) — not part of P1's
acceptance, but its shape (submit → review → apply) is the design's reference consumer.
<!-- /ref:delegate-p1-goal -->

<!-- ref:delegate-p1-decisions -->
## Decision register (P1-D) — freeze on review

Vision-level decisions resolved here (V-D4, V-D9, V-D10, V-D11) + substrate decisions new
to this plan (P1-D5…P1-D11, flagged **NEW** — not yet user-discussed unless noted).

- **P1-D1 (= V-D4) — Residency: worker grows inside `mcp-server/`.** New module tree
  `src/ollama_mcp/oficina/`; console entry point `oficina` added to ollama-bridge's
  `pyproject.toml` (the `st-*` uv-tool precedent — no separate package, no pre-built split).
  The MCP tools are thin additions to `server.py` and share `client.py`/`config.py`.
  Split-to-own-repo trigger mirrors T-33: first external adopter, or it competes with llm
  session serialization. *(Agreed in discussion 2026-07-11.)*
- **P1-D2 (= V-D9) — Retention: parameterized, observable, previewable.**
  `retention:` config section (`ledger: forever`, `workspaces_ttl_days: 7`,
  `artifacts_keep_runs: 20` — all parameters, defaults encode the P6-harvest argument);
  every prune appends `RetentionPruned` to the **worker ledger** (what, bytes freed, which
  policy — silence only when nothing pruned); `oficina runs` lists footprint + eligibility,
  `oficina prune --dry-run` previews. Retention pass runs on worker start, automatic, with
  events. Push-channel (session-start hook) deferred to usage (user 2026-07-11). Run IDs
  stay resolvable against the ledger after artifact pruning — `run_result` on a pruned run
  returns the report, not the workspace.
- **P1-D3 (= V-D10) — `ask_ollama` profile: same spec, trivial profile — no second schema.**
  `deliverable.kind: answer` → no acceptance block, no target file required, budget
  implicitly 1, `workspace: in_place`. `generate_code` profile: `kind: file` with `target`
  (today's `output_file` semantics), `context.files`/`refs` passthrough. Profiles differ in
  *intake rules*, not code shape.
- **P1-D4 (= V-D11) — Plain Python; no orchestration framework.** Two research passes
  2026-07-11 confirm S19 — full record in `docs/vision/coding-delegate/decisions.md`
  § "V-D11 re-check record" (general survey incl. DBOS; Axon 5 addendum). Libraries at the
  edges only: pydantic for spec/event schemas; nothing else until felt need.
- **P1-D5 — Event freeze: the `freeze-at-P1` set + envelope from `ref:delegate-event-model`.**
  Envelope `{offset, ts, event, payload}`; run events `RunSubmitted, IntakeRejected,
  GenerationStarted, GenerationFinished, Delivered, Failed, Cancelled`; worker events
  `WorkerStarted, WorkerStopped, RetentionPruned`. Folds MUST tolerate unknown event names
  (forward compatibility for draft-PN events). **NEW sub-decision:** `offset` = 0-based
  event index (line number), not byte offset — `since_offset` slices a list, and partial
  lines from a crashed writer are detectable by JSON parse failure on the last line. *(Agreed 2026-07-11.)*
- **P1-D6 — Single-writer ledger discipline.** **NEW.** Exactly one writer per ledger file
  at a time: the MCP surface writes only `RunSubmitted` (at run-dir creation, before the run
  is queued — the worker cannot own a file that doesn't exist yet); from queue-pop onward,
  ONLY the worker appends. Cancellation therefore is a **flag file** (`runs/<id>/cancel`),
  written by the MCP surface, observed by the worker, which emits `Cancelled` at its next
  check — the command→event gap is real and visible in the ledger, by design.
- **P1-D7 — Storage: machine-global under `~/.local/share/oficina/`.** **NEW.** Layout:
  `runs/<run_id>/{spec.json, events.jsonl, artifacts/}`, `queue/`, `worker.pid`,
  `worker-events.jsonl`, `worker.log`. Precedent: `calls.jsonl` lives at
  `~/.local/share/ollama-bridge/` — the bridge is machine-global (user-level MCP
  registration), so its runs are too; the spec carries absolute target paths into whatever
  repo the deliverable lands in. Config: `~/.config/oficina/config.yaml` (XDG), embedded
  defaults so a missing file is not an error.
- **P1-D8 — Run IDs: `secrets.token_urlsafe(16)`.** **NEW.** Unguessable bearer-like
  handles (WorkOS analysis via `ref:delegate-evidence-mcp`); no sequential IDs.
- **P1-D9 — Queue + worker-spawn mechanics.** **NEW.** FIFO = `queue/<epoch-ms>-<run_id>`
  marker files; worker pops lowest name; push and pop are atomic renames. `submit_run`
  ensures a worker: read `worker.pid`, liveness-check (`kill -0`), spawn detached
  (`setsid`, stdio → `worker.log`) if dead; pidfile created with `O_CREAT|O_EXCL` to close
  the double-spawn race (claude-code lockfile pattern, `ref:delegate-evidence-clones`).
  Worker exits when queue is empty (lazy daemon — nothing to babysit); next submit respawns.
  *(Agreed 2026-07-11; pidfile stores PID + start-timestamp per the concurrency review.)*
- **P1-D10 — Watch path: CLI-first.** **NEW.** `oficina watch <run_id>` blocks (poll/tail)
  until state change or terminal event, printing new events; `watch-run.sh` is the 3-line
  bash wrapper per `patterns-script-conventions` (whitelisting seam). `submit_run`'s
  response includes the exact watch command so Claude can background it immediately
  (`ref:delegate-monitoring`).
- **P1-D11 — CLI surface (v1): `oficina submit|status|result|cancel|watch|runs|prune`.**
  **NEW.** Single entry point + plain literal verbs (naming boundary rule); `submit` exists
  on the CLI too (shell parity — any script can submit without MCP). MCP tools and CLI verbs
  share one implementation layer. *(Agreed 2026-07-11.)*
<!-- /ref:delegate-p1-decisions -->

## Run spec (P1 subset of `ref:delegate-run-spec`)

```yaml
deliverable:
  kind: file | answer          # P1 profiles (P1-D3); P2+ adds test_file/function/class/patch
  target: /abs/or/repo/rel     # required for kind: file, forbidden for kind: answer
objective: >-                  # behavioral intent (required, non-empty)
context:
  files: [...]                 # server-side read — existing context_files semantics
  refs: [...]                  # existing refs/refs_root semantics
workspace: in_place            # P1 only supports in_place (worktree is P2)
model: auto | <persona>        # existing ollama-bridge routing
timeout_s: 1800                # per-generation ceiling (parameter, generous default)
```

**Intake rejects (deterministic, before any model call):** missing/empty `objective`;
`kind: file` without `target`; `kind: answer` with `target`; unknown `kind`; unknown top-level
keys (fail loud — a typo'd `contxt:` must not silently produce a context-free run);
nonexistent `context.files`; `workspace` other than `in_place` (P1). Every rejection names
the rule in `IntakeRejected.payload` (where/whose/what: stage=intake, fault=payload).

## MCP surface (thin — validates, persists, pokes, reads)

- `submit_run(spec) → {run_id, watch_cmd, queue_position}` — shape-validate, create run dir,
  write `spec.json`, append `RunSubmitted`, push queue marker, ensure worker. Never blocks
  on the GPU.
- `run_status(run_id, since_offset=0) → {state, phase, events[since:], next_offset}` —
  state/phase are folds computed server-side; events carry the narrative (polling is the
  only channel — `ref:delegate-evidence-mcp`).
- `run_result(run_id) → {state, report, deliverable}` — for `kind: file`: target path +
  summary; for `kind: answer`: the answer text. Errors distinguish `unknown run_id` from
  `not terminal yet` from `artifacts pruned` (discriminating signals).
- `cancel_run(run_id) → {state}` — writes the flag file (P1-D6); returns current state
  immediately (the `Cancelled` event lands when the worker next checks).

## Concurrency model (P1-D6 × P1-D7 — reviewed with user 2026-07-11)

Claude Code spawns one MCP server process per session; the CLI is another process; all of
them plus the worker share the machine-global store (P1-D7). The invariant is **per-file
ownership with an ordered handoff**, never a lock:

| File | Writers | Why it's safe |
|---|---|---|
| `runs/<id>/events.jsonl` | MCP surface (only `RunSubmitted`, pre-queue) → worker (everything after) | The surface appends `RunSubmitted` **then** pushes the queue marker; the worker can only discover a run through the queue → happens-before handoff, never two appenders |
| `runs/<id>/spec.json` | MCP surface, write-once | Immutable after creation |
| `runs/<id>/cancel` | Any MCP surface / CLI | Idempotent flag; never touches the ledger |
| `queue/` | Many pushers, one popper | Distinct names (`<epoch-ms>-<run_id>`, unique by construction), atomic renames |
| `worker.pid` | Arbitrated | `O_CREAT\|O_EXCL`; loser liveness-checks; stores PID **+ start-timestamp** (PID-reuse guard); stale file removed + retry |
| `worker-events.jsonl` | Worker only | Single process by pidfile arbitration |

Consequences: concurrent submits (same or different sessions) never conflict — each run has
its own dir, and runs serialize only at the worker's FIFO (the GPU is the scarce resource,
not the API). Reads are lock-free against append-only files (torn-last-line rule, P1-D5).
**Cross-session access to a run is by design** ("consult later, from a different session"):
status/result are reads; cancel is the flag file. Possession of the unguessable run ID is
the authorization (bearer-handle framing, `ref:delegate-evidence-mcp`) — acceptable for
single-user infra; revisit only if the store ever becomes multi-user.

## Module tree & task breakdown (TDD; local-first per `ref:local-model-conventions`)

```
mcp-server/src/ollama_mcp/oficina/
  __init__.py
  ids.py        # run-ID minting (P1-D8)
  ledger.py     # append / read(since_offset) / fold_state (P1-D5, P1-D6)
  store.py      # run-dir layout, spec persist/load (P1-D7)
  intake.py     # spec validation, per-profile rules (P1-D3)
  fifo.py       # queue push/pop, atomic renames (P1-D9)
  workerproc.py # pidfile, liveness, detached spawn (P1-D9)
  worker.py     # main loop: pop → intake → generate → package → events
  retention.py  # sweep + RetentionPruned + dry-run report (P1-D2)
  cli.py        # `oficina` entry point (P1-D11)
```

| # | Task | Tests prove |
|---|------|-------------|
| T1 | `ledger.py` | envelope shape; offset slicing; fold over known events; unknown events tolerated; torn-last-line detection |
| T2 | `ids.py` + `store.py` | run-dir creation; spec round-trip; unknown-id errors |
| T3 | `intake.py` | every rejection rule, both profiles; unknown-key fail-loud; accepted specs pass through unchanged |
| T4 | `fifo.py` | FIFO order; atomicity under concurrent push; pop on empty |
| T5 | `workerproc.py` | pidfile exclusivity; stale-pid recovery incl. PID-reuse (start-timestamp mismatch); detached spawn survives parent exit (integration) |
| T6 | `worker.py` | pop→generate→deliver happy path (Ollama client mocked); Failed with where/whose/what on stage error; cancel-flag honored between stages; cold-start grace |
| T7 | MCP tools in `server.py` | submit/status/result/cancel wiring; result error discrimination |
| T8 | `cli.py` | verb parity with MCP tools; `runs`/`prune --dry-run` output |
| T9 | `retention.py` | policy firing per class; RetentionPruned payload; dry-run touches nothing |
| T10 | Acceptance (live) | below |

Estimate: 2 sessions (T1–T5 one; T6–T10 one). Worker internals use named semantic methods
over generic dispatch (`ref:patterns-code-named-methods`) — e.g. `ledger.generation_started(...)`,
not `ledger.append("GenerationStarted", ...)` at call sites.

<!-- ref:delegate-p1-acceptance -->
## Acceptance (from `ref:delegate-phasing` § P1, made concrete)

1. **Long-run survival:** submit a generation known to exceed 120s (T-81-class input);
   `submit_run` returns in <1s; Claude does unrelated work; poll collects `Delivered`.
2. **Session detach/reattach:** kill the Claude session mid-run; from a NEW session,
   `run_status(run_id, 0)` replays the full narrative and the run completes untouched.
3. **Cancel:** `cancel_run` on a running generation → `Cancelled` within one worker
   checkpoint; ledger shows the command→event gap.
4. **Ledger replay:** state computed from `events.jsonl` alone matches reported state for
   every run in the acceptance set (delete no state, recompute all).
5. **Retention observability:** with TTLs forced low, a sweep prunes artifacts, emits
   `RetentionPruned` with correct byte counts, and `run_result` on the pruned run still
   returns its report.
6. **Verdict protocol continuity:** every generation logs to `calls.jsonl` exactly as today
   (plus `run_id` field) — the existing DPO pipeline sees no regression.
<!-- /ref:delegate-p1-acceptance -->

## Open items — RESOLVED at freeze (2026-07-11)

- **`IntakeAccepted`: SILENT** (user decision, "for now") — acceptance stays visible as
  `GenerationStarted`; `ref:delegate-event-model` already matches. Revisit trigger: a fold
  consumer that genuinely needs to distinguish "accepted, waiting for GPU" from "queued"
  (P2's loop or a UI would be the first candidates).
- **`calls.jsonl` `run_id` field: CONFIRMED additive-safe** — both readers
  (`ollama-stats.py`, `ollama-verdicts.py`) access fields only via `dict.get()` on parsed
  lines; unknown fields are ignored by construction.
- **Worker idle behavior: exit-when-empty stands** (P1-D9 agreed). Revisit trigger: spawn
  latency felt in practice.
