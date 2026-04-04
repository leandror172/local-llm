# Observability & Instrumentation Layer

How the benchmark/evaluator framework maps to LLM pipeline monitoring —
structured as a response to Arize Phoenix's evaluation model.

## What the observability/instrumentation layer actually looks like

### Layer 1: Trace collection — `calls.jsonl`

Every call through `ollama-bridge` (the MCP server) is automatically appended to `~/.local/share/ollama-bridge/calls.jsonl`. Each record contains:
- prompt text, response text
- model name, latency
- `prompt_eval_count` (input tokens), `eval_count` (output tokens), `total_duration_ms`

This is the direct analogue to **Phoenix traces** — a structured log of every inference execution. The difference is that Phoenix instruments live application traffic; this project instruments deliberate benchmark runs and everyday coding use via Claude Code.

### Layer 2: Automated quality signals — Phase 1 of `evaluator/lib/evaluate.py`

Phase 1 runs deterministic validators against generated code:
- **Go**: `go build` + `go vet` → scores on `compiles` (weight 3.0) and `vet_clean` (weight 1.0)
- **Shell**: `shellcheck`
- **Python/Java**: syntax + compilation checks
- **JSON output**: schema validation (required fields, type checking, confidence range)

Each check produces a 1/3/5 score with a reason string. Output is structured JSON. This is the automated/static part of what Phoenix calls "Phase 1 evals."

### Layer 3: LLM-as-judge — Phase 2 of the same file

For subjective criteria (`correctness`, `idiomatic_go`, `readability`, `completeness`), a local Ollama model (default: `my-codegen-q3`) judges each criterion independently:
- **One call per criterion** — avoids multi-criteria interference where the judge trades off qualities internally
- **Forced structured output** via Ollama's `format` param → always returns `{"score": int, "reasoning": string}`
- **Temperature 0.1** → deterministic enough to be comparable across runs
- **Weighted aggregation** → produces `phase1.weighted_score`, `phase2.weighted_score`, `overall.percentage`

The rubric YAML (`evaluator/rubrics/code-go.yaml`) defines the full criteria set with descriptions and scoring scales — exactly what Phoenix calls an "eval template."

### Layer 4: Human verdict capture — `run-record-verdicts.sh`

For every model comparison run, a human verdict (ACCEPTED / IMPROVED / REJECTED) is recorded alongside the task. The 3-dimension verdict policy (defect type x fix scope x prompt cost) governs classification. This pairs with the LLM judge scores to form DPO training triples: `(prompt, local_response, verdict + score)`.

Phoenix's equivalent is the "logged back to Phoenix" step — evaluation results becoming inspectable signals. The difference: this feeds a fine-tuning pipeline rather than a monitoring dashboard.

## Direct mapping to Phoenix concepts

| Phoenix concept | Equivalent in this project |
|---|---|
| "judge model" | local Ollama persona at temp=0.1 |
| "prompt template / rubric" | `evaluator/rubrics/code-go.yaml` (YAML with criteria, weights, scoring scales) |
| "your data" | `calls.jsonl` + benchmark results in `evaluator/results/` |
| "Phoenix traces" | ollama-bridge call logs (prompt + response + latency per inference) |
| "structured quality signals" | `evaluate.py` JSON output: per-criterion scores + weighted aggregate |
| "logged back to Phoenix" | DPO verdict triples feeding a future fine-tuning dataset |

## Framing

The evaluation layer was built first (because DPO training data needs quality signals), not the observability layer first (because there was no production application generating traffic to monitor). The observability infrastructure — `calls.jsonl`, latency tracking, token counts — grew naturally as a side effect of wanting to measure what local models cost vs. what they produce.

The specific capability that most directly answers "collection tools for robust monitoring of LLM pipelines" is the verdict + eval scoring pipeline as a **data collection instrument** — not just monitoring for anomalies, but collecting *labeled quality signals* from every generation for future model improvement.
