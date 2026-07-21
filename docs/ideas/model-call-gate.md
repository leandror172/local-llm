# Model-Call Gate — resource scheduler for all model calls (idea + decision record)

**Status:** Decision record (session 116, 2026-07-13). Not planned, not built — triggers below.
**Working name:** "model-call gate" (label only; real name follows the oficina V-D1 precedent —
decide at plan-freeze, metaphor never in code/schema/CLI verbs).
**Origin:** the oficina first-client discussion — the user has long imagined an async
queue/organizer between ALL tools and model calls, and asked whether oficina is that thing.
**Supersedes-in-scope:** `docs/ideas/ollama-coordination-layer.md` (T-21) — that doc designs a
*busy-check contract* (is the GPU in use?); this one names the *scheduler* (who goes next,
where, in what order). T-21's shared-directory mechanism survives as a candidate substrate.
**Task:** T-88.

<!-- ref:model-gate-altitude -->
## G-D1 (DECIDED 2026-07-13) — Two altitudes: oficina is NOT the gate

| | **oficina** | **model-call gate** |
|---|---|---|
| Unit of work | a **run** (deliverable: multi-call, stateful, loop in P2) | a **call** (one model invocation) |
| Job | workload semantics: intake, iterate, evaluate, package, review | resource multiplexing: admission, placement, ordering |
| Knows about | objectives, targets, evaluators, verdicts | models, footprints, capacity, who's waiting |
| Topology | **product** | **layer-0 primitive** |
| Analogy | a CI system | the connection pool / OS scheduler under it |

**Consequences:**
- LTG refresh, expense-reporter probes/acceptance, benchmarks, and ollama-bridge sync tools
  are **gate clients**, never oficina clients. Forcing them through `submit_run` means faking
  deliverable specs past intake — when a client must lie to an abstraction, the abstraction is
  wrong for it. There is no loop in those workloads; oficina's machinery is meaningless to them.
- **oficina's worker becomes a gate client like everyone else** once the gate exists.
  Dependency arrows: products → primitive, never product↔product (the T-76 topology rule);
  and oficina→LTG stays the only allowed direction between those two — routing LTG's calls
  through oficina would invert it.
- **Queue-of-queues is fine because the units differ:** oficina's FIFO serializes *run
  admission* ("which deliverable next"); the gate serializes *GPU access* ("which call next,
  ordered how"). oficina's FIFO only looks like a GPU serializer today because its worker is
  the only async consumer.
<!-- /ref:model-gate-altitude -->

<!-- ref:model-gate-decisions -->
## Decision register

- **G-D1 — altitude split: DECIDED** (above).
- **G-D2 — client-owns-plan / gate-owns-admission: DECIDED.** Clients know their optimal
  ordering (e.g. LTG: 5 files × 2 same-model extraction calls, then a heavier-model pass —
  cache-affinity the gate cannot derive). The gate takes **hints, not intelligence**: batch
  submission with model-affinity tags, a priority class, intra-batch order preserved; the gate
  does admission, placement, and cross-client interleaving to minimize swaps. Keeps the gate
  dumb, small, product-agnostic.
  **⚠ Note added 2026-07-18 (M-D4):** batching does **not** by itself force an async contract —
  `gate.run_batch([...])` can block once on the whole batch while the gate still interleaves its
  calls with other clients'. What batching *does* expose is that the caller's wait is now bounded
  by the interleaved queue, not by its own work. See **G-D7** below: the missing axis is
  blocking-vs-ticket, not batching. *(An earlier version of this note claimed a semaphore cannot
  implement G-D2 — refuted on advisor review; recorded so it is not re-derived.)*
- **G-D3 — resource model: two constraint families, vocabulary now, capacity-only v1.**
  - **Family A — capacity/placement** (residency): local GPU VRAM, hybrid VRAM+RAM
    (30B MoE partial offload), CPU-only pools, second/network/cloud GPUs. Placement logic:
    two models fit → co-resident; a big model needs everything → takes over; heterogeneous
    GPUs → route candidates to the pool they fit.
  - **Family B — rate/budget** (remote APIs: Claude API, Claude Code headless, ChatGPT,
    Groq): the constraint is tokens/min, requests/day, spend — *time-window budgets*, not
    residency. Different admission math, same "pool with an admission policy" abstraction.
  - **v1 scope = one pool: the local Ollama endpoint** (Family A, single GPU + host-RAM
    ceiling). The resource descriptor must not hardcode "one GPU" — but nothing beyond the
    descriptor generalizes in v1. Family B is recorded so the vocabulary doesn't paint us
    into a corner; it is NOT designed. (Same move as LTG's `source_group`: capture the axis
    at day one, defer the logic.)
- **G-D4 — build priority vs oficina P2: OPEN.** User 2026-07-13: gate "deserves soon, but
  undecided if oficina goes first." Neither blocks the other architecturally (the worker's
  generation seam is injectable — a gate client slots in behind `GenerateFn` later).
- **G-D5 — mechanism: OPEN.** Candidates: T-21's shared-directory contract (zero-daemon,
  crash-safe by PID liveness) vs a small always-on broker owning the Ollama socket vs a
  library-level semaphore in ollama-bridge. **⚠ This register conflates two independent axes
  (2026-07-18, M-D4):** *mechanism location* (shared dir / broker / in-process library) vs.
  *client contract* (blocking wait / ticket). Only the first is varied above. The contract axis
  is mechanism-independent: **no** blocking contract can bound the wait below the caller's
  deadline when the queue ahead holds 14B swaps and multi-minute generations — queueing *ahead
  of* batch work does not help if the wait itself exhausts the caller. Every candidate therefore
  needs a **ticket** path for clients that cannot tolerate unbounded wait. See **G-D7** and
  `ref:multi-session-transport-requirement`. Note Ollama itself already provides: request
  queueing, refCount protection (evict-during-generation is safe), co-residency via
  `OLLAMA_MAX_LOADED_MODELS` when models fit. The v1 gate is **policy over Ollama's
  scheduler**, not a replacement: cross-client priority, cache-affinity reordering,
  cross-call rules Ollama can't see. Watch PR #9392 (`ACTIVE` field) and #11159 (metrics)
  — both reduce mechanism cost.
- **G-D6 — oficina-substrate reuse: OPEN, trigger-disciplined.** oficina's P1 modules
  (`ledger`, `fifo`, `workerproc`, `ids`, `store`) are generic async-run machinery — nothing
  coding-specific (that lives in `intake.py`/`worker.py`). If the gate wants an event ledger
  + atomic queue + pidfile-arbitrated worker, extraction into a shared primitive becomes the
  T-76-style move: **do not extract until the gate is real** (second consumer rule).
  **⚠ Trigger likely fired (2026-07-18, M-D4):** if the gate must hand out tickets (G-D5 above),
  it needs exactly this machinery — the gate *is* the second consumer, and the altitude split
  survives with both altitudes sitting on one shared async primitive.
- **G-D7 — wait tolerance is a distinct axis from admission policy: OPEN (filed 2026-07-18).**
  Admission policy answers *who goes next*; wait tolerance answers *how long a client can wait
  before its transport dies*. The register above only ever modelled the first. A client waiting
  **fairly** for four minutes is as dead as one waiting unfairly. Proposed resolution: clients
  declare a deadline at submission; the gate answers admission *instantly* — capacity free ⇒
  admit sync; projected wait > deadline ⇒ **refuse fast and return a ticket**. This is not the
  "timeout-redirect hint" T-89 rejected (that was model-mediated recovery *after* paying for a
  failed call); this is admission-time routing decided by the only component holding capacity
  state. Full argument: `ref:multi-session-transport-requirement` (T-102).
  **Decomposes into D1/D2/D3 with different costs — resolve separately, do NOT freeze as one:**
  `ref:multi-session-busy-check`. Only D3 needs a gate to exist.
- **G-D8 — the MVP is T-21's busy-check, not this scheduler: PROPOSED (2026-07-18).** A
  pre-flight *"is the GPU busy, and with which model?"* check addresses the concrete failure mode
  (`ref:multi-session-failure-mode`) with **no admission control, queue, broker, or daemon** —
  largely readable from Ollama's existing `/api/ps`, ~a day of work — **and it produces the
  contention measurement this doc's triggers have been waiting for, as a byproduct.** Estate
  lesson attached: T-88 superseded T-21 by *generalizing* it, which made it big enough never to
  build and lost the founding problem statement in the same move. Build the busy-check first;
  design the gate when its data justifies one.

## First rules the gate would own (concrete value, day one)

1. **The embed/infer sequential constraint** — today enforced ONLY by convention in
   `ltg/.memories/QUICK.md` ("embed and infer calls must not run in parallel — VRAM"). A rule
   that lives in a memory file is exactly what a gate owns in code.
2. **Interactive > batch priority** — a Claude session's sync `generate_code` should preempt
   (queue ahead of, not interrupt) an LTG batch refresh. **Note (2026-07-18):** singular "a
   Claude session" — G-D2's priority *class* model gives no tie-break **within** a class, and N
   concurrent sessions are all the same class. Interactive-vs-interactive ordering is unowned;
   `ref:multi-session-contention`.
3. **Swap-minimizing interleave** — group queued calls by model across clients; a 14B↔14B
   swap costs ~15s cold-load each way (ext4 store), so naive FIFO across two clients thrashes.

## Triggers (build when one fires)

> **STATUS: FIRED (session 124, 2026-07-18 — M-D3).** The user confirmed **concurrent Claude
> Code sessions are standing practice**, which is the T-21 trigger the first bullet inherited.
> Session 118's "trigger NOT yet met" note rested on T-90 (Windows-desktop VRAM) being a
> *different* cause — it is, and it does not bear on this. Note the client roster in
> `ref:model-gate-altitude` enumerates *products* (LTG, expenses, benchmarks, oficina, "sync
> tools") and **never modelled N instances of the same client** — the session-level framing was
> lost when this doc superseded T-21. `ref:multi-session-contention` (T-102).
>
> **⚠ These triggers are unfalsifiable as written.** "Observed contention" cannot fire while the
> *user manually serializes GPU work by hand* (documented once: session 115 ran two Opus subagents
> *"serial for the 12 GB VRAM ceiling"*, logged as a build note, never as a problem). **A trigger
> a person can satisfy by hand is not a trigger.** Compounding it: `calls.jsonl` sees only the MCP
> bridge — LTG refresh, expense classification/acceptance, and benchmarks call Ollama directly and
> are **invisible** to it, so measured load is a lower bound by an unknown factor. Instrument at
> the Ollama endpoint, not the bridge. See `ref:multi-session-contention` § caveats.

- **Observed contention:** swap-thrash or a blocked interactive call once oficina runs, LTG
  refreshes, and expense probes actually overlap in practice (the T-21 trigger, inherited).
- **LTG per-commit refresh goes automatic:** `triggers.on_commit: refresh` would make
  contention routine *by design*, not by accident — deciding that IS deciding to build the gate.
- **G-D4 resolves to gate-first:** an explicit prioritization decision also fires it.

## Relations

- **T-21 / `ollama-coordination-layer.md`:** subsumed in scope; its mechanism + empirical
  findings (refCount safety, PR #9392 watch) are inputs to G-D5.
- **T-76 model registry:** the gate consumes the registry (model footprints, roles, fallback
  chains) — registry sits below the gate; both are layer-0. A gate build is a plausible
  third consumer that fires T-76's extraction trigger.
- **oficina:** `ref:delegate-phasing`, `ref:delegate-p1-decisions`. The worker's injectable
  `generate: GenerateFn` seam is where a gate client later lands — no P1/P2 rework required.
<!-- /ref:model-gate-decisions -->
