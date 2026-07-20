# oficina write-model benchmark — full report (T-104)

**Date:** 2026-07-18 (session 124). **Model:** `my-python-q25c14` (qwen2.5-coder:14b).
**Run:** 108 generations (12 tasks × 3 arms × 3 runs), 0 errors.
**Harness:** `benchmarks/lib/writemodel_{apply,corpus,bench}.py` (`run-write-model-bench.sh`).
**Spec + pre-registered decision rule:** `docs/plans/oficina-write-model-benchmark.md`
(`ref:oficina-write-model-benchmark`).

<!-- ref:oficina-write-model-report -->
## The question

oficina's evaluated loop overwrites the whole target file every iteration (`loop.py:263`), so its
only real client is a greenfield single-unit file (T-104, `ref:oficina-function-kind-write-model`).
To support editing a **named function inside an existing populated file**, the loop needs an
edit-apply mechanism. Which one — decided by measurement, before paying to build a per-language
locator?

## Method

Three apply arms, differing ONLY in how a model's output becomes a file change:

| Arm | Model returns | Applied by | Apply-failure mode |
|---|---|---|---|
| **A. code-anchored** | only the rewritten function | code locates the span (`ast`), reads `old_string` from disk, exact-replace | none — 100% by construction |
| **B. whole-file** | the complete modified file | overwrite | silent: drops/paraphrases unchanged code |
| **C. model-anchored** | aider SEARCH/REPLACE blocks | exact-match apply (+ fair interior-fence stripping) | loud: `old_string` not present → fail |

**Corpus:** programmatic, size-bucketed (small ~20 lines/1 filler fn, medium ~100/8, large
~300/20). Each task has one defective target function to fix, plus filler functions **each carrying
a passing test** — so the regression surface scales with file size. Ground truth was verified
deterministically before any model call (original fails target + passes regression; a known-good
fix flips target; a simulated omission trips no-regression).

**Metrics per (task, arm, run):** applied? · target-test passes? · no-regression (rest of the
file's tests still pass)? · combined = all three · output tokens. Reported **by size bucket** (the
pre-registered rule — aggregating would hide the crossover).

## Results

```
COMBINED success   small   med   large        output tokens   small   med   large
code_anchored       100%   100%   100%         code_anchored     25     25     25
whole_file          100%   100%   100%         whole_file        40    134    310
model_anchored      100%   100%   100%         model_anchored    46     48     49
```

## Analysis — two axes, opposite outcomes

### Correctness: NULL / inconclusive

Every arm tied at 100% combined in every bucket. **The regression trap never sprang** — whole-file
did not drop a single function even at 20-function/300-line files.

**This is a coverage failure of the instrument, not a finding about the mechanisms.** The corpus's
filler is 20 *structurally-identical* `op_k` functions, which is the *best possible case* for
whole-file fidelity: a model rarely drops a line of a regular, repetitive pattern. The
lazy-omission failure that motivates search/replace in real tools (aider) appears on
**heterogeneous, messy, large** files. The synthetic corpus accidentally optimized *for* whole-file.

**Consequence for the pre-registered rule:** its "keep whole-file if within 5 points at large"
branch is **inapplicable** — that branch presumes the discriminating condition (whole-file showing
regressions) was tested. It was not reached. You cannot conclude "whole-file is safe" from a test
that did not stress it.

### Cost: clean, strong, size-confirming

code-anchored is **size-invariant** (25 tokens flat) because it emits only the function. whole-file
grows **linearly** (40 → 134 → 310, a 12× gap at large) because it must reproduce the entire file.
model-anchored is roughly flat (~48) — it emits only the changed region as blocks.

This axis is **decision-relevant, not cosmetic.** A large-file whole-file edit emitting 310+ output
tokens is precisely what pushed `my-python-q25c14` past the 120s `OLLAMA_TIMEOUT` ceiling **twice in
this same session** (T-103) while delegating the Phase-1 code. code-anchored, emitting ~25 tokens,
structurally cannot hit that wall.

## Threats to validity

- **Corpus too easy / too regular** (primary): the null on correctness is almost certainly this.
  Uniform filler + trivial defects + a capable 14B = a ceiling effect. A hardened corpus
  (heterogeneous realistic functions, trickier multi-site defects, large→500+ lines) would be
  required to actually test the omission hypothesis.
- **Single model:** `qwen2.5-coder:14b` only. Weaker models fail search/replace more (arm C would
  degrade); the relative ranking could shift.
- **Synthetic tests:** ground-truth is exact but not ecologically messy.
- **N=3 per cell:** rates are coarse; fine differences would be noise. (Immaterial here — the
  correctness spread was zero.)

## Decision (T-104): M2 = code-anchored

**M2 (edit an existing named unit) = code-anchored** (`LanguagePack.locate_unit` → `patch_file`),
decided on **cost + timeout-safety**, explicitly **NOT correctness** (a genuine tie at tested
difficulty). **The re-run (harder corpus) is declined** because the open axis is not load-bearing:
the decision rests on the cost/ceiling axis, which the benchmark measured cleanly and which a re-run
would not change. M1 (greenfield new file) stays = compose `output_file`.

Why defensible despite the null: the decision's justification (cheaper + can't blow the timeout
ceiling) and the benchmark's failed axis (correctness superiority) are **different axes.** You only
re-run when the open question is load-bearing for the choice. Here it is not.

## Carried caveat + future work

- **We choose code-anchored knowing correctness is a tie at this difficulty, not a win.** If real
  use ever shows whole-file dropping code on big messy files, it is the **corpus** that needs
  revisiting (harden + re-run), not the decision.
- **Build (later, not now):** `locate_unit` for Python (`ast` — the benchmark's `locate_function`
  is a working seed) + Go (`go/parser`); wire the loop to compose `patch_file` for edit kinds
  (retire the bespoke `write_text` there); flip C0 baseline to target-present for edit kinds
  (P2-D12 delta-scoping).

## Meta-finding (free, on-theme)

The 14B mis-generated the SEARCH/REPLACE **parser** during the build (wrong `=======` divider) and
fenced its own block **contents** at runtime — the exact-format fragility arm C exists to measure,
appearing in both the framework code and the live output. A cheap independent prior in favor of
removing exact-format reproduction from the model's plate (i.e. code-anchoring), even though the
correctness benchmark itself could not confirm it.
<!-- /ref:oficina-write-model-report -->
