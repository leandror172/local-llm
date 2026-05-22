# Task: Backfill SOLID + Scope Constraints to All Coding Personas

## Background

During session 63 (2026-05-22), three 14B coding personas received two new
constraint groups after observing consistent failure modes during Plan 1
(refs param) implementation:

**Already updated (skip these):**
- `modelfiles/mcp-q25c14-qwen25c14.Modelfile`
- `modelfiles/python-q25c14-qwen25c14.Modelfile`
- `modelfiles/python-q3-14b-qwen3-14b.Modelfile`

## Failure modes that motivated the constraints

1. **Scope creep** — when asked for a targeted addition, models rewrote
   surrounding code (dropped persona validation, swapped `client.chat()`
   for invented methods, removed try/except).

2. **Monolithic functions** — generated helpers that mixed I/O with logic
   and used vague names like `process_data`.

## Constraints to add to each coding persona

Add after the last existing `MUST NOT` line, before `FORMAT:`:

```
- MUST give each function exactly one responsibility — if its name would need "and", split it into two
- MUST name functions after what they return or do (e.g., _build_refs_block, _validate_path — never process_data)
- MUST write function bodies as delegated steps: call named helpers, combine results, return — avoid inline logic mixed with I/O in the same function
- MUST keep function bodies under ~15 lines; extract inner concepts into named helpers when longer
- MUST NOT modify any code outside the explicitly requested scope — leave all surrounding lines exactly as provided in context
```

## Scope: which Modelfiles to update

All coding personas that don't already have the constraints (grep for
`MUST NOT modify.*scope` to find what's missing). As of session 63, the
full Modelfile list is in `modelfiles/`. Candidates include but are not
limited to: all `go-`, `java-`, `python-` (non-updated), `rust-`,
`react-`, `angular-`, `codegen-`, `coding-assistant-`, `shell-` variants.

Non-coding personas (summarizer, translator, classifier, career-coach,
tech-writer, etc.) should be skipped — the constraints are code-specific.

## Execution steps

1. Grep for missing constraints: `grep -rL "MUST NOT modify.*scope" modelfiles/*.Modelfile`
2. For each coding Modelfile in the result: add the 5 constraint lines
3. Re-register each with `ollama create <persona-name> -f <modelfile>`
4. Commit as: `feat(personas): backfill SOLID + scope constraints to all coding personas`

No tests needed — system prompt changes are validated by use.
