# personas/ — Quick Memory

*Working memory for the persona system. Keep under 30 lines.*

## Status

35+ active personas from 13 base models. Registry stable.
Last additions: session 45 (2026-03-20) — 5 new Python personas + context audit.
MCP tools (create_persona, copy_persona) operational via ollama-bridge.

## Architecture

Three independent tools that coordinate through shared YAML files:
- **create-persona.py** — interactive/non-interactive Modelfile generator
- **detect-persona.py** — codebase analyzer → best persona recommendation
- **build-persona.py** — LLM-driven conversational persona proposal

Shared data:
- `models.yaml` — single source of truth for 13 base models (contexts, temps, domains)
- `registry.yaml` — persona inventory (name, model, role, temperature, tier, status)

## Key Concepts

- **Tier system:** full (with SYSTEM prompt) vs bare (no SYSTEM, for external tools like Aider)
- **Temperature as model-selection substitute:** 0.1=deterministic, 0.3=balanced, 0.7=creative
- **Naming:** `my-<role>[-model-suffix]` (e.g., my-go-q3, my-java-q25c14)
- **Detection:** Three-signal scoring — extensions (50%), imports (30%), config files (20%)

## Deeper Memory -> KNOWLEDGE.md

- **MODEL_MATRIX** — domain-to-model mapping rationale
- **Constraint Reliability** — 4-7 constraints for 7-8B, why not more
- **Detection Algorithm** — three-signal scoring details
- **Tier Design** — full vs bare, when each is used
