# evaluator/ — Quick Memory

*Working memory for the evaluation framework. Keep under 30 lines.*

## Status

Operational. 7 rubrics (Go, Python, Java, Shell, general, classification, writing).
Phase 1 validators for Go, Shell, Python, Java, JSON schema. Phase 2 LLM judge working.
Used in Layer 4 benchmark runs; results in `evaluator/results/`.

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
