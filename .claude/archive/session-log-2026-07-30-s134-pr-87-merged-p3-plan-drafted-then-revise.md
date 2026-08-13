## 2026-07-30 - Session 134: PR #87 merged; P3 plan drafted then REVISED by re-grounding — the output-shape field was a duplicate axis, and `context.callers` is declared-but-unconsumed

### Context

Opened with PR #87 already merged and master updated, for a "discuss next steps" session. No
code was written: the session sequenced the phase in front, then authored P3's plan doc — and
the plan was materially wrong until it was re-grounded against the inception docs, which is the
session's main lesson.

### What Was Done

- **PR #87 merged** (T-129/T-130 landed on master; suite 408, `make accept-p4` green). Verified rather than assumed — `gh pr view 87` shows MERGED, `master` at `3f3348d`.
- **`docs/plans/oficina-p3-context-assembly.md` authored** (505 lines, `d0cae93`) — register **P3-D1…D9 OPEN**, no build steps, `ref:delegate-p3-goal` / `-decisions` / `-probe`, indexed.
- **The plan was then REVISED IN PLACE after reading the whole oficina inception set** (`vision`/`decisions`/`evidence`/`architecture`/`integration`/`phasing`/`naming`/`event-model` /`index`/`README`, both `.memories`, plus `mcp-server/.memories/*`). Three of five worked entries changed; the reversal is recorded in the plan rather than smoothed over (P4 precedent).
- **`context.callers` found declared-but-unconsumed** (`intake.py:44`) — verified by grep over all of `mcp-server/{src,tests}`, where the symbol appears exactly once. Filed **T-133**.
- **Two records of P4-T3 corrected** (`37ce27b`) — `mcp-server/.memories/KNOWLEDGE.md` was STALE and `event-model.md` was NEVER TRUE, in opposite directions. Both applied in place, not appended (the s133 lesson from that same KNOWLEDGE.md).
- Two commits on branch `docs/p3-plan-and-join-record`; **no PR opened yet**.

### Decisions Made

- **T-122 remedy (a) — code-anchored output for large targets — CHOSEN**, with (b) closed on measurement rather than left "blocked on T-113": s133 showed `loop.py` clearing the 32K window and producing nothing in 7,066 s at ~49% utilisation. A window you cannot drive is not a remedy, and T-113 cannot revive it because throughput is downstream of footprint.
- **P3-D1's first draft (`deliverable.output_shape`) REJECTED as a duplicate axis.** The draft run spec already listed `kind: …|patch` (specified, dropped at build); **E-D8 froze the taxonomy with the Axis-B kind-widening pass as its NAMED trigger**, so a kind-shaped answer is Axis B work, not P3; and the recorded fallback names `deliverable.unit`, not a shape toggle. A third orthogonal axis is the drift V-D1 named when it killed the `my-aprendiz-*` family.
- **Recommendation (not frozen): caller-declared on the `unit` axis.** Auto-select must guess when `_context_limit is None`, and `transport.model_context_limit`'s docstring is a written refusal of that guess — caller-declares removes the question instead of answering it. E-D2's no-spec-field-for-derivable-facts precedent addressed out loud (shape depends on a budget, not a repo fact).
- **P3-T0 gates P3-D1** — an anchor-emission probe on `parser.py`/`intake.py` (NOT `loop.py`, which measures throughput). If anchors are unreliable at 14B, **T-122 collapses to (c) by measurement rather than concession** — and (c) is consistent with `ref:delegate-non-goals`.
- **Founding-evidence claim corrected:** P3's own predates P4 by four months — `ref:delegate-evidence-verdicts` records the March re-declaration defect class *disappearing* once conventions required protocol files + callers in context. T-129/T-130/T-122 are carried constraints, not founding.
- **Two commits, deliberately split.** The as-built correction is reviewable against `worker.py:134` / `loop.py:320` in a minute; the plan's review question is "are these the right forks?" Reviewing them together means the mechanical question loses.

### Next

- **Walk the P3 register with the user** (user's words: "we'll run through the decisions next session"). **P3-D1 BLOCKS** — `deliverable.unit` (P3 owns it) vs reviving `kind: patch` (E-D8's trigger routes it to Axis B, P3 becomes a consumer). D2/D3/D5 are ready to freeze.
- **P3-T0** — the anchor-emission probe. Write the apply-side negative control FIRST (s133: a delegated model inverted `applies_to` with the case spelled out in its brief).
- **T-133** (`context.callers`) — independent of the probe, smallest change in the phase, best evidenced. Its test must fail today, or it encodes the bug.
- Open a PR for `docs/p3-plan-and-join-record` (2 commits, docs-only) or land on master.
- Still carried: **T-131** (weigh with T-111), **T-132** (root QUICK, own session), **Axis B** (now load-bearing for P3-D1, not just carried), T-125/126/127/128.

### Gotchas

- **A plan authored from the phase doc alone was wrong in three places; the inception folder had already priced all three.** Exactly the cause P4 recorded for its own two pre-freeze reversals (*"the fork was framed from the phase doc alone, and the vision folder had already priced the trade"*). It has now happened twice — treat "read the vision folder before authoring a phase plan" as a rule, not advice.
- **A declared schema field is how a silent ignore becomes possible.** `Context` sets `extra="forbid"`, so an UNDECLARED key is rejected at intake; `context.callers` is swallowed *precisely because* it is declared. The schema converts a loud rejection into silence — the inverse of first principle 4 ("the harness should refuse"). No checker can see this: nothing reports anything at all, which is why no audit found it.
- **There are THREE prompt builders, not two** — `server.py` (`<refs>`→`<context_files>`→hint, 2026-05), `prompt.py` (P2-D2 stable-first), `judge.py` (criterion-last, T-129) — with three independently-authored ordering rules and no shared definition. `loop.py` calls `server._build_refs_block` then re-orders, so bridge and oficina agree **by coincidence, not construction**. First `ref:corpus-divergence-pattern` instance in prompt construction rather than in a checker.
- **T-129's 79–85% win is bounded by a 15-minute slot life** (`ref:mcp-keep-alive`: `keep_alive="15m"`, llama.cpp reuses a leading prefix only while the slot lives). Order is a *within-run* win, not a free property.
- **Two stale records, opposite failure modes, neither catchable by tooling.** KNOWLEDGE.md was true-when-written and overtaken; event-model.md was written the same session as the code and attributed P4-T3 to the wrong row. Both survived because the docs were checked against the *narrative* ("thread `call_id` through so the join is identity-based"), which is accurate, rather than re-derived from the emitter. `check-ref-integrity.py` validates markers, not claims.
- **The correction had a scope qualifier nobody had written down:** the identity-based join holds for LOOP kinds only. `file`/`answer` runs still join on `run_id` alone — harmless today (one generation per run, nothing to pair within it), which is exactly why it stayed invisible. A flat "it's identity-based now" would have replaced an understatement with an overstatement.
- **The unpriced cost of code-anchored output is narrower than s126 implies.** T-104's principle — *oficina composes the bridge tools, it does not reimplement them* — means `patch_file` is the apply path and already exists. What is genuinely unpriced is the AMENDMENT's narrower set: the `unit` field, response-shape validation, import merging, the constants boundary.
