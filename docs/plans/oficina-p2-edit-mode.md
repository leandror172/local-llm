# oficina P2 — edit mode (whole-file-with-context) — build plan

**Status:** Plan, session 126 (2026-07-22). **NOT built — implementation gated on explicit user go.**
**Task:** T-110 (proposed id; register in `.claude/tasks.md` at handoff — T-109 was claimed
2026-07-22 by a cross-session entry from expenses/code s63). Amends the T-104 M2 decision.
**Branch (when built):** `feature/oficina-p2-edit-mode`, fresh from master.
**Provenance:** the session-126 re-grounding. The code-anchored M2 build plan had grown a
constrained edit language (a `unit` spec field, response-shape validation, deterministic import
merging, a constants boundary) — complexity that serves none of the vision's five measured facts
(`ref:delegate-vision`) and contradicts the product intent: **oficina is an async coding
subagent**, and a subagent that cannot edit existing files is a scaffold generator. Records
amended alongside this plan: `ref:oficina-write-model-report` § AMENDMENT (T-104),
`ref:oficina-function-kind-write-model` amendment, `ref:oficina-async-migration-shape` routing
revision (T-89).

<!-- ref:oficina-edit-mode -->
## Goal

`kind: function` pointed at an **existing committed file** becomes a first-class **edit run**:
the file's current content enters the prompt as a stable segment, the model returns the complete
modified file, and the existing loop machinery — C0 baseline, delta-scope attribution
(P2-D12), anti-cheat, per-iteration snapshots, budgets — evaluates it **unchanged**. Pointed at
an absent path, behavior is today's greenfield generation, byte-identical.

**The bug being fixed** (T-104): today an edit-shaped run silently nukes the module — iteration 1
generates *from scratch* because the target is never in the prompt and C0 assumed absence. The
fix is to **model the edit, not to guard against it**: fed the file, the same whole-file write
mechanism becomes a correct edit, and the previously-dangerous case (target exists) becomes the
capability the caller wanted.

**Deliberately NOT built** (the session-126 reversal): no `deliverable.unit` field, no
`locate_unit` locator, no response-shape validation, no import merging, no shared patch core.
The model holds whole-file authority; the evaluated loop + declared tests + H1 diff review are
the safety mechanism — which is what they were built to be. Sibling effect: the Go widening's
predicted `LanguagePack.locate_unit` member drops out (Warning 2's "expect one predicted seam to
prove unnecessary" — fulfilled), and edit mode is **language-agnostic for free**.

## Mechanism — every change, by file

| File | Change | Anchor |
|---|---|---|
| `oficina/workspace.py` | mode detection (target present in worktree at assemble); `current_file` stable part; uncommitted-target guard; `Assembly.mode`; additive `mode` key on the `AssemblyDone` payload | `assemble` :109, `_build_stable_parts` :214 |
| `oficina/prompt.py` | new stable segment `current_file` between `context` and `tests` (reorder-within-stable is explicitly allowed); ordering-guard test updated deliberately | `SEGMENTS` :41 |
| `oficina/loop.py` | constraints variant selected by mode; fence-strip on write (both modes); edit-mode `num_predict` sizing | `_CONSTRAINTS` :43, `_generate_with_snapshot` write :263, `default_coder` :314 |
| `oficina/evaluator.py` | **none** — verify only: compile already runs when the target exists (:192-198); `attributable_failures` already never subtracts target-scope failures, so the file's current failing tests are live from iteration 1. P2-D12 anticipated target-present C0 | — |
| `oficina/intake.py` | **no rule changes** — docstring honesty only (`kind: function` covers greenfield AND edit); pin-test that `function` + existing target is accepted | module docstring :5-7 |
| `worker.py` / `parser.py` / ledger / service / retention | none | — |
<!-- /ref:oficina-edit-mode -->

<!-- ref:oficina-edit-mode-decisions -->
## Decision register (E-D1–E-D9, settled session 126)

- **E-D1 — M2 mechanism = whole-file-with-context. Amends T-104's code-anchored choice.**
  New evidence (each absent from the original decision): (1) the **timeout-safety leg does not
  transfer** — both blown ceilings were on the *sync* `generate_code` path (T-103); the loop's
  coder runs under `spec.timeout_s` (default 1800s) where a ~310-token whole-file generation is
  ~10s; (2) **code-anchored's real cost was never priced** — span confinement forces a
  constrained edit language (unit naming, response validation, import merging, a constants
  boundary); (3) **product intent** — edit-shaped work routes through the async loop by default,
  so spec simplicity dominates per-iteration output tokens; (4) the pre-registered rule's own
  "within ~5 points at large → the locator isn't worth its cost" branch is satisfied by the
  observed ties (corpus caveat carried). **Code-anchored stays on file as the fallback
  mechanism.** Observable trigger: a real edit run shows silently dropped sibling code — a
  delta-scope regression or an H1 diff-review catch. Fires → harden the corpus, re-run, revisit.
- **E-D2 — Mode discriminator: the target exists at HEAD in the worktree. No new spec fields.**
  The caller expresses edit intent by naming an existing committed file — nothing to declare.
  Two sub-rules: **(a) uncommitted-target guard** — target present on the base-repo disk but
  absent at HEAD → `AssemblyError` (fail loud: the worktree checks out HEAD, so the model cannot
  see uncommitted WIP; silent greenfield would generate against an invisible file and the
  delivered branch would collide with it). **(b)** target committed but **empty** → greenfield
  (no content to preserve; `build_prompt` drops blank segments anyway).
- **E-D3 — `current_file` is a STABLE prompt segment** (placed between `context` and `tests`).
  The cache contract (P2-D2) holds because the segment carries the **C0 content, which is
  run-constant**; the worktree file changes each iteration, but that state is fully determined
  by C0 + the variable tail (`previous_attempt` — the previous whole-file response), which is
  already how the layout works. One deliberate `SEGMENTS` edit + guard-test update.
- **E-D4 — Constraints variant per mode; `_SYSTEM` shared.** Greenfield keeps today's
  `_CONSTRAINTS` byte-identical. Edit adds the preservation contract: *modify the current file
  to meet the objective; preserve all code the objective does not require changing; return the
  complete updated file; no fences.* Selected from `Assembly.mode` — constraints are stable
  within a run, so the cache contract is unaffected.
- **E-D5 — Fence-strip at the loop's write step, both modes, composing
  `server._strip_code_fences` (server.py:731).** The loop's raw `_chat_generation` transport
  writes fences verbatim today → compile fails → the repair feedback says "syntax error", which
  misleads the model into fixing code that was never broken (a wasted iteration on a 3-iteration
  budget). One spelling: import the existing server helper (lazy import, the established idiom —
  `workspace._build_stable_parts` and the worker's refs resolution already do this). No new module.
- **E-D6 — No omission heuristic in v1.** No shrink-guard, no similarity check. Omission
  detection is behavioral: declared tests + delta-scope attribution catch dropped code whose
  tests are in `test_cmd` scope; the H1 diff review catches the rest. Production edit runs ARE
  the hardened corpus the T-104 report called for. Trigger to revisit = E-D1's fallback trigger.
- **E-D7 — C0 keeps the shared first-failing-stage `evaluate` (P2-D8).** Documented edge: an
  edit target that fails *compile* at C0 stops the baseline before the test stage, so
  pre-existing out-of-scope *test* failures are absent from the baseline and would be falsely
  attributed to iterations. Failure direction is SAFE (extra attributed failures → more repair /
  `Exhausted`, never a false `Delivered`) and the precondition (committed code that doesn't
  compile) is rare. Trigger for a both-stages C0 baseline variant: an edit run Exhausts with
  out-of-scope test failures attributed while its C0 baseline was compile-only.
- **E-D8 — Kind taxonomy unchanged.** `function` stays (docstring updated: "a code deliverable
  gated by tests — greenfield or edit by target presence"). Rename deferred; trigger: the Axis-B
  kind-widening pass, which must touch the taxonomy anyway.
- **E-D9 — Edit-mode `num_predict` sizes to the input file.** The T-91 truncation class recurs
  one level up: `NUM_PREDICT = 2048` caps ~150–200 code lines, so a 300-line module *cannot* be
  returned whole and would truncate mid-file every iteration. Rule: edit-mode default
  `num_predict = max(NUM_PREDICT, ceil(chars(current_file)/4) × 2)`, capped at 8192; an explicit
  `budgets.num_predict` still wins (explicit over derived). This is the output-side sibling of
  the "context window sizes to the INPUT" lesson (T-81 P2): an output budget justified by "a
  function is small" is a defect marker once the output is a whole file.
<!-- /ref:oficina-edit-mode-decisions -->

## Build steps (TDD — tests first within every step)

Local-model delegation per `ref:local-model-conventions`: test bodies + mechanical helpers via
`my-python-q25c14` (full-file context; pass `pyproject.toml` for pytest style). Session-125
caveat: repeated `TIMEOUT_COLD_START` is a VRAM-contention signal, not a prompt-size one —
check `gpu-vram-windows.sh` before rewriting prompts.

1. **T1 — workspace.** Mode detection + `Assembly.mode` (`"edit" | "greenfield"`) +
   `current_file` stable part (read from the worktree post-checkout) + E-D2(a) uncommitted
   guard + additive `mode` key on the `AssemblyDone` payload. Tests (~6, git-integration style
   like the existing T4 suite): edit assembly carries `current_file` + `mode="edit"`; greenfield
   assembly unchanged (pin: no `current_file` key, `mode="greenfield"`); uncommitted target →
   `AssemblyError` with triad; empty-at-HEAD → greenfield; `AssemblyDone` payload shape.
2. **T2 — prompt.** `current_file` segment (stable, between `context` and `tests`, header names
   the modification contract). Update the ordering-guard test deliberately (the designed
   single-swappable-SEGMENTS move). Tests (~2): segment renders in position; blank → omitted.
3. **T3 — loop.** Consume `Assembly.mode`: constraints variant (E-D4), fence-strip before
   `write_text` (E-D5), `num_predict` sizing (E-D9) threaded through `default_coder`'s factory
   arg from the worker. Tests (~6, executable-spec DSL): edit-mode prompt contains the current
   file + edit constraints; greenfield prompt byte-identical to today (pin); fenced generation
   lands stripped on disk; num_predict floor derived from file size; explicit budget override wins.
4. **T4 — evaluator + intake pins.** No behavior changes — add the discriminating pins: intake
   accepts `function` + existing target (explicit test for the formerly-dangerous case);
   evaluator integration test: target-present C0 runs the compile stage on current content.
   (~3 tests.)
5. **T5 — docstrings.** `intake.py` kind table, `loop.py`/`workspace.py` module docstrings
   ("deliverable ABSENT" language in workspace.py:8-11 is now mode-dependent — reword).
6. **T6 — live acceptance** (real Ollama, real git repo, mirrors P2-T8): a populated module with
   ≥2 functions, each covered by tests inside `test_cmd` scope (the regression trap, now live in
   acceptance); seeded failing test on ONE function; submit → Delivered; sibling tests green;
   diff inspected (only the intended region + nothing dropped); cache criterion on
   `prompt_eval_duration` (never `prompt_eval_count`, `ref:oficina-p2-cache-measurement`).
   Plus one suite-level omission simulation: a fake coder that drops the sibling → its test
   fails → attributable → iteration rejected, never `Delivered` (acceptance criterion 6).

Estimated new tests: ~17. Suite 279 → ~296.

## Acceptance criteria

1. **Edit headline:** seeded defect in one function of a populated committed module → repaired →
   `Delivered`, sibling functions intact (their tests pass; diff shows no unrelated loss).
2. **Greenfield unchanged:** target-absent runs produce byte-identical prompts and behavior
   (suite pins; no regression across the existing 279).
3. **Fence-strip:** a fenced coder response never lands fenced on disk.
4. **Uncommitted guard:** target on disk but not at HEAD → loud `AssemblyError` triad.
5. **Cache:** edit-mode iteration ≥2 shows prefix reuse on `prompt_eval_duration`.
6. **Omission is caught when tested:** simulated dropped sibling → attributed regression → not
   `Delivered`.
7. **No truncation:** a ~300-line module round-trips complete (E-D9 verified live).

## Risks & carried caveats

- **Omission risk carried open** (E-D1/E-D6): correctness parity was measured only at
  easy-corpus difficulty. Real edit runs generate the evidence; the fallback mechanism is
  recorded and unbuilt.
- **Prompt growth:** stable prefix now includes the whole target file — cached after iteration
  1, but input sizing matters at the margins. Observable: prompt `chars/4` approaching the
  persona's 32K `num_ctx` → that is the `fit_num_ctx` trigger (T-81 P2 lesson), not built now.
- **Output cost:** ~file-size output tokens per iteration (40→134→310 measured) — accepted per
  E-D1 inside the async budget.
- **14B output-reliability ceiling** (root KNOWLEDGE, model-tier finding): 14B output is
  empirically reliable to ~800 tokens; a whole-file edit on a 200+ line module exceeds that,
  risking quality degradation independent of `num_predict` (E-D9 prevents *truncation*, not
  *drift*). This observable feeds the SAME E-D1 fallback trigger — degradation or omission on
  large-file edit runs is exactly the evidence that would justify building code-anchored. v1
  accepts it; the natural fit for edit runs is small-to-medium modules.

## Records moved with this plan (same series)

- `docs/findings/oficina-write-model-benchmark-2026-07-18.md` — § AMENDMENT added inside
  `ref:oficina-write-model-report`.
- `docs/plans/oficina-write-model-benchmark.md` — amendment pointer after the verdict.
- `docs/plans/oficina-language-widening-notes.md` — amendment appended to the M2 decision inside
  `ref:oficina-function-kind-write-model` (locator design kept as fallback capital).
- `docs/plans/oficina-async-ergonomics.md` — routing-default revision inside
  `ref:oficina-async-migration-shape` (T-89): delegated codegen — small edits included —
  defaults async; sync = opportunistic fast path pending the busy-check (G-D8).
- At handoff: register T-110 in `.claude/tasks.md`; update coding-delegate QUICK/KNOWLEDGE +
  mcp-server QUICK (write-protocol: in place); `.claude/index.md` row (done with this plan).

## RESULTS — T6 live acceptance (session 126, 2026-07-22): **PASSED**

Build: T1–T5 by an Opus subagent (6 commits, suite 279→297), adversarially reviewed
(MERGE-READY, 10/10 invariants, findings F1–F6 all LOW; F1 fixed + omission pin `08d72ad`,
suite 298; F2/F3/F6 accepted-with-note). Live runs, all real Ollama (`my-python-q25c14`):

- **R1 — small edit, symlink-spelled target** (`~/workspaces/...`): Delivered, 1 iteration.
  `mode: "edit"` in AssemblyDone; CURRENT FILE segment + edit constraints confirmed in the
  live prompt; sibling body intact, 2/2 green on the branch. **Verdict 1** — the first live
  E-D6 observation: drift was *additive* (unrequested type annotations on both functions),
  not omissive; plainly visible in the diff (the H1 gate's class).
- **R2 — 246-line module, 24 tested fillers**: Delivered, 1 iteration. **Diff 2+/2− — only
  the target function touched; all 24 fillers byte-intact; 25/25 green.** Round-trip complete
  (criterion 7): `eval_count` 1299, no truncation. The derived E-D9 budget (~2850) was
  operative but not load-bearing (output < 2048) — an above-floor live stress needs a
  ~500-line file; the resolution logic is unit-pinned. **Verdict 2.**
- **R3 — greenfield control**: Delivered, 1 iteration; `mode: "greenfield"`; **zero**
  edit-mode bytes in the live prompt, greenfield constraints verbatim (review F4 closed).
  **Verdict 1** (one unused import).
- **R4 — E-D2a guard probe**: uncommitted target → **Failed in 1.3 s at `assembling`**,
  `whose: payload`, message names the target + both exits; zero GPU spent. No verdict —
  Failed runs carry no deliverable (by design).

**Criterion 5 (cache)** could not be re-measured live: every run converged in iteration 1
(tests-as-context, the T8 product note — a positive result in itself). The contract is
structurally confirmed (review invariant 2) and was measured live in T8 for the same layout.
**Criterion 6 (omission)**: suite-level integration pin via the real evaluator (collection-
error path); R2 sprang no omission at 246 lines. **Product note:** omission-by-import-breakage
yields thin repair feedback (the `-q` summary is just `ERROR <file>` — the symbol name prints
above the summary block); a future parser enhancement could capture the `E ImportError` line.
