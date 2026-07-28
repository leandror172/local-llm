# oficina P4 — Judge gate + delivery report (plan)

**Status:** REGISTER FROZEN (session 131, 2026-07-27) — P4-D1…P4-D7 all decided with the user.
Run spec delta, acceptance and build steps remain to be written. Sequencing decided this session:
**P4 before P3**, see § "Why P4 before P3".

**Two decisions were reversed during the walk-through, both by reading upstream docs rather than
by new evidence** — recorded because the reversals are the plan's most useful content: **P4-D2**
(`my-codegen-q3` → same-base judge, on `ref:delegate-gpu-policy`'s zero-swap preference, which the
first decision never priced) and **P4-D5** (retire `auto_verdict` → keep it untouched, on first
principle 8, `ref:delegate-evidence-dpo`, and its `frozen-P2` wire status). Both reversals share a
cause worth naming: *the fork was framed from the phase doc alone, and the vision folder had
already priced the trade.*

**Phase source:** `ref:delegate-phasing` § P4. **Vision stances:** S14 (approval gate is the
first question channel), S17 (judge-gates-DPO-labels). **Open vision decision this plan must
answer:** V-D7 (judge cadence + judge persona).

---

<!-- ref:delegate-p4-goal -->
## Goal & scope

P1 made a run survivable, P2 made it converge. Neither made it **legible**. A finished run
today reports `passed` / `auto_verdict` / Delivered and nothing about *what it actually did* —
which is why a run that pasted ~110 lines of its own acceptance tests into a production module
reported success and was believed until a human read the diff (T-119, quantified session 130).

P4 is the layer that turns "the loop terminated" into "here is what changed, here is what a
judge thought of it, and here is what you are being asked to approve."

**In scope:**

- **Phase-2 rubric judge at packaging** — the evaluator's existing LLM-as-judge stage, run on
  the packaged deliverable rather than never. Cadence and persona are P4-D1 / P4-D2.
- **Approval gate (S14)** — one structured pause after assembly ("the criteria/tests I'll hold
  this to"), surfacing as `input_required`. This is the *first* question channel; the general
  model-initiated `blocked` union stays P5.
- **Delivery report** — diff summary, iterations narrative, auto-verdict trail, and
  where/whose/what on failure.
- **Mechanical drift surfacing (T-119)** — the free half of the s130 split: the mechanical
  layer reports *magnitude*, the judge/H1 classifies *scope*.
- **S17 recording** — `auto_verdict`, `curated_verdict` and a judge verdict kept as separate
  fields so P6 can gate DPO extraction on the judge without re-deriving anything.
- **Curated-verdict capture folded into review flow** — an oficina run is judged per-run via
  `run_result` (T-105, session 125); P4 is where that becomes a prompted step rather than a
  convention someone has to remember.

**Explicitly out of scope:**

- **Automatic classification of whether a change was in scope.** T-119's recast is that one
  mechanical detector per observed drift face is a ratchet; the judge classifies, the mechanical
  layer only measures. The demoted detectors stay demoted — trigger is a *second* observed leak
  in any run.
- **P5's full question channel.** S14's gate is a single structured pause at a known point, not
  a model-initiated escape hatch at arbitrary stages.
- **P3's prompt compiler.** P4 consumes whatever assembly produces; it does not reshape it.
- **P6's DPO pair extraction.** P4 *records* what P6 will gate on. It does not extract.

**The founding evidence:** T-119 (`.claude/tasks.md`) — owner P4, no other owner. The delivery
report already promises a diff summary and S17 already names the `auto_verdict` seam at
`loop.py:251`; both are promises with nothing wired to them. P4 is where they get wired.
<!-- /ref:delegate-p4-goal -->

---

## Why P4 before P3

Recorded because the sequencing was deferred from session 130 and decided in 131.

`ref:delegate-phasing` states the licence directly: *"every phase is independently valuable; a
phase may ship and sit — nothing downstream is load-bearing until its own plan says so."*
P4-before-P3 is therefore legal by design, not an exception that needs justifying.

What decided it:

1. **T-119 has owner P4 and no other owner.** It is a measured, live defect on a mode
   (edit runs) that has been in production use since session 126.
2. **P4's promises are already written and unwired.** The diff summary and the S17 seam exist
   as commitments in the phasing doc and as a named seam in code, with nothing behind them.
3. **Curated-verdict capture feeds T-105 Phase 6**, whose carried caveat is that ~81% of calls
   hold no judgment in any form.

**Rejected argument, recorded so it is not re-raised:** that P3 owns a remedy for T-122's
feasibility band via `steps:` (decomposed generation). It does not. The band is the **2×
multiplier on the target file** — in as `current_file`, out as the generated file. Decomposing
the generation task does not stop each step emitting a whole file; only span-confined *output*
removes the multiplier, and that is precisely the M2 reversal session 126 rejected (the model
must emit a precisely-applicable edit language). None of P3's deliverables — prompt compiler,
typed fetchers, LTG retrieve/relate, signature extractor, bounded re-request, `steps:` — shrink
the target's double cost. The strongest honest version of P3's claim is that better context
fetching trims the *tests* term in `(num_ctx − tests − overhead)/2`: real, second-order, and not
a phase-sequencing argument.

**Consequently the T-122 estate sweep is not a tiebreaker and was not run as one.** Its three
remedies route to T-104 (unfired trigger), T-113 (VRAM-blocked) and the admission gate
(T-88/G-D4/T-89) respectively — never to P3. The measurement it asks for is relocated into this
plan under P4-D2, scoped to the judge persona's window, where it answers a question that
actually blocks a decision.

---

<!-- ref:delegate-p4-decisions -->
## Decision register (P4-D) — ALL OPEN

Each entry states the fork, the constraints that bound it, and a recommendation. Freeze on
review with the user; house rule is reverse-only-with-new-evidence once frozen.

- **P4-D1 — Judge cadence (V-D7, first half). DECIDED 2026-07-27 — once at packaging.**
  Once at packaging (lean) vs every K iterations. **Bounded below by S17:** any iteration logged
  as a DPO *chosen* example must pass the judge, whatever the cadence elsewhere — so "never
  during the loop" is only available if no intermediate iteration is ever a chosen example.
  **T-114 collapses most of this fork:** edit runs default to 1 iteration, so packaging *is* the
  only iteration; the question is live only for greenfield (budget 3). Cost side: the judge is a
  second model role on a card that already cannot hold a 14B at 32K (T-113), and per-iteration
  judging multiplies that by the budget.
  *Recommendation:* **once at packaging**, with S17 satisfied by judging the packaged best
  attempt — which is the one that becomes a chosen example. Revisit only if greenfield runs
  start logging intermediate iterations as chosen.

- **P4-D2 — Judge persona (V-D7, second half). DECIDED 2026-07-27 — `my-codegen-q3`.**
  **Acceptance condition attached at freeze:** this measured *fit*, not *judgment quality*. An
  8B classifying "is this diff in scope" is unvalidated, so P4's acceptance must replay the
  T-119 run (`refs/oficina/dy-Bi1nMo5LIqnpzrtXRTw`) and require the judge to catch the leak
  before the gate is trusted. If it cannot, the decision reopens with evidence — not before.
  Genuine tension between two documented positions. `ref:delegate-phasing` § P4 says *same-base
  judge persona for zero-swap* — the coder defaults are `my-python-q25c14-16k` /
  `my-go-q25c14-16k` (qwen2.5-coder:14b), so a same-base judge means no eviction and no reload,
  which matters because Ollama's VRAM split is load-time-stale (session 127) and the GPU is
  contended (T-102). Against that, T-119 §(ii) records that the existing rubric judge is
  designed for the **7–8B tier, one criterion per call, "for reliability at 7-8B"** — a
  different model class with a different prompt discipline.
  **MEASURED session 131** (`.claude/tools/judge-window-sweep.py`, 27-file Python estate,
  `loop.py:_context_overflow` arithmetic, live `/api/show` ceilings):

  | Judge candidate | Size | Ceiling | Holds both artifacts + criterion |
  |---|---|---|---|
  | `my-codegen-q3` (today's `DEFAULT_JUDGE_MODEL`) | 8.2B Q4 | 32768 | **27/27 — 100%** |
  | `my-python-q25c14-16k` (same-base, zero-swap) | 14.8B Q4 | 16384 | 26/27 — 96.3% |

  **The fork the phasing doc framed does not survive the numbers.** It assumed the zero-swap
  same-base judge would be the cheaper resident; in fact the 8B judge carries **twice the
  window** of the 16K coder default and roughly half the weight footprint, so it is both roomier
  and lighter. The only file the 14B judge cannot hold (`server.py`, 15,401 tokens) is one the
  8B holds comfortably. Zero-swap remains a real cost — but it is now a cost paid for a
  *strictly smaller* window, which inverts the argument phasing made for it.
  Also relevant: `my-codegen-q3` is a **7–8B-tier model, matching the rubric's own
  one-criterion-per-call design** (T-119 §(ii)), so the two positions were never actually in
  tension — they only appeared to be while the tier and the window were conflated.
  **DECIDED — a judge persona on the coder's base (qwen2.5-coder:14b), created for the role.**
  *Reversed in session 131 before freeze.* `my-codegen-q3` was chosen first on window and weight,
  then reopened on reading `ref:delegate-gpu-policy`, which states the preference directly:
  *"Same-base persona switching is free (no reload): prefer a judge persona on the coder's base
  (qwen2.5-coder:14b) during packaging; qwen3:14b only where reasoning is the point."* The first
  decision never priced the swap. Re-scored: the 8B/32K judge's fit advantage is **one file out of
  27**, against **one model load per run** that the same-base judge does not pay; and the
  "lighter footprint" argument was weak because judge and coder run sequentially, so resident
  weight barely matters. Exceeding the rubric's designed 7–8B tier is not a defect.
  Cost accepted: a same-base judge persona does not exist yet and must be created
  (`create-persona`, `--num-ctx` 16384 per the s127 VRAM finding).

- **P4-D3 — What the mechanical layer surfaces. DECIDED 2026-07-27 — four metrics, gate on none.**
  The free half of the s130 split. Surfaced at packaging, riding in `run_result` (P4-D6) with the
  full diff in the artifact:

  | Metric | Covers | Mode |
  |---|---|---|
  | `lines_added` / `lines_removed` | gross magnitude | both |
  | `files_touched` | an edit run touching >1 file is itself drift | both |
  | **`hunks` — count + line ranges** | E-D6 (removal hunk) *and* T-119 (addition hunk) | both |
  | `max_verbatim_run_vs_tests` | T-119, the leak specifically | both |

  **Why hunk locality rather than `siblings_intact`.** Three candidates were weighed: (A) parse
  both files and compare top-level definitions, reporting *names*; (B) count baseline lines absent
  from the delivered file; (C) report the diff's hunk count and ranges. **B was rejected** — it
  measures absence only, so it does not detect T-119 (a purely additive defect) at all, and it
  yields a count with no location. **A was deferred, not rejected:** it wants a structural view of
  a source file, which **P3 already owns** (`ref:delegate-phasing` § P3 — *"signature extractor
  when T-77 exists (this system is its second consumer)"*). Building it in the reporting phase,
  one phase ahead of the phase that owns it, either duplicates T-77 or pre-empts it. Recorded so
  it is not re-litigated: the **duplicate-first** convention (`ref:patterns-refactoring-duplicate-first`)
  is a genuine counter-reading — it would say build the second implementation concretely and let
  T-77 extract from two working consumers. It was put to the user and **C was chosen**; when T-77
  lands, upgrading the report to name symbols is additive, not a rewrite.
  **C is also empirically well-suited here:** whole-file edit output is byte-faithful outside the
  change region (s126: a 246-line module returned a **2+/2− diff, 24 siblings byte-intact**; s127:
  a surgical 1-line Go diff), so near-zero is the baseline and a drift hunk stands out rather than
  drowning in reformatting noise.

  **Why this is not the demoted detector (b) under another name.** The computation for
  `max_verbatim_run_vs_tests` is identical to detector (b); only the action differs. It is
  legitimate because the deferral's own trigger — *"a second leak observed in any run"* — is a
  **countable event, and nothing currently counts.** Detecting a second leak today depends on a
  human reading a diff closely enough to notice ~110 pasted lines, which is the path that let the
  first one through. A countable trigger needs a counter; surfacing builds the counter without
  picking a threshold or blocking anything.
  **Honest cost:** this detects nothing. A detector would have blocked the iteration; surfacing
  only makes drift visible to a reader. Under T-114 (edit runs = 1 iteration) the in-loop-feedback
  advantage a detector would have had is largely theoretical — a check firing on iteration 1 ends
  the run either way.
  **Cheap by construction:** `_previous_attempt_view` (T-120) already computes the diff, and every
  input is in scope at `loop.py:384`, one line above `diff_touches_test_files` — the existing
  anti-cheat, which is **the same rule in the opposite direction** (it catches content flowing
  source→tests; the leak flows tests→source).

- **P4-D4 — Approval gate. DECIDED 2026-07-27 — build `input_required`, auto-proceed default ON,
  gate opt-in per run.**
  **P4 builds the state, it does not configure an existing one:** `input_required` occurs **zero
  times** in the oficina source — P2's "declared-but-unreachable" is literal.

  **The binding constraint is queue starvation, not mode.** Assembly runs inside `run()`
  (`loop.py:408`), the FIFO is claim-and-remove (`fifo.py:58`), and there is one worker — so a run
  parked awaiting approval holds the slot and starves everything behind it. This is the failure
  T-111 already demonstrated live (a doomed generation held the FIFO 25+ minutes and starved its
  own replacement), so defaulting a worker-holding pause ON under GPU contention (T-102) repeats
  an observed failure rather than risking a predicted one.
  *Rejected en route:* auto-proceed on for edit / off for greenfield. Wrong axis — under a
  single-worker FIFO **any** defaulted-on gate starves the queue, and the parked run's mode is
  irrelevant to the runs stuck behind it.

  **What the gate displays.** S14 words it as *"criteria/tests I'll hold the code to"*, but under
  P2-D1 tests are caller-supplied, so echoing them back confirms the caller's own input to the
  caller. **Corrected during review (user challenge, 2026-07-27):** context *files and refs are
  caller-declared too* — `_build_stable_parts` (`workspace.py:253`) renders exactly what the spec
  names through the server's `_build_context_block`, and refs can only be **dropped** on failure
  to resolve (T-96 `RefsDropped`), never added. Fetching context the caller did not name is a **P3**
  capability that does not exist. So the honest payload is derived *decisions and numbers*, not
  derived content: **`mode`** (`_detect_mode` — never declared, and it selects the constraint set,
  the E-D9 `num_predict` rule and the T-114 iteration budget), `baseline_failures` at C0, refs
  dropped, resolved `num_predict`/`max_iterations` (`loop.py:410-412`), and the T-112 prompt-vs-
  ceiling fit — the last being where the T-122 envelope becomes visible *before* spend.

  **Why opt-in is the right thinness, and when to revisit.** The payload is thin precisely because
  context is declared rather than derived; it gets rich when **P3** lands and assembly starts
  choosing context on the caller's behalf. A gate showing "what I decided to fetch" is worth
  pausing for; one showing "what you told me to fetch" is not. **Park-and-release (option b) —
  worker returns the run to a waiting state and claims the next — is the recorded shape to build
  when P3 makes the payload worth defaulting ON.** Also rejected: gating at submit time before
  dispatch, which is starvation-safe but discards the assembly results that are the only reason to
  pause.
  **Known weakness, accepted:** an opt-in gate is one nobody opts into, so the fit-before-spend
  display may reach a reader only when they already suspected a problem.

- **P4-D5 — S17 enforcement. DECIDED 2026-07-27 — judge verdict rides `JudgePassed`/`JudgeFailed`;
  `auto_verdict` untouched; P6 enforces the gate.**
  **Retiring `auto_verdict` was proposed and REVERSED at freeze.** The proposal came from a true
  observation — it is a pure restatement of `passed` in the same event (`loop.py:255-259`), adding
  no bits while re-encoding a boolean on the 0/1/2 human verdict scale. Three sources say it is
  load-bearing anyway:
  1. **First principle 8** (`ref:delegate-first-principles`) — *"Per-iteration (prompt, response,
     auto-verdict) rows; the accepted iteration vs its failed predecessors are natural DPO pairs
     — gated by the judge rule."*
  2. **`ref:delegate-evidence-dpo`** — it is *deliberately* the cheap, gameable signal: *"models
     game narrow tests… The cheap per-iteration signal (tests) is precisely the most gameable one,
     and it is what would feed 'chosen' labels → S17: the judge gates every DPO chosen label —
     integrity costs one judge call per delivered run, not per iteration."* (Which also re-derives
     P4-D1 independently.)
  3. **`IterationEvaluated` is `frozen-P2`** (`ref:delegate-event-model`) — a wire format whose
     freeze ladder defines change as breaking.

  **So T-119 is not a naming defect; it is the gate that was specified and never built.** The
  design anticipated exactly this failure four months before it occurred. `auto_verdict` exists to
  *name the gameable signal at the seam where the gate attaches*; deleting it would delete what S17
  gates. The delivery report must label it as **tests-green**, never as a quality verdict.
  **Enforcement:** P4 emits the already-drafted `JudgePassed`/`JudgeFailed` events at packaging;
  P6 gates DPO extraction on them. By P4-D1 the judge runs once at packaging, so the set of
  judge-verdicted iterations is exactly the set of packageable candidates — the rule *"chosen only
  if judge-passed"* is checkable by construction rather than by convention.

  **T-99's deferred revisit, answered (it said: "revisit the join mechanics at P4").** The
  ledger↔calls join is keyed on `run_id`, which is per-run, so per-iteration matching is
  **order-based**. That is the positional fallback T-105 banned — *"when identity is unknown, stay
  silent; a positional fallback names the wrong call, and mislabeled is worse than missing"*
  (`ref:active-decisions`). The two were never connected because they live in different documents.
  **Fix: thread `call_id` through `GenerationResult`** (`worker.py:34-40` carries `content`,
  `model`, `eval_count`, `duration_ms` and no identity, while `client.py:324` mints a fresh
  `call_id` per record), making the join identity-based.

- **P4-D6 — Delivery report: artifact + pointer. DECIDED 2026-07-27 — largely pre-decided upstream.**
  Not a genuine fork: `ref:delegate-architecture`'s run store is already
  `runs/<id>/{spec.json, events.jsonl, iters/NN/*, report.md, workspace ref}`, and
  `ref:delegate-event-model` defines `RunResult` as the read model behind `run_result` — *"report
  + deliverable location"* — with a constraint neither the phasing doc nor this plan had recorded:
  **it stays resolvable after workspace artifacts are pruned (V-D9).** So the report is a durable
  artifact and the pruner must not orphan it.
  **P4-D3's four metrics ride in the `RunResult` payload; the full diff stays in the artifact** —
  which is what makes the summary cheap to read in Claude's context and complete on disk.

- **P4-D7 — Failure report: format only. DECIDED 2026-07-27.**
  Also narrower than drafted: the `Failed` event payload is **already** the where/whose/what triad
  and is `freeze-at-P1` (`ref:delegate-event-model`), and P2 already ships rule-based failure
  classification. P4 formats what exists. Extending classification in the phase that owns
  *reporting* is how a reporting layer grows a second brain.
<!-- /ref:delegate-p4-decisions -->

---

## Run spec delta over `ref:delegate-run-spec`

**Two fields, and one existing field becomes load-bearing.** P4 is mostly *activation*, not new
surface: it plugs in two sockets P1/P2 deliberately left unplugged — `input_required` (zero
occurrences in the oficina source) and `acceptance.rubric` (already in the draft run spec;
`intake.py:48`'s docstring reads *"`rubric` (Phase-2 judge) is P4, not here"*).

```yaml
acceptance:
  rubric: <evaluator rubric>   # EXISTING field, becomes load-bearing (P4-D1: runs once at packaging)
judge_model: auto | <persona>  # NEW. `auto` derives the same-base judge for the resolved coder
                               #      (P4-D2 zero-swap); mirrors the existing `model:` shape
approval_gate: false | true    # NEW. Default false (P4-D4: opt-in, single-worker FIFO starvation)
```

**Cadence is deliberately NOT a field.** P4-D1 fixes it at once-at-packaging, and
`ref:delegate-evidence-dpo` prices it there (*"integrity costs one judge call per delivered run,
not per iteration"*). A knob would invite per-iteration judging, whose cost the evidence already
rejected. **Design check for the build: if this delta grows, that is the signal P4 is designing
past its phase.**

Nothing in P4-D3 (report metrics), P4-D5 (`judge_verdict`), P4-D6 (report location) or P4-D7
(failure formatting) touches the spec — they are event, artifact and report concerns.

## Acceptance (from `ref:delegate-phasing` § P4, made concrete)

**A1 — the real defective deliverable, replayed.** The T-119 run is reachable at
`refs/oficina/dy-Bi1nMo5LIqnpzrtXRTw` (`cd852fa`), so acceptance runs against a *measured* defect
rather than a synthetic one. Required: the delivery report makes the leak legible to a reader —
a large addition hunk and `max_verbatim_run_vs_tests` ≈ 77 against a legitimate baseline of 4 —
**with no detector firing**, and the judge classifies the change as out of scope.

**A2 — the negative control, and it is not optional.** On a clean run (s126's baseline: a
246-line module, 2+/2− diff, 24 siblings byte-intact) the same metrics must be quiet and the
judge must pass. This is first principle 6 made testable: *"A signal that fires unconditionally
carries zero bits."* A1 without A2 would accept a report that always cries drift.

**A3 — events fold, and old clients survive.** `JudgePassed`/`JudgeFailed` and
`ApprovalRequested` appear in the ledger and fold to the right public state; a P1-era fold
tolerating unknown event names is exercised, per the envelope's forward-compatibility rule.

**A4 — the report outlives the workspace.** After a retention prune, `run_result` still resolves
the report (`ref:delegate-event-model`'s `RunResult` constraint, V-D9). Guards the D6 split from
a pruner that orphans `report.md`.

**A5 — S17 has something to gate on.** The packaged iteration carries a `judge_verdict` distinct
from `auto_verdict` and `curated_verdict`, and — per the T-99 revisit — the ledger↔calls join
resolves by `call_id` rather than by order.

**A6 — failure path.** An exhausted run's report states where/whose/what from the existing
`Failed` payload, with the best attempt attached (`Exhausted` maps to public `failed`, **not**
`Delivered` — the s124 correction in `ref:delegate-event-model`).

### OPEN — surfaced while writing A3: the gate can pause but nothing can resume it

P4-D4 builds `input_required`, but the only mechanism that clears it, `answer_run`, is **P5**
(`ref:delegate-mcp-surface`). So as decided, P4 can enter a state it cannot leave. Three ways
out, none chosen — **this needs a call before the gate is built**:

- **(a) Ship the field, defer the state.** `approval_gate` is accepted and validated at intake but
  rejected as unsupported until P5. Honest, keeps P4 small, and costs nothing since the default is
  `false`. Leaves S14 unfulfilled another phase.
- **(b) Pull a minimal resume forward** — an `approve_run(run_id)` narrower than `answer_run`
  (no payload, just proceed/abort). Small, but it puts a second resume verb on the MCP surface
  that P5 must then reconcile with `answer_run`.
- **(c) Pull `answer_run` itself forward** from P5. Cleanest vocabulary, largest scope increase,
  and it drags the `blocked` schema-union question with it.

Leaning **(a)**: D4 already accepted that an opt-in gate may never be opted into, and the payload
is thin until P3 makes assembly derive context. Building an unresumable state to satisfy a
default-off flag is the worse trade.

## Build steps (TDD-ordered — NOT started; awaiting explicit go-ahead)

Two standing conventions govern the whole sequence:

- **Compose the evaluator, do not reimplement it.** Phase 2 rubric judging already exists in
  `evaluator/lib/benchmark.py` (one criterion per call). T-104's lesson is exactly this class of
  mistake — *"oficina composes the ollama-bridge tools; it does not reimplement them"*, where
  `loop.py`'s bespoke `write_text` silently dropped `patch_file`. The judge stage consumes the
  evaluator as-is, per `ref:delegate-architecture`.
- **Inject the judge behind a seam, like `GenerateFn`.** P2 made the coder an injected callable so
  the loop is testable without a GPU, and T-112 did the same for `/api/show`. The judge gets the
  same treatment, so every step below has network-free tests.

| Step | Delivers | Notes |
|---|---|---|
| **T1** | Revise `event-model.md`; promote `JudgePassed` / `JudgeFailed` / `ApprovalRequested` from `draft-P4` | **Fixed by process, not choice** — that file states its own protocol: *"Each phase plan revises this artifact first, then promotes its events to frozen."* Adding events is safe by design: the envelope requires folds to tolerate unknown event names, which is what lets these land without breaking P1 clients |
| **T2** | The same-base judge persona | `create-persona`, `--num-ctx 16384` per the s127 VRAM finding. Infra, not code; blocks live runs, not tests (T1 seam) |
| **T3** | `call_id` threaded through `GenerationResult` | Small, independent, and it closes T-99's deferred join question + the T-105 positional-fallback hazard. Early because nothing depends on it and it de-risks A5 |
| **T4** | The four P4-D3 metrics computed at packaging | `hunks`, `lines_added/removed`, `files_touched`, `max_verbatim_run_vs_tests`. Reuses `_previous_attempt_view`'s diff; inputs already in scope at `loop.py:384` |
| **T5** | Judge invocation at packaging + `JudgePassed`/`JudgeFailed` + `judge_verdict` recorded | Depends on T1 (events) and T2 (persona for live runs) |
| **T6** | `report.md` artifact + `RunResult` payload carrying T4's metrics and a pointer | Depends on T4 and T5. Must satisfy A4 (survives pruning) |
| **T7** | Failure-report formatting from the existing `Failed` payload | Format only (P4-D7). No new classification |
| **T8** | Approval gate (`input_required`, `ApprovalRequested`, `approval_gate` field) | **BLOCKED on the open acceptance question** — as decided, P4 can enter `input_required` and nothing can clear it (`answer_run` is P5). Resolve (a)/(b)/(c) before starting |
| **T9** | Acceptance A1 + A2 against the replayed T-119 run | A2 (the negative control on a clean run) is not optional — first principle 6 |

**Carried watch-item, due here:** `event-model.md`'s medium-decision record parks **EventCatalog**
with *"Revisit at P4 (delivery-report format) or first external consumer."* P4 is that revisit.
Default expectation is still no — it is an event *dictionary*, and this plan's output is a
per-run narrative — but the trigger has fired and should be answered rather than left standing.
