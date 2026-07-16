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
  **T7 DONE.** `worker.process_run` branches on kind (`function`→`_run_loop`, else single-shot);
  worker owns terminal Delivered (deliverable = run branch + commit); workspace torn down in finally;
  `context.refs` resolved via `server._build_refs_block` into the loop's stable prefix (closes the
  carried-from-P1 refs gap; the T-93 diagram seam is now LIVE — a run spec's `context.refs` injects a
  mermaid anchor). Loop cancel via injected `is_cancelled`. 5 worker-loop tests; full suite 223.
- 2026-07-15 (session 120): **P2 FIRST SLICE COMPLETE (T1–T8), branch `feature/oficina-p2-loop`.**
  All 6 acceptance criteria met (`ref:delegate-p2-acceptance`); criterion 5 cache confirmed on
  `prompt_eval_duration` (`ref:oficina-p2-cache-measurement`). T-91 resolved. New modules:
  `parser.py`/`prompt.py`/`workspace.py`/`evaluator.py`/`loop.py` + intake/ledger/client/worker
  extensions. Full suite 223 (was 150). ~64 new tests.
- 2026-07-16 (session 121): **P2 first slice REVIEWED (PR #76) + hardened.** 10 confirmed correctness
  bugs fixed w/ regression tests (false-Delivered exit-code guard, eval subprocess + wall-clock
  timeouts, symlink path canonicalization, kind-scoped intake, Exhausted surfaced in result/phase/hook,
  budgets `num_predict`); 5 deferred w/ tasks **T-95–T-99** (`docs/findings/oficina-p2-review-deferred-2026-07-16.md`,
  `ref:oficina-p2-review-deferred`). Test-authoring DSL piloted (`ref:test-executable-spec`, T-100).
  Loop readability refactors landed (0622c26). Suite 235. Commits d0a90df/9b1c5bc/0622c26/961c1e9.
- **Next:** (1) **`/simplify`** the PR diff — orientation `docs/plans/oficina-p2-simplify-orientation-2026-07-16.md`
  (continues the 0622c26 readability thread across the rest of the diff). (2) **T-99** decide
  `auto_verdict`→`calls.jsonl`. (3) post-slice widening (P2-D1: kinds/validators, escalation ladder
  P2-D9, tiny-model classifier P2-D4). T-93 refs-diagram verdict still unmeasured; T-86 distribution
  (`OFICINA_VALIDATE_CODE`). Then push/merge PR #76.
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
