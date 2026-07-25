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
- 2026-07-16 (session 122): **`/simplify` DONE** (`5b35301` — 13 fixes: run() decomposed, TriadError,
  intake table, `target_relpath`, Budgets-from-schema; suite 241). **T-99 DECIDED (b)** (`21172f0` —
  auto_verdict ledger-only, P4 joins on run_id). **T-95 RESOLVED (b)** — shared per-call transport
  (`_chat_generation`+`_cold_start_grace`); Generation events single-shot-only by design.
- 2026-07-18 (session 124): **Founding problem RECOVERED + Go-widening groundwork + write-model
  decided.** (1) **T-102**: the founding problem is *multi-session GPU contention* (dropped in the
  T-21→T-88 supersession); sync times out under contention; T-89 scope-limited (interactive-vs-batch
  only), gate needs a wait-tolerance axis (G-D7) + busy-check MVP (G-D8). (2) **T-92 Axis A**: Phase 1
  shipped — `deliverable.language` (declared+inferred, kind-scoped rejects); R1/R3/R4 settled by a
  worktree `go build` experiment. (3) **T-104**: `kind:function` is file-granular (`loop.py:263`
  overwrites whole file) → the loop **reimplements what it should compose** (dropped `patch_file`).
  **M2 (edit) DECIDED = code-anchored** (`locate_unit`→`patch_file`) on cost/timeout-safety;
  benchmark run 1 null on correctness (corpus too easy), clean cost win. Report:
  `ref:oficina-write-model-report`.
- 2026-07-22 (session 126): **M2 REVERSED → whole-file-with-context; edit mode BUILT + ACCEPTED
  (T-110).** Re-grounding caught the code-anchored plan growing an edit language (unit field,
  response validation, import merge) serving no founding fact; T-104 amended (code-anchored =
  on-file fallback, omission trigger); **T-89 routing default revised — delegated codegen async-first,
  small edits included**. Build: Opus subagent T1–T5 + Opus-med adversarial review (MERGE-READY,
  10/10 invariants) + live acceptance R1–R4 (246-line module diff 2+/2−, siblings byte-intact;
  observed drift additive not omissive; uncommitted-guard Failed 1.3s). Suite 279→298. E-D1–E-D9 +
  RESULTS: `docs/plans/oficina-p2-edit-mode.md`.
- 2026-07-23 (session 127): **AXIS A COMPLETE — Go is a supported language (T-92 Phases 2–5, one
  session, suite 329).** Both parsers + language-dispatched `evaluate()` (A2 imposed `-json`;
  greenfield stderr fallback pinned empirically) + loop language axis + **`LanguagePack`
  extracted from the two working implementations** (4 members vs 5–6 predicted; delta =
  `ref:patterns-refactoring-duplicate-first`, duplicate-first discipline validated). **Coder
  defaults = 16K-ctx personas** (32K cannot fit the card — measured 14.2 GiB / 2.5 tok/s
  offloaded vs 11.1 GiB / 13–21 tok/s). Live acceptance greenfield 1-iter Delivered + first Go
  EDIT run (1-line surgical diff). Build via 5 dogfood edit runs incl. stubs-then-retry;
  **loop-economics finding: iteration 1 lands 90–95% and repeat iterations never see the
  residual defect — review-fix-inline won every time** (argues for budgets.iterations=1 default
  on reviewed edit runs). Docstring deleted 4-for-4 (E-D6 systematic). **T-111** filed:
  cooperative cancel can't interrupt an in-flight generation (cancel latency = transport window).
- 2026-07-24 (session 129): **INPUT-FIT GUARD SHIPPED (T-112) + previous-attempt diff (T-120);
  suite 332→340.** A s127 production edit run was found to have **crossed its 16,384 window live**
  (16,425 tokens; crossing verified by probe — Ollama does NOT stop generation at `num_ctx`, it
  evicts). The loop now refuses what cannot fit: `_context_overflow` weighs prompt estimate +
  resolved `num_predict` against the window read from `/api/show` via an injected seam; iteration 1
  fails loud (`ContextBudgetError`, `whose="payload"`), later ones exhaust on `context_budget`, an
  unresolvable ceiling emits `ContextLimitUnknown` once and runs unguarded. Live: refused in 0.72 s,
  zero GPU calls; chars/4 landed within 1.3%. **Bound discovered:** a whole-file edit pays for the
  file TWICE, so files above ~`(num_ctx − tests)/2` cannot be edited whole at all — `loop.py` on the
  16K coder is one, which is why its own build ran on the 32K persona. T-120 removes the *third*
  copy: an edit run's previous attempt is now a diff, so iteration 2 costs what iteration 1 costs.
  **T-119 filed** — a whole-file edit pasted ~110 lines of the acceptance tests INTO the source and
  still reported `passed`/`auto_verdict: 2`/Delivered; tests-green ≠ deliverable-good. **E-D6
  corrected to 5-for-6** (a small-file run preserved the docstring; every deletion has been on a
  large file). Findings: `ref:oficina-ctx-overflow`.
- **Next:** (1) **Axis B kinds reconsideration** (fed by Axis A: language axis proven, taxonomy
  trigger for E-D8 rename + dead `acceptance.validators` removal). (2) **T-119** contamination
  check — decide which of the three candidate detections. (3) T-93 refs-diagram verdict;
  T-86 distribution (`OFICINA_VALIDATE_CODE`/`_REF_LOOKUP`/`OFICINA_GO`). Standing: T-102 gate
  busy-check (G-D8); T-111 cancel gap; T-118 run-provenance convention; prefix-reuse tracking via
  `.claude/tools/ollama-cache-report.py`; harden write-model corpus IF a real edit run drops
  sibling code (the E-D1 fallback trigger — docstring deletions are DOC omissions, not
  code; trigger not fired).
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
- Iteration budget by mode (T-114): edit runs default to **1** (retries never see their own residual), greenfield ~3; +1 repetition-triggered fresh start; explicit budget always wins; phase batching (~3 VRAM swaps/run)
- Judge gates every DPO chosen label (S17); `auto_verdict` ≠ `curated_verdict`
- **Session verdicts ship per RUN, on the deliverable** (T-105, 2026-07-21) — a `run_result` hook
  injects `[VERDICT run_id=…]` iff a deliverable exists. A **second axis** beside `auto_verdict`,
  which is binary and cannot express `1 (improved)`. Detail: KNOWLEDGE.md § "Session verdicts for
  runs".

## Deeper memory

`KNOWLEDGE.md` (implementation invariants — created 2026-07-12 at first build) +
`decisions.md` (S1–S21, V-D1–V-D13) + `evidence.md`.
