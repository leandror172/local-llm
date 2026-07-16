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
- 2026-07-15: **P2 BUILD STARTED (branch `feature/oficina-p2-loop`).** **T1+T2 DONE.**
  T1 `oficina/parser.py` (`parse_validator_output → ParsedFailure{stage,file,error_key,raw}`;
  `category_for`/`scope_of`; Python normalizer; 20 tests). T2 `oficina/prompt.py` (`SEGMENTS`
  tuple + `build_prompt` fold + ordering-guard test, P2-D2/D3 cache contract; 8 tests). Full
  suite 178. Test bodies + impl local-model-generated (`my-python-q25c14`).
  **T3 DONE** — `intake.py` gained `Acceptance`/`Budgets` models, `function` kind, 3 loop rejections
  (acceptance/worktree/git-repo required), and **triad unified on where/whose/what** (retired
  intake's stage/fault/detail). 28 intake tests (17 P1 + 11 new); full suite 189.
  **T4 DONE** — `workspace.py` `Workspace` (assemble → worktree add + C0 baseline + injected
  EvaluateFn seam + stable parts + AssemblyDone; snapshot; teardown remove+prune, keeps run branch).
  11 git-integration tests; ledger gained `assembly_done`/`AssemblyDone`→working. Full suite 200.
  **T5 DONE** — `evaluator.py`: real `evaluate` (stage-ordered compile→test via run-validate-code.sh
  + pytest, T1-parsed), `attribute` (P2-D12 masking-hole guard), `diff_touches_test_files` (anti-cheat).
  9 tests incl. 2 real-subprocess evaluate integration tests. `EvaluateFn` refined to (worktree,
  base_repo, spec). Full suite 209.
  **T6 DONE + T-91 RESOLVED.** `loop.py` `EvaluatedLoop` (injected coder/evaluate/workspace/ledger;
  generate→snapshot→anti-cheat→evaluate→attribute→classify→signature/fresh-start→budget; emits
  iteration events + Exhausted, NOT Delivered). `client.chat` gained `num_predict` (T-91 fix);
  `default_coder` floors/caps at 2048. Ledger gained 5 loop events. 8 loop tests; full suite 217.
- **Next:** **T7** wire the loop as the worker's generator for code kinds (`function`→loop,
  `answer`→single-shot); worker emits terminal Delivered on loop `delivered`, maps `exhausted`→Failed;
  teardown workspace; resolve `context.refs` into the loop's stable `context` part (carried-from-P1).
  Then **T8** live acceptance (all 6 criteria). NOTE for T7/postmortem: the T-93 mermaid-as-context
  field test hasn't fired — P2's remaining code is architectural (hand-written per conventions); the
  diagram refs are wired + available, so a future loop-adjacent delegation can use them.
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
