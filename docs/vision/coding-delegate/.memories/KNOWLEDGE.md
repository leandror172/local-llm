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
