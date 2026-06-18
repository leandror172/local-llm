# Overlays — Quick Memory

## session-tracking overlay
- **Version:** v7 (2026-06-17)
- **Status:** session-93 append↔checkoff fix + failure-clarity sweep COMPLETE (2026-06-17)
- **Tests:** 173 green (full handoff suite; xfailed test now xpasses)
- **Installed in:** expenses/code, web-research, career-search (all v6 + B+C migrated); llm runs the engine from source. `session-log.md` latest-only in ALL 4 repos.
- **PR:** #52 on `feature/handoff-redesign-stage-promote`
- **Key files:** `files/handoff/` (source), `manifest.yaml`, `files/rotate-session-log.sh`, `files/handoff-harvest.sh`, `files/session-handoff/SKILL.md`

### B+C distribution (2026-06-17)
- **Pipeline modules:** always user-level at `~/.claude/tools/handoff/` — new `always_user_files:` manifest key; never per-repo.
- **Shim + SKILL.md:** follow `--install-level` (renamed from `--skill-level`); default `user` → `~/.claude/`; `project` → per-repo `.claude/`.
- **run-handoff.sh:** rewritten as thin shim; calls `$HOME/.claude/tools/handoff/handoff.py`; registry guard (`exit 0` if no registry) makes user-level hooks safe in uninstalled repos.
- **Migration:** 3 target repos committed — old `.py` copies removed, new shim written; `~/.claude/tools/handoff/` populated via installer.
- **Future:** D (pip editable) deferred; G/H remain long-term targets; shim is the stable per-repo seam.

### Session-90 increments (see KNOWLEDGE.md for detail)
- Latest-only topology + value-only payload + git-log harvest + clean break v5→v6.

### Prior rounds (see KNOWLEDGE.md)
- **session-89 stage/promote + session-29 fixes:** `--payload` stage / `--id` promote / `--amend` / `--abort`; error messages name regions `role(target)@file:line`; copy-don't-move; idempotency by commit-title suffix.
- **Deferred:** Increment-4 separate-window synthesis (documented only); local-model Placer (E1–E2) fills the same value schema.

## ref-indexing overlay
- No changes this session
