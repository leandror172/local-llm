# oficina P4 — Judge gate + delivery report (plan)

**Status:** BUILT + ACCEPTED (session 131, 2026-07-27/28) — T1–T9 complete, acceptance A1–A6 all
pass, PR #86 open. **P4-D1…P4-D11 frozen** — D8–D11 come from the post-build code review
(2026-07-28) and were decided the same day; D11 is deferred with a named trigger. Sequencing
decided in session 131: **P4 before P3**, see § "Why P4 before P3".

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
## Decision register (P4-D) — D1–D10 FROZEN

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
  | **`hunks` — count + line ranges** | E-D6 (removal hunk) *and* T-119 (addition hunk) | both |
  | `max_verbatim_run_vs_tests` | T-119, the leak specifically | both |
  | ~~`files_touched`~~ | **DROPPED at build time — see below** | — |

  **`files_touched` dropped (T4, session 131).** It was listed at freeze and removed when the
  build reached it, because in the current write model it cannot discriminate: the loop writes
  exactly one file (the target), and anti-cheat already rejects any iteration that touches a
  declared test file — so the metric would read `1` on every non-cheating run. **First principle 6
  is explicit** (`ref:delegate-first-principles`): *"A signal that fires unconditionally carries
  zero bits. Every warning/verdict/status in this system must discriminate."* Shipping it would
  also spend payload on nothing, and the D6 correction makes payload size a hard constraint.
  **Revisit when multi-file deliverables exist** — that is the change that makes it discriminate,
  and it is a countable trigger rather than a guessed one.

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

- **P4-D4 — Approval gate. DECIDED 2026-07-27, then AMENDED the same day — the *policy* is
  decided here, the *state* defers to P5.**
  **AMENDMENT (a), from writing acceptance A3:** the original decision was "build `input_required`,
  auto-proceed default ON, gate opt-in per run". Writing A3 exposed that nothing could clear the
  state — `answer_run` is P5 — so P4 would have built a state it could not exit. P4 now ships
  `approval_gate` as a recognized key, rejects `true` at intake naming P5, and re-tags
  `ApprovalRequested` to `draft-P5`. Everything below stands as the *reasoning that fixes the
  policy* for whenever the state is built; only the build scope shrank.
  **The state genuinely does not exist yet:** `input_required` occurs **zero times** in the
  oficina source — P2's "declared-but-unreachable" is literal.

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

- **P4-D6 — Delivery report location. CORRECTED 2026-07-27 against the as-built code — the report
  lives in the `Delivered` event payload. There is no report artifact.**
  **The original decision here was wrong.** It read `ref:delegate-architecture`'s run-store sketch
  (`runs/<id>/{… report.md …}`) as the built shape and chose "artifact + pointer". That sketch is a
  vision draft. The invariant is recorded in the vision folder's `KNOWLEDGE.md`:

  > **Report location:** the delivery report lives in the `Delivered` event payload
  > (`events.jsonl`, `ledger: forever`) — **NOT** in `artifacts/`. This is what keeps `run_result`
  > answerable after retention prunes the workspace.

  **Verified in code, not taken on trust:** `service.result()` reads `delivered.get("report")`
  directly from the `Delivered` payload (`service.py:148-153`), and `artifacts_pruned` is a flag on
  the very same result — because artifacts are exactly the thing that does *not* survive.
  So the goal I derived independently for A4 (survive pruning) was right, and the mechanism I chose
  was the opposite of the one already built and already justified.

  **What this settles:** P4-D3's four metrics ride in the **`Delivered` payload's report**. No new
  storage, no pruner coordination.
  **What survives from the original reasoning:** the context-cost concern. A payload-resident report
  is paid for in Claude's context on every `run_result`, and there is no pointer indirection to hide
  behind — so **compactness is a hard content constraint, not a preference.** Metrics are numbers
  and ranges; the diff itself is never inlined (it is reconstructible from the run branch, which
  `refs/oficina/<run_id>` now pins — T-118 R-D2).

  **Process note:** three documents (phasing, architecture, the event model) were consulted and all
  three left this wrong; the folder's `KNOWLEDGE.md` had it right. As-built truth lives in the
  memory files — read them before editing, not after.

- **P4-D7 — Failure report: format only. DECIDED 2026-07-27.**
  Also narrower than drafted: the `Failed` event payload is **already** the where/whose/what triad
  and is `freeze-at-P1` (`ref:delegate-event-model`), and P2 already ships rule-based failure
  classification. P4 formats what exists. Extending classification in the phase that owns
  *reporting* is how a reporting layer grows a second brain.

### Post-build review (2026-07-28) — three findings that are DESIGN forks, not defects

A full-branch review after T9 raised 13 findings. Ten are ordinary defects with obvious remedies
and are tracked as build follow-ups. **Three are decisions this register never took** — recorded
here rather than settled inside a fix commit, because a register amended silently by fixes stops
recording what was decided and starts recording what survived. That is the drift P4-D6 already
caught once. **All three DECIDED 2026-07-28 with the user, walked in the order D8 → D9 → D10** —
each one collapsed part of the next, which is why the order mattered: D8's min removed the only
possible consumer of `weight`, and D9's per-criterion cut settled the ownership half of D10.

- **P4-D8 — The report's second number. DECIDED 2026-07-28 — `judge_verdict` is the MIN of the
  scored criteria; `0` when none scored.**
  **The build shipped two summaries of one evidence set, computed by different rules.** `passed` is
  `_all_criteria_pass` — every criterion ≥ its cut, a **conjunction of gates** — and it handles the
  unscoreable case correctly (*"a gate that cannot see is not a gate that passes"*). `judge_verdict`
  was `_mean_score` — an **unweighted arithmetic mean over the criteria that actually scored**. Both
  rode in the same `Judged` payload with nothing marking which was authoritative.
  **Measured on the real criterion shapes:** `scope_adherence 2` beside `objective_met 5` →
  `passed False`, **`judge_verdict 4`**; the worst expressible case, `scope_adherence 1` beside
  `objective_met 5`, still yields **3**. The mean cannot fall below a cut of 3 however badly scope is
  violated, so long as one criterion is clean. Worse, one *unparseable* criterion beside a 5 yields
  **`judge_verdict 5`** on a run whose gate withheld — pinned today by
  `test_unparseable_output_scores_none_rather_than_guessing`. Note the tell: `_mean_score`'s
  docstring has to *explain away* the unscoreable case ("the criteria that actually scored"), while
  `_all_criteria_pass` twelve lines below absorbs it into the rule — `None` simply is not `>= 3`.
  A special-case comment is the residue of an accident, not its justification.
  **This is the thing P4-D5's own argument rules out.** § RESULTS ¶3: *"A single blended quality
  score would have averaged that into a pass; splitting the question is what makes the gate work."*
  The split was built — and a blended score shipped beside it.
  **Why it was live and not cosmetic:** S17 gates DPO *chosen* labels on judge-passed, and **P6 —
  the consumer — does not exist yet**, so whichever field the report makes prominent is the one P6
  would have been written against. A P6 pass keying on `judge_verdict >= 3` inverts S17 silently,
  and nothing in the payload would flag it.
  **DECIDED — the min.** It cannot disagree with `passed` by construction, it carries the
  split-questions property into the single number, it stays on the rubric's own 1–5 scale (legible
  to a human reading the report), and payload cost is unchanged. **`0` when ANY criterion is
  unscored:** 0 is already this codebase's "no verdict" sentinel (the judge-error path sets it), it
  sits provably outside the 1–5 value space — the condition `ref:patterns-code-value-or-error`
  requires before a sentinel is legitimate — and it matches T-105's *when identity is unknown, stay
  silent*.
  **SHARPENED AT BUILD TIME — the freeze wording would have left the hole open.** This entry first
  read *"0 when **none** scored"*. `test_unparseable_output_scores_none_rather_than_guessing` shows
  that is one rung too narrow: with one criterion unparseable and one scoring 5, a min over *the
  criteria that actually scored* is `min([5]) == 5` — the same 5 the mean reported, on a run whose
  gate withheld. **The defect was never mean-vs-min; it was that both reduce over a FILTERED
  subset.** `passed` already fails on any `None`, so the number agrees with it only if an unscored
  criterion drags the verdict below every cut. Same lesson as the tell above: the unscoreable case
  belongs in the rule, not in a docstring explaining it away.
  **A SECOND gap of the same shape, found immediately after the first fix shipped:** `all([])` is
  True while `_min_score([])` is 0, so a rubric with no phase-2 criteria reported `passed: True`
  beside `judge_verdict: 0`, having judged nothing and called no model — **the invariant this entry
  asserts, violated by the very commit asserting it.** The post-build review had filed this
  separately as an ordinary defect; it is not separate, it is D8's other half, and
  `_all_criteria_pass` now requires a non-empty criterion set. Worth recording as calibration: two
  of the three holes in "the number and the boolean cannot disagree" were invisible from the
  decision text and only appeared against the code — a frozen invariant is a claim to re-derive at
  build time, not a conclusion to carry forward.
  *Rejected — drop the field entirely:* the per-criterion scores are already in the payload, so a min
  is derivable and the field is redundant. But P4's goal text keeps the three verdicts separate *"so
  P6 can gate DPO extraction on the judge **without re-deriving anything**"*, and dropping it forces
  exactly that re-derivation.
  *Rejected — keep the mean:* it is the conventional "overall quality" number and matches
  `evaluate.py`'s `percentage`. That is precisely the **greenfield** framing — an aggregate over
  independent qualities. P4's question is a **conjunction**, and a conjunction has no average.
  **Recorded upgrade, with a countable trigger.** A strictly better number exists once per-criterion
  cuts diverge (P4-D9): the **margin**, `score(c) − passing_score(c)`, minimised across criteria.
  `passed ⟺ min(margin) ≥ 0` still holds, and it distinguishes a 4 against a cut of 4 (barely
  passing) from a 4 against a cut of 3 (comfortable), which a raw min cannot. **Not built now**
  because both cuts are 4 today, so margin is `score − 4` uniformly: identical ordering, zero new
  information — and it would add a **fourth** verdict scale, running negative, beside `auto_verdict`
  0/1/2, `curated_verdict` 0/1/2 and `judge_verdict` 1–5. **Trigger: the first rubric in which two
  criteria declare different `passing_score` values.** Building it before that is designing from a
  prediction (`ref:patterns-refactoring-duplicate-first`).

- **P4-D9 — The passing cut. DECIDED 2026-07-28 — the cut moves INTO the rubric as a per-criterion
  `passing_score`; `oficina-edit` declares 4 on both criteria; the scale text is untouched.**
  **REVERSED during the walk-through — by reading the rubric rather than the finding's quoted line.**
  The review reported that rung 3 of `scope_adherence` (*"the requested change plus a small
  unrequested edit a reviewer would ask to remove"*) sits above `_PASSING_SCORE = 3`, and the first
  recommendation recorded here was to **rewrite that rung**. Reading **both** ladders side by side
  shows the scale is not what is wrong:

  | | `scope_adherence` | `objective_met` |
  |---|---|---|
  | **4** | + a *trivial incidental* edit (whitespace, import ordering) | implements it; a *minor* stated requirement missing |
  | **3** | + a small unrequested edit *a reviewer would ask to remove* | partial; a *major* stated requirement missing or wrong |

  **Rung 4 is the lowest acceptable rung in BOTH ladders, and rung 3 in both describes something a
  reviewer would send back.** The rungs are a coherent, well-ordered severity ladder with the
  boundary drawn in the same place twice — that consistency is evidence the *scale* is right, and a
  single number sitting one rung off is the likelier and cheaper error. This entry originally
  claimed raising the cut would over-tighten `objective_met` *"where 3 may be legitimately passing"*;
  that was **wrong**, and reading the ladder is what showed it — `objective_met: 3` is *a major
  stated requirement missing or wrong*. **A scale and a threshold are two halves of one statement
  ("which rungs pass?"); when they disagree, ask which half is wrong rather than assuming it is the
  one you looked at first.**
  **The fix is free, which the rewrite would not have been.** Changing the cut does not touch the
  prompt, so judge behaviour is unchanged and **A1/A2 hold without re-measurement**: A1 (`2, 5`)
  fails under ≥3 *and* ≥4; A2 (`5, 5`) passes under both. The pre-T9 probe that scored a smaller
  synthetic leak **3** — § RESULTS' unresolved calibration note — now correctly **fails**, closing
  it. Rewriting scale text would have re-opened both acceptances, since scoring-scale text *is* the
  prompt template (`evaluator/.memories/KNOWLEDGE.md` § "Rubric YAML Format").
  **Why per-criterion rather than a global constant or a per-rubric key.** A cut is a claim *about a
  scale*; the scale is per-criterion, so that is where its referent lives. Keeping it in code leaves
  the two halves of *"which rungs pass?"* in different files with nothing holding them together —
  and that divergence is **not hypothetical here: it is exactly what produced this finding**
  (`ref:corpus-divergence-pattern`, now instantiated inside P4 itself). A per-*rubric* key is one
  number against N ladders — a smaller copy of the same mismatch.
  *Weak argument deliberately NOT relied on:* "different criteria might want different bars." Both
  ladders break at 4, so as a **knob** the field has exactly one value, and
  `ref:patterns-code-extract-keep-divergence` rule 3 would reject it as speculative generality. The
  justification is **co-location, not variation** — first principle 6 governs *signals that must
  discriminate*, whereas a field whose purpose is adjacency carries value at zero variance.
  **Default: `_DEFAULT_PASSING_SCORE = 3` for criteria that do not declare one.** The six other
  shipped rubrics' ladders have not been read, so imposing 4 on them would be the same unexamined
  assumption in the other direction. Verified safe: `evaluate.py`'s `load_rubric` asserts only
  `id`/`criteria`/`name`/`phase`/`weight` and **does not reject unknown keys**, so `passing_score` is
  invisible to the benchmark path.
  **Build guard, non-optional.** `weight` on this very file is already a per-criterion number nobody
  reads (P4-D10). A second one must not join it: `passing_score` has to be genuinely consumed by
  `judge.py`, pinned by a test in which a criterion scoring **below its declared cut fails the
  gate**.

- **P4-D10 — `weight` in `oficina-edit.yaml`. DECIDED 2026-07-28 — DELETE it, and record why it
  could never have worked.**
  The *ownership* half of this fork is settled by P4-D9: the cut moves to the rubric. What remained
  was `weight: 3.0`, declared on both criteria and **never read by `judge.py`**, while
  `evaluator/lib/evaluate.py:75` *asserts* it is present and aggregates via `weighted_average` —
  one YAML file meaning two different things to its two readers, with tuning a weight silently
  changing nothing on the oficina path. It is also the one place the build crossed the boundary it
  declared: *"compose the evaluator, do not reimplement it"* (T-104) was honoured for rubric loading
  and for prompts, and **aggregation was re-derived with different semantics**.
  **The fork "make `judge.py` honour it" is not merely unattractive — it is impossible.** Under
  P4-D8 `passed` is a conjunction, and **no weighting makes an average agree with an AND.** With
  both cuts at 4: `(4,4)` passes and scores `4(w₁+w₂)`; `(5,3)` fails and must rank below it,
  requiring `w₁ < w₂`; `(3,5)` also fails and requires `w₂ < w₁`. Contradiction, for every possible
  pair of weights. So `weight` is not just unused on this path — it is **unusable** for it. That is
  a far stronger reason to delete it than "nothing reads it".
  **One reader, not two — structurally shared, semantically private.** The file lives in
  `evaluator/rubrics/` and `load_rubric` takes a path, so the benchmark path *can* load it; but its
  criteria instruct the judge to *"consult the drift metrics in the prompt"*, which only oficina's
  `_judge_user_prompt` supplies. Run through `evaluate.py` it loads and cannot mean anything.
  **Accepted cost:** deleting `weight` makes `evaluate.py` refuse the file — correct in outcome, but
  for a **misleading stated reason** (a missing weight, rather than "this rubric needs drift metrics
  you do not supply"). Mitigated by an in-file comment carrying the real reason, so whoever hits the
  assertion reads it two lines above. **Making the assertion itself smarter is out of scope on this
  branch:** `evaluator/` has **zero automated tests** (`evaluator/.memories/QUICK.md`), so touching
  `evaluate.py` requires a characterization pass first
  (`ref:patterns-refactoring-characterize-first`) — the convention acting as a real scope boundary
  rather than as advice.
  *Rejected — keep it, documented as evaluator-only:* zero-risk, but P4-D9 adds `passing_score`
  directly beside it, leaving **two adjacent per-criterion numbers, one live and one inert**, with
  nothing on the page distinguishing them. That is the confusion this entry exists to remove, made
  worse rather than better.
  *Rejected — move the file out of `evaluator/rubrics/`:* the evaluator's KNOWLEDGE.md records that
  a new rubric file is *"the sanctioned extension — no code change was needed"*. P4 got its rubric
  without touching untested code; moving it now spends that advantage to restate what a comment
  already says.

- **P4-D11 — Per-criterion `call_id` on judge calls. DEFERRED 2026-07-28 — not built, trigger
  named. (`run_id` fixed the same day; that half was a defect, not a fork.)**
  P4-T3 threaded `call_id` for the **coder** because the ledger↔`calls.jsonl` join would otherwise
  be order-based — the positional fallback T-105 banned. The judge is the same fork one level down:
  a run makes **N judge calls, one per criterion**, and `Judged` carries a `criteria[]` array with
  no ids.
  **What is already recoverable without it.** With `run_id` fixed, every judge call for a run is
  findable, and each call's prompt *names its criterion* — `_judge_system_prompt` renders
  `Criterion: {name}`, `_judge_user_prompt` ends *"Score the output on the criterion: **{name}**"*.
  Within one run criterion names are unique, so **`(run_id, criterion_name)` is a genuine composite
  key**, not a positional guess. Its weakness is that it is *content-derived*: recovering the name
  means parsing prompt text, which breaks silently if the wording changes.
  **No consumer needs it yet.** P6 gates DPO extraction on `passed`, not on judge-call identity,
  and a DPO pair is (coder prompt, coder response) — **the judge call is the gating signal, not a
  pair**. Judge-quality DPO (fine-tuning the judge itself) would need it, but no phase owns that,
  so building for it now is designing from a prediction
  (`ref:patterns-refactoring-duplicate-first`).
  **The hazard — recorded because the cheap route is the banned one.** The seam is
  `chat(system, prompt, schema) -> str`; there is no channel for an id to come back through.
  Collecting ids side-band inside `default_judge` preserves the seam but then matches ids to
  criteria **by order** — the exact fallback T-105 banned, reintroduced in the one module whose
  docstring cites T-105 as its reason for existing. Doing it properly means changing the seam's
  return type (`judge_deliverable`, `_score_criterion`, `_FakeChat`, `default_judge`).
  **Trigger: the first consumer that needs to name an individual judge call.**
  *Shipped instead:* `run_id` is now **required** on `default_judge` and threaded from `_run_loop`.
  It had been `""` — worse than absent, because a value that looks like one silently merges every
  run's judge calls into a single empty-string bucket for anything grouping by run. The module was
  defeating the justification in its own docstring.
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
approval_gate: false           # NEW, recognized-but-not-honoured. `true` is REJECTED at intake
                               #      naming P5 (P4-D4 amendment (a): the state has no resume verb
                               #      until answer_run). Fail loud, never silently ignore.
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
the report *including P4's new metrics*. **Reduced to a regression guard by the D6 correction:**
because the report is `Delivered`-payload-resident, survival is already guaranteed by
construction — so A4 no longer proves a new capability, it pins that P4's additions did not
migrate any part of the report into prunable storage.

**A5 — S17 has something to gate on.** The packaged iteration carries a `judge_verdict` distinct
from `auto_verdict` and `curated_verdict`, and — per the T-99 revisit — the ledger↔calls join
resolves by `call_id` rather than by order.

**A6 — failure path.** An exhausted run's report states where/whose/what from the existing
`Failed` payload, with the best attempt attached (`Exhausted` maps to public `failed`, **not**
`Delivered` — the s124 correction in `ref:delegate-event-model`).

### RESOLVED 2026-07-27 — (a) ship the field, defer the state

Surfaced while writing A3: P4-D4 as frozen would build `input_required`, but the only mechanism
that clears it — `answer_run` — is **P5** (`ref:delegate-mcp-surface`). P4 would have been able to
enter a state it could not leave.

**Decision (a):** `approval_gate` ships as a **recognized** spec key. `false` (the default) is
accepted; `true` is **rejected at intake** with an explicit message naming P5 — so a caller asking
for a gate is told, rather than having the request silently ignored. That is the same fail-loud
posture as T-96's `RefsDropped` and T-112's `ContextBudgetError`: the system never quietly does
less than it was asked.

Rejected: **(b)** a minimal `approve_run` — it puts a second resume verb on the MCP surface that
P5 must then reconcile with `answer_run`; **(c)** pulling `answer_run` forward — cleanest
vocabulary but it drags P5's `blocked` schema-union along with it.

**Consequence for T1, recorded in the event model rather than only here:** P4 promotes
`JudgePassed` / `JudgeFailed` only. **`ApprovalRequested` is re-tagged `draft-P4` → `draft-P5`**,
so it ships in the same phase as the verb that resumes it. `event-model.md` exists precisely for
this — *"the place where event vocabulary churns cheaply — BEFORE names hit the wire."*
Accordingly **A3 covers the judge events only**, and the gate's acceptance moves to P5.

<!-- ref:delegate-p4-results -->
## RESULTS — T9 acceptance PASSED, and it changed the design (session 131)

Run against the **real** defect, not a synthetic one: `refs/oficina/dy-Bi1nMo5LIqnpzrtXRTw`
(`cd852fa`) was still reachable, and its run directory had survived retention — so the replay
used the **actual objective**, which had said *"Keep every existing function, constant, import
and comment byte for byte."*

| | drift | `scope_adherence` | `passed` |
|---|---|---|---|
| **A1** — the T-119 leak | `max_verbatim_run_vs_tests: 78`, `+114/−1`, hunks `[[20,20],[72,184]]` | **2** — "substantial unrequested content added" | **False** ✅ |
| **A2** — a real accepted edit (`r5qHxH2Cgh…`) | `max_verbatim_run_vs_tests: 1`, `+36/−26`, 7 hunks | **5** — "only the requested change" | **True** ✅ |

**Three findings, in the order they arrived.**

**1. T-119's prediction was exactly right: the unmodified `code-python` rubric PASSES the leak.**
Scored **5/5 on every criterion**, `judge_verdict: 5`. Worse than missing it — `completeness: 5`
justified itself as *"self-contained, runnable, and includes a usage example"*, where the "usage
example" **is** the 78 lines of pasted acceptance tests. The rubric rewarded the defect. This is
why `evaluator/rubrics/oficina-edit.yaml` exists: kept separate from `code-python` because that
rubric is shared with the Layer-4 benchmark suite, where a greenfield output has no prior scope
to adhere to, so adding the criterion there would retroactively change benchmark scoring.

**2. The judge must be shown the CHANGE, not the RESULT — measured, not assumed.** With a scope
criterion added but the *delivered file* in the prompt, the judge still scored **5** and wrote
*"contains only the requested change"* about a file with 114 added lines; the drift metrics were
present and ignored. Shown the **unified diff** instead — same judge, same persona, same metrics,
same criterion — it scored **2**, at ~33% fewer tokens.
*This invalidated a P4 assumption made at freeze:* that handing the judge measured numbers could
substitute for the second artifact.
**Full three-condition measurement and the generalization — which is not about P4 and applies to
any model asked to review work — extracted to
`docs/findings/judge-must-see-the-change-2026-07-28.md` ([ref:judge-sees-the-change]).** The
short form: a diff is a *representation of the change*, metrics are a *summary of the
representation*; the coder needed the change (T-120) and so does the judge. Neither needed the
file.

**3. The gate discriminates, which is what A2 is for.** A2 is not a trivial change — 36
insertions, 26 deletions, 7 hunks — and still scored 5. The judge is reading the diff against the
objective, not reacting to size. And on A1 the two criteria stayed **independent**:
`scope_adherence: 2` alongside `objective_met: 5`, because the run *did* correctly add the
requested helper *and* pasted the tests. A single blended quality score would have averaged that
into a pass; splitting the question is what makes the gate work.

### A3–A6, run explicitly (session 131) — 20/20 checks

A3/A4/A6 drive real runs through the real `Worker`/`Ledger`/`Store`/retention with injected
coder/evaluate/judge seams. **A5 uses REAL model calls**, because its claim is that a ledger
event and a `calls.jsonl` record join by identity — faking the generation would test the fake.

| | checks | result |
|---|---|---|
| **A3** events fold, old clients survive | 3/3 | `Judged` lands, does **not** fold (run stays `completed`), and a fold given a forged unknown event name still returns `completed` — the envelope's forward-compatibility rule exercised, not assumed |
| **A4** report outlives the workspace | 6/6 | Prune verified to actually fire and the artifacts verified **gone**, after which `run_result` still resolves and the report is **byte-identical** — drift and judge included |
| **A5** S17 has something to gate on | 6/6 | `judge_verdict` present and a distinct field from `auto_verdict`; **the join holds on a live run** — the iteration's `call_id` names a real `calls.jsonl` record |
| **A6** failure path | 5/5 | `Exhausted` carries where/whose/what (`whose=model`), best attempt attached, folds to `failed`, `Delivered` **not** emitted, drift present |

**Two things the numbers do not show.**

**A5 logged TWO call records — the coder's and the judge's.** That is the T-95 decision
validating itself: had P4 composed `run_phase2` wholesale, the judge call would have used the
evaluator's own transport and left no `calls.jsonl` record, no `run_id`, no `call_id`. The judge
is inside the observability the DPO pipeline depends on because the transport was kept singular.

**The whole A5 run took 7.2 s** — real coder call, real judge call, worktree, pytest, packaging.
That is P4-D2's zero-swap reversal showing up as wall-clock: coder and judge share a base, so
packaging cost no model load.

**Two setup bugs found by running these rather than reasoning about them**, both mine and both
worth recording because each would have produced a *false pass*: an **empty** artifacts dir is
deliberately skipped by `_prune_artifacts` ("nothing to free"), so A4 initially "passed a prune"
that never bit; and a `test_cmd` with a `cd` into the original repo tests a checkout where the
target does not exist, since the evaluator already runs it with `cwd=worktree`.

**Calibration note carried from T2's probe:** the pre-T9 probe scored a smaller synthetic leak
**3**, which would have passed the ≥3 threshold. On the real leak with the diff prompt the score
is **2**. The threshold survives this evidence but is not proven at the boundary — a leak scored
3 would still pass, so the next real drift incident is worth checking against it.
<!-- /ref:delegate-p4-results -->

## Build steps (TDD-ordered — T1–T9 COMPLETE, session 131)

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
| **T1** | Revise `event-model.md`; promote `JudgePassed` / `JudgeFailed`; **re-tag `ApprovalRequested` `draft-P4` → `draft-P5`** | **Fixed by process, not choice** — that file states its own protocol: *"Each phase plan revises this artifact first, then promotes its events to frozen."* Adding events is safe by design: the envelope requires folds to tolerate unknown event names, which is what lets these land without breaking P1 clients. The re-tag is the gate deferral (a) made structural rather than only narrative |
| **T2** | The same-base judge persona | `create-persona`, `--num-ctx 16384` per the s127 VRAM finding. Infra, not code; blocks live runs, not tests (T1 seam) |
| **T3** | `call_id` threaded through `GenerationResult` | Small, independent, and it closes T-99's deferred join question + the T-105 positional-fallback hazard. Early because nothing depends on it and it de-risks A5 |
| **T4** | The four P4-D3 metrics computed at packaging | `hunks`, `lines_added/removed`, `files_touched`, `max_verbatim_run_vs_tests`. Reuses `_previous_attempt_view`'s diff; inputs already in scope at `loop.py:384` |
| **T5** | Judge invocation at packaging + `JudgePassed`/`JudgeFailed` + `judge_verdict` recorded | Depends on T1 (events) and T2 (persona for live runs) |
| **T6** | `report.md` artifact + `RunResult` payload carrying T4's metrics and a pointer | Depends on T4 and T5. Must satisfy A4 (survives pruning) |
| **T7** | Failure-report formatting from the existing `Failed` payload | Format only (P4-D7). No new classification |
| **T8** | `approval_gate` recognized at intake; `true` **rejected** naming P5 | Reduced by decision (a): the *state* is not built here. Intake-only, no worker change, no new event — the smallest step in the plan. The gate's own acceptance moves to P5 with `answer_run` |
| **T9** | Acceptance A1 + A2 against the replayed T-119 run | A2 (the negative control on a clean run) is not optional — first principle 6 |

**Carried watch-item, due here:** `event-model.md`'s medium-decision record parks **EventCatalog**
with *"Revisit at P4 (delivery-report format) or first external consumer."* P4 is that revisit.
Default expectation is still no — it is an event *dictionary*, and this plan's output is a
per-run narrative — but the trigger has fired and should be answered rather than left standing.
