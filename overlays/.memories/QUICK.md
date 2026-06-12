# Overlays — Quick Status

## session-tracking overlay
- **Version:** v5 (2026-06-12)
- **Status:** stage/promote + session-29 feedback fixes COMPLETE — `--payload` (stage) / `--id` (promote) / `--amend` / `--abort`
- **Tests:** 126 green (full handoff suite)
- **Installed in:** expenses/code, web-research, career-search (all v5, byte-verified per-file with cmp)
- **PR:** #52 on `feature/handoff-redesign-stage-promote` (stacked on feature/ltg-phase3-anchors)
- **Key files:** `overlays/session-tracking/files/handoff/` (source), `overlays/session-tracking/manifest.yaml`
- **SKILL.md:** ACTUALLY rewritten 2026-06-12 (commit 979f66f) — the session-88 commit 75886bb claimed it but only touched manifest.yaml. All 3 copies (overlay/project/user) byte-identical, --dry-run gone
- **Pipeline entry:** `run-handoff.sh` → `handoff.py` — `--payload` stage, `--id <handle>` promote, `--payload f.md --amend` follow-up to last committed session (append+checkoff only, no scalars/header), `--abort <handle>` discard pending run
- **Idempotency:** `--id` checks commit by title suffix (not session number); skipped for amend (never writes header)
- **Session-29 feedback (expenses) fixes:** error messages name regions `role(target)@file:line` + say WHY scalars required; failed stage leaves payload at original path (copy, unlink-last); T-57 `_effective_range` fix now propagated (expenses had stale verifier.py — root cause of their P2)
- **Feedback report:** `~/workspaces/expenses/code/.claude/local/handoff-pipeline-feedback-session29.md` (P1–P5, all closed)

## ref-indexing overlay
- No changes this session
