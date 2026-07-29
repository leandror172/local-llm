# evaluator/ — Quick Memory

*Working memory for the evaluation framework. Keep under 30 lines.*

## Status

Operational. 8 rubrics (Go, Python, Java, Shell, general, classification, writing, oficina-edit),
split across `phase: 1` / `phase: 2`. The seven benchmark rubrics carry **5–6 weighted criteria
each**; **`oficina-edit` is the exception on both counts** — 2 phase-2 criteria, and **no
`weight:` at all**, because its consumer is a conjunction of per-criterion gates rather than a
weighted average (P4-D10). It instead declares **`passing_score: 4`** per criterion, a key only
the oficina judge reads. See KNOWLEDGE.md § "A Greenfield Rubric Can Reward an Edit Defect".
Phase 1 validators for Go, Shell, Python, Java, JSON schema. Phase 2 LLM judge working.
Used in Layer 4 benchmark runs; results in `evaluator/results/`.

⚠️ **This module has ZERO automated tests** (verified 2026-07-21 — no `def test_` anywhere
under `evaluator/`). The only source files are `lib/evaluate.py` and `lib/benchmark.py`;
everything else in the tree is generated benchmark *output*. Characterize before changing.
⚠️ **The judge is a LOCAL model**, not a frontier one — `DEFAULT_JUDGE_MODEL = "my-codegen-q3"`.

## Architecture

Two-phase evaluation pipeline:
- **Phase 1** — Automated: compilation (go build), linting (go vet, shellcheck),
  JSON schema validation. Deterministic, fast, 1/3/5 scores.
- **Phase 2** — LLM-as-judge: local Ollama model scores subjective criteria
  (correctness, idiom, readability, completeness). One call per criterion.

Output: JSON with per-criterion scores, weighted aggregates, overall percentage.

## Key Files

- `lib/evaluate.py` — main pipeline (Phase 1 + Phase 2 + aggregation)
- `rubrics/*.yaml` — criteria definitions with weights and scoring scales
- `run-evaluate.sh` — bash wrapper entry point

## Deeper Memory -> KNOWLEDGE.md

- **One Criterion Per Call** — why, and what it prevents
- **Rubric Format** — YAML schema, weight semantics
- **Phoenix/Arize Mapping** — how this maps to industry LLM evaluation
- **Verdict Integration** — connection to DPO data pipeline
