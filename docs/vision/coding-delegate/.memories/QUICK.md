# coding-delegate — Quick Memory

*Working memory for the **oficina** vision project (folder keeps the coding-delegate working
label). Keep under 30 lines.*

## Status

- 2026-07-11: **Vision v1 authored + stress-tested** — full-session exploration with the user;
  two-agent prior-art comparison (frontier + web-research arms), clones survey, verdict-data
  mining (457 calls / 49 verdicts). All knowledge in this folder; map in `index.md`.
- **No phase plans yet.** Next concrete step: **P1 plan doc** (async substrate) — freezes V-D4
  (residency/packaging), V-D9 (retention/TTL), V-D10 (ask_ollama profile), V-D11
  (orchestration-lib re-check) + ledger event names. First client candidate: **T-81**.
- 2026-07-11: **Name DECIDED (V-D1): `oficina`** (runner-up aprendiz). Identity = the
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
