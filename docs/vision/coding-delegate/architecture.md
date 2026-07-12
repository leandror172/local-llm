# Architecture

<!-- ref:delegate-architecture -->
## System shape

```
Claude session (coordinator + verifier)
   │  submit_run(spec) ──────────────► run_id            (instant)
   │  run_status(run_id, since_offset) ◄─ event deltas   (poll — the ONLY channel)
   │  run_result / cancel_run / answer_run
   ▼
MCP surface (thin: validates, writes spec, spawns/pokes worker, reads ledger)
   ▼
Detached worker (deterministic spine; survives the Claude session)
   S0 Intake      validate spec, reject underspecified, snapshot inputs, init ledger
   S1 Assemble    deterministic prompt/context compile (conventions mechanized);
                  H2: planner-model brief + typed context requests
   S2 Loop        coder model ⇄ evaluator Phase 1 (compile/lint/tests, CPU-only)
                  per iteration; budgets; repetition-triggered fresh start
   S3 Package     evaluator Phase 2 (judge) once; delivery report; artifacts
   ▼
Run store  runs/<id>/{spec.json, events.jsonl, iters/NN/*, report.md, workspace ref}
           + every model call → calls.jsonl (existing log, gains run_id + auto_verdict)
```

Component ownership: MCP surface lives in `mcp-server/` (ollama-bridge); worker is a new
module with its own entry point (packaging/topology open — V-D4). The evaluator
(`evaluator/`) is consumed as-is: Phase 1 validators (go build+vet, shellcheck, Python
compile(), javac) + Phase 2 rubric judge, one criterion per call.
<!-- /ref:delegate-architecture -->

<!-- ref:delegate-mcp-surface -->
## MCP surface

- `submit_run(spec) → {run_id}` — validates + persists, returns immediately. Never blocks on
  the GPU.
- `run_status(run_id, since_offset) → {state, events[offset:], next_offset}` — offset-delta
  polling (pattern proven in the claude-code task store,
  `ref:delegate-evidence-clones`). Polling is the only channel: Claude Code's MCP client is
  blocking-only and ignores progress notifications (`ref:delegate-evidence-mcp`), so status
  must be *rich* — the events are the narrative.
- `run_result(run_id)` — final report + deliverable location (branch/diff or file).
- `cancel_run(run_id)` — cooperative (worker checks between model calls / iterations).
- `answer_run(run_id, answer)` — P5; resumes an `input_required` run.
- **Generalization:** the substrate is deliverable-agnostic; `ask_ollama`-class jobs get
  `submit_run` with a trivial (no-loop) profile from P1 (user: no objection, 2026-07-11).
- Run IDs are unguessable handles (bearer-like — WorkOS MCP-async analysis); retention/TTL is
  an explicit policy, not an accident (V-D9).
<!-- /ref:delegate-mcp-surface -->

<!-- ref:delegate-run-spec -->
## Run spec (draft shape — freeze in the P1/P2 plans)

```yaml
deliverable:      # what ONE thing comes back
  kind: test_file | function | class | file | patch
  target: rel/path            # where it lands (workspace-relative)
objective: >-                 # behavioral intent — "behavior, not implementation"
context:
  files: [...]                # explicit seed (server-side read, zero Claude tokens)
  refs: [...]                 # ref:KEY injection (existing mechanism)
  callers: [...]              # per conventions: callers of generated code MUST be included
acceptance:
  test_cmd: "..."             # executable gate, runs every iteration
  test_files: [...]           # tests-first: authored/reviewed BEFORE implementation runs
  validators: [go, python...] # evaluator Phase 1 selection
  structural: default         # CONSTRAINTS block checks (fn length, naming)
  rubric: <evaluator rubric>  # Phase 2 judge, runs once at packaging
steps: [...]                  # optional ordered generation steps (decomposed generation)
workspace: worktree | in_place
budgets: {iterations: 3, fresh_starts: 1, wall_clock_s: ..., tokens: ...}
model: auto | <persona>       # persona routing reuses ollama-bridge language routing
```

Intake rejects (deterministically, before any model call): missing acceptance, missing
objective, `kind` without target, workspace `in_place` combined with `test_cmd` (tests need
isolation), budgets absent (defaults applied, never unbounded).
<!-- /ref:delegate-run-spec -->

<!-- ref:delegate-worker -->
## Worker lifecycle

- **Detached** (setsid/nohup, own process group), spawned by the MCP surface if not running;
  consumes a FIFO queue of pending specs; **single run at a time** (v1).
- **Survives the Claude session** (that's the point of "consult later", including from a
  *different* session days later). **Does NOT resume mid-run after a reboot** — decided
  2026-07-11: reruns are cheap, resumable-loop state is not; revisit with usage (V-D3 area).
- Crash containment: any uncaught stage error → `failed` event with where/whose/what triad;
  the ledger up to that point is the forensic record.
- Cold-start handling is mechanized: first call to an unloaded model gets the conventions
  doc's grace (warm-up retry, not a failure verdict) — the protocol slip found in the data
  (a cold-start timeout hand-recorded as verdict 0) becomes impossible.
<!-- /ref:delegate-worker -->

<!-- ref:delegate-ledger -->
## Event-sourced ledger (decision: pattern yes, event-store DB no)

Append-only JSONL per run: `RunSubmitted, IntakeRejected, AssemblyDone, IterationStarted,
IterationEvaluated, FreshStart, QuestionRaised, AnswerReceived, JudgePassed/Failed,
Delivered, Exhausted, Failed, Cancelled` (names drafted; freeze in P1 plan). Status = fold of
events; `run_status` returns deltas by offset; watchers subscribe by tailing.

Why not KurrentDB (ex-EventStoreDB, user's suggestion 2026-07-11): it is a faithful
implementation of exactly this pattern, but an always-on server + operational surface
(backups, upgrades, a daemon to babysit) for a single-user single-worker system with tiny
event volume. JSONL + fsync gives replay, audit, subscription, and DPO-extraction-as-query at
zero infra. **Upgrade trigger (named, per T-76 discipline):** multiple concurrent
workers/machines, or a real subscription fan-out need. Precedent: `calls.jsonl` is already an
event log.
<!-- /ref:delegate-ledger -->

<!-- ref:delegate-state-machine -->
## State machine

Public states adopt the MCP Tasks extension vocabulary (interop-friendly, zero cost):
**`working` / `input_required` / `completed` / `failed` / `cancelled`**, plus `queued`.
Internal phases within `working`: `intake → assembling → looping(iter k) → packaging`.
`input_required` is entered two ways: the optional **approval gate** (run pauses after
assembly with "here are the criteria/tests I will hold the code to") and, from P5, a model
`blocked` escape. Exhausted budgets → `failed` with reason `exhausted` and the best attempt
attached (SWE-agent's auto-submit-on-exhaustion pattern: degraded result beats nothing).
<!-- /ref:delegate-state-machine -->

<!-- ref:delegate-loop -->
## Iteration anatomy (S2)

1. **Generate** — coder persona; if `steps:` present, generate step-by-step (mechanizes
   `benchmarks/lib/decomposed-run.py`; Layer-0 finding: 3-stage decomposition reduces bug
   severity). Direct-to-workspace via existing `output_file` semantics.
2. **Evaluate (cheap, every iteration)** — evaluator Phase 1 validators + `test_cmd` +
   structural checks. **Delta-scoped:** snapshot-before/diff-after so only regressions this
   iteration caused count (claude-code edit-safety pattern) — pre-existing warts in context
   files must not create unfixable loops.
3. **Classify the failure** — mechanical / structural / conceptual, the conventions doc's own
   taxonomy. v1: rule-based (compiler/test output parsing). Later: a tiny-model classifier
   (qwen3.5:0.8b/2b, phi4-mini — gives the idle M-P1b/P2 benchmark a product consumer).
4. **Repair or fresh-start** — repair prompt carries the classified failure + failing output.
   **Fresh start triggers on repetition, not just exhaustion:** a deterministic signature over
   the last outputs; same defect signature twice → discard history, re-anchor with stubs
   (mechanized stubs-then-Ollama). Evidence this fires in practice: the same typo
   (`html23text`) appeared in two separate runs in our verdict data. Pattern source:
   open-multi-agent's LoopDetector (MIT).
5. **Budget check** — default ~3 iterations + 1 fresh start (evidence: 76–95% of repair gains
   land in rounds 1–2, exponential decay after — `ref:delegate-evidence-selfrepair`).
6. **Model escalation** — tier 1 coder → tier 2 (per conventions retry ladder), mechanized as
   a budget-scoped policy. **14B floor** for the coder role (7B does not reliably converge).
<!-- /ref:delegate-loop -->

<!-- ref:delegate-workspace -->
## Workspace seam

`workspace: in_place | worktree` (parameterizable — user, 2026-07-11), designed as an
abstraction seam so a container backend can slot in later without redesign (OpenHands
independently converged on workspace-as-abstraction: `LocalWorkspace`/`DockerWorkspace`
behind one factory). Default **worktree** whenever acceptance executes code: tests need a
stable snapshot isolated from concurrent session edits, and the deliverable becomes a
**branch + diff report** Claude reviews and merges — "coordinator and verifier" made literal.
`in_place` remains for P1 single-shot generation (today's `output_file` semantics).
**Security note:** worktrees isolate files, not processes — generated tests run with user
privileges. Acceptable for personal infra; a container workspace is the upgrade path.
Repo convention: `ref:git-worktrees`.
<!-- /ref:delegate-workspace -->

<!-- ref:delegate-gpu-policy -->
## GPU policy (12GB VRAM, one resident 14B at a time)

- **Phase batching, not per-iteration swapping.** Naive planner→coder→judge per iteration =
  3–4 swaps × ~15s warm load + full re-prefill ≈ ~1 min/iteration of pure overhead. Batched:
  assembly models (if any) finish first, the loop runs coder-only (Phase 1 evaluation is CPU),
  judge runs once at packaging → ~3 swaps per run total.
- **Same-base persona switching is free** (no reload): prefer a judge persona on the coder's
  base (qwen2.5-coder:14b) during packaging; qwen3:14b only where reasoning is the point.
- **Queue at the application level** (the worker's FIFO), not in Ollama: phase batching,
  priorities, cancellation, and visibility all live above HTTP. Ollama's internal queue is the
  *collision absorber* when an interactive MCP call lands mid-run (empirically safe: Ollama
  queues unloads without correctness risk — `docs/findings/ollama-eviction-concurrency-findings.md`).
- **Interactive contention (v1):** interactive calls simply queue behind the active run's
  current model call; a cooperative yield/pause flag between iterations is the cheap next
  step; real priority/preemption is T-21 territory (file-based coordination layer) — do not
  build early.
- keep_alive tuning per stage (evict assembly models entering the loop); wedge detection
  (Ollama can be loaded-but-unresponsive; restart clears — known failure mode).
<!-- /ref:delegate-gpu-policy -->

<!-- ref:delegate-monitoring -->
## Monitoring ergonomics ("a hook starts a tool to monitor it")

- **Works today, zero new harness features:** `submit_run`'s response includes the watcher
  command; Claude backgrounds `watch-run.sh <id>` (blocks until state change / exits on
  terminal state) and the harness's background-task notification re-invokes Claude. CLI parity
  for free (any shell can watch a run without MCP).
- **Optional polish, later:** a PostToolUse hook auto-starting the watcher on submit;
  hook-injected status on session start (adjacent to T-14 hook-based auto-resume).
- **Not available, by measurement:** MCP progress notifications (client ignores them) and MCP
  sampling (unsupported + deprecated) — see `ref:delegate-evidence-mcp`.
<!-- /ref:delegate-monitoring -->
