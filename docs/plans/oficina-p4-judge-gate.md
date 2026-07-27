# oficina P4 — Judge gate + delivery report (plan)

**Status:** AUTHORING (session 131, 2026-07-27). Decision register is OPEN — nothing here is
frozen. Sequencing decided this session: **P4 before P3**, see § "Why P4 before P3".

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

- **P4-D1 — Judge cadence (V-D7, first half). OPEN.**
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

- **P4-D2 — Judge persona (V-D7, second half). OPEN. Blocked on a measurement.**
  Genuine tension between two documented positions. `ref:delegate-phasing` § P4 says *same-base
  judge persona for zero-swap* — the coder defaults are `my-python-q25c14-16k` /
  `my-go-q25c14-16k` (qwen2.5-coder:14b), so a same-base judge means no eviction and no reload,
  which matters because Ollama's VRAM split is load-time-stale (session 127) and the GPU is
  contended (T-102). Against that, T-119 §(ii) records that the existing rubric judge is
  designed for the **7–8B tier, one criterion per call, "for reliability at 7-8B"** — a
  different model class with a different prompt discipline.
  **The measurement this needs** (the relocated T-122 sweep, scoped): a packaging judge must
  hold **both** artifacts — the baseline and the delivered file — plus its rubric criterion.
  Context is the binding constraint on this hardware (T-112, T-122), so the question "does the
  judge fit?" is answerable and unanswered. Sweep real source files against the candidate judge
  persona's live `/api/show` ceiling, reusing the `_context_overflow` arithmetic from T-112
  rather than re-deriving it.
  *Recommendation:* measure first, then choose. Prior leans same-base-14B on zero-swap grounds,
  but not before the window number exists.

- **P4-D3 — What the mechanical layer surfaces. OPEN.**
  The free half of the s130 split. Candidates for the diff summary: lines added/removed, files
  touched, siblings-byte-intact count, and **longest contiguous verbatim run against the declared
  `test_files`** — the exact quantity that made T-119 measurable (77 lines observed against a
  max-4 legitimate baseline across all 14 `oficina` source↔test pairs, ~20× separation).
  **The distinction that keeps this from being the demoted detector:** surfacing a number in a
  report is not gating on a threshold. The fallback detector (b) was deferred on n=1 with a
  countable trigger; reporting the metric neither blocks a run nor picks a threshold, and it
  makes the *second* occurrence — the trigger — observable rather than dependent on someone
  re-reading a diff.
  *Recommendation:* surface all four, gate on none. Cheap: `_previous_attempt_view` (T-120)
  already computes the diff, and every input is in scope at `loop.py:384`.

- **P4-D4 — Approval-gate default under async-first routing. OPEN.**
  S14 specifies one structured pause after assembly with auto-proceed configurable, and the user
  confirmed the stance. But T-89's routing default was revised in session 126 to **async-first,
  small edits included** — so a pause means the run parks in `input_required` and waits for a
  session that may be doing something else. Sub-question: does the gate apply to edit runs
  (1 iteration, fast, usually a known target) the same as greenfield?
  *Recommendation:* auto-proceed **on** by default for edit runs, **off** for greenfield — the
  gate's value is highest where the criteria are least obvious, and greenfield is where the run
  is inventing them.

- **P4-D5 — Where S17 is enforced, and what P4 records. OPEN.**
  Established fact (verified session 130): `auto_verdict` is written to **ledger events only**
  (`loop.py:259,273`); an oficina run's real training label is the per-run curated verdict via
  `run_result`. So there are two fields today and S17 needs a third — the judge's own verdict —
  or it has nothing to gate on. Fork: enforce at ledger write, at packaging, or at DPO
  extraction (P6).
  *Recommendation:* **P4 records `judge_verdict` as a third, separate field; P6 enforces the
  gate.** Keeps extraction's policy in the phase that owns extraction, and matches S17's own
  wording that the three verdict kinds stay distinct fields.

- **P4-D6 — Delivery report: payload or artifact? OPEN.**
  `run_result` is the MCP surface Claude reads, and a verbose report inside a tool result is paid
  for in Claude's context every time. Fork: the report *is* the `run_result` payload; or it is an
  artifact in the run dir that `run_result` summarises and points to.
  *Recommendation:* artifact + summary pointer, mirroring the `output_file`/`output_only` pattern
  the bridge already established — the full narrative is worth keeping and rarely worth reading
  in full.

- **P4-D7 — Failure report: format or extend? OPEN.**
  Phasing promises where/whose/what on exhaustion. P2 already ships rule-based failure
  classification (mechanical/structural/conceptual). Fork: P4 formats what P2 classifies, or P4
  extends the classification.
  *Recommendation:* format only. Extending classification in the phase that owns *reporting* is
  how a reporting layer grows a second brain.
<!-- /ref:delegate-p4-decisions -->

---

## Run spec delta over `ref:delegate-run-spec`

TO BE WRITTEN at freeze — depends on P4-D1 (cadence field), P4-D4 (gate/auto-proceed field) and
P4-D5 (`judge_verdict` field).

## Acceptance

TO BE WRITTEN at freeze, from `ref:delegate-phasing` § P4 made concrete. Anchor candidate: the
T-119 run is replayable from `refs/oficina/dy-Bi1nMo5LIqnpzrtXRTw` (`cd852fa`), so P4's
acceptance can be stated against a **real** defective deliverable rather than a synthetic one —
the delivery report for that run must make the leak visible to a reader without a detector
firing.

## Build steps

TO BE WRITTEN at freeze (TDD-ordered, like P1's T1–T10 and P2's build steps).
