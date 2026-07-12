# coding-delegate — Quick Memory

*Working memory for the **oficina** vision project (folder keeps the coding-delegate working
label). Keep under 30 lines.*

## Status

- 2026-07-11: **Vision v1 authored + stress-tested** — full-session exploration with the user;
  two-agent prior-art comparison (frontier + web-research arms), clones survey, verdict-data
  mining (457 calls / 49 verdicts). All knowledge in this folder; map in `index.md`.
- 2026-07-11: **P1 plan FROZEN** — `docs/plans/oficina-p1-async-substrate.md` (P1-D1–D11;
  resolves V-D4/V-D9/V-D10/V-D11 + event freeze set; concurrency model = per-file ownership
  with queue-push handoff). **Event model artifact:** `event-model.md`
  (`ref:delegate-event-model`, Mermaid `eventmodeling`; envelope + freeze ladder;
  IntakeAccepted stays silent). V-D11 re-checked twice (general + Axon 5) — plain Python
  confirmed; record in `decisions.md`. Branch `feature/oficina-p1-plan`.
- **Next: BUILD T1–T10** (~2 sessions, TDD, module tree in the plan). First client
  candidate: **T-81**.
- **Name DECIDED (V-D1, 2026-07-11): `oficina`** (runner-up aprendiz). Identity = the
  delegation harness; the flywheel is a property, not the objective (user correction).
  Guild roles demoted — no `my-aprendiz-*` personas; `journeyman` reserved for H2. Boundary
  rule: metaphor in prose only, never in code/schema/CLI verbs. Record: `naming.md`.

## What this is

Async **deliverable runs** for local models: Claude submits one bounded deliverable spec →
`run_id` → a detached worker loops the coder model against the Layer-4 evaluator → Claude
reviews the result against plan + quality. H1: Claude gates everything. H2 (autonomous plan
runs) only if H1 run logs validate the planner hypothesis (V-D2 — "graduation").

## Key rules

- One call, one deliverable; tests-first (test run → review → implementation run)
- Deterministic spine; structured output only (never free-form tool use); 14B coder floor
- ~3 iterations + 1 repetition-triggered fresh start; phase batching (~3 VRAM swaps/run)
- Judge gates every DPO chosen label (S17); `auto_verdict` ≠ `curated_verdict`

## Deeper memory

`decisions.md` (S1–S21, V-D1–V-D13) + `evidence.md` serve as this folder's KNOWLEDGE.md.
Create a real one when implementation knowledge accretes (trigger: first phase built).
