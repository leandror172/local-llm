# Ollama Scaffolding — Merge Instructions

## Goal

Inject a short pointer section into the target repo's CLAUDE.md that directs agents
to read the full verdict/retry policy in `.claude/overlays/local-model-retry-patterns.md`.

The CLAUDE.md section is intentionally small (~6 lines). The full policy lives in the
reference file, not in CLAUDE.md.

## Placement rule

Insert the section **near** any existing "Local Model Usage" section. If one exists,
place it immediately **after** that section (do not replace it — the existing section
has repo-specific model tier lists and conventions).

If no local model section exists, insert after any environment/infrastructure sections
and before project-specific workflow rules.

## Retrofit rule

- If an older version of this overlay section exists (identified by overlay markers):
  replace it with the new version.
- Do NOT delete any existing "Local Model Usage" content that is not inside overlay
  markers — it contains repo-specific model choices and tier lists.

## Do not

- Do not remove unrelated content from CLAUDE.md
- Do not delete repo-specific local model tier lists or cascade rules
- Do not add the section twice
- Do not modify the section content — it is injected as-is by the installer
