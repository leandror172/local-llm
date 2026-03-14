# Ollama Scaffolding — Merge Instructions

## Goal

Inject local model usage conventions into the target repo's CLAUDE.md so that Claude
Code knows to try local models first, how to evaluate output, and how to handle
imperfect results.

## Placement rule

Insert the section **after** any existing environment/infrastructure sections (like
"Environment Context", "Key Technical Facts", or "Build Commands") and **before**
project-specific workflow rules or task-specific instructions.

If the file has no clear structure yet, insert after the first heading.

## Retrofit rule

- If a simpler version exists (e.g., just "try local models first" without the verdict
  protocol or decision tree): **delete** the old section (including its heading) and
  insert the full overlay section in its place.
- If a verbatim or near-verbatim match exists: wrap with overlay markers instead of
  duplicating.

## Do not

- Do not remove unrelated content from CLAUDE.md
- Do not add the section twice
- Do not modify the section content — it is injected as-is by the installer
- Do not place inside a ref block (the section is CLAUDE.md-level, not a ref block)
