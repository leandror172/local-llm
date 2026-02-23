# Evaluator Framework

Standardized scoring system for comparing model/persona outputs across domains.

## Overview

The evaluator answers: **"Which persona is best for X?"** by running the same prompt through multiple personas and scoring each output using a two-phase approach:

- **Phase 1 — Automated checks:** Deterministic, free, no model required. Compilation (Go), JSON schema validation (classification), etc.
- **Phase 2 — LLM judge:** Rubric-driven scoring via a local judge model. One criterion per call with structured JSON output for reliability at 7-8B.

All components are standalone scripts with structured JSON I/O and model as parameter — composable for future pipeline use.

## Two scripts, two levels

**`run-evaluate.sh` scores one output.** It takes an LLM response you already have and runs it through the rubric. No generation — just judgment.

```
prompt file + output file + rubric → score JSON
```

Use it when you have an output from any source (a benchmark run, a live session, another tool) and want to know how it scores.

**`run-benchmark.sh` runs the full N personas × M prompts matrix.** It calls Ollama to generate outputs, then scores each one using `evaluate.py` internally.

```
prompt directory + persona list + rubric → results directory + leaderboard
```

Use it when you want to compare personas head-to-head.

**The relationship:**

```
benchmark.py
  └── for each persona × prompt:
        ollama_chat(persona, prompt)   ← generate
        evaluate.py functions          ← score
  └── aggregate all scores → summary.json + report.md
```

`benchmark.py` imports `evaluate.py`'s functions directly (via `importlib`) so there is no subprocess overhead per evaluation — but both remain independently usable scripts.

---

## Quick Start

### Evaluate a single output

```bash
# Score one LLM output against the Go rubric
./evaluator/run-evaluate.sh \
  --prompt evaluator/prompts/go/01-http-handler.md \
  --output /path/to/llm-output.txt \
  --rubric evaluator/rubrics/code-go.yaml \
  --judge-model my-codegen-q3

# Skip Phase 2 (automated checks only — fast, no Ollama needed)
./evaluator/run-evaluate.sh \
  --prompt evaluator/prompts/go/04-concurrent-cache.md \
  --output /path/to/output.txt \
  --rubric evaluator/rubrics/code-go.yaml \
  --skip-phase2
```

Output is JSON to stdout:
```json
{
  "prompt_id": "go-01-http-handler",
  "rubric_id": "code-go",
  "phase1": { "weighted_score": 5.0, "criteria": [...] },
  "phase2": { "weighted_score": 4.2, "criteria": [...] },
  "overall": { "weighted_score": 4.42, "percentage": 88.4 }
}
```

### Run a benchmark

```bash
# Dry run — see the execution plan without making API calls
./evaluator/run-benchmark.sh \
  --prompts evaluator/prompts/go \
  --personas my-go-q3,my-coder-q3 \
  --rubric evaluator/rubrics/code-go.yaml \
  --judge-model my-codegen-q3 \
  --dry-run

# Full run
./evaluator/run-benchmark.sh \
  --prompts evaluator/prompts/go \
  --personas my-go-q3,my-coder-q3 \
  --rubric evaluator/rubrics/code-go.yaml \
  --judge-model my-codegen-q3

# Auto-discover all coding personas from registry
./evaluator/run-benchmark.sh \
  --prompts evaluator/prompts/go \
  --all-coding \
  --rubric evaluator/rubrics/code-go.yaml
```

Results land in `evaluator/results/{timestamp}/`:
```
results/2026-02-21T143000/
├── raw/          # raw Ollama API responses
├── code/         # extracted code files
├── evals/        # per-output evaluation JSONs
├── summary.json  # aggregated scores + leaderboard
└── report.md     # human-readable comparison
```

## Directory Structure

```
evaluator/
├── rubrics/              # Scoring criteria (YAML data files)
│   ├── code-go.yaml      # Go: compile/vet (Phase 1) + correctness/idioms (Phase 2)
│   ├── code-java.yaml    # Java: jakarta.*, Spring patterns, readability
│   ├── code-python.yaml  # Python: type hints, pythonic style, completeness
│   ├── code-general.yaml # Language-agnostic fallback rubric
│   ├── classification.yaml  # JSON schema validation + category correctness
│   └── writing.yaml      # Accuracy, clarity, structure, conciseness
├── prompts/              # Benchmark prompt sets (YAML frontmatter + markdown)
│   ├── go/               # 10 prompts: easy (3) / medium (4) / hard (3)
│   ├── java/             # 10 prompts: easy (3) / medium (4) / hard (3)
│   ├── python/           # 10 prompts: easy (3) / medium (4) / hard (3)
│   ├── classification/   # 5 prompts: easy (2) / medium (2) / hard (1)
│   └── shell/            # 5 prompts: easy (2) / medium (2) / hard (1)
├── lib/
│   ├── evaluate.py       # Core scoring engine (Phase 1 + Phase 2)
│   └── benchmark.py      # Orchestrator (persona × prompt matrix)
├── run-evaluate.sh       # Wrapper — whitelist-safe, unbuffered stdout
├── run-benchmark.sh      # Wrapper — whitelist-safe, unbuffered stdout
├── results/              # Generated outputs (gitignored)
└── .gitignore
```

## Rubric Format

Rubrics are YAML data files — add a new domain without touching Python:

```yaml
id: code-go
domain: go
description: Evaluation rubric for Go code generation

validators:                     # Phase 1: automated tools to run
  - type: code
    extensions: [.go]           # maps to benchmarks/lib/validate-code.py

criteria:
  - name: compiles
    phase: 1                    # 1 = automated, 2 = LLM judge
    description: Code compiles without errors
    weight: 3.0                 # relative importance in weighted average
    auto_source: validator      # score derived from validator output
    scoring:
      5: "Zero errors and zero warnings"
      3: "Warnings only"
      1: "Does not compile"

  - name: correctness
    phase: 2                    # LLM judge evaluates this
    description: Does the code solve the stated problem?
    weight: 3.0
    scoring:
      5: "Fully solves the problem with all requirements met"
      3: "Partial solution; major requirements missing"
      1: "Does not address the problem"
```

**Phase 1 validators supported:**
| `type` | Tool | Languages |
|--------|------|-----------|
| `code` | `benchmarks/lib/validate-code.py` (go build + vet) | Go |
| `json_schema` | Python `json.loads` + field/type checks | Classification tasks |

## Prompt Format

Same YAML frontmatter convention as `benchmarks/prompts/`:

```yaml
---
id: go-04-concurrent-cache
domain: go
difficulty: medium
timeout: 300
description: Concurrent-safe LRU cache with TTL expiration
---

Implement a concurrent-safe LRU cache in Go...
```

## VRAM Strategy (12GB constraint)

The benchmark runner groups personas by `base_model` to minimize GPU reloads:

- `my-go-q3` and `my-java-q3` both use `qwen3:8b` — switching between them is free (same base weights, different Modelfile)
- All prompts for one base_model group run before switching to the next group
- Phase 2 judging is deferred until after all generation is complete, to avoid ping-ponging between subject and judge models

## Options Reference

### run-evaluate.sh

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt` | required | Path to prompt file |
| `--output` | required | Path to LLM output file (raw text or Ollama JSON) |
| `--rubric` | required | Path to rubric YAML |
| `--judge-model` | `my-codegen-q3` | Ollama model for Phase 2 judging |
| `--skip-phase1` | off | Skip automated checks |
| `--skip-phase2` | off | Skip LLM judge (generation + Phase 1 only) |
| `--quiet` | off | Suppress progress output on stderr |

### run-benchmark.sh

| Flag | Default | Description |
|------|---------|-------------|
| `--prompts` | required | Directory of prompt files |
| `--personas` | `""` | Comma-separated persona names |
| `--rubric` | required | Path to rubric YAML |
| `--judge-model` | `my-codegen-q3` | Judge model for Phase 2 |
| `--all-coding` | off | Auto-discover coding personas from registry |
| `--dry-run` | off | Print execution plan without API calls |
| `--no-warmup` | off | Skip warmup calls |
| `--timeout` | `300` | Per-prompt Ollama timeout (seconds) |
| `--skip-phase1` | off | Skip automated checks |
| `--skip-phase2` | off | Skip LLM judge |
| `--results-dir` | `evaluator/results/` | Override results location |

## Extending

**Add a new domain:**
1. Create `evaluator/rubrics/{domain}.yaml` with your criteria
2. Create `evaluator/prompts/{domain}/` with prompt files
3. Run with `--rubric evaluator/rubrics/{domain}.yaml --prompts evaluator/prompts/{domain}`

**Add a new Phase 1 validator:**
1. Add `validators: [{type: mytype, ...}]` to the rubric
2. Add a handler for `mytype` in `evaluate.py:run_phase1()`
3. Map validator output to criterion scores via `auto_source: validator`

**Add Phase 3 (frontier judge):**
The scoring pipeline in `evaluate.py:run_phase2()` is designed to be extended. A Phase 3 call to Claude API can be added as a fallback when Phase 2 scores are ambiguous or for subjective quality ranking. See `docs/plans/2026-02-21-layer4-discussion-context.md` for the design rationale.
