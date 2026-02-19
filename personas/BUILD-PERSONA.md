# BUILD-PERSONA: LLM-Driven Persona Builder

`build-persona.py` is the AI-powered sibling of `create-persona.py`. Instead of asking you to fill in a form step-by-step, it takes your plain-language description and uses a local Ollama model (`my-persona-designer-q3`) to reason about what persona to build.

## How It Differs from `create-persona.py`

| | `create-persona.py` | `build-persona.py` |
|-|---------------------|--------------------|
| Input | Interactive 8-step form | Free-form description |
| Constraint source | You write each MUST/MUST NOT | LLM proposes based on domain knowledge |
| Best for | Precise control, known constraints | "I need a persona for X" starting point |
| LLM calls | None (pure form-filling) | 1–2 calls to `my-persona-designer-q3` |
| Output | Modelfile + Ollama registration | Same (via handoff to `create-persona.py`) |

## Usage

```bash
# Interactive (prompts for description)
personas/run-build-persona.sh

# Non-interactive
personas/run-build-persona.sh --describe "Java Spring Boot microservice developer"

# With codebase seeding (detect language/framework from repo)
personas/run-build-persona.sh --describe "backend developer" --codebase /path/to/repo

# Preview without writing files
personas/run-build-persona.sh --describe "Python FastAPI dev" --dry-run

# Skip refinement prompt
personas/run-build-persona.sh --describe "Go gRPC developer" --skip-refinement

# JSON-only output (for testing/piping)
personas/run-build-persona.sh --describe "Rust systems programmer" --json-only
```

## Architecture

```
User
  │
  ├─ --describe "..."   (free-form text)
  └─ --codebase PATH    (optional)
         │
         ▼
  detect-persona.py     (heuristic: extensions + imports + config files)
  (if --codebase given)
         │
         ▼ top-3 matches + confidence scores
         │
  build_initial_prompt()
         │
         ▼ structured prompt
  my-persona-designer-q3  (Qwen3:8b, temp=0.3)
  /api/chat + format={JSON schema}
         │
         ▼ validated JSON spec
  display_proposal()    (shows name, domain, language, temp, constraints)
         │
         ├─ want to refine? → build_refinement_prompt() → LLM (second pass)
         │
         ▼ final spec
  create-persona.py --non-interactive
  (Modelfile generation + ollama create + registry update)
```

## The Designer Model

`my-persona-designer-q3` (`qwen3:8b`, temperature 0.3) is purpose-built for this task. Its system prompt teaches it:

- What Modelfile personas are and why constraints matter
- The MUST/MUST NOT constraint vocabulary (observable, testable rules)
- Valid domains, temperatures, and tiers
- The `my-<slug>-q3` naming convention
- Why fewer constraints are better at 7-8B (≤7 rules follow more reliably)

It uses Ollama's structured output (`format` parameter with JSON schema) to guarantee the response is parseable — no regex, no markdown stripping required.

## Output Schema

The LLM always produces this JSON:

```json
{
  "persona_name": "my-fastapi-q3",
  "domain": "code",
  "language": "Python",
  "temperature": 0.3,
  "role": "Python FastAPI backend developer",
  "constraints": [
    "MUST use async/await for all route handlers; NOT synchronous functions",
    "MUST use Pydantic models for request/response validation",
    "MUST NOT use raw dict returns; always return typed response models"
  ],
  "output_format": "Python code with type annotations",
  "tier": "full"
}
```

This maps directly to `create-persona.py --non-interactive` flags.

## Constraint Sanitization

The LLM may generate constraints with embedded commas (e.g., `"MUST use X, NOT Y"`). Since `create-persona.py --constraints` splits on commas, `build-persona.py` replaces commas within each constraint with semicolons before joining. Constraint meaning is preserved; splitting is reliable.

## Known Limitations

- **8B quality ceiling**: `my-persona-designer-q3` runs on Qwen3:8b. Constraint quality is good but not expert-level. Treat proposals as a strong starting draft — review before accepting.
- **Single refinement pass**: Only one round of feedback is supported. For iterative refinement, run again from scratch with a more specific `--describe`.
- **Name collisions**: If the LLM suggests a name that already exists in the registry, `create-persona.py` will refuse with `[ERROR] Persona already exists`. Re-run with a more specific description, or use `create-persona.py --non-interactive --name my-custom-name ...` to override.

## Future Extensions (Out of Scope)

- Multi-round conversation loop (N turns with history accumulation)
- `qwen3:14b` as the designer model for higher constraint quality
- Auto-retry with a modified name on collision detection
