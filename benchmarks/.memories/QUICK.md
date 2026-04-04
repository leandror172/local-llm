# benchmarks/ — Quick Memory

*Working memory for the benchmark suite. Keep under 30 lines.*

## Status

Operational. 4 test categories, multi-language validators.
Used for Layer 4 evaluation runs and model comparison experiments.
Results in `benchmarks/results/` (timestamped directories).

## Architecture

Orchestrator (`run-benchmark.sh`) drives models through prompts, extracts code,
validates, and generates comparison reports. Each category has its own validator.

## Test Categories

| Category | Prompts | Validator |
|----------|---------|-----------|
| backend | 3 (Go, Java) | go build + go vet, javac |
| structured | 5 (JSON) | JSON schema validation |
| visual | 3 (Canvas) | Puppeteer headless browser |
| decomposed | 3x3 stages | Stage-chained + Puppeteer |

## Key Tools

- `lib/compare-models.py` — side-by-side model comparison, captures verdicts
- `lib/record-verdicts.py` — DPO verdict recording (ACCEPTED/IMPROVED/REJECTED)
- `lib/validate-code.py` — scaffolds + compiles code (Go, Shell)
- `lib/validate-html.js` — Puppeteer runtime smoke test

## Deeper Memory -> KNOWLEDGE.md

- **Few-Shot Injection** — 47% token reduction measured
- **Prompt Decomposition** — 3-stage sweet spot, empirical validation
- **Idempotent Runs** — skip existing results, --no-skip to re-run
- **Compare-Models Pipeline** — DPO verdict collection workflow
