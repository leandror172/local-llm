# Multi-session GPU contention — the founding problem, recovered (decision record)

**Status:** Decision record (session 124, 2026-07-18). Open decisions M-D1–M-D5; nothing built.
**Origin:** the user's challenge, 2026-07-18 — *"my problem, as was discussed in the pitch, is
running concurrent Claude Code sessions, and those sessions trying to use ollama as coding, and
all of them fighting for the model allocation… generating code through ollama, synchronously,
would still time out."*
**Task:** T-102. Amends T-89 (scope) and T-88 (client model + transport requirement).
**Relations:** `ref:oficina-async-migration-shape` (T-89), `ref:model-gate-altitude` /
`ref:model-gate-decisions` (T-88), `docs/ideas/ollama-coordination-layer.md` (T-21).

<!-- ref:multi-session-contention -->
## The problem, and where the record lost it

**The problem:** N concurrent Claude Code sessions (across this repo and others — the bridge is
registered user-level, so every session in every repo has the tools) each delegate coding work
to Ollama. They contend for one 12 GB GPU. Each may want a *different* 14B persona, forcing
swaps. A synchronous `generate_code` that waits its turn exhausts its own transport deadline
and dies — the caller is not slow, it is **structurally unable to wait**.

This is not a new idea. It is the **founding** problem, and the record dropped it in a
supersession. The provenance:

| Session | Date | What happened |
|---|---|---|
| 42 | 2026-03-14 | `ollama-coordination-layer.md:13-18` names it exactly: *"Two Claude Code sessions load different models simultaneously, thrashing VRAM"* |
| 43 | 2026-03-15 | Empirically downgraded — Ollama's `refCount` means **zero correctness risk**; reclassified performance-only; deferred behind a "when observed" trigger (T-21, still open). `:113` notes the trigger *"(two Claude Code sessions) is **now routine**"* — and uses that to justify *not* building |
| 112 | 2026-07-11 | oficina pitch authored. Its four measured facts (`ref:delegate-vision`) are token waste, the 120s ceiling, verdict compliance, verdict distribution. **Multi-session contention does not appear.** The only concurrency non-goal (`vision.md:89`) is about concurrent *runs*, not sessions |
| 116 | 2026-07-13 | Gate (T-88) declares itself T-21's successor — but **reframes clients from *processes/sessions* to *products*** (LTG, expenses, benchmarks, oficina, "sync tools"). The two-sessions framing does not survive the handoff |
| 117 | 2026-07-14 | No-facade decision (T-89) built on "sync bypasses the FIFO" — an argument valid for one interactive caller |
| 118 | 2026-07-15 | The one contention-caused sync-timeout incident is diagnosed as **Windows-desktop VRAM** (T-90) and explicitly ruled *not* the thrash the gate waits for |

**Diagnosis: a supersession artifact.** When T-21 folded into T-88, the client model shifted
from *processes/sessions* to *products*. Nothing in the oficina/gate line re-derives the
session-level problem, and no incident forced it back — because the incident that looked like
it (T-90) had a different cause.

**Corollary for the estate (this is the third instance):** *a deferral whose trigger is guessed
will fire on a different trigger* (`ref:active-decisions`). T-21's trigger was "VRAM thrash
becomes an observed pain point." What actually happened is that the pain arrived as **sync
timeouts under contention**, not as measurable thrash — so the trigger never fired even though
the condition was, in the March doc's own words, "now routine."

## Why sync is already at the edge — measured

`~/.local/share/ollama-bridge/calls.jsonl`, 2026-07-18 (sync path, n=596):

```
median  31.6s   p90 147.3s   p95 202.9s   p99 294.3s   max 580.7s
  >120s: 86     >300s: 4     >540s: 1     >600s: 0
async path (n=18): zero over 60s
```

**The operative ceiling is ~600 s, not 120 s.** Every one of those 86 calls past 120 s is a
*completed* row — `calls.jsonl` is written on success — so 120 s was never binding. The hard
wall shows up at 600 s: max 580.7 s, **zero rows above 600 s**, matching `MCP_TIMEOUT=600000`
in `~/.claude.json`.

**Config does not match behaviour** (small finding, worth its own fix): `config.py:33` declares
`DEFAULT_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))`, and `OLLAMA_TIMEOUT` is set
**nowhere** — yet calls run to 580 s. `~/.bashrc:132` sets `MCP_TIMEOUT=120000` while
`~/.claude.json` sets `600000` in two places. The effective ceiling is ambiguous and depends on
launch path; the declared 120 s is not what the system does.

**The honest reading, which is the stronger one:** sync generations *routinely* run minutes —
p95 over 3 min, p99 ~5 min, max 9.7 min — **on a single session with an uncontended GPU**, and
the longest already brush the ~600 s wall. Add a second session forcing a 14B↔14B swap (~15 s
cold-load each way, gate rule 3) and queueing behind a multi-minute generation, and that tail
crosses it. **No new contention evidence is needed — the tail already exists; concurrency is
what pushes it past the ceiling.**

### ⚠ Two caveats that make this a LOWER BOUND, not a picture (user, 2026-07-18)

Do not read the numbers above as "the GPU's workload." Both biases run the same direction:

1. **`calls.jsonl` only sees the MCP bridge.** LTG refresh, expense classification, expense
   acceptance probes, and benchmark runs **do not go through `generate_code`/`ask_ollama`** —
   they call Ollama directly and are invisible to this log. **Real GPU load is strictly higher
   than measured, by an unknown factor.** Any future contention measurement must instrument at
   the Ollama endpoint, not the bridge.
2. **The user has been acting as the gate.** The record's "zero recorded session collisions" is
   evidence of *manual serialization*, not of system safety. It shows up explicitly once:
   session 115 ran two Opus subagents *"serial for the 12 GB VRAM ceiling"* — logged as a build
   note, never as a problem. **A human scheduler has been holding this together, which is
   precisely why no incident exists to trigger the fix.**

Corollary for T-88's trigger discipline: *"observed contention"* is unfalsifiable as a trigger
while a human silently prevents the observation. A trigger that a person can satisfy by hand is
not a trigger.
<!-- /ref:multi-session-contention -->

<!-- ref:multi-session-failure-mode -->
## The failure mode (user, 2026-07-18) — the strongest argument in the record

Ollama's internal queueing does **not** solve this. The sequence:

1. Session A submits a generation; Ollama begins it
2. Session B submits; Ollama queues it
3. **B's deadline expires while B is still queued — B never received a token**
4. B receives a timeout carrying **no information about why**
5. B must choose: retry / rewrite the prompt / switch models / give up and write it itself

**Every one of those choices is wrong**, because the correct action was *"wait, you were second
in line."* And two are actively harmful:

- **retry** appends another entry to the queue
- **switching models** forces a swap, penalizing every client

**The recovery amplifies the contention that caused it.**

### The reframe: the scarce resource is information, not GPU time

This is congestion collapse, and its root cause is a **signalling gap, not a scheduling gap**. A
timeout conflates three unrelated states — *you were queued*, *the model is broken*, *the host is
down* — and the caller must guess between them with no evidence. This is exactly why TCP grew
explicit congestion notification rather than relying on retransmit timers.

**Consequence for M-D4:** a ticket's primary value is **not** "don't hold the transport open."
It is **"return a reason instead of a timeout."** Even a bare refusal — *"busy: qwen3:14b
resident, you want qwen2.5-coder:14b, 1 queued ahead"* — lets the caller decide correctly. A
timeout structurally cannot, no matter how generous.

**This also demotes the "just raise the timeout" objection.** Raising `MCP_TIMEOUT` adds no
information; it converts a fast uninformed failure into a slow uninformed stall, and the session
is idle either way.

### Two deadlines, never one

Conflating these produced an earlier sloppy "120 s cliff" framing. Every client has both:

| | What it is | Claude session | LTG refresh |
|---|---|---|---|
| **Transport ceiling** | hard; exceeding it *kills* the call | ~600 s | unbounded (own process) |
| **Useful-wait horizon** | soft; beyond it, waiting costs more than doing something else | ~30 s | unbounded |

The transport ceiling is a *failure* boundary; the useful-wait horizon is an *economics*
boundary. A Claude session's real constraint is the second — a 4-minute **successful** block is
nearly as bad as a timeout, because the session sat idle. A wait-tolerance contract that models
only the first solves the wrong problem.
<!-- /ref:multi-session-failure-mode -->

<!-- ref:multi-session-t89-scope -->
## What T-89 actually decided (scope, not reversal)

T-89's facade rejection is **correct within its scope and is not reopened.** Its axis is
*interactive vs. batch*: one privileged interactive caller against queued background work, with
priority delivered topologically — sync skips oficina's FIFO and waits only at Ollama's door.

**That mechanism gives no ordering whatsoever between two sync callers.** N sessions all bypass
the FIFO, arrive in undefined order, each demanding a possibly different model, each burning
its own transport deadline while the others swap. *Sync's directness is a priority mechanism
only when exactly one caller uses it.* The doc's own language is singular throughout — *"an
interactive call"*, *"a Claude session's sync `generate_code`"*.

**Conclusion: T-89 answered interactive-vs-batch. The founding question is
interactive-vs-interactive, and was never posed.** T-89 is annotated with this scope limit; its
decision stands.
<!-- /ref:multi-session-t89-scope -->

<!-- ref:multi-session-transport-requirement -->
## The gate's missing axis: admission policy ≠ wait tolerance

The gate (T-88) does not close this either, and the reason is a distinction the gate doc never
draws:

> **Admission policy** = *who goes next*. **Wait tolerance** = *how long a client can wait
> before its transport dies.*

These are independent. A scheduler that gets admission perfect still kills clients on wait
tolerance: a sync `generate_code` waiting **fairly** for four minutes is as dead as one waiting
unfairly. `model-call-gate.md` has no non-goals section and says nothing anywhere about a
client's gate-wait consuming its own transport deadline.

### What this surfaces in the gate's own register

- **G-D2 (DECIDED)** — *"the gate takes hints, not intelligence: **batch submission** with
  model-affinity tags, a priority class, intra-batch order preserved; the gate does admission,
  placement, and cross-client interleaving."*
- **G-D5 (OPEN)** — candidate mechanisms: T-21's shared-directory contract, a broker owning the
  Ollama socket, or *"a **library-level semaphore in ollama-bridge**."*

**G-D5 conflates two independent axes: *mechanism location* and *client contract*.** Where the
coordination state lives (shared dir / broker / in-process library) is orthogonal to what the
caller receives (a blocking wait / a ticket). The register only ever varies the first.

> **Do not overstate this** (advisor correction, 2026-07-18). It is tempting to argue "a
> semaphore cannot implement G-D2, because batching is async by construction." **That is wrong.**
> A library call `results = gate.run_batch([...])` blocks **once on the whole batch** while the
> gate interleaves those calls with other clients' via shared coordination state — a blocking
> contract that *does* interleave. Batching does not force a ticket. The refutable claim sits
> next to the sound one and endangers it.

**The sound claim is wait-tolerance alone, and it is mechanism-independent:** *no* blocking
contract — semaphore, dir-lock, or broker — can bound the wait below the caller's deadline when
the queue ahead contains 14B swaps and multi-minute generations. `gate.run_batch()` might block
five minutes and blow the transport. So the axis the register is missing is
**blocking-vs-ticket (G-D7)**, not "semaphores are incompatible with batching."

### Which forces the client contract to be a handle, not a block

| Contract | Client holds | Bounded by | Viable? |
|---|---|---|---|
| `gate.acquire()` blocks | its transport connection | the client's own deadline (120 s / 600 s) | only if the gate can guarantee wait < deadline — it cannot, with 14B swaps and multi-minute generations |
| gate returns a **ticket** | nothing | nothing | requires the client to have somewhere to park the work |

"Somewhere to park the work" is exactly `submit_run` → `run_id` → ledger → poll/watch.
**oficina's P1 substrate is already the general answer to "how does a client wait for a
contended resource without holding a connection open."**

### Consequence for the altitude split (G-D1) and the extraction trigger (G-D6)

G-D1 frames oficina and the gate as peers at different altitudes, *"queue-of-queues is fine
because the units differ."* If the gate needs handle-based waiting, then oficina's `ledger`,
`fifo`, `workerproc`, `ids`, `store` are not a *peer's* machinery — they are the substrate the
gate needs in order to be async at all. G-D6 names those five modules as generic and says *"do
not extract until the gate is real (second consumer rule)."*

**The transport requirement is the argument that the gate IS the second consumer — it makes
G-D6's own trigger fire.** The altitude split survives (units still differ: runs vs. calls);
what changes is that both altitudes sit on one shared async primitive.

### The payoff: this dissolves the routing problem T-89 left open

T-89 made sync-vs-async a **per-call convention in the caller's head**. But *"is the GPU
contended right now?"* is not knowable by the caller at call time — which is precisely why a
convention is the wrong instrument. **The gate knows.** So admission can be answered instantly
with information the caller never had:

- capacity free → **admit sync**; the caller blocks briefly and gets its answer
- contended, projected wait exceeds the caller's declared deadline → **refuse fast, return a
  ticket**; the caller converts to async

A fail-fast refusal in ~50 ms is strictly better than a hang that dies at 120 s: same outcome,
120 s cheaper, and *actionable*. Note this is **not** the "timeout-redirect hint" T-89 rejected
— that was model-mediated recovery *after* paying for a failed call. This is admission-time
routing *before* paying anything, decided by the component holding the capacity state.

**Synthesis: sync survives, but as a best-effort fast path the gate may decline, rather than an
unconditional bypass.** Interactive priority is preserved — promoted from a topological
accident to a real priority class, which is the only form that works with N interactive callers.

### Corollary: a gate dissolves T-89's actual objection

T-89 rejected the bounded-wait facade because it would **invert interactive priority** — a
facade would put an interactive call behind every queued run in a *priority-less* FIFO. That
reason is contingent on there being no priority mechanism to appeal to.

**Under a gate that owns real priority classes, the objection disappears.** Priority stops
being a property of topology (who skips which queue) and becomes a property the scheduler
holds explicitly. A bounded-wait-then-ticket facade then becomes viable *precisely because the
gate exists* — it was never viable *without* one.

This sharpens M-D2 rather than weakening it: **T-89 correctly answered the no-gate question.**
Its conclusion is sound for the world it was decided in, and the world changes when the gate
lands. That is the difference between a decision being *wrong* and a decision being *scoped*.
<!-- /ref:multi-session-transport-requirement -->

<!-- ref:multi-session-busy-check -->
## M-D4 decomposes into three separable decisions — and the MVP is not the gate

M-D4 as filed bundles three claims of very different cost and confidence. Future sessions should
resolve them **separately**, in this order:

| | Claim | Cost | Needs a gate? | Status |
|---|---|---|---|---|
| **D1** | Wait tolerance is a distinct axis from admission policy (the two-deadline model above) | ~zero — vocabulary | no | **freeze-ready**; carried by G-D7 |
| **D2** | Ticket-vs-block is a **per-client declared property**, not a global async mode | moderate — API shape | no | needs one sub-call, below |
| **D3** | Admission returns **information**, fast | highest | **yes** | proposed; least evidence |

**D2's open sub-call — contract or deadline?** Does a client declare `block | ticket`, or declare
`useful_wait_s: 30` and let the gate derive the contract? *Lean: the deadline.* It is the honest
input (a client knows its own economics, not the right mechanism), and a boolean gives the gate
nothing to reason with — which makes D3 unimplementable. **Blocking is not deprecated:** LTG's
batch refresh *should* block — no other work, no transport ceiling, and a ticket would add
complexity for zero gain. Only clients with something else to do want tickets.

**D3's two corrections** (both from this session, neither in the original M-D4 text):
- **Drop the prediction requirement.** "Projected wait exceeds the deadline" needs generation-
  duration estimates — unreliable, and a rabbit hole. The **structural** signals need no
  estimation and are knowable exactly: *is anything running? is the resident model different from
  the one I want (⇒ swap incoming)? how many are queued ahead?* Conservative refusal on those
  alone is sufficient, and degrades gracefully.
- **The gate must NOT unilaterally convert a call to async.** G-D2 already answers this —
  *client-owns-plan, gate-owns-admission*. The gate returns the verdict plus the reason; **the
  client decides** whether to wait, take a ticket, or do something else. Keeps the gate dumb,
  which G-D2 explicitly wants.

## The MVP is T-21's original busy-check, not the scheduler

**The minimum viable version of D3 is a pre-flight busy-check** — which is exactly what T-21
designed in March, before T-88 superseded it into a full scheduler.

Before submitting, a client asks: *is the GPU busy, and with which model?* If a different model
is resident, don't submit sync — go async. That is:

- no admission control, no queue, no broker, no daemon, no new architecture
- largely readable from Ollama's **existing** `/api/ps` — "which model is resident" covers the
  swap-detection case, which is the expensive one. (PR #9392's `ACTIVE` field would add "is it
  *currently generating*"; **verify the live field set under load — checked 2026-07-18 while idle,
  `models: []`, so the populated shape is unconfirmed.**)
- ~a day of work, not a project
- **and it produces the contention measurement the record lacks, as a byproduct** — the only
  option here that *generates* evidence instead of consuming it

> **Estate lesson — generalization deferred this fix twice.** T-88 superseded T-21 by
> *generalizing* it: busy-check became full scheduler, which made it big enough never to build.
> The same move lost the founding problem statement (clients reframed *sessions*→*products*). The
> busy-check was buildable in March and addresses the failure mode directly; the scheduler has
> been "deserves soon" for four months. **Sibling of the existing corollary in
> `ref:active-decisions`** (*"a deferral whose trigger is guessed will fire on a different
> trigger"*): **a deferral that is generalized may become unbuildable, and take its problem
> statement with it.**

**Recommended sequencing** (supersedes the framing in M-D5 — the question is not "gate before or
after P2 widening"):
1. **Busy-check now** — small, addresses the failure mode, needs no new architecture, produces the
   missing measurement
2. **oficina P2-D1 widening** on its own merits, independently
3. **The gate** when (1)'s data justifies it, designed with D1–D3 already in the register
<!-- /ref:multi-session-busy-check -->

<!-- ref:multi-session-decisions -->
## Decision register

- **M-D1 — the founding problem is multi-session contention: RECOVERED, not new.** The pitch's
  four measured facts are incomplete, not wrong. `vision.md` is amended with a fifth fact rather
  than rewritten. Session 42's framing is restored as the canonical statement.
- **M-D2 — T-89 is scope-limited, not reopened: DECIDED.** Its interactive-vs-batch reasoning
  stands. It is annotated to say it does not address interactive-vs-interactive. Reversal would
  discard a correct result; silence would let the next session read it as settling this too.
- **M-D3 — trigger status: FIRED (user, 2026-07-18).** T-21's "VRAM thrash becomes an observed
  pain point" and T-88's "observed contention" triggers are **met** — the user runs concurrent
  sessions as standing practice. The T-90 finding (desktop VRAM) is a *separate* cause and does
  not bear on this. Session 118's "trigger NOT yet met" note is superseded.
- **M-D4 — transport requirement on the gate: PROPOSED, not decided.** Gate clients that cannot
  tolerate unbounded wait must be able to receive a **ticket** rather than a block. The claim is
  **mechanism-independent**: no blocking contract can bound the wait below the caller's deadline
  when the queue ahead holds 14B swaps and multi-minute generations. Implies (a) G-D5 must add a
  client-contract axis — *any* candidate mechanism needs a ticket path, not just the semaphore
  one; (b) G-D6's extraction trigger fires (a ticket-issuing gate needs oficina's `ledger` /
  `fifo` / `workerproc` / `ids` / `store`); (c) fail-fast admission replaces convention-based
  routing, since the gate holds capacity state the caller cannot. **Open for review before
  freeze.** *(Revised after advisor review 2026-07-18: an earlier draft claimed "a semaphore
  cannot implement G-D2 because batching is async by construction" — refuted, see
  `ref:multi-session-transport-requirement`. `gate.run_batch()` blocks once on the batch and
  still interleaves. Wait-tolerance is the sound axis; batching is not.)*
- **M-D5 — build ordering vs. G-D4: OPEN.** G-D4 (gate vs. oficina-P2-widening priority) was
  open with a mild lean to gate-after-P2, resting partly on the unmet trigger. M-D3 removes that
  support. Not decided here — flagged as materially changed.

## Non-goals (stated, since the gate doc lacks a non-goals section)

- **Not a correctness fix.** Ollama's `refCount` makes concurrent evict-during-generation safe
  (`ollama-eviction-concurrency-findings.md:117-124`). This is availability and latency only.
- **Not preemption.** Interrupting an in-flight model call remains out of scope (V-D13, T-21).
  Queue-ahead, not interrupt.
- **Not multi-user.** The store's bearer-handle authorization model is unchanged; this is one
  user running N sessions.
<!-- /ref:multi-session-decisions -->
