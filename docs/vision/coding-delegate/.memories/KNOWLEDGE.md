# coding-delegate (oficina) — Knowledge (Semantic Memory)

*Implementation invariants accreted during the P1 build. Decisions/rationale at the
vision level stay in `decisions.md`; this file records what the CODE now guarantees.
Write protocol: update sections in place; never append a dated block.*

## Ledger invariants (P1-D5/D6) — 2026-07-12, T1

Offset is derived from disk on every append (count of valid events), never an in-memory
counter — this is what makes the MCP-surface→worker process handoff safe. Named emitters
(`run_submitted()`, `generation_started()`, …) are the public API; `_append` is private.

**The ledger owns its file's integrity: `_append` repairs a crashed-writer tail before
writing** — `_repair_tail` truncates any torn / blank / unterminated tail back to the end
of the last valid newline-terminated line (byte-position truncate via
`_valid_prefix_bytes`, not a rewrite). Without repair, an append onto a torn tail either
swallows the new event (no trailing newline → concatenation) or turns the tolerated tear
into permanent mid-file corruption (trailing newline → tear becomes a middle line).
Repair is race-free by the single-writer invariant. Read-side is symmetric: torn last
line tolerated, trailing blanks stripped, mid-file corruption still raises
`LedgerCorruptionError`.

*Review lesson:* the original test asserted the append's return value but never read the
ledger afterward — green while encoding the bug (`feedback_review_rederive_invariants`).

## Single-writer topology (P1-D6) — 2026-07-12

Enforced by call order, not locks: the MCP surface appends only `RunSubmitted`, then
pushes the queue marker; the worker can only discover a run through the queue →
happens-before handoff. The ONLY lock in the tree is the pidfile `O_CREAT|O_EXCL`.
Cancellation is a flag file (`runs/<id>/cancel`) precisely so non-workers never touch a
ledger.

## PID-reuse guard (P1-D9) — 2026-07-12, T5

Pidfile stores `{pid, start}`; liveness = `kill(pid, 0)` AND `/proc/<pid>/stat` field-22
start-time match (parsed after the LAST `)` — comm may contain spaces/parens). The
start-time reader is injectable, so PID-reuse is testable by feeding a wrong start-time
against a live PID; two smoke tests exercise the real `/proc` reader.

**Implemented in T6:** `ensure_worker` spawns WITHOUT claiming the pidfile — the worker
claims as its FIRST act (`Worker.run()`) and exits immediately if it loses. Until a
worker claims, concurrent submits may briefly double-spawn; the pidfile race decides
the survivor.

## Worker invariants (T6) — 2026-07-12

Generation is an **injectable seam** (`generate: GenerateFn`, mirrors T5's
`start_time_reader`); the default runs today's `generate_code`/`ask_ollama` semantics
per `deliverable.kind` and tags every call in `calls.jsonl` with `run_id` (the one
deliberate `client.py` seam — additive, `dict.get()`-safe, DPO readers unaffected).
Cold-start grace = one retry on `OllamaTimeoutError`. Cancel is cooperative between
stages (checkpoints: intake / pre_generation / pre_packaging) — never interrupts an
in-flight model call. **Triad UNIFIED (P2-T3):** both `Failed` and `IntakeRejected`
payloads now emit `where/whose/what` (intake's old `stage/fault/detail` retired; the
`Rejection` dataclass fields are `where/whose/what`, `what` carrying the detail; a `rule`
name rides alongside for intake).

**Report location:** the delivery report lives in the `Delivered` event payload
(`events.jsonl`, `ledger: forever`) — NOT in `artifacts/`. This is what keeps
`run_result` answerable after retention prunes the workspace.

**`OFICINA_ROOT`** env var overrides the storage root (default
`~/.local/share/oficina/`); tests and acceptance point it at temp dirs.

**P2 wiring (T7):** `process_run` branches on `deliverable.kind` — `LOOP_KINDS` (`function`)
route to `_run_loop` (the P2 evaluated loop); `answer`/`file` keep the P1 single-shot
(GenerationStarted→Finished→Delivered). `_run_loop` constructs the Workspace + EvaluatedLoop
(coder/evaluate are injected seams, default to `loop.default_coder()`/`evaluator.evaluate`),
runs it, and **owns only the terminal `Delivered`** — the deliverable payload references the run
branch + commit (the branch IS the deliverable), not a written target. The loop emits everything
else (AssemblyDone/iteration events/Exhausted/Cancelled). Workspace is always torn down (finally).
`context.refs` is resolved via `server._build_refs_block` (`_resolve_refs_block`, fail-open) into
the loop's stable prompt prefix — closing the carried-from-P1 refs gap AND making a run spec's
`context.refs: ["<diagram-anchor>"]` the live T-93 mechanism. Loop mid-iteration cancel via an
injected `is_cancelled`. The P1 `artifacts/` retention no-op is closed by the worktree branch model.

**Now planned (T-92 P2 plan, session 119, `docs/plans/oficina-p2-evaluated-loop.md`):** the
worktree workspace (P2-D5) fixes the `artifacts/` retention no-op; `refs` in the worker + triad-key
unification are the plan's explicit carried-from-P1 items; the `server.py` private-helper promotion
lands in build step T7. See the plan's "Build kickoff" section for module/seam/test/validator anchors.

## Write model: the loop composes bridge tools, it does NOT reimplement them — 2026-07-18 (session 124, T-104)

`loop.py:263` `target_path.write_text(gen.content)` **overwrites the entire target file** each
iteration → `kind:function` is **file-granular, not function-granular**: its only real client is a
greenfield single-unit file (the shape of the P2 acceptance fixture — behavior shaped by the test,
not a real editing client). Point it at a populated module and it nukes the module.

**Root cause = the loop reimplements what it should compose.** It rightly shares the chat transport
(T-95) and rightly reimplements prompt assembly (the P2-D2 cache-prefix contract), but its bespoke
`write_text` **silently dropped `patch_file`**, which already exists in the same server. "Lacks
patch_file's mode" IS "whole-file only". **Principle: oficina composes the ollama-bridge tools, it
does not reimplement them** — sibling of T-95 (transport) and the T-102 gate/busy-check (a scheduler
proposed where a busy-check existed). Each time, the re-authored local version is the cruder one.

**M2 (edit) REVERSED to whole-file-with-context and BUILT + ACCEPTED (T-110, session 126,
E-D1–E-D9).** The code-anchored `locate_unit`→`patch_file` design above is retained as the recorded
FALLBACK — its timeout-safety leg was sync-path-only (the loop runs under `spec.timeout_s` 1800s)
and its edit-language cost (a `unit` spec field, response-shape validation, import merging) was
never priced; `ref:oficina-write-model-report` § AMENDMENT. Edit runs feed the committed file into
the prompt as a `current_file` STABLE segment (C0 content — cache-safe by construction) with
mode-selected constraints; the model returns the whole modified file; the unchanged loop evaluates
it. Mode = target committed at HEAD (E-D2, no spec field); an uncommitted target is a fail-loud
`AssemblyError` (live: Failed in 1.3 s, zero GPU). Fence-strip moved to the loop's write step (the
loop owns its write invariant); edit `num_predict` sizes to the file — `max(2048, ceil(chars/4)*2)`
cap 8192, explicit budget wins — resolved post-assembly, passed per-call (E-D9). Iteration budget
follows the same shape (T-114): an edit run defaults to 1 iteration (s127 5/5 — retries never saw
their own residual defect), greenfield keeps 3, explicit always wins, resolved post-assembly in `run()`. Live acceptance
(4 runs): a 246-line module delivered with diff 2+/2−, all 24 siblings byte-intact; the observed
whole-file drift is ADDITIVE (unrequested annotations), not omissive; every run converged in
iteration 1 (tests-as-context). Fallback trigger unchanged: a real edit run dropping sibling code
→ harden the corpus, revisit code-anchored. Plan + results: `docs/plans/oficina-p2-edit-mode.md`
(`ref:oficina-edit-mode`, `ref:oficina-edit-mode-decisions`).

## P4 judge gate — what the code now guarantees (T1–T9) — 2026-07-28

- **The judge runs ONCE at packaging and gates nothing.** `Judged{rubric, model, passed,
  judge_verdict, criteria[]}` is a **non-folding run event** — the run is `working` before and
  after, and `passed: false` does NOT block `Delivered`. S17 gates DPO *chosen labels*, not
  delivery; H1 is Claude-gated by design. A judge that errors, times out or returns unparseable
  output degrades to a report, because by packaging the deliverable already exists.
- **Opt-in by `acceptance.rubric`.** No rubric → no judge, and the run delivers exactly as it did
  before P4. `approval_gate` is recognized but **refused** until P5 supplies `answer_run`; a gate
  built now could enter `input_required` with nothing able to clear it.
- **The judge is fed the run's DIFF, not the delivered file** (`LoopResult.change`). Measured,
  not assumed: with the file plus drift metrics it scored a 78-line acceptance-test leak **5**
  and wrote "contains only the requested change"; with the diff, **2** — at ~33% fewer tokens.
  A comparative question is unanswerable from one side of the comparison, and metrics are read as
  background when they contradict the artifact in view. `ref:judge-sees-the-change`.
- **oficina composes the RUBRIC and owns the CALL.** The rubric YAML is read as-is; the model call
  goes through `_chat_generation` (extended with optional `system=`/`schema=`) because per-call
  transport is ONE spelling (T-95). Composing the evaluator's `run_phase2` would have used its own
  transport, leaving the judge call with no `calls.jsonl` record, no `run_id` and no `call_id`.
  Verified: an accepted run logs **two** call records, coder and judge.
- **A rubric written for greenfield can REWARD an edit defect.** Unmodified `code-python` scored
  the leaked file 5/5, its `completeness` criterion calling the pasted tests "a usage example".
  `evaluator/rubrics/oficina-edit.yaml` exists for edit runs and is kept separate, since
  `code-python` is shared with the Layer-4 benchmark suite where output has no prior scope.
- **`passed` is a CONJUNCTION and `judge_verdict` is its MIN — never an average (P4-D8/D9/D10).**
  Each criterion's cut is declared in the rubric as `passing_score`, beside the scale it judges
  (`oficina-edit` = 4 on both criteria; `_DEFAULT_PASSING_SCORE = 3` for rubrics declaring none) —
  a cut kept in code against a scale kept in data is how a coherent severity ladder came to sit one
  rung above its threshold. The verdict reduces the way the gate gates, and **any** unscoreable
  criterion yields `0`: reducing over only the criteria that *did* score is how the old mean
  reported **5** on a run whose gate withheld, and a min over the same filtered subset would have
  too. **An empty criterion set withholds as well** — `all([])` is True, so a rubric declaring no
  phase-2 criteria would otherwise pass having judged nothing and called no model. `weight` is **deleted** from `oficina-edit.yaml` — no weighting can make an average agree
  with an AND (ranking `(5,3)` below `(4,4)` needs `w₁<w₂`; `(3,5)` needs `w₂<w₁`), so it was
  unusable here, not merely unused.
- **Drift is surfaced, never gated** (`drift.py` → `LoopResult.drift` → the report):
  `hunks`, `lines_added`/`lines_removed`, `max_verbatim_run_vs_tests`. `files_touched` was
  specified at freeze and **dropped at build**: the loop writes exactly one file, so it would fire
  unconditionally (first principle 6). Blank lines are filtered BEFORE matching — `SequenceMatcher`'s
  `isjunk` stops junk anchoring a match but the winning block still absorbs adjacent junk.
- **The report is `Delivered`-payload-resident and compactness is a hard constraint** — it is paid
  for in the caller's context on every `run_result`, with no pointer indirection. `auto_verdict`
  is surfaced as `tests_passed`; `error_keys` are omitted.

## LanguagePack — the language axis contract (T-92 Phase 4) — 2026-07-23

- **One algorithm, N packs.** `evaluate()`'s flow (target-presence rule, first-failing-stage
  P2-D8) is invariant; a frozen `LanguagePack` in `evaluator.py` supplies the varying steps:
  `{compile_stage, test_stage, system_prompt, coder_model}`. `LANGUAGES = {"python": PYTHON,
  "go": GO}`; selection via `language_pack(spec)` → `resolve_language` (R1), Python fallback.
- **Stage functions share one signature** `(worktree, base_repo, spec, timeout_s)` — each
  adapter consumes what it needs. The member is the whole STAGE, not a parse function:
  Go's test stage OWNS its command (imposes `go test -json ./...`, A2 — Package-field
  attribution) while Python honors the caller's `test_cmd`. Do not "unify" that away.
- **Go internals stay module-private, not pack surface:** `_go_binary` (`OFICINA_GO` env →
  `which` → literal), `_read_go_module` (go.mod), and the go<1.24 stderr fallback (build
  failures under `go test -json` arrive UNWRAPPED on stderr in go-build shape — every
  greenfield C0 hits this; without the `_parse_go_build(stderr)` fallback, assembly dies).
- **The pack lives in `evaluator.py`** (loop imports it) — a separate module would need
  evaluator's stages AND be needed by `evaluate()` (cycle). The generation-side values
  (system/persona) in an evaluation module are an accepted altitude wart, noted in-code.
- **Coder defaults are the 16K-ctx personas** (`my-*-q25c14-16k`): 32K live footprint
  14.2 GiB cannot fit the 12 GB card (2.5 tok/s offloaded); 16K = 11.1 GiB VRAM-fit at
  13–21 tok/s.
- **Input-fit guard (T-112, s129) — the loop refuses what cannot fit.** `_context_overflow`
  weighs `ceil(len(prompt)/4) + the resolved num_predict` against the model's window, read
  live from `/api/show` via an injected `context_limit_for` seam (the loop resolves its own
  model, so the worker cannot look it up first). Iteration 1 over → fail-loud
  `ContextBudgetError` (`whose="payload"`; the remedy is the caller's), later iterations →
  `_exhausted(limit_hit="context_budget")` with the best attempt. An unresolvable ceiling
  disables the guard and says so ONCE via the `ContextLimitUnknown` run event — never guesses,
  because guessing high disables it silently and guessing low aborts valid work. Live: refused
  in 0.72 s with zero GPU calls; the chars/4 estimate came within 1.3% of the real count.
- **A whole-file edit pays for the file TWICE** (once in the prompt, once in the output), so on
  a given persona files above roughly `(num_ctx − tests − overhead) / 2` cannot be edited whole
  **at all** — `loop.py` on the 16K coder is a worked example (no `num_predict` both fits the
  window and suffices to emit the file). Code-anchoring does not have this bound: it pays for
  the file once. This is a third leg the M2 decision never weighed — it priced cost-per-token
  and timeout safety, never window feasibility. `ref:oficina-ctx-overflow`.
- Extraction delta vs the seam-map prediction: `ref:patterns-refactoring-duplicate-first`.

## P2 evaluated loop — validator-output parser contract (P2-T1) — 2026-07-15

`oficina/parser.py` is the ONE place validator/evaluation output is parsed. `parse_validator_output(stage, payload)`
folds two unrelated raw shapes — the compile stage's `validate-code.py` JSON array (`{file, status,
errors:[{type,text,line}]}`) and the test stage's raw pytest short-summary text — into a list of
`ParsedFailure{stage, file, error_key, raw}`. **Stage is passed in, never sniffed** (the caller always
knows which stage it just ran). Three readers consume the one shape and never re-parse: `category_for`
reads `.stage` (P2-D8), the repetition signature reads `.error_key` (P2-D7), `scope_of` reads `.file`
(P2-D12). **Category is not a pure function of `.stage`** — the test stage splits by `error_key[0]`
prefix (`pytest-error:`→mechanical, `pytest-failed:`→structural), the Python `py_compile`-only caveat
where undefined-name/import defects only surface at the test stage. `error_key` = `(kind, detail)` with
volatile coordinates stripped by `_normalize` (paths→basename, line/col removed, hex addrs removed,
slugified) so a defect keys identically across line shifts. 20 tests; test bodies + impl local-model-generated.

## P2 evaluated loop (P2-T6; P2-D1/D2/D4/D7/D10) — 2026-07-15

`oficina/loop.py` `EvaluatedLoop.run()` — collaborators (coder, evaluate, workspace, ledger) are
INJECTED so the loop is unit-testable with fakes (no GPU/git in the pure path; the worker wires
real ones at T7). Flow per iteration: `IterationStarted` → `build_prompt({**stable, **variable})`
→ coder → write output to the target in the worktree → `snapshot` → **anti-cheat** (`diff_touches_
test_files` vs the previous snapshot; a hit short-circuits eval and rejects the iteration) →
`evaluate` (injected `EvaluateFn`) → `attribute` (delta-scope) → `IterationEvaluated{passed,
stage_failed, failure_class, error_keys, auto_verdict}` → pass ⇒ return `delivered`; else classify
(rule-based `category_for`, P2-D4 — NO model call) + `_signature` (sorted error_key set, P2-D7):
repeated signature within budget ⇒ `FreshStart` (drop the variable tail, keep the stable prefix);
else append repair feedback. Budget out ⇒ `Exhausted` (best attempt = fewest attributable failures,
never silently empty — S11). **The loop emits iteration events + `Exhausted` but NOT `Delivered`** —
terminal `Delivered`/packaging stays the worker's job (T7). Model is a single persona (P2-D1, no
escalation ladder yet). `category_for` is **fail-loud** — a test-stage failure must carry a
`pytest-error:`/`pytest-failed:` key (which the real T1 parser guarantees).

**T-91 RESOLVED (P2 prereq):** `client.chat` gained `num_predict`; the loop's `default_coder` floors
it (never truncate a function) and caps it (bound runaway) via `NUM_PREDICT=2048`. Root cause
confirmed live this session: the sync `generate_code` path inherited the model default and truncated
functions mid-body 4× during T1/T2/T5 test-body delegation. The async worker path was unaffected,
which is why the plan routes the loop through the worker seam, not the sync tool.

## Session verdicts for runs — a second axis beside `auto_verdict` (T-105) — 2026-07-21

A `PostToolUse` hook on `run_result` injects `[VERDICT run_id=…]` **once per run, judged on the
deliverable** — never per loop iteration. The calling session reviews the artifact, not the N
repair attempts; 18 oficina-tagged calls spanned 12 runs, so per-run judging asks ~12 questions
instead of 18, and asks about the thing actually inspected.

**Trigger rule:** prompted iff `result["deliverable"]` is non-null. That single condition gets the
whole state machine right — `Failed`/`IntakeRejected`/`Cancelled` stay silent (the ledger's
`auto_verdict` already records those as 0), `Exhausted` **is** judged because it surfaces a best
attempt (S11), and polling `run_result` before terminal does not prompt.

**Identity is free here, unlike the generate_code path.** `run_result(run_id)` names its subject in
the *request*, so the hook reads `tool_input["run_id"]`; `generate_code` reveals identity only
through its *response* and must match on content. Tools that name what they operate on are
trivially hookable — worth remembering when designing future tools.

**Why this is NOT redundant with `auto_verdict`.** `loop.py`'s `auto_verdict = 2 if passed else 0`
is mechanical and binary: did the evaluator's tests pass. It **structurally cannot express
`1 (improved)`** — *correct, but I had to change it* — historically **64.8%** of all verdicts and
the richest DPO category. The two are different axes; keep both. (`auto_verdict` remains
ledger-only per T-99; the P4 DPO pass joins ledger↔`calls.jsonl` on `run_id`.)

**Record shape:** `run_id` + `tool: "oficina"`, and deliberately **no `call_id`** — a run spans
several calls and naming one would misattribute the judgment. Readers tolerate the heterogeneous
key. **Gotcha:** run ids are base64url (`-L-rwoCLLsoL33eirtSRzw`), so the capture regex had to widen
from `[a-f0-9]` to `[A-Za-z0-9_-]`; a hex-only class rejects run-keyed blocks *silently*. Tests must
use a real run id — a hex-shaped stand-in passes against the broken regex and proves nothing.

Source / more detail: `docs/findings/verdict-coverage-collapse-2026-07-21.md`,
`docs/plans/verdict-capture-repair.md` § Phase 4.

## P2 T8 live acceptance — all 6 criteria met — 2026-07-15

Verified live (real Ollama, real git repo) + by the 223-test suite. (1) **Headline:** a seeded
compile defect (iter1, mechanical/verdict-0) was repaired by the real model on iter2 → Delivered,
zero Claude edits. (2) exhaustion attaches best attempt (suite). (3) delta-scope both directions incl.
the masking inverse (suite). (4) anti-cheat rejects a test-editing iteration (suite). (5) **cache**
confirmed on `prompt_eval_duration` — 477 tok @ 156 ms vs cold 409 tok @ 443 ms (prefix reused);
NOT on `prompt_eval_count` (Ollama reports full tokens) — `calls.jsonl` now logs
`prompt_eval_duration_ms` (`ref:oficina-p2-cache-measurement`). (6) ledger folds correctly;
AssemblyDone carries `baseline_failure_count`, IterationEvaluated carries `auto_verdict`.
**Product note:** tests-as-context (P2-D13) makes the coder converge on iter1 when the pre-authored
tests fully specify behavior — observed live (a ValueError edge case the terse objective omitted was
satisfied because the test was in the stable prefix).

## P2 review hardening (PR #76, session 121) — invariants a green suite hid

The T8 suite was green but encoded the same assumptions as several bugs (the "re-derive invariants,
not trust green tests" rule paid off). Load-bearing fixes now in place — treat these as invariants:
- **Evaluation NEVER reports a false pass.** `evaluator._run_test_stage` reads the exit code: a
  non-zero exit with no parseable pytest short-summary failure **raises** (tooling failure), it does
  not return `[]`. The parser scans only the `short test summary info` block, so application `ERROR`
  log lines are not phantom failures. A tooling failure must never flow through delta-scoping.
- **Every eval subprocess is time-bounded** (`_STAGE_TIMEOUT_S`, and the loop's `budgets.wall_clock_s`
  guard emitting `Exhausted(limit_hit="timeout")`) — a generated infinite loop can't wedge the worker.
- **Paths are canonicalized** (`os.path.realpath` both sides before `relpath`) — a symlink-spelled
  target (this host's `~/workspaces` → `/mnt/i/workspaces`) no longer escapes the worktree.
- **Intake is kind-scoped:** `worktree`/`acceptance.test_cmd` are rejected on non-loop kinds (a
  `kind:file`+acceptance spec was silently single-shot in place); budgets keys are fail-loud;
  `budgets.num_predict` is a real field threaded to the coder.
- **`Exhausted` is a first-class terminal:** surfaced by `service.result()` (best-attempt branch/commit,
  S11), the phase map, and the runs-scan hook — it was invisible to all three.

**Deferred (need frozen-code reshape / a decision), tasks T-95–T-99:** ~~the loop is a parallel
`_run_loop` beside the `GenerateFn` seam~~ **T-95 RESOLVED (b), session 122:** per-call transport
is ONE spelling (`worker._chat_generation` + `_cold_start_grace`, used by single-shot AND
`default_coder`; `spec.timeout_s` reaches the loop coder) — Generation events stay
**single-shot-only BY DESIGN** (the loop narrates via Iteration events; per-call telemetry =
`calls.jsonl` run_id join per T-99(b); `fold_phase` would break otherwise). Still open:
`context.refs` dropped when the worker lacks `LLM_REPO_ROOT` (T-96); retention doesn't
`git worktree prune` (T-97); `scope_of`/anti-cheat compare by basename only (T-98).
~~`auto_verdict` never reaches `calls.jsonl`~~ **T-99 DECIDED (b), session 122: ledger-only** —
the P4 DPO pass joins ledger↔calls on `run_id` (no call-record back-write); plan corrected in
place; revisit join mechanics at P4. Full analysis + decision records:
`docs/findings/oficina-p2-review-deferred-2026-07-16.md` (`ref:oficina-p2-review-deferred`).

**Tests use the executable-spec DSL** (`ref:test-executable-spec`): `test_loop`/`test_intake`/
`test_worker_loop` converted; the `given`/`when` split is the triage rule for which tests to convert.

## P2 evaluation + delta-scoped attribution (P2-T5; P2-D8/D12/D13) — 2026-07-15

`oficina/evaluator.py`. `evaluate(worktree, base_repo, spec)` is the real `EvaluateFn`: stages run
IN ORDER, first failing stage wins (P2-D8). Compile runs only if the target exists in the worktree
(so C0 — deliverable absent — goes straight to the test stage, surfacing the import/undefined
failure); it shells `benchmarks/lib/run-validate-code.sh` (resolved via `OFICINA_VALIDATE_CODE` env
or repo-relative `parents[4]` — the machine-global-install path fix is deferred to T-86) and parses
its JSON with T1. Test stage runs `test_cmd` (`shell=True`, `cwd=worktree`) and parses pytest via T1.
**`attribute(current, baseline, target_files, test_files)` is the P2-D12 correctness core** (the
advisor's masking hole): a current failure is subtracted **only if out-of-scope AND its error_key is
in the out-of-scope baseline** — target-file failures and ALL test outcomes are never subtracted, so
a misnamed/absent target (whose `undefined foo` shares C0's baseline key but lands in target/test
scope) stays live and the loop can't declare success on broken code. `diff_touches_test_files(worktree,
from, to, test_files)` is the free anti-cheat (P2-D13): non-empty ⇒ the iteration edited the acceptance
criteria ⇒ reject it. `EvaluateFn` seam is now `(worktree, base_repo, spec)` (refined from T4's
2-arg — evaluation needs the repo→worktree target mapping).

## P2 worktree workspace lifecycle (P2-T4; P2-D5/D13) — 2026-07-15

`oficina/workspace.py` `Workspace` owns one git worktree per run, reused across iterations.
`assemble()` runs the P2-D13 sequence: resolve the base repo (git top-level above the target) →
`git worktree add -b oficina-run-<id> <run_dir>/worktree HEAD` → verify every declared `test_file`
is present in the checkout (first slice: tests are committed; a declared-but-absent test_file is an
`AssemblyError` — no content source in v1 schema) → commit **C0** (`--allow-empty`, oficina identity
via `-c` flags so host git-config is irrelevant) → evaluate C0 via the **injected `EvaluateFn` seam**
(mirrors P1's `start_time_reader`/`generate`; the worker passes the real evaluator, T5) → build the
run-constant stable prompt parts (objective + tests-read-from-worktree + context files; system/
constraints/refs layered in T6) → return `Assembly`, and if given an `emit` callback, fire
`AssemblyDone{worktree_path, base_commit, test_files_materialized, baseline_failure_count}`.
`snapshot(msg)` commits per iteration (powers the T5 delta diff + forensics). `teardown()` is
`git worktree remove --force` + **`git worktree prune`** (both, per the P2-D5 advisor note — retention's
`rm -rf` alone leaves a dangling `.git/worktrees/<id>`) and is idempotent; it **keeps the run branch**
(the branch IS the deliverable, S15). Ledger gained the `assembly_done` emitter + `AssemblyDone`→working
fold. This closes the P1 `artifacts/` retention no-op.

## Intake rule model (P1-D3) — 2026-07-12, T3

Pydantic models (`extra="forbid"`) are the schema of record; the allowed-key sets for
the fail-loud unknown-key checks are DERIVED from `model_fields`, so schema and check
cannot drift. Every rejection is a named rule constant + where/whose/what triad
(`stage=intake, fault=payload`). Accepted specs pass through as the same object — no
normalization. Intake returns its verdict; it never raises (the worker turns a rejection
into `IntakeRejected` whose payload IS the rejection).

**P2-T3 additions (P2-D13):** new schema models `Acceptance` (`test_cmd`/`test_files`/`validators`/
`structural`; `rubric` deliberately absent → `extra="forbid"` rejects it, keeping P4 scope out) and
`Budgets` (iterations/fresh_starts/wall_clock_s/tokens; enforced later in T6). New kind `function`
(the loop deliverable) requires a `target` (like `file`) AND `acceptance.test_cmd`. Three new
rejections: `acceptance_required` (function without a test_cmd gate), `worktree_required`
(`test_cmd` with a non-worktree workspace — tests need isolation, P2-D5), `target_not_git_repo`
(worktree workspace whose target isn't inside a git repo — checked by `_git_root` walking up for a
`.git` entry, subprocess-free). `SUPPORTED_WORKSPACES` now = {in_place, worktree}.

## FIFO details that would be easy to break — 2026-07-12, T4

Pop order is the NUMERIC epoch-ms prefix (not lexicographic), tie-broken by name.
Run-ID recovery splits on the FIRST dash — `token_urlsafe` IDs may contain `-`.
Push is tmp+`os.rename` (atomic, same dir); markers are distinct by construction.
Pop is not concurrent-pop-safe — safe only because pidfile arbitration guarantees a
single popper.

## Distribution: oficina is machine-global, NOT an overlay — 2026-07-12 (session 115)

oficina is a **machine-global capability**, not per-repo files. The three channels that
enable it are all machine-level and independent of any repo's overlays:
1. **CLI** — `~/.local/bin/oficina` (`uv tool install --editable <repo>/mcp-server`; entry
   point `ollama_mcp.oficina.cli:main`).
2. **MCP tools** — `submit_run`/`run_status`/`run_result`/`cancel_run` come from
   `ollama-bridge` registered **user-level** in `~/.claude.json`, so they're live in EVERY
   Claude Code session (any repo).
3. **Store** — `~/.local/share/oficina/` (shared; runs carry absolute target paths, P1-D7),
   plus Ollama running.

**Overlays vs oficina (the mental model):** overlays (`install-overlay.py` → `session-tracking`
/ `ref-indexing` / `ollama-scaffolding`) copy **text/config into a repo** — the *recipe card*.
oficina is **executable code + a registered service** — the *kitchen*. Installing an overlay on
a new machine gives you conventions docs, NOT the oficina capability. **`ollama-scaffolding` has
zero reference to oficina** (grep-confirmed) — it teaches only the synchronous
`generate_code`/`ask_ollama` path; it is NOT the way oficina is distributed and does not "point"
to it. **New-machine enablement = the 3 steps above, never an overlay install.**

Open (T-86): whether `ollama-scaffolding` should eventually teach async-vs-sync (P2-era, not
now — sync is right for small calls), a provisioning runbook for the 3 steps, and when oficina
crosses P1-D1's "split to a published package" trigger (installable without the mcp-server
checkout).

## T-81 outcome — install-overlay was the WRONG first client for oficina — 2026-07-12 (session 115)

T-81 (`install-overlay --mode ai` preview) was the plan's candidate first client. Building it
proved it does **not** benefit from oficina: install-overlay is a **one-shot CLI with nothing to
do while the GPU works**, so oficina's headline win (Claude-works-while-GPU-works parallelism) is
worthless to it. Its two real defects were solved WITHOUT async — a preview/stage-apply split
(client-side) and a `num_ctx`-fit + `think:false` latency fix (`docs/plans/t81-part1-*` /
`t81-part2-*`, `ref:overlay-ai-merge-mode`). **Lesson for picking oficina's real first client:
the value lands only when the client is an AGENT that can parallelize** (submit → do other work →
collect), not a batch CLI. Revisit which consumer that is (a long Claude-driven multi-deliverable
flow, or T-81 Part 2's own big merges *if* driven from an agent loop).
