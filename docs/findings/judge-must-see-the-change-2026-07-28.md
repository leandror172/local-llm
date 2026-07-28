# A reviewing model must be shown the CHANGE, not the RESULT

**Date:** 2026-07-28 (session 131, P4-T9). **Status:** measured on a real defect, three
conditions, same model and persona throughout. Extracted from the P4 plan because the lesson
is not about P4 — it applies to any model asked to review work.

<!-- ref:judge-sees-the-change -->
## The measurement

Replay of the T-119 leak (`refs/oficina/dy-Bi1nMo5LIqnpzrtXRTw`): a whole-file edit that added
114 lines to a 71-line module, 78 of them copied verbatim out of its own acceptance tests, while
the objective had said *"Keep every existing function, constant, import and comment byte for
byte."* Judge persona `my-judge-q25c14-16k` (qwen2.5-coder:14b, temp 0.1), one criterion per
call, structured output.

| What the judge was shown | Criterion available | Tokens | Score | What it said |
|---|---|---|---|---|
| Delivered file | `code-python` (no scope criterion) | 2,293 | **5/5 all** | *"self-contained, runnable, and includes a usage example"* |
| Delivered file + drift metrics | `scope_adherence` added | 2,293 | **5** | *"contains only the requested change, with no unrequested additions or deletions"* |
| **Unified diff** + drift metrics | `scope_adherence` | **1,529** | **2** | *"Substantial unrequested content added alongside the requested change"* |

## Three things this establishes

**1. A comparative question is unanswerable from one side of the comparison.** "Does this contain
only the requested change?" requires the before-state. Shown only the after-state, the model
reasons about the artifact in front of it — which is valid, runnable, well-formed Python — and
concludes it is fine. It is not being careless; it is answering the only question it can see.

**2. Handing it measured numbers does not substitute for the artifact.** Row 2 is the important
one: the drift metrics were **in the prompt** (`lines_added: 114`, `max_verbatim_run_vs_tests:
78`), the criterion description **told it what a large value means**, and the scoring scale
reserved **1** for exactly this case. It still said 5. Numbers are read as background when they
contradict the artifact the model can see; they are corroboration, not evidence, unless the thing
they describe is also present.

**3. The correct answer is cheaper.** The diff is ~33% fewer tokens than the file. Accuracy and
cost point the same way, so there is no trade to make — which is worth stating because the
opposite was assumed at design time (T-119 §(iii) worried that showing both artifacts would be
too expensive; the answer is a diff, which is neither artifact).

## Why this was not obvious in advance

The same substitution had already been made once, correctly, in the other direction.
**T-120** replaced a coder's *previous attempt* (a whole file) with a diff, purely to halve token
cost, and it worked. The P4 design then reasoned that if a diff was enough for the coder, measured
*numbers* would be enough for the judge — compressing one step further. That step is where it
broke: a diff is a **representation of the change**, while metrics are a **summary of the
representation**. The coder needed the change; the judge needs the change. Neither needed the file.

**Generalization worth carrying:** when a model must judge *whether something changed correctly*,
give it the change. Reserve summaries for what cannot be shown, not for what can.

## Corollary — the rubric can reward the defect

Row 1 is its own warning. The unmodified `code-python` rubric did not merely miss the leak; its
`completeness` criterion scored **5** and justified it as *"includes a usage example"* — the
"usage example" being the pasted acceptance tests. A rubric written for greenfield generation has
no vocabulary for *unrequested* content, so extra material reads as thoroughness. Judging an
**edit** needs a criterion that asks about scope; `evaluator/rubrics/oficina-edit.yaml` exists for
that, deliberately separate from `code-python` (shared with the Layer-4 benchmark suite, where a
greenfield output has no prior scope to adhere to).
<!-- /ref:judge-sees-the-change -->
