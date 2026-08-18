# benchmarks/ — Quick Memory

*Working memory for the benchmark suite. Keep under 30 lines.*

## Status

Operational. 4 test categories, multi-language validators.
Used for Layer 4 evaluation runs and model comparison experiments.
Results in `benchmarks/results/` (timestamped directories).

## Test Categories
`backend` (3, Go+Java), `structured` (5, JSON), `visual` (3, Canvas), `decomposed` (3×3 stages)

## Key Tools
- `lib/writemodel_bench.py` (+ `run-write-model-bench.sh`) — oficina write-model benchmark (T-104):
  **4 apply arms** (code-anchored/whole-file/model-anchored/**symbol-addressed**) × size-bucketed
  corpus. Reusable pattern: programmatic corpus where every filler fn carries a test (regression
  surface scales with size); `writemodel_apply.py` (ast locators + appliers, **67 unit tests**
  across `test_writemodel_apply.py` + `test_writemodel_corpus.py`). **Run-1 finding:** at 14B on
  easy edits all arms tie on correctness (uniform filler = whole-file's best case → null);
  code-anchored wins on cost (size-invariant vs whole-file's linear token growth).
  `ref:oficina-write-model-report`
- **P3-T0 result (s137, 2026-08-18) — the model can NAME the unit, and it stays cheap.** Arm D has
  the model emit `{path, kind, body}` rather than being handed the name (arm A's case). On the
  class-bearing corpus, `my-python-q25c14-16k`, 24 generations, **both arms 100% correct** so this
  is cost at equal quality: whole-file **120 / 216 / 479** tokens by bucket against symbol-addressed
  **43 / 43 / 43 — flat**. Address fidelity 12/12 unique; **0/12 addressed >50% of the file**, so the
  degeneration failure did not occur. Detail + limits: `ref:delegate-p3-probe` § RESULTS.
  **Criterion 5's 0/12 is UNEXERCISED, not passed** — no task here needs a new top-level statement.
- **The corpus's ground truth is now tested** (`test_writemodel_corpus.py`): the generated original
  must FAIL its target test and PASS every filler. Nothing checked that before, and if it inverts
  every arm scores against a task with no defect while the numbers still print.
- ⚠️ **None of these tests run in any suite** — `make test` is `pytest tests/` under `mcp-server`
  with `testpaths=["tests"]`, and there is no root Makefile. Run them with
  `cd benchmarks/lib && python3 -m pytest`. **T-136.**
- `lib/compare-models.py` — side-by-side comparison, verdict capture
- `lib/record-verdicts.py` — verdict scale: 2=accepted 1=improved 0=rejected; use `--verdicts 2,1 --notes "|n2"`
  for non-interactive mode (Claude Code has no TTY — interactive `input()` hits EOFError)
- `lib/validate-code.py` — compile gate (Go, Shell); `lib/validate-html.js` — Puppeteer

## Model Findings (durable)
- **gemma3:12b** — ~31 tok/s, verdict-1 (improved) tier on Go + Python; 3-4× faster than qwen2.5-coder:14b
- **gemma3:27b** — 3.2 tok/s, timeouts on all coding tasks even warm; not viable on RTX 3060

## Deeper Memory -> KNOWLEDGE.md
- Few-Shot Injection (47% token reduction), Prompt Decomposition (3-stage sweet spot),
  Idempotent Runs, Compare-Models DPO pipeline
