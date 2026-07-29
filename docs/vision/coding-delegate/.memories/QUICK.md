# coding-delegate — Quick Memory

*Working memory for the **oficina** vision project (folder keeps the coding-delegate working
label). Keep under 30 lines.*

## Status

**P4 complete. P3 is next.** Suite 408; live gate `make accept-p4`.
In flight: `feature/oficina-judge-payload` → **PR #87** (T-129/T-130).

Recent sessions — pointers only; measurements and invariants live in KNOWLEDGE.md:

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
  (fed by Axis A: language axis proven, taxonomy trigger for E-D8 rename + dead
  `acceptance.validators` removal). (3) T-93 refs-diagram verdict;
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
