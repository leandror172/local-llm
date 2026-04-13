# benchmarks/ — Quick Memory

*Working memory for the benchmark suite. Keep under 30 lines.*

## Status

Operational. 4 test categories, multi-language validators.
Used for Layer 4 evaluation runs and model comparison experiments.
Results in `benchmarks/results/` (timestamped directories).

## Test Categories
`backend` (3, Go+Java), `structured` (5, JSON), `visual` (3, Canvas), `decomposed` (3×3 stages)

## Key Tools
- `lib/compare-models.py` — side-by-side comparison, verdict capture
- `lib/record-verdicts.py` — ACCEPTED/IMPROVED/REJECTED; use `--verdicts A,I --notes "n1|n2"`
  for non-interactive mode (Claude Code has no TTY — interactive `input()` hits EOFError)
- `lib/validate-code.py` — compile gate (Go, Shell); `lib/validate-html.js` — Puppeteer

## Model Findings (durable)
- **gemma3:12b** — ~31 tok/s, IMPROVED tier on Go + Python; 3-4× faster than qwen2.5-coder:14b
- **gemma3:27b** — 3.2 tok/s, timeouts on all coding tasks even warm; not viable on RTX 3060

## Deeper Memory -> KNOWLEDGE.md
- Few-Shot Injection (47% token reduction), Prompt Decomposition (3-stage sweet spot),
  Idempotent Runs, Compare-Models DPO pipeline
