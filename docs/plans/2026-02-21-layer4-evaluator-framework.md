# Layer 4: Evaluator Framework — Implementation Plan

## Context

We have 30 specialized personas but no systematic way to answer "which persona is best for X?" Layer 4 builds a standardized scoring system so persona selection becomes data-driven.

**Architectural stance (Stance 3 — Unix-style seams):** Every component is a standalone script with structured JSON I/O, model as parameter. No formal pipeline abstraction — composability via convention, not framework. The future configurable pipeline (Layer 7+?) just becomes an orchestrator that wires these scripts together.

**Scope:** Tight — 4 tasks. Frontier-as-judge (Phase 3) and calibration are deferred extensions. Full discussion context saved in `docs/plans/2026-02-21-layer4-discussion-context.md`.

---

## Task 4.1: Define Evaluation Rubrics

**Create:** `evaluator/rubrics/` with 6 YAML rubric files.

### Rubric Schema

```yaml
id: code-go
domain: go
description: Evaluation rubric for Go code generation

validators:                     # Phase 1: which automated tools to run
  - type: code                  # maps to benchmarks/lib/validate-code.py
    extensions: [.go]

criteria:
  - name: compiles
    phase: 1                    # 1 = automated, 2 = LLM judge
    description: Code compiles without errors
    weight: 3.0
    auto_source: validator      # score derived from validator JSON
    scoring:
      5: "Zero errors, zero warnings"
      3: "Warnings only"
      1: "Does not compile"

  - name: correctness
    phase: 2                    # LLM judge evaluates this
    description: Does the code solve the stated problem?
    weight: 3.0
    scoring:
      5: "Fully solves the problem with all requirements met"
      3: "Partial solution, major requirements missing"
      1: "Does not address the problem"
```

### Files

| File | Phase 1 | Phase 2 Focus |
|------|---------|---------------|
| `code-go.yaml` | `validate-code.py` (compiles, vet) | correctness, idiomatic Go, readability, completeness |
| `code-java.yaml` | None yet (future: `javac`) | correctness, jakarta.* usage, Spring patterns, readability |
| `code-python.yaml` | None yet (future: `py_compile`) | correctness, type hints, pythonic idioms, readability |
| `code-general.yaml` | None | correctness, readability, completeness |
| `classification.yaml` | JSON schema validation | correct category, confidence calibration |
| `writing.yaml` | None | clarity, structure, audience fit |

**Key design:** `phase` field tells evaluate.py *how* to score. `auto_source: validator` means derive from tool output; Phase 2 criteria get sent to the LLM judge. Weights control relative importance.

---

## Task 4.2: Build evaluate.py

**Create:** `evaluator/lib/evaluate.py` + `evaluator/run-evaluate.sh`

### CLI

```bash
./evaluator/run-evaluate.sh \
  --prompt evaluator/prompts/go/01-http-handler.md \
  --output /path/to/llm-output.txt \
  --rubric evaluator/rubrics/code-go.yaml \
  --judge-model my-codegen-q3 \
  [--skip-phase1] [--skip-phase2] [--quiet]
```

### Three-Phase Scoring (Phase 3 deferred)

**Phase 1 — Automated checks:**
- Read rubric `validators` section → determine which tools to call
- Extract code from LLM output (reuse `extract-code.py` via importlib — hyphenated filename)
- Write to temp file → call validator as subprocess → parse JSON result
- Map validator output to criterion scores (e.g., error_count=0 → score 5)

**Phase 2 — LLM rubric judge:**
- For each Phase 2 criterion: build system prompt with criterion description + scoring scale
- User prompt includes: original prompt, LLM output, extracted code
- Call `ollama_chat()` with `format_schema` for structured JSON (`{score: 1-5, reasoning: "..."}`)
- One criterion per LLM call (keeps task simple for 7-8B judge)
- `temperature: 0.1`, `think: false` for deterministic judging

**Aggregation:**
- Weighted average per phase, then overall
- Criteria with `score: null` (skipped/no validator) excluded from averages

### Output (stdout JSON)

```json
{
  "prompt_id": "go-01-http-handler",
  "rubric_id": "code-go",
  "judge_model": "my-codegen-q3",
  "phase1": {
    "criteria": [{"name": "compiles", "score": 5, "max": 5, "weight": 3.0, "reason": "0 errors"}],
    "weighted_score": 5.0
  },
  "phase2": {
    "criteria": [{"name": "correctness", "score": 4, "max": 5, "weight": 3.0, "reason": "..."}],
    "weighted_score": 4.2,
    "judge_eval_count": 342,
    "judge_duration_ms": 5200
  },
  "overall": {"weighted_score": 4.42, "percentage": 88.4},
  "evaluated_at": "2026-02-21T14:30:00Z"
}
```

### Imports / Reuse

| Need | Source | Method |
|------|--------|--------|
| Ollama calls | `personas/lib/ollama_client.py` | `sys.path.insert` + `from ollama_client import ollama_chat` |
| Code extraction | `benchmarks/lib/extract-code.py` | `importlib.util.spec_from_file_location` (hyphenated name) |
| Go validation | `benchmarks/lib/validate-code.py` | subprocess call via wrapper |
| HTML validation | `benchmarks/lib/validate-html.js` | subprocess call via wrapper |
| YAML parsing | stdlib-adjacent | `pip install pyyaml` (already installed system-wide) |

### Wrapper (`evaluator/run-evaluate.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec python3 -u "$SCRIPT_DIR/lib/evaluate.py" "$@"
```

---

## Task 4.3: Build benchmark.py

**Create:** `evaluator/lib/benchmark.py` + `evaluator/run-benchmark.sh`

### CLI

```bash
./evaluator/run-benchmark.sh \
  --prompts evaluator/prompts/go \
  --personas my-go-q3,my-coder-q3 \
  --rubric evaluator/rubrics/code-go.yaml \
  --judge-model my-codegen-q3 \
  [--all-coding]    # auto-discover coding personas from registry
  [--dry-run]       # show plan, no API calls
  [--timeout 300]
```

### Model Loading Strategy (12GB VRAM)

Only one model fits in VRAM at a time. Key optimization:

1. **Group personas by `base_model`** from registry. Switching between `my-go-q3` and `my-java-q3` (both `qwen3:8b`) is free — same base weights, different Modelfile.
2. **Run all prompts for one base_model group before switching.** Minimizes cold reloads.
3. **Defer Phase 2 judging.** Collect all outputs first, then load judge model and batch-evaluate. Avoids ping-ponging between subject and judge.

```
for each base_model_group:
    warmup(first_persona)
    for each persona in group:
        for each prompt:
            → call Ollama (subject) → save raw JSON + extracted code
load judge model
for each saved output:
    → run evaluate.py logic (Phase 1 + Phase 2) → save eval JSON
aggregate → summary.json + report.md
```

### Results Directory

```
evaluator/results/{YYYY-MM-DDTHHMMSS}/
├── raw/           # Ollama API responses
├── code/          # Extracted code files
├── evals/         # Per-output evaluation JSONs
├── summary.json   # Aggregated scores + leaderboard
└── report.md      # Human-readable comparison
```

### Summary JSON includes a leaderboard

```json
{
  "leaderboard": [
    {"persona": "my-go-q3", "avg_score": 4.42, "avg_pct": 88.4, "prompts": 10},
    {"persona": "my-coder-q3", "avg_score": 3.85, "avg_pct": 77.0, "prompts": 10}
  ]
}
```

### Report.md includes
- Run metadata (date, rubric, judge, personas)
- Leaderboard table
- Per-persona breakdown (each prompt's score)
- Per-criterion analysis (which criteria differentiate personas most)

---

## Task 4.4: Create Initial Prompt Sets

**Create:** `evaluator/prompts/{domain}/` with YAML frontmatter + markdown body.

### Format

```yaml
---
id: go-01-http-handler
domain: go
difficulty: medium
timeout: 300
description: HTTP handler with middleware chain
---

Write an HTTP server in Go that...
```

### Distribution

| Domain | Count | Difficulty | Key tests |
|--------|-------|------------|-----------|
| `go/` | 10 | 3 easy, 4 medium, 3 hard | net/http, channels, generics, context, slog |
| `java/` | 10 | 3 easy, 4 medium, 3 hard | jakarta.*, Spring Boot 3.x, records, Stream API |
| `python/` | 10 | 3 easy, 4 medium, 3 hard | FastAPI, type hints, asyncio, dataclasses |
| `classification/` | 5 | 2 easy, 2 medium, 1 hard | expense categories, sentiment, multi-label |
| `shell/` | 5 | 2 easy, 2 medium, 1 hard | log analysis, backup rotation, git hooks |

Prompts target known persona-specific strengths and documented failure modes from Layer 2 (e.g., `javax.persistence` misuse, missing coordinate transforms).

---

## Implementation Sequence

| Step | Task | Depends On | Notes |
|------|------|------------|-------|
| 1 | 4.1 Rubrics | — | Pure data; start here |
| 2 | 4.4 Prompts | — | Pure data; can parallel with 4.1 |
| 3 | 4.2 evaluate.py | 4.1 | Core engine; test with one rubric + one prompt |
| 4 | 4.3 benchmark.py | 4.2 + 4.4 | Orchestrator; test with small subset first |

---

## Directory Structure

```
evaluator/
├── rubrics/           # Task 4.1 — YAML rubric definitions
├── prompts/           # Task 4.4 — prompt sets by domain
│   ├── go/
│   ├── java/
│   ├── python/
│   ├── classification/
│   └── shell/
├── lib/
│   ├── evaluate.py    # Task 4.2 — core scoring engine
│   └── benchmark.py   # Task 4.3 — orchestrator
├── run-evaluate.sh    # Task 4.2 — bash wrapper
├── run-benchmark.sh   # Task 4.3 — bash wrapper
├── results/           # gitignored
└── .gitignore
```

---

## Verification

### Task 4.1
- Validate all rubric YAML files parse correctly (`python3 -c "import yaml; yaml.safe_load(open('...'))"`)

### Task 4.2
- Run evaluate on a single Go prompt + output against `code-go.yaml`
- Verify Phase 1 calls `validate-code.py` and maps scores correctly
- Verify Phase 2 calls judge model and returns valid structured scores
- Test `--skip-phase1` and `--skip-phase2` flags
- Test with missing code (no code block in output) — Phase 1 should gracefully skip

### Task 4.3
- Dry run: `./evaluator/run-benchmark.sh --prompts evaluator/prompts/go --personas my-go-q3 --rubric evaluator/rubrics/code-go.yaml --dry-run`
- Small run: 2 prompts × 1 persona → verify results directory, summary.json, report.md
- Multi-persona: 2 prompts × 2 personas → verify leaderboard ordering

### End-to-end
- Full Go benchmark: 10 prompts × 2 personas (my-go-q3 vs my-coder-q3)
- Verify report.md is readable and leaderboard matches expectations

---

## Risks

| Risk | Mitigation |
|------|------------|
| Java/Python have no Phase 1 validator | Phase 1 criteria score as `null`, excluded from averages. Future: add `javac`/`py_compile` validators |
| LLM judge at 7-8B may be unreliable | Structured output + one criterion per call + temp 0.1. Phase 3 frontier judge is a designed extension point |
| Judge shares same base model as subject | Phase 1 automated checks cover objective correctness. Frontier judge (deferred) handles the rest |
| Long wall-clock time (120+ Ollama calls) | Group by base_model; allow filtering; checkpoint results |
