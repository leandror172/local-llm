# oficina write-model benchmark — spec (T-104 gate)

**Status:** Spec, session 124 (2026-07-18). Not built. Gates the M2 (edit) write-model decision.
**Task:** T-104. Design context: `ref:oficina-function-kind-write-model` in
`docs/plans/oficina-language-widening-notes.md`.
**Purpose:** decide, by measurement not argument, which edit-apply mechanism oficina's loop should
use for editing an *existing* file — before paying to build the locator.

<!-- ref:oficina-write-model-benchmark -->
## Question

For `qwen2.5-coder:14b`, editing a **named function inside an existing populated file**, which
apply mechanism produces the most *correct, non-regressing* result — and how does that change with
**file size**?

## Hypothesis (from prior art + the loud-vs-silent-failure argument)

Code-anchored is **size-invariant** (emits only the unit); whole-file **degrades with size**
(lazy omission, fidelity loss, token cost). Crossover is somewhere in the medium bucket. Below it,
whole-file may tie or win on simplicity; above it, code-anchored should dominate.

## Pre-registered decision rule (fix BEFORE running — no post-hoc)

Report **by size bucket**, never aggregate (an aggregate hides the crossover, which is the whole
point). Then:

- **Adopt code-anchored for M2** if, in the **medium + large** buckets, its combined-success rate
  is **≥ whole-file's** AND its apply-success is meaningfully higher (whole-file shows real
  regressions/omissions there). This is the expected outcome.
- **Keep whole-file, drop the locator** if whole-file's combined-success **holds within ~5 points
  of code-anchored even in the large bucket** — then the locator isn't worth its cost.
- **Model-anchored search/replace is a control, not a candidate.** It ships only if it beats BOTH
  others outright (unlikely; included to confirm the fragility argument empirically, so the
  decision rests on data not assertion).
- **Small bucket does not decide anything** — it is reported to locate the crossover, not to pick
  the winner. Real deliverables are not one-function files (that is the T-104 finding itself).

## The three arms (differ ONLY in how output becomes a file change)

| Arm | Model is asked for | Applied by | Apply-failure mode |
|---|---|---|---|
| **A. code-anchored** (M2 candidate) | *only the rewritten function* | code locates the span (Python `ast`), reads `old_string` from disk, applies via `patch_file` semantics | **none — 100% apply by construction** |
| **B. whole-file-with-context** (WM-2) | the *complete modified file* | overwrite | silent: drops/paraphrases unchanged code |
| **C. model-anchored search/replace** (WM-4, control) | `SEARCH`/`REPLACE` blocks (aider format) | exact-match apply | loud: `old_string` doesn't match → apply fails |

Prompts are held as parallel as possible; each arm's *ask* is the minimal one its mechanism needs.
The differing ask is part of what is measured (does "write just the function" yield better
functions than "rewrite the whole file"?), so it is deliberately **not** controlled away.

**Arm A requires a minimal Python locator** (`ast.parse` → find `FunctionDef`/`AsyncFunctionDef`
by name → `lineno`..`end_lineno` span). That locator is a build cost of the benchmark; if A wins,
it graduates into `LanguagePack.locate_unit` — the benchmark is not zero-build.

## Task corpus

Each task = `(existing_file, target_function_name, behavior_change, tests)` where `tests` are
pre-authored and committed, and the *original* file fails them (the edit must make them pass).

Dimensions to vary:
- **File size (the discriminator): small (~20 lines / 1–2 funcs), medium (~100 / ~8 funcs),
  large (~300 / ~20 funcs).** Report by this axis.
- **Edit type:** modify-body · change-signature (callers in-file must still work) · add-branch.
- **A regression trap in every medium/large file:** at least one *other* function whose test
  breaks if the arm drops or mangles it — this is what exposes whole-file's silent-omission mode.

Target: **~12 tasks** (4 per size bucket, spanning edit types). Synthetic-but-realistic with
known-correct tests (control over ground truth beats ecological messiness for a mechanism test).

## Metrics (per task × arm, aggregated to a rate)

1. **Applied?** — did the mechanism yield a changed file at all (C can fail here).
2. **Target-test passes?** — the acceptance test for the edited function.
3. **No regression?** — the **rest of the file's tests still pass** (this single metric captures
   whole-file's fidelity/omission failure elegantly: dropping another function breaks its test).
4. **Combined success = 1 ∧ 2 ∧ 3.** ← the headline number, per size bucket.
5. **Output tokens** — cost proxy; whole-file re-emits the whole file, code-anchored emits one unit.

## Protocol

- Model: `my-python-q25c14` at its persona default temperature (stochastic → rates, not samples).
- **N = 3 runs per (task, arm)** cell → 12 × 3 × 3 = **108 generations**. Report pass *rates*.
- **Single-shot per generation** (no repair loop) — this measures the write model, not the loop.
  A loop would confound apply-mechanism with iteration budget.
- Serial (VRAM ceiling; `ref:local-model-conventions`). ~108 serial 14B generations is real
  wall-clock (est. 1–3 h depending on file size / output length) — and it is itself a workload the
  async path can't help with (T-104), so budget it as a sit-and-run.

## Confounds

- **Controlled:** same model, same temperature, same tasks/tests across arms; same N.
- **Measured, not controlled:** the per-arm *ask* (whole-file vs unit vs blocks) — because "which
  ask yields better code" is part of the write-model question.
- **Out of scope:** anti-cheat, delta-scoping, multi-language. Python only — the locator is
  per-language but the **write-model choice is not**, so a Python result generalizes to the Go
  decision (build Go's locator only if A wins).

## What the result feeds

- A-wins → build `LanguagePack.locate_unit` (Python + Go) + wire M2 = code-anchored → `patch_file`;
  `loop.py:263` `write_text` becomes M1-only (compose `output_file`).
- B-wins → M2 = whole-file-with-context; no locator; far cheaper Go path.
- The number also sizes the anti-cheat surface: A only ever touches one span, so a surgical write
  hitting a test file is still detectable by the existing `diff_touches_test_files`.

## RESULTS — run 1 (2026-07-18, 108 gens, `my-python-q25c14`, 0 errors)

| COMBINED success | small | med | large | | output tokens | small | med | large |
|---|---|---|---|---|---|---|---|---|
| code_anchored | 100% | 100% | 100% | | code_anchored | 25 | 25 | 25 |
| whole_file | 100% | 100% | 100% | | whole_file | 40 | 134 | **310** |
| model_anchored | 100% | 100% | 100% | | model_anchored | 46 | 48 | 49 |

**Correctness axis: NULL / inconclusive — do not misread.** Every arm tied at 100% in every bucket;
the regression trap **never sprang**. This is a **coverage failure of the corpus, not a finding
about the mechanisms**: the filler is 20 structurally-identical `op_k` functions, which is the
*best case* for whole-file fidelity (a model rarely drops a line of a repetitive pattern). aider's
lazy-omission effect needs heterogeneous, messy, large files. **You cannot conclude "whole-file is
safe" from a test that did not stress it.** The pre-registered rule's literal "keep whole-file if
within 5 points" branch is therefore INAPPLICABLE — the discriminating condition was not reached.

**Cost axis: clean, strong, decision-relevant.** code-anchored is **size-invariant (25 tok flat)**;
whole-file grows **linearly (40→134→310, a 12× gap at large)** because it must reproduce the whole
file. This is not cosmetic: whole-file on a large file emitting ~310+ output tokens is exactly what
blows the 120s `OLLAMA_TIMEOUT` ceiling we hit twice this session (T-103). code-anchored structurally
never does.

**Verdict:** code-anchored is favored on **cost + timeout-safety**, NOT on correctness (a genuine
tie at this difficulty — the correctness question remains OPEN). Two forward paths:
1. **Harden + re-run** — heterogeneous realistic filler, trickier defects, large→~500+ lines — to
   actually test the omission hypothesis (the instrument, as built, optimized *for* whole-file).
2. **Decide M2 = code-anchored now** on the cost/latency/ceiling argument alone (it solves a problem
   hit today), accepting correctness as "equivalent at this difficulty."

Meta-finding (free, on-theme): the 14B mis-generated the SEARCH/REPLACE *parser* during the build
(wrong `=======` divider) and fenced its own block *contents* at runtime — the exact-format
fragility arm C exists to measure, showing up in both the framework and the live output. A cheap
prior in favor of removing exact-format reproduction from the model's plate (i.e. code-anchoring).
<!-- /ref:oficina-write-model-benchmark -->
