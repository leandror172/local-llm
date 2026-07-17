# oficina P2 (PR #76) review — deferred findings

**Date:** 2026-07-16 (session 121). **Reviewed:** branch `feature/oficina-p2-loop` (PR #76), the
evaluated coder⇄evaluator loop first slice (T-92). **Method:** plan-conformance read + 8-angle
code-review with adversarial verify + live Opus behavioral run + security review.

The confirmed correctness bugs with unambiguous fixes were fixed in session 121 (parser exit-code /
short-summary scoping, subprocess+wall-clock timeouts, symlink path canonicalization, intake
kind-scoped worktree/acceptance rejections + budgets unknown-key check + `num_predict`, `service`
Exhausted terminal + phase map, runs-scan hook Exhausted case, dup `CONSTRAINTS:` header, loop
cold-start retry). **This file logs the items deliberately NOT fixed in that pass** — each either
reshapes a frozen decision, touches P1 spawn code, needs a design choice, or is a plan/reality
mismatch to resolve rather than a patch. Tasks: T-95…T-99.

<!-- ref:oficina-p2-review-deferred -->

## T-95 — The loop is a parallel `_run_loop` path, not a `GenerateFn` filling P1's seam

**What the plan froze.** `docs/plans/oficina-p2-evaluated-loop.md` repeatedly frames the loop as
"a new `GenerateFn` filling the worker's injectable `generate:` seam — additive, not a restructure"
(plan lines 9, 28–30, 424–426). The freeze's intent: reuse P1's one seam so the single-shot default
stays for `kind: answer`/`file` and the loop is just another `GenerateFn` for code kinds.

**What was actually built (T7, commit `69de350`).** `worker.process_run` branches on
`deliverable.kind in LOOP_KINDS` into a **separate `_run_loop` method** beside the seam, with two
new ad-hoc injection points (`loop_coder`, `loop_evaluate`). The original `generate: GenerateFn`
seam is untouched and unused by loop runs.

### Why it was frozen "as a GenerateFn" — and why that framing was imprecise
The freeze was written before T6/T7 were built, reasoning by analogy to P1's seam ("the worker seam
exists; the loop is a new implementation of it"). But the two are **different altitudes with
incompatible contracts**, which the implementation correctly discovered:
- `GenerateFn = Callable[[Dict, str], GenerationResult]` — takes `(spec, run_id)`, returns ONE
  `GenerationResult` (a content string). `_package` then writes that content to the target file.
- The loop's per-iteration generator is `CoderFn = Callable[[str, str, str], GenerationResult]` —
  takes `(prompt, model, run_id)`, a *different signature*.
- The loop **as a whole** returns a `LoopResult` (branch + commit), NOT a `GenerationResult`, and its
  deliverable is a **git branch**, not written content. The worker's `_run_loop` owns a bespoke
  terminal `Delivered` referencing the branch; the loop emits its own event stream
  (AssemblyDone/iteration events/Exhausted) and owns a worktree lifecycle.

So the frozen "loop IS a GenerateFn" conflated *the run* (which produces a branch, not content) with
*a single generation call inside the run* (which is a `CoderFn`). The parallel `_run_loop` is a
defensible correction of an imprecise freeze — cramming the loop into `GenerateFn` would leak branch
semantics through a content-shaped return, or force `GenerateFn`/`_package` to become a variant type
serving two very different consumers.

### A reason (other than the freeze) to keep it as-is
The one-shot seam's contract stays clean: "generate content → package writes it." The loop's
run-level shape (branch deliverable, multi-event, worktree-owning) is genuinely different and
deserves its own path rather than a widened union seam used by only two consumers. Keeping them
separate honors the house rule against over-generalizing a seam ahead of a real third consumer.

### What we lose by NOT unifying (the real cost — and the *targeted* fix)
The finding is NOT "the run should be a GenerateFn." It is that **the per-call cross-cutting behavior
is not shared**, because the loop's `self.coder(...)` call site bypasses the wrapper the single-shot
path uses (`_run_generation` → `_generate_with_cold_start_grace`). Concretely, loop runs lose:
- **cold-start grace** — single-shot retries once on `OllamaTimeoutError`; the loop originally did
  not (session-121 patched this *narrowly* inside `default_coder`, but the asymmetry remains as a
  pattern). CONFIRMED.
- **`GenerationStarted`/`GenerationFinished` events** — never emitted for loop runs, so any ledger
  consumer of per-generation telemetry sees single-shot runs only. CONFIRMED.
- **`spec.timeout_s`** — read only by the single-shot path; `default_coder` hardcodes 1800. CONFIRMED.

**Targeted fix (deferred):** extract the per-call wrapper (cold-start grace + Generation events +
timeout resolution) so BOTH the single-shot `GenerateFn` path and each loop iteration's `CoderFn`
call route through it. This shares the cross-cutting behavior WITHOUT forcing the loop into the
one-shot seam. **Deferred because** it restructures the frozen worker and wants the author's eyes on
the seam design (which of `GenerateFn`/`CoderFn` owns the wrapper), not an unattended rewrite.

**RESOLVED (b): call-level transport helper; Generation events single-shot-only BY DESIGN**
(2026-07-16, session 122, user call). The finding's three losses decompose: grace and timeout are
per-call *transport* mechanics — now written once as `worker._chat_generation` (client lifecycle,
`think=False`, `run_id` tag, `num_predict`, fence-strip) + `worker._cold_start_grace` (the single
retry), composed by both `_default_generate` and `loop.default_coder`; `spec.timeout_s` now reaches
the loop coder. The Generation events, by contrast, are the single-shot run's *phase narrative*, not
per-call mechanics — injecting them into loop runs would duplicate what IterationStarted/Evaluated +
`calls.jsonl` (run_id-joined, per T-99(b)) already record, and would break `fold_phase`
(`GenerationFinished`→phase `packaging` mid-loop). The asymmetry is therefore intended, and was
already pinned by `test_worker_loop`'s "`GenerationStarted` not in loop runs" assertion. The
rejected alternative (worker-side wrapper emitting Generation events per iteration) is on record
here in case a ledger consumer someday needs per-iteration generation telemetry the calls.jsonl
join cannot provide. 6 new tests incl. the `EvaluationError.where`-attribution pin (suite 241).

## T-96 — `context.refs` silently dropped when the worker lacks `LLM_REPO_ROOT`

**Bug.** `worker._resolve_refs_block` (worker.py:168-185) resolves `context.refs` (the T-93 diagram
seam) through `server._build_refs_block`, which needs `LLM_REPO_ROOT` to locate
`.claude/tools/ref-lookup.sh` (server.py:107; `config.REPO_ROOT` reads it at import). That env var is
exported **only** by `mcp-server/run-server.sh`. `workerproc.spawn_detached` passes no `env=`, so the
long-lived detached worker permanently inherits whatever surface won the spawn race:
- MCP-spawned worker → has `LLM_REPO_ROOT` → refs resolve.
- CLI-spawned worker (`oficina submit` from a plain shell) → lacks it → `_build_refs_block` returns
  the string `"Error: LLM_REPO_ROOT not set"`, and the fail-open guard (worker.py:183-185) converts
  it to `""` with **no event and no log line**.

**Impact.** A run whose spec injects `context.refs` runs every iteration WITHOUT the docs it asked
for; the quality degradation is untraceable to its cause. CONFIRMED (chain verified link-by-link).

**Severity:** lower — `context.refs` is optional and the T-93 seam is not yet field-used.

**Fix approach (deferred — touches P1 spawn code):** either (a) `workerproc.spawn_detached` captures
a resolved repo root and passes it in `env=`, or (b) ref-resolution falls back to a package-relative
root the way `evaluator._validate_code_script` already does (`Path(__file__).resolve().parents[4]` /
an `OFICINA_*` override), or (c) at minimum, stop silently swallowing — emit a ledger note or log
when refs were requested but dropped. **Deferred because** getting env-propagation wrong on a
detached, long-lived daemon is exactly what not to do unattended; and it reaches outside P2's blast
radius. Cross-ref: T-86 distribution runbook (the worker's env on fresh machines).

## T-97 — Retention never prunes worktrees (P2-D5 half unmet)

**Bug.** P2-D5 states *both* teardown AND the retention sweep must `git worktree prune` the target,
else dangling `.git/worktrees/<id>` entries accumulate. Teardown holds up its half (worktree remove
+ prune, in a `finally`). **Retention does not:** `retention._prune_artifacts` only `rmtree`s the
`artifacts/` dir; no retention path touches `runs/<id>/workspace/worktree` or runs `git worktree
prune`. CONFIRMED.

**When it bites.** Only after a **hard crash** (SIGKILL/OOM/power-loss) that skips teardown's
`finally`. Sharpened: the `workspaces_ttl_days` policy measures staleness by the *artifacts* dir
mtime and **skips runs whose artifacts are empty** — which is exactly a crashed worktree run's state
— so the leak is doubly unreachable by the current sweep. Also note the policy-name/action mismatch:
`workspaces_ttl_days` prunes artifacts, not workspaces.

**Fix approach (deferred — new retention logic):** teach the sweep about worktrees — for each run
past TTL, `git worktree prune` the target repo and remove the run's `workspace/` tree — and fix the
policy to measure staleness by the run dir, not the artifacts dir. Wants a small design (which repo
to prune when the target moved/was deleted) rather than a bolt-on.

## T-98 — `scope_of` (and anti-cheat, and `target_files`) compare by basename only

**Bug.** `parser.scope_of` classifies a failure's file as target/test/out **by basename**
(parser.py:209), as do `evaluator.diff_touches_test_files` (basename set) and the loop's
`target_files = [basename(target_rel)]` (loop.py). Scope drives the P2-D12 masking guard, so a
basename collision flips scope *silently*:
- out-of-scope wart in `lib/util.py` with target `src/util.py` → classified `target` → never
  subtracted → the loop can never pass (permanent false-exhaustion on a wart the coder can't fix);
- target `src/test_utils.py` colliding with declared `tests/test_utils.py` → every iteration's own
  write fires anti-cheat → evaluation never runs.
CONFIRMED. The code chose basename deliberately ("so absolute-path vs relative-path spellings
agree") — a bandaid for a path-normalization problem.

**Severity:** in the single-file first slice a collision is unlikely but real; goes more live with
multi-file deliverables (post-slice).

**Fix approach (deferred — coordinated, deeper change):** normalize both sides to **worktree-relative
paths** once (target and each failure's file), then compare full relative paths, not basenames. This
ripples through `scope_of`, `diff_touches_test_files`, and the loop's `target_files`, and interacts
with T-95's parser attribution — worth doing as one path-normalization change rather than piecemeal.

## T-99 — `auto_verdict` is never written to `calls.jsonl` (plan/reality mismatch)

**Not a code bug — a plan overclaim the live run exposed.** Plan T6 and event-note S17 state the loop
"writes `auto_verdict` into `calls.jsonl` with `run_id`." The live verification run showed all three
coder calls with `auto_verdict=None` in `calls.jsonl`, and grep confirms no code path back-writes it:
`auto_verdict` exists only in the ledger's `IterationEvaluated` payload (loop.py). CONFIRMED live.

**Why it matters.** This is the seam to the future DPO-labeling pipeline (S17: `auto_verdict` kept
separate from `curated_verdict`, judge-gated at P4). The headline acceptance criterion 6 (ledger
carries `auto_verdict`) DOES hold; only the `calls.jsonl` coupling the plan claims is absent.

**Decision needed (deferred — not a patch):** either (a) implement the coupling — thread the
iteration's `auto_verdict` into the `calls.jsonl` record the coder call already writes (it is already
`run_id`-tagged, so the join key exists) — or (b) correct the plan/KNOWLEDGE to say the auto-verdict
lives in the ledger, and let the P4 DPO pass join ledger↔calls on `run_id`. Pick per the intended DPO
data path; do not silently choose.

**DECIDED: (b)** (2026-07-16, session 122, user call). The ledger is the auto-verdict's single home;
`calls.jsonl` stays verdict-free (the call record is appended at generation time, before the verdict
exists — the coupling would mean back-writing an append-only log for a consumer that only arrives at
P4). Plan + KNOWLEDGE corrected in place. **Note for P4:** revisit the join mechanics then — `run_id`
joins per-run, so per-iteration call matching is order-based, and anti-cheat iterations record a
verdict without an evaluation call.

## Minor items (no dedicated task — fold into T-92 widening / T-86)
- **Plan run-spec example `base: HEAD` is rejected by intake** (`RunSpec` forbids unknown keys, has no
  `base` field; the worktree hardcodes `HEAD`). Drop `base:` from the example in
  `docs/plans/oficina-p2-evaluated-loop.md`. (Live-verify.)
- **CLI: run_ids can start with `-`** (e.g. `-L-rwo…`) → breaks `oficina watch <id>` argparse; needs
  `watch -- <id>` or an argparse tweak. (Live-verify.)
- **`git add -A` in `workspace._commit` commits `__pycache__/*.pyc`** into the deliverable commit when
  the target repo has no covering `.gitignore` (`.pytest_cache` self-ignores). Observed live. NOT a
  CLAUDE.md violation (fresh worktree, no pre-existing files swept). Fix = scoped add of the target,
  or write a `.gitignore` into the worktree at C0. (PR comment on `workspace.py:198` + live-verify.)

## Security note (from the security review — no code change, boundary to watch)
Under today's threat model (only the author submits run specs) there are **no** exploitable findings:
`evaluator._run_test_stage` runs `test_cmd` via `shell=True` but nothing untrusted is interpolated,
and model-generated code execution is by design. **Load-bearing assumption:** if any non-author local
process can write to the run FIFO / spec store, that `shell=True` `test_cmd` becomes a HIGH command
injection → RCE as the worker's user. This diff does not touch the submit/authorization surface, so
it holds here — confirm it at that boundary as oficina goes machine-global (relates to T-86, T-88).

<!-- /ref:oficina-p2-review-deferred -->
