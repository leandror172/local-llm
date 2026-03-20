---
name: create-persona
description: Create Ollama personas — copy an existing persona to a new model, create from specs, or propose via LLM. Use when the user asks to create, copy, or port a persona.
disable-model-invocation: false
argument-hint: "[copy my-python-q3 to qwen3.5:9b | create Python coder on qwen3:14b | build 'data pipeline developer']"
---

# Create Persona Skill

Create one or more Ollama personas using MCP tools. Never hand-write Modelfiles.

## Available MCP tools

| Tool | Purpose |
|---|---|
| `query_personas` | List/filter existing personas (check before creating) |
| `list_models` | Show available base models in Ollama |
| `copy_persona` | Port an existing persona to a different base model |
| `create_persona` | Create a persona from explicit specs |
| `build_persona` | Propose a spec via LLM (read-only, needs create_persona to execute) |

## Three creation patterns

### Pattern 1: Copy to new model (most common)

One MCP call. Name, context size, and suffixes are auto-derived.

```
copy_persona(source="my-python-q3", base_model="qwen3.5:9b")
```

Pass `name=` to override the auto-derived name. Use `dry_run=True` to preview.

### Pattern 2: Create from explicit specs

One MCP call. Name is auto-derived from role + language + model if omitted.

```
create_persona(
    role="Python 3.11+ developer specializing in FastAPI, async/await, and CLI tools",
    base_model="qwen3.5:9b",
    language="python",
    constraints="MUST include type hints,...,MUST NOT import *",
)
```

### Pattern 3: LLM-assisted

Two calls: `build_persona` proposes, then `create_persona` executes.

```
build_persona(description="data pipeline developer using Airflow and dbt")
# → review output with user
create_persona(role=..., base_model=..., ...)
```

## Rules

- **Always `dry_run=True` first** when creating multiple personas.
- **Check `query_personas` first** — don't create duplicates.
- **One persona at a time** — create, verify, then proceed to the next.
- **Names are auto-derived** — both `copy_persona` and `create_persona` compute the correct name from the model's naming convention. Only pass `name=` to override.
