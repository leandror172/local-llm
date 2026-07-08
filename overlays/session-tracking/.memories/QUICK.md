# session-tracking overlay — Quick Memory

*Handoff-pipeline current state. Deep design + per-session history: `KNOWLEDGE.md` (this folder).*

## session-tracking overlay
- **Version:** v9 (2026-07-06)
- **Status:** v9 handoff-tooling bug sweep COMPLETE (2026-07-06) — T-78 wrapped-bullet parser continuation-join (`payload.py`), T-62 shim honors `--registry` + prefers co-located engine, T-61 resume.sh reading-guide backported (source ⊇ installed). llm commit on `fix/handoff-tooling-bugs`.
- **Tests:** 178 green (174 + 4 new wrapped-bullet tests in `test_payload.py`, T-78)
- **Installed in:** shared user-level engine `~/.claude/tools/handoff/` is **v9** (carries the T-78 `payload.py` fix) — ALL repos execute it. Per-repo files synced v9 (2026-07-06): expenses/code + web-research got `resume.sh` (T-61) + project shim (T-62); career-search got the shim ONLY — its local "What to read first" `resume.sh` variant preserved (T-61 option 2). llm runs the engine from source. `session-log.md` latest-only in ALL repos.
- **PR:** #53 (failure-clarity) stacked on #52 (`feature/handoff-redesign-stage-promote`)
- **Home-repo invocation (FIXED v9, T-62):** the `run-handoff.sh` shim now honors an explicit `--registry` (bypasses the registry-file guard) and prefers a co-located `handoff.py` over the user-level install — so `overlays/session-tracking/files/handoff/run-handoff.sh --registry overlays/session-tracking/files/registry.yaml` works from the llm home repo AND runs source. The old "call `handoff.py` directly" workaround is retired.
- **Key files:** `files/handoff/` (source), `manifest.yaml`, `files/rotate-session-log.sh`, `files/handoff-harvest.sh` (boundary: `^chore(session-handoff): session `), `files/session-handoff/SKILL.md`

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

