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
- 2026-07-12: **P1 BUILD COMPLETE (T1–T10)** — full substrate in
  `mcp-server/src/ollama_mcp/oficina/` (ledger, ids, store, intake, fifo, workerproc,
  worker, service, retention, cli, config) + 4 MCP tools in server.py + `oficina` CLI +
  `watch-run.sh`. 149 mcp-server tests green. **Live acceptance 6/6 PASSED** (real
  Ollama; #2 detach/reattach verified from a foreign session). Ledger gained
  repair-on-append in review. Opus subagent + local delegation (15 calls, all 1/2).
- 2026-07-12: **P1 MERGED** (PR #73/#74 to master) + **`oficina` CLI installed**
  (`uv tool install --editable ./mcp-server` → `~/.local/bin/oficina`; MCP tools already
  user-level). Live-smoke OK (pong run). **T-81 first client BUILT — but WITHOUT oficina**
  (a one-shot CLI gains nothing from async; solved via preview stage/apply + num_ctx/think
  fixes). **Lesson: oficina's real first client must be an AGENT that parallelizes**, not a
  batch CLI — see KNOWLEDGE.md "T-81 outcome" + "Distribution" sections.
- 2026-07-15: **P2 plan FROZEN (T-92, session 119)** — `docs/plans/oficina-p2-evaluated-loop.md`
  (P2-D1–D13; caching-first: monotonic-prefix prompt layout, rule-based in-loop classifier,
  per-run worktree, delta-scope baseline + free anti-cheat; first slice = function-against-tests,
  Python, 3-iter, no escalation). Advisor caught + fixed a delta-scope masking hole (blanket
  baseline-subtraction would mask an absent target). Diagrams individually ref-anchored. **See the
  plan's "Build kickoff" section** for where code / tests / the validator live.
- **Next:** **build P2 (T-92)** — start at **T1** (`parse_validator_output`; the plan's
  Build-kickoff map pins module/seam/test/validator anchors). **T-91 is a prerequisite**
  (num_predict floor/cap on the loop generator). T-86 distribution runbook still pending; G-D4
  gate-vs-P2 priority open (mild lean gate-after-P2).
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

`KNOWLEDGE.md` (implementation invariants — created 2026-07-12 at first build) +
`decisions.md` (S1–S21, V-D1–V-D13) + `evidence.md`.
