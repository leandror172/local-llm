## 2026-07-28 - Session 132: "P4 REVIEWED, SIMPLIFIED and RE-ACCEPTED LIVE — 13 findings closed, P4-D8/D9/D10 frozen, acceptance made durable"

### Context

Opened on the session-131 handoff's own Next — *"review/merge PR #86; consider `/simplify` over the branch first"* — and ran the whole sequence in order: `/code-review`, freeze the design forks it surfaced, `/simplify`, then re-run the acceptance live because the review had changed the gate's arithmetic underneath it.

### What Was Done

- **`/code-review` over the full branch: 13 findings, all closed.** Ten were ordinary defects; **three turned out to be design forks** and were escalated to the P4 decision register rather than settled inside fix commits — a register amended silently by fixes stops recording what was decided and starts recording what survived.
- **P4-D8/D9/D10 frozen, P4-D11 deferred** (see Decisions), then implemented: `judge_verdict` as a min, the cut moved into the rubric, `weight` deleted, judge calls given a real `run_id`.
- **Report bounded** — judge `reasoning` clips at 200 chars, `hunks` at 10 with a conditional `hunks_total`; worst case measured **~750 → ~206 tokens**, and bounded rather than merely smaller.
- **Every terminal now reports.** `Cancelled` carried no drift (the payload, not the object — `service.result()` returns it verbatim); a no-attempt run reported the whole baseline as deleted; the iterations trail was missing on the exhausted path; anti-cheat rejections were indistinguishable from ordinary structural failures.
- **`/simplify` (4 parallel angles): 9 cleanups applied, 7 deferred to tasks.** `judge.py` gained `unavailable_verdict()`; the cancelled terminal became a named method; the report's size bound now holds on **all three** terminals; `drift.py` states its clamp as an invariant rather than the endpoint one incident exposed.
- **Live acceptance re-run and made durable** — `mcp-server/run-acceptance-p4.sh` / `make accept-p4`, indexed. A1/A2 replay the **pinned** runs (base commit from each run's own `AssemblyDone`, delivered bytes from `refs/oficina/<run_id>`); **A5 drives a real end-to-end run**. All pass. It had been authored ad hoc twice and rebuilt from scratch both times.
- **`worker.py` split** — `transport.py` (the ONE T-95 per-call transport, three callers) and `report.py` (the `Delivered`-payload bounds). `class Worker` had not started until line 330 of 566. **`loop.py` no longer imports from `worker.py` at all.**
- **Three "one owner" fixes:** the declared tests are read once at assembly, strictly (two readers had drifted on decoding); one call-time `repo_root()` (`LLM_REPO_ROOT` was honoured by **1 of 4** asset resolvers); `errors.py` owns the `whose` vocabulary and the limit→attribution map.
- **The event phase-registry is pinned by a test** — `Judged` had been omitted, so a run reported `looping` through its whole judging window, and `fold_phase` tolerates unknown names silently.
- **PR #86 description updated** — it still advertised the ≥3 threshold as an open, unproven risk that P4-D9 had closed, plus a stale suite count.
- **Memories/README converged**; a new cross-session memory recorded (measure magnitude, don't estimate it). Suite **369 → 393**; 17 commits.

### Decisions Made

- **P4-D8 — `judge_verdict` is the MIN of the criteria, not their mean, and is `0` when ANY criterion is unscored.** A conjunction has no average: the mean reported **4** on the T-119 leak while `passed` correctly withheld. **Sharpened at build time** — the freeze wording said *"0 when none scored"*, which would have left the hole open, because a min over *the criteria that actually scored* is still 5. The defect was never mean-vs-min; both reduced over a filtered subset.
- **P4-D9 — the passing cut moved INTO the rubric as a per-criterion `passing_score: 4`.** Rung 3 of `scope_adherence` describes a defect yet sat above a threshold of 3; reading **both** ladders showed rung 4 is the lowest acceptable rung in each, so the scale was right and the number was one rung low. **Changed zero prompt bytes** (`passing_score` never reaches the model), so A1/A2 held without re-measurement — and it **closes the plan's carried calibration note** (a leak scoring 3 used to pass). Reversal recorded: the first recommendation was to rewrite the rung, and reading the rubric overturned it.
- **P4-D10 — `weight` deleted from `oficina-edit.yaml`.** Not merely unused but **unusable**: no weighting can make an average agree with an AND (with both cuts at 4, ranking `(5,3)` below `(4,4)` needs `w₁<w₂` while `(3,5)` needs `w₂<w₁`).
- **P4-D11 — per-criterion judge `call_id` deferred with a countable trigger.** The cheap route (side-band collection) matches ids to criteria **by order** — the positional fallback T-105 banned, in the one module whose docstring cites T-105. The `run_id` half was a real defect (judge calls logged under `""`, a value that looks like one) and is fixed.
- **Test-file decoding is STRICT, one read, at assembly.** Under P2-D13 the tests ARE the spec, so a file that cannot be decoded cannot be handed to the model as one. Accepted cost, stated rather than discovered: a `# -*- coding: latin-1 -*-` test file is legal Python that pytest would run, and oficina now refuses it — loudly, naming the file.
- **Won't-fix, with measurements:** the redundant `change` computation (0.37 ms on a 599-line file, and making it conditional would put an outcome-specific branch back into the single terminal seam whose value is having none); `ContextLimitUnknown` stays OUT of the phase map (it reports a capability, not progress) but is now *declared* phase-neutral, because "neutral" and "forgotten" looked identical to `fold_phase`.

### Next

- **Merge PR #86** — 393 green, live acceptance passing, description updated.
- **P3 — context & prompt assembly**, the phase in front, and the one that makes the approval gate's payload worth defaulting on.
- **T-129 + T-130 together** — both change what the judge is sent, so one `make accept-p4` A/B covers both.
- Still carried: **T-118** R-D1/R-D3; **Axis B kinds reconsideration** (E-D8 rename + dead `acceptance.validators`, untouched since s128); the four s131 tasks (T-125/126/127/128), of which T-125 and T-128 remain the cheapest.

### Gotchas

- **A fix shipped this morning was UNREACHABLE, and its test proved nothing.** `_read_test_sources` gained `errors="replace"` so a latin-1 test file would not kill a run — but `Workspace._build_stable_parts` reads the same declared files **strictly**, during `assemble()`, and the run dies there first. The unit test called the fixed function directly and passed. This is the producer→consumer seam mistake `ref:active-decisions` already records; the question that catches it is one grep — **who else reads these files?**
- **Five findings identified their MECHANISM correctly and got their MAGNITUDE wrong**, in both directions: *"tens of seconds"* measured **2.4–3.1 s**; my own counter-estimate of *"well under a second"* was wrong the other way (I anchored on the recorded 7.2 s run, which judged a **tiny synthetic fixture**, not a real ~1,300-token diff); *"tens of milliseconds"* measured **0.37 ms**. Mechanism is derivable by reading; magnitude and reachability are not.
- **`rtk grep` under-reported** — it returned 5 of 7 matches, missing two in a file I had just read on screen. Use plain `grep` when completeness is the point. Joins `rtk git log` (drops merge commits) and `rtk curl` (mangles JSON).
- **A5's `judge_verdict` came back 5 and then 1 an hour apart, same code and same rubric.** It is a *greenfield* run judged with `oficina-edit`, whose `change` is a 100%-additions diff — `scope_adherence` on it is incoherent, not merely noisy (→ T-130). The A5 check only asserts the field is *distinct* from `auto_verdict`, so it passes either way: that is the check being loose, not the behaviour being stable.
- **A fake at an injected seam is blind to everything upstream of it.** `verify_cuts.py` proves the cuts and the reduction and cannot prove the judge was asked the right question, because a fake `chat` never reads the prompt. That is why the live harness exists and why it is the gate for any change to `judge.py`, the rubric's scale text, or the judge persona.
