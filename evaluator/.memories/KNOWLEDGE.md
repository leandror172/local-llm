# evaluator/ — Knowledge (Semantic Memory)

*Evaluation framework decisions. Read on demand.*

## One Criterion Per LLM Call (2026-02)

Phase 2 sends one Ollama call per rubric criterion, not one call scoring everything.
Each call gets a focused system prompt: criterion name, description, and scoring scale.
The judge returns `{"score": int, "reasoning": string}` via structured output.

**Rationale:** Multi-criteria evaluation in a single call causes the judge to trade off
qualities internally — a model might score readability high because correctness is low,
or vice versa. Isolated calls produce independent, stable scores.
**Implication:** More Ollama calls per evaluation (4-6 per rubric), but each is small
and fast. Total evaluation time for one output: ~30-60 seconds on local hardware.

## Rubric YAML Format (2026-02)

Each rubric defines: id, domain, validators (type + extensions), and criteria list.
Each criterion: name, phase (1 or 2), description, weight, scoring scale (1-5 with descriptions).
Phase 1 criteria have `auto_source: validator` to map to automated check results.
Phase 2 criteria have full 5-point scoring descriptions for the LLM judge.

**Rationale:** YAML is human-readable and version-controllable. Separating rubrics from
code means adding a new evaluation domain (e.g., Rust) requires only a new YAML file,
not code changes.
**Implication:** Rubric authoring is accessible to non-programmers. The scoring scale
descriptions are the "prompt template" — they directly influence judge behavior.

## A Greenfield Rubric Can Reward an Edit Defect (2026-07-28, oficina P4-T9)

`code-python` scored a file **5/5 on every criterion** when that file contained 114 unrequested
added lines, 78 of them copied verbatim out of its own acceptance tests. Its `completeness`
criterion justified the 5 as *"self-contained, runnable, and includes a usage example"* — the
"usage example" being the pasted tests.

**Rationale:** the rubric was written to judge *generated* code, which has no prior state, so it
has no vocabulary for **unrequested** content; extra material reads as thoroughness. Judging an
**edit** is a different question — did this change only what was asked — and no criterion asked it.
**Implication:** `evaluator/rubrics/oficina-edit.yaml` judges edit deliverables and is kept
SEPARATE from `code-python` on purpose: that rubric is shared with the Layer-4 benchmark suite,
where adding a scope criterion would retroactively change benchmark scoring. A new rubric file is
the sanctioned extension (see "Rubric YAML Format") — no code change was needed.
**Second implication, measured the same day:** a judge shown the delivered FILE plus measured
drift metrics still scored the leak 5; shown the unified DIFF it scored 2, at ~33% fewer tokens.
Scoring-scale text is the prompt template, but it cannot compensate for the wrong artifact being
in the prompt. `ref:judge-sees-the-change`.

**Third implication (2026-07-28): a rubric's CUT belongs beside its scale, and `oficina-edit`
carries no `weight`.** `oficina-edit.yaml` declares **`passing_score: 4`** on each criterion — a
key `evaluate.py` ignores and the oficina judge reads. The cut had lived in Python while the 1–5
scale lived in YAML, and they disagreed: rung 3 of `scope_adherence` describes *"a small
unrequested edit a reviewer would ask to remove"* yet sat above a threshold of 3, so the rubric
passed a weaker instance of the defect it was written to catch. Reading both ladders shows rung 4
is the lowest acceptable rung in each — the scale was right and the number was one rung low.
Changing the cut touches no prompt, so the acceptance held without re-measurement; rewriting the
rung would have re-opened it, since scale text IS the prompt template.
**`weight` is deliberately absent** from this rubric alone: the oficina judge is a conjunction of
per-criterion gates, and **no weighting can make an average agree with an AND** (with both cuts at
4, ranking `(5,3)` below `(4,4)` needs `w₁<w₂` while `(3,5)` needs `w₂<w₁`). `evaluate.py`
*asserts* `weight` is present, so it can no longer load this file — correct, since its criteria
require drift metrics only oficina supplies. The reason is written into the YAML itself.

## Temperature 0.1 for Deterministic Judging (2026-02)

The LLM judge runs at temperature 0.1 (not 0.0, which some models handle poorly).
This produces near-deterministic scoring — the same code evaluated twice gets the
same or very similar scores.

**Rationale:** Evaluation must be reproducible. If scores vary significantly across
runs, they can't be used for model comparison or DPO signal.
**Implication:** Reviewer personas in the persona system also use 0.1 for the same reason.

## Weighted Score Aggregation (2026-02)

Each criterion has a weight (e.g., correctness: 3.0, readability: 1.5). The overall
score is a weighted average of all criteria where a score was produced. Criteria that
couldn't be evaluated (no code found, validator error) are excluded from the average
rather than scored as zero.

**Rationale:** Not all criteria matter equally. Correctness should dominate the score.
Excluding unevaluated criteria prevents punishing models for framework failures.
**Implication:** Two evaluations with different subsets of evaluated criteria are not
directly comparable. The `percentage` field (0-100%) normalizes for comparison.

## Connection to Phoenix/Arize Evaluation Model (2026-04)

The evaluator maps directly to Arize Phoenix's LLM-as-a-judge pattern:
- Rubric YAML = Phoenix "eval template"
- Local Ollama judge at temp=0.1 = Phoenix "judge model"
- calls.jsonl = Phoenix "traces"
- Evaluator JSON output = Phoenix "structured quality signals"
- Verdict triples feeding DPO = Phoenix "logged back to Phoenix"

Key difference: this system was built evaluation-first (DPO data needs quality signals),
not observability-first (no production app generating traffic to monitor). The observability
infrastructure grew as a side effect of measuring what local models produce.

## Verdict Integration (2026-03)

The evaluator scores complement human verdicts (0/1/2).
Together they form the full quality signal for DPO:
- Human verdict: was the output usable? (binary quality)
- Evaluator scores: how good was it on specific criteria? (granular quality)
- Call log: what was the prompt and response? (the training pair)

**Rationale:** Neither signal alone is sufficient. Human verdicts are coarse but reliable.
Evaluator scores are granular but depend on judge model quality.
**Implication:** The 3-dimension verdict policy (defect type / fix scope / prompt cost)
and the evaluator scoring are complementary, not redundant.
