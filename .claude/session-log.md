# Session Log

**Current Layer:** Layer 5 — Expense Classifier (oficina P4 shipped; P3 next)
**Current Session:** 2026-07-28 — Session 131: P4 judge gate BUILT + ACCEPTED — T-119 resolved (PR #86); P3-vs-P4 sequencing decided; T-122 measured

---
## 2026-07-28 - Session 131: P4 judge gate BUILT + ACCEPTED — T-119 resolved (PR #86); P3-vs-P4 sequencing decided; T-122 measured

### Context

Opened on the one item session 130 explicitly deferred — P3-vs-P4 sequencing — and ran straight through to a built, accepted and PR'd P4.

### What Was Done

- **P3-vs-P4 decided: P4 first**, then P4 authored, frozen, BUILT (T1–T9) and ACCEPTED on `feature/oficina-p4-judge-gate` — **PR #86 open**, suite **340→369**.
- **T-119 RESOLVED** — the gate P4 owed it exists: `oficina-edit` rubric + `Judged` at packaging + drift metrics in the delivery report.
- **T-122 measured** (`.claude/tools/judge-window-sweep.py`): the delegate can edit **21/27** files on the 16K coder — optimistically, since 13 have no paired test — and the blocked set is oficina's own core (`loop.py`/`parser.py`/`intake.py`/`evaluator.py`). Judge side unconstrained (27/27).
- Acceptance **A1–A6 all pass**, run against the *real* T-119 leak rather than a fixture; A3–A6 explicitly, 20/20, A5 on live model calls.
- New: `oficina/drift.py`, `oficina/judge.py`, `evaluator/rubrics/oficina-edit.yaml`, persona `my-judge-q25c14-16k`, `.claude/tools/judge-window-sweep.py`, `.claude/ltg-usage-guide.md`.
- T-124 keep-or-drop resolved (two ref-bearing docs tracked; `.claude` ignores made nested-aware); stale merged branch removed local+origin.
- Filed **T-125** (LTG index broader than its declared corpus), **T-126** (corpus-divergence pattern), **T-127** (`create_persona` MCP tool lacks `num_ctx`), **T-128** (a hand-written VERDICT block can name a nonexistent `call_id`).
- First llm-side **LTG usage guide**, derived from career-search's, after using LTG unaided and getting the query-altitude rule backwards.

### Decisions Made

- **P4 before P3.** T-119 has owner P4 and no other owner; phasing permits reordering. Recorded the *rejected* counter-argument too: P3's `steps:` does NOT remedy the T-122 band, because the band is the 2× multiplier on the target file and only span-confined output removes it (the s126 M2 reversal).
- **Two freeze-time decisions reversed by reading upstream, not by new evidence.** P4-D2 (judge persona → same-base, on `ref:delegate-gpu-policy`'s zero-swap preference the first decision never priced) and P4-D5 (retire `auto_verdict` → keep it; first principle 8 and `ref:delegate-evidence-dpo` show it is *deliberately* the gameable signal S17 exists to gate). Shared cause: the fork was framed off the phase doc while the vision folder had already priced the trade.
- **P4-D6 corrected against the as-built code** — the report is `Delivered`-payload-resident, not an artifact. Three documents left this wrong; the folder's `KNOWLEDGE.md` had it right.
- **Approval gate: ship the field, defer the state** — `approval_gate` is recognized and refused until P5 supplies `answer_run`, since a gate built now could enter `input_required` with nothing able to clear it. `ApprovalRequested` re-tagged `draft-P5`.
- `files_touched` dropped at build time: the loop writes exactly one file, so it would fire unconditionally (first principle 6).

### Next

- **Review/merge PR #86**; consider `/simplify` over the branch first.
- **P3 — context & prompt assembly** is now the phase in front.
- Decide **T-118**'s remaining scope (R-D1/R-D3); **Axis B kinds reconsideration** still not started (carried since s128).
- Triage the four new tasks — **T-125** (widen `corpus.yaml` vs rebuild the index) and **T-128** (validate verdict ids at capture) are the cheap ones.

### Gotchas

- **A greenfield rubric can REWARD an edit defect.** Unmodified `code-python` scored the leaked file **5/5**, its `completeness` criterion calling the 78 pasted test lines *"a usage example"*.
- **A reviewing model must be shown the CHANGE, not the RESULT.** With the delivered file *plus* drift metrics in the prompt the judge still said "contains only the requested change"; with the unified diff it caught it, at 33% fewer tokens. Measured numbers do not substitute for the artifact. `ref:judge-sees-the-change`.
- **`SequenceMatcher`'s `isjunk` stops junk anchoring a match but the winning block still absorbs adjacent junk** — blank lines must be filtered *before* matching, not marked junk.
- **I invented a `call_id` for a backgrounded call and the harness accepted it**, creating an orphan verdict (removed, backup kept). T-105 hardened the hook's ids; nothing validates a hand-written one → T-128.
- Running A3–A6 caught **two of my own false-pass setups**: an *empty* artifacts dir is deliberately skipped by the pruner ("nothing to free"), and a `test_cmd` with a `cd` tests a checkout where the target does not exist (the evaluator already runs it with `cwd=worktree`).
