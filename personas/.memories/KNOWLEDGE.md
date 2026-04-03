# personas/ — Knowledge (Semantic Memory)

*Persona system decisions. Read on demand.*

## MODEL_MATRIX Domain Mapping (2026-02)

Each domain (code, reasoning, classification, writing, etc.) maps to a default model
and context size. Reasoning tasks use qwen3:14b (needs more capacity). Classification
uses qwen3:4b (speed over depth). Code uses qwen3:8b (balance of speed and quality).

**Rationale:** Different tasks have different quality/speed tradeoffs. A classification
call should be fast (sub-second); a code generation call can take 10-30 seconds.
**Implication:** Domain selection in create-persona automatically picks the right base
model. Override is possible but discouraged without benchmarking.

## Constraint Reliability at 7-8B (2026-02)

7-8B models reliably follow 4-7 constraints in the SYSTEM prompt. Beyond 7, constraints
start conflicting or being ignored. Domain-specific defaults encode tested constraints:
code ("complete, runnable code", "error handling", "idiomatic style"), classification
("exactly one category", "confidence score", "valid JSON").

**Rationale:** Discovered empirically across benchmark runs. More constraints don't mean
better output — they mean more ways for the model to fail.
**Implication:** Constraint editing should subtract before adding. If a constraint isn't
producing visible behavior, remove it to give others more attention budget.

## Three-Signal Detection Algorithm (2026-02)

detect-persona.py scores a codebase using three signals with fixed weights:
1. File extensions (50%) — most reliable, broadest coverage
2. Import statements (30%) — first 100 lines, framework-specific patterns
3. Config file content (20%) — parsed for framework keywords (not just presence)

Scores are normalized 0-1, then matched against registry personas by keyword scan
of their role descriptions. Top-3 results returned.

**Rationale:** Extensions alone miss framework details (Java could be Spring or Android).
Imports catch frameworks but miss the language. Config parsing catches build tools.
The 50/30/20 weighting was tuned against 5 test fixtures (Java, Go, React, Python, monorepo).
**Implication:** Adding a new language requires: extension mapping, import patterns,
config file parser, and a registered persona to match against.

## Tier Design: Full vs Bare (2026-02)

Full tier: Modelfile includes a SYSTEM prompt with role, constraints, and output format.
The persona is self-contained — Ollama returns shaped output without external prompting.
Bare tier: Modelfile has only model parameters (temperature, context, penalties), no SYSTEM.
External tools (Aider, OpenCode) inject their own system prompts.

**Rationale:** Tools like Aider have their own prompt templates. A persona's SYSTEM prompt
would conflict. Bare tier provides model tuning without prompt interference.
**Implication:** Bare personas are invisible in direct Ollama chat — they behave like
the base model. Their value is in the temperature/context/penalty tuning only.

## Temperature as Model-Selection Substitute (2026-02)

Three temperature presets serve as a lightweight alternative to maintaining separate
models per task type: deterministic (0.1) for review/classification, balanced (0.3) for
coding, creative (0.7) for writing/brainstorming. Same base model, different behavior.

**Rationale:** On 12GB VRAM, loading different models for each task is expensive (cold start).
Temperature tuning gives behavioral diversity without model switching.
**Implication:** The "right persona" for a task often means the right temperature, not
the right model. My-coder-q3 (0.3) and my-reviewer-q3 (0.1) share a base model.

## Registry as Source of Truth (2026-02)

registry.yaml is the single inventory of all personas. Every tool reads from it.
Entries include: name, modelfile path, base_model, role, temperature, num_ctx, tier, status.
Status values: active, archived, deprecated.

**Rationale:** No scanning Modelfile directories. No querying Ollama's model list.
One file tells you what exists, what it does, and whether it's current.
**Implication:** Creating a persona without registering it means the MCP server's
language routing and detect-persona won't find it. Registration is not optional.
