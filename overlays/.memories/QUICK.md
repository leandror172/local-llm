# Overlays — Quick Memory

## session-tracking overlay
- **Version:** v6 (2026-06-16)
- **Status:** session-90 redesign COMPLETE — latest-only topology + value-only payload + git-log harvest, on top of stage/promote (`--payload` / `--id` / `--amend` / `--abort`)
- **Tests:** 166 green (full handoff suite)
- **Installed in:** expenses/code, web-research, career-search (all v6, per-file `cmp`-verified); llm runs the engine from source. `session-log.md` migrated to latest-only in ALL 4 repos.
- **PR:** #52 on `feature/handoff-redesign-stage-promote`
- **Key files:** `files/handoff/` (source), `manifest.yaml`, `files/rotate-session-log.sh`, `files/handoff-harvest.sh`, `files/session-handoff/SKILL.md`

### Session-90 increments (this round)
- **Latest-only topology (P1):** `session-log.md` holds ONLY the newest entry; each handoff rotates the prior entry to a slugged archive `session-log-<date>-s<N>-<slug>.md`; the ~46-ref `Previous logs:` pointer line is GONE (archive dir + filenames = index). `rotate-session-log.sh --keep 1`; `header-previous-logs` role dropped from `registry.yaml`.
- **Value-only payload (P2, D1=2-full):** `log-entry` = structured snake_case slots (`context`/`what_was_done`/`decisions`/`next`/`gotchas`); the pipeline renders ALL scaffold incl. the `## <date> - Session N: <title>` heading. Claude never writes the heading or computes N. `LogEntry` + `render_log_entry()` (mechanics.py); `parse()` excludes log-entry from `blocks` (no double-apply); newline contract double-guarded.
- **Git-log harvest (P3):** `handoff-harvest.sh` emits commit subjects since the last `chore(session-handoff):` commit → seeds `what_was_done` (zero model, zero re-read). SKILL Step 2 calls it; Step 3 reuses resident interiors instead of re-`ref-lookup`.
- **Clean break (D2):** manifest v5→v6; all repos migrate in lockstep; no dual-accept.

### Prior rounds (see KNOWLEDGE.md)
- **session-89 stage/promote + session-29 fixes:** `--payload` stage / `--id` promote / `--amend` / `--abort`; error messages name regions `role(target)@file:line`; copy-don't-move; idempotency by commit-title suffix.
- **Deferred:** Increment-4 separate-window synthesis (documented only); local-model Placer (E1–E2) fills the same value schema.

## ref-indexing overlay
- No changes this session
