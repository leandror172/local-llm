# coding-delegate — Quick Memory

*Working memory for the **oficina** vision project (folder keeps the coding-delegate working
label). Keep under 30 lines.*

## Status

**P4 complete. P3 IN PROGRESS.** Suite 416 (mcp-server; repo-wide **894** via root `make test`, T-136 s138); live gate `make accept-p4`.
**PR #87, #88 and #89 ALL MERGED** (#89 on 2026-08-18) — master carries P1–P4, the P3 plan,
T-133, and **P3-T0's benchmark half** (dotted addressing + the `symbol_addressed` arm:
43 output tokens FLAT vs whole-file's 120/216/479, both arms 100% correct). Nothing in flight.
**P3-D1 FROZEN (s140) on (B), four operations** — `replace_unit` (built) · a `Constant` kind
(resolver gap, no new op) · `insert_top_level` · `insert_unit`. **Criterion 3 is no longer gate
evidence:** reclassified probe→BUILD and attached as D1's acceptance condition (P4-D2 pattern).
**"Who chooses" lifted to P3-D10, still OPEN.**

Recent sessions — pointers only; measurements and invariants live in KNOWLEDGE.md:

- **s140** (08-20) — **P3-D1 FROZEN, and the magnitude was corrected AT the freeze.** 5b's
  30.4% constant slice counts statements *added OR changed*; only the **changed** half is
  convertible by a `Constant` kind. Measured over 487 edits: oficina src ≤40 splits **CONVERT
  17.4% / ADDED 13.0%**; across cuts CONVERT is **6.4%–17.4%**. **So "cheapest first and largest
  first are the same thing" is FALSE** — the resolver extension TIES imports alone (17.4%), while
  `insert_top_level` (imports + added constants + docstrings) is strictly larger. Cheapest-first
  survives on its own merits; the 30.4% justification does not. All six of s139's published rows
  REPRODUCE (four exact), so the split is additive. Cuts made durable (`run-census-report.sh`) —
  and the first draft of them filtered on the substring `"oficina/"`, which also matches
  `tests/oficina/` and would have "corrected" a correct number. Benchmarks 116→141.
  **Then remedy 2 BUILT and its model-facing half MEASURED** — module constants are addressable
  (`Constant`/`ClassConstant`, position still the only discriminator; a multi-name statement
  REFUSES with its own `shared_binding` reason). Live: **address fidelity 12/12, degeneration
  0/12, 30 output tokens FLAT vs whole-file 84/176/352**. **The plan's predicted `_UNIT_NODES`
  was written and DELETED** — a membership pre-filter blocked nothing the name dispatch did not,
  and it made the rule untestable: two mutations both left the suite green, each neutralised by
  the other. **Every defect this session came from a mutation or a reproduction check, none from
  a green run** — including a prompt that hardcoded the kind vocabulary, so the new capability
  was unreachable by the model. Repo 1009.

- **s137** (08-18) — **P3-T0's BENCHMARK HALF BUILT AND MEASURED; the naming half clears its
  gate.** Dotted addressing (`find_units`/`resolve_unit`/`apply_unit`) + class-bearing corpus +
  a 4th `symbol_addressed` arm; 67 tests. **Measured: 43 output tokens FLAT vs whole-file's
  120/216/479 by bucket, both arms 100% correct**; address fidelity 12/12, degeneration 0/12.
  Four findings the plan lacked — the **~10.9% unaddressable-by-construction bound** (the
  census's unread complement), **harness-owned indentation**, the corpus having **no classes**
  at all, and one vehicle named for two questions. Also corrected: **"16K is VRAM-fit" is FALSE
  on this host** (9.31 GiB resident / 1.76 on CPU with a quiet card) — **but s139 walks back the
  INFERENCE drawn from it**: 49 logged calls on that model run 5.4 / 14.6 / 24.6 tok/s
  (min/med/max), so "13–21 never reached" is false and partial-offload-by-default is an open
  question, not a standing condition. **Criterion 5a MEASURED s139 and it BITES:** on an
  import-requiring corpus the coder never once added a correct top-level import (it cannot —
  no operation expresses one), symbol-addressed scored **4/12 and 6/12 combined against
  whole-file's 12/12 and 12/12**, and `avoided_the_module` was **0/24**. Criteria 1/2/4 stayed
  clean and tokens stayed flat (47 vs 171), so this is **not** an addressing failure — it is a
  **coverage bound**. The predicted function-local import is the BENIGN half (10 of 14 PASS,
  the silent case); the unpredicted half uses the module without importing it and never runs.
  **The plan's assumed refusal fallback does not exist — the model never refuses**, so the
  fallback must be detected by the harness (first principle 1). **5b MEASURED same session over 486 real edits: 23–48%**
  depending on the cut (23.1% at the most favourable — bridge source, ≤10-line edits), so this
  is **not a rare fallback**. **The prediction picked the second-largest class:** the module
  **constant** outnumbers the import at every cut (30.4% vs 17.4% in oficina's own source) —
  and a constant **HAS a name**, so that 30% is a **resolver gap** (`KINDS` omits assignments),
  not a construction bound. Genuinely nameless: import ~17%, docstring ~4%. Plus a gap the plan
  never named — **adding a NEW top-level unit (~17%)**, which `replace_unit` cannot create.
  **Net: more favourable for (B) than 5a alone implied**, but "detect + fall back to whole-file
  because it's smaller" is RETRACTED — falling back on a quarter to a half of edits means
  falling back on exactly the files whole-file cannot reach. Criterion 3 remains unrun. § "The judge's payload" is unaffected.
- **s134–s136** (07-30 → 08-11) — P3 planned, then **re-grounded twice**; P3-D1 still OPEN.
  T-133 shipped (`context.callers` wired, `acceptance.validators` deleted). Headline:
  **a 4-arm external prior-art survey never enumerated our own repo**, where the operation
  was already built and measured. New T-135.
- **s133** (07-29) — judge PAYLOAD: prompt made prefix-cacheable, rubrics declare
  `applies_to`, greenfield gets its own ladder. New T-131. § "The judge's payload".
- **s132** (07-28) — P4 reviewed, simplified, re-accepted live; **P4-D8/D9/D10** frozen
  (`judge_verdict` = MIN, cut moved into the rubric, `weight` deleted); `transport.py` +
  `report.py` split out of `worker.py`; acceptance made durable. § "P4 judge gate".

### How we got here — one line per phase, not per session

- **Vision v1** (07-11) — prior-art + clones survey + verdict mining. `vision.md`,
  `decisions.md` (S1–S21, V-D1–V-D13), `evidence.md`. Name `oficina` = V-D1 → `naming.md`.
- **Founding problem** — multi-session GPU contention (T-102), *recovered* 07-18 after the
  T-21→T-88 supersession dropped it. `ref:multi-session-contention`.
- **P1 async substrate** (07-12, merged #73/#74) — ledger/store/intake/fifo/worker/service,
  4 MCP tools, CLI; live acceptance 6/6. `ref:delegate-p1-goal`.
  *Lesson: the first real client must be an AGENT that parallelizes, not a batch CLI (T-81).*
- **P2 evaluated loop** (07-16, merged #76) — parser/prompt/workspace/evaluator/loop;
  reviewed (10 fixes, T-95–T-99 deferred) then simplified. `ref:delegate-p2-goal`.
- **P2 edit mode** (07-22, T-110) — M2 **reversed** to whole-file-with-context; code-anchored
  is the recorded fallback with a stated trigger. `docs/plans/oficina-p2-edit-mode.md`.
- **Axis A / Go** (07-23, T-92) — second language; `LanguagePack` extracted from two working
  implementations. Coder defaults = 16K personas.
- **Context guard** (07-24, T-112/T-120) — the loop refuses what cannot fit; previous attempt
  is a diff; the feasibility band discovered. `ref:oficina-ctx-overflow`.
- **P4 judge gate** (07-29, T-119, merged #86) — `drift.py` + `judge.py`, Phase-2 rubric judge
  at packaging. `ref:delegate-p4-goal`, `ref:delegate-p4-results`.

### Next

- (1) **P3** — context & prompt assembly, now the phase in front, and the phase T-129/
  T-130 just gathered evidence for: prompt ORDER is worth 79–85% of a call's prefix eval, and a
  payload must name the artifact it carries. (2) **Axis B kinds reconsideration**
  (fed by Axis A: language axis proven, taxonomy trigger for the E-D8 rename. **The dead
  `acceptance.validators` removal is NO LONGER Axis B's — it shipped in P3 as T-133, s136.**
  The routing conflict resolved in P3's favour by mechanism: `validators` is not a *kind*, so
  E-D8's trigger never covered it; only the QUICK "Next" line had routed it here).
  (3) T-93 refs-diagram verdict;
  T-86 distribution (`OFICINA_VALIDATE_CODE`/`_REF_LOOKUP`/`OFICINA_GO`). Standing: T-102 gate
  busy-check (G-D8); T-111 cancel gap; T-118 run-provenance convention; prefix-reuse tracking via
  `.claude/tools/ollama-cache-report.py`; harden write-model corpus IF a real edit run drops
  sibling code (the E-D1 fallback trigger — docstring deletions are DOC omissions, not
  code; trigger not fired).

## What this is

Async **deliverable runs** for local models: Claude submits one bounded deliverable spec →
`run_id` → a detached worker loops the coder model against the Layer-4 evaluator → Claude
reviews the result against plan + quality. H1: Claude gates everything. H2 (autonomous plan
runs) only if H1 run logs validate the planner hypothesis (V-D2 — "graduation").

## Key rules

- One call, one deliverable; tests-first (test run → review → implementation run)
- Deterministic spine; structured output only (never free-form tool use); 14B coder floor
- Iteration budget by mode (T-114): edit runs default to **1** (retries never see their own residual), greenfield ~3; +1 repetition-triggered fresh start; explicit budget always wins; phase batching (~3 VRAM swaps/run)
- Judge gates every DPO chosen label (S17); `auto_verdict` ≠ `curated_verdict`
- **Session verdicts ship per RUN, on the deliverable** (T-105, 2026-07-21) — a `run_result` hook
  injects `[VERDICT run_id=…]` iff a deliverable exists. A **second axis** beside `auto_verdict`,
  which is binary and cannot express `1 (improved)`. Detail: KNOWLEDGE.md § "Session verdicts for
  runs".

## Deeper memory

`KNOWLEDGE.md` (implementation invariants — created 2026-07-12 at first build) +
`decisions.md` (S1–S21, V-D1–V-D13) + `evidence.md`.
