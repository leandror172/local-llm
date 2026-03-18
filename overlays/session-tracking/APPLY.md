# APPLY.md — session-tracking overlay

## Goal

Inject the session tracking workflow rules into CLAUDE.md so agents know to run
`resume.sh` at session start and to wait for explicit user permission before
proceeding between phases.

## Placement rule

Insert near the top of CLAUDE.md — after any `<!-- overlay:ref-indexing -->` section
if present, before any project-specific rules. The resume instruction should appear
early so it is one of the first things an agent reads on session start.

## Retrofit rule

- If CLAUDE.md already has a "Resuming Multi-Session Work" section **without** overlay
  markers: delete that section (including its heading) and insert the full overlay section
- If CLAUDE.md already has `<!-- overlay:session-tracking -->` markers: wrap existing
  content with updated markers instead of duplicating content

## Do not

- Do not remove unrelated content from CLAUDE.md
- Do not add the section twice
- Do not remove or modify any `<!-- overlay:ref-indexing -->` section if present
