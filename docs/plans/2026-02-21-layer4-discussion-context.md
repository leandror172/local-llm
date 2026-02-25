# Layer 4 Discussion Context

**Date:** 2026-02-21 (Session 27)
**Purpose:** Capture architectural decisions and deferred ideas from planning discussion, so they survive context compression.

---

## Key Decisions Made

### Stance 3: Unix-Style Seams (No Formal Pipeline Abstraction Yet)
- No "step" class or pipeline framework in Layer 4
- Every component has: structured input (JSON/YAML), structured output (JSON/YAML), model as parameter
- Convention: each tool is a standalone script that reads stdin/args and writes stdout
- The future pipeline system (Layer 7+?) just becomes an orchestrator that wires these scripts together
- Rationale: "three examples" rule — don't build abstractions until you have 3+ concrete instances to generalize from

### Three-Phase Scoring Architecture
```
Score(prompt, output) =
    Phase 1: automated checks  →  pass/fail flags (deterministic, free)
    Phase 2: rubric check (local model, structured output)  →  rubric scores
    Phase 3: frontier judge only if needed  →  holistic quality score
```
- Phase 3 triggers: close comparisons, subjective quality, calibration
- Judge model is always a parameter, never hardcoded

### Three Judgment Domains
- **Domain A (Deterministic):** compile, lint, test, schema validation → automated tools, no model
- **Domain B (Semi-structured):** constraint compliance, completeness, edge cases → local model + rubric, structured output
- **Domain C (Subjective):** readability, design quality, explanation clarity → stronger model needed

### Scope: Tight Core (4 tasks)
- 4.1: Define rubrics per domain (YAML format)
- 4.2: Build evaluate.py (phases 1→2→3, structured JSON output)
- 4.3: Build benchmark.py (N personas × prompt set → report)
- 4.4: Create initial prompt sets (10-15 per domain)

### Task 4.6 Split Out
- Claude Desktop insights is a standalone utility, NOT part of Layer 4
- It's `tools/claude-desktop-insights.py` or similar — independent script
- Uses Anthropic API directly to analyze exported Claude Desktop JSON
- Build whenever desired, no dependency on evaluator framework

---

## Deferred / Future Ideas

### Comprehensive Extensions (Layer 4 v2, if needed)
- **Frontier-as-judge integration:** Phase 3 using Claude API. Useful but costs money. Build when local rubrics prove insufficient.
- **Calibration methodology:** Ground-truth labeled outputs to validate judge reliability. Build when you need to detect/fix bias.
- **Frontier judge model options:** Haiku ($0.25/MTok, fast) for rubric checks; Sonnet ($3/MTok) for everyday judging; Opus ($15/MTok) for calibration/edge cases.

### Configurable Pipeline System (Layer 7+?)
User's vision: a declarative file defines a sequence of steps, each step being a call to a different agent/persona/model.

**Example workflows described:**
1. **Web research emulation:** URL → web scraper → evaluator (quality check) → summarizer → aggregate → final summary
2. **Code development loop:** coder → reviewer → iterate → tester → security analyzer

**Key properties:**
- Steps are DAG nodes (not just linear)
- Steps can branch (parallel), loop (conditional retry), and aggregate
- Each step has: input schema, processor (model/persona), output schema
- The whole thing is defined in a config file (YAML?)

**Why Layer 4 supports this future:**
- Stance 3 means every Layer 4 tool is already a composable unit
- Structured I/O (JSON in, JSON out) means any tool can be a pipeline step
- Model-as-parameter means the pipeline config just specifies which model per step
- The evaluator itself becomes a reusable "check quality" step in any pipeline

### Model Flexibility
- All solutions parameterized on model (never hardcode `qwen3:8b`)
- Rubrics are data (YAML), not code — swappable without code changes
- Judge model is a config parameter — swap when hardware/models change
- Re-runnable: same benchmark prompts, different models, comparable scores

---

## LLM-as-Judge Caveats (Research Notes)

Known biases from MT-Bench, Alpaca Eval research:
- **Verbosity bias:** judges prefer longer outputs regardless of quality
- **Self-enhancement bias:** a model prefers outputs in its own style
- **Position bias:** first/last answer shown gets preference in A/B comparisons
- **Capability ceiling:** judge can't recognize quality it can't produce

**Mitigation for this project:**
- Automated checks (Phase 1) handle objective correctness — no bias possible
- Structured rubrics (Phase 2) constrain the judge to specific criteria — reduces verbosity bias
- Frontier judge (Phase 3) only for subjective quality — most reliable
- Calibration set (future) detects systematic bias

---

## Integration Points with Existing Infrastructure

- **MCP server:** `generate_code`, `ask_ollama` with persona routing → subjects to evaluate
- **Persona registry:** `personas/registry.yaml` → list of personas to benchmark
- **Persona detector:** `personas/detect-persona.py` → could auto-select relevant benchmarks for a codebase
- **Existing benchmark infra:** `benchmarks/` directory has run scripts, prompt files, result storage patterns
