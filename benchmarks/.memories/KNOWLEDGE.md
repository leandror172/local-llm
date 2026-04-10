# benchmarks/ — Knowledge (Semantic Memory)

*Benchmark suite decisions. Read on demand.*

## Few-Shot Injection (2026-02)

Providing 1-2 reference implementations as examples in the prompt reduces output tokens
by 47% while maintaining quality. The model copies the structure and style rather than
inventing from scratch.

**Rationale:** Measured across structured output benchmarks. Few-shot examples act as
implicit constraints more reliably than written rules at the 7-8B tier.
**Implication:** Benchmark prompts in `prompts/` have paired examples in `examples/`.
The benchmark runner injects examples when available.

## Prompt Decomposition: 3-Stage Sweet Spot (2026-02)

Multi-stage prompts (where stage N's output feeds stage N+1) outperform single-shot
for complex tasks. Empirically validated: 3 stages works best. 2 stages leaves too
much per stage. 4+ stages adds overhead with diminishing returns.

**Rationale:** Each stage stays within the model's reliable output budget (~400 tokens
for 8B, ~800 for 14B). The decomposed/visual category validates this — each project
has 3 stages (structure, animation, refinement).
**Implication:** Complex coding tasks should be decomposed into 3 prompts before
attempting. This applies beyond benchmarks — it's a general prompting strategy.

## Idempotent Benchmark Runs (2026-02)

Each run creates a timestamped directory. Re-running with the same timestamp skips
existing results (model/prompt pairs already present). Force re-run with --no-skip.

**Rationale:** Benchmark runs take 10-30 minutes. Resuming after interruption without
re-running completed prompts saves significant time.
**Implication:** Safe to re-run the full suite after adding new prompts — only new
prompt/model combinations execute.

## Compare-Models Pipeline (2026-03)

`compare-models.py` runs the same prompt through 2+ models side-by-side.
`record-verdicts.py` then captures human verdicts per model's output.
The combination produces DPO preference pairs: same prompt, two responses,
one labeled better.

**Rationale:** DPO fine-tuning requires preference pairs (chosen vs rejected).
Model comparison naturally produces these — the ACCEPTED response is "chosen",
the REJECTED response is "rejected".
**Implication:** Every comparison run is both a quality assessment and a training
data collection event. The workflow was designed for this dual purpose.

## Compare-Models Timeout Design (2026-04)

The 300s per-model timeout in compare-models.py is calibrated for the 30B-A3B MoE at
10-20 tok/s (max ~6000 tokens). Dense models slower than ~5 tok/s cannot complete
coding tasks within this limit. Empirically: gemma3:27b at 3.2 tok/s generates
1500-2000 tokens for coding tasks, requiring 470-625s — always times out.

**Rationale:** The timeout is not a tuning parameter — it's a practical signal that
a model is too slow for iterative coding use. If a model times out consistently on
warmed benchmarks, it should be marked inactive regardless of quality.
**Implication:** Before benchmarking a new model, estimate: (expected_tokens / tok/s).
If that exceeds 240s (giving 60s margin), the model will fail the benchmark regardless
of the quality it would produce.

## Validate-Code Scaffolding (2026-02)

validate-code.py doesn't just compile raw code — it scaffolds it first. If Go code
is missing `package main` or `func main()`, the validator adds them. If Shell code
is missing a shebang, it adds `#!/usr/bin/env bash`.

**Rationale:** LLM output often omits boilerplate that's implied by context. Penalizing
compilation failure for missing `package main` when the model clearly wrote a main
function would be unfair — the signal should be about code quality, not formatting.
**Implication:** Phase 1 compilation scores (in the evaluator) reflect actual code
errors, not missing boilerplate. This makes scores more meaningful for comparison.
