## 2026-06-11 - Session 87: Handoff stage/promote redesign — design + plan

### Context
Continuing handoff-pipeline work. User surfaced a collision problem: `.claude/local/handoff-pending.md` is a well-known path — leftover from a failed session gets silently overwritten. Opened design discussion for a redesign.

### What Was Done
- Diagnosed the collision problem and three orthogonal design axes (input transport / input shape / execution mechanism)
- Two advisor reviews: design discussion + final plan — 7 issues surfaced and resolved (vestigial `--dry-run` flag, `Path.rename()` cross-device failure, commit/dir-rename non-atomicity, session-N stale in handle, `create_run_dir` compat default, two failure-state distinction, residual collision note)
- Designed stage/promote flow: **rename-on-ingest** (Option b) + **dry-run mints handle** (Option Y)
- Created `docs/ideas/handoff-mcp-migration.md` — full design notes (MCP deferred as T-55)
- Copied `.claude/handoff/overlap-bug-report.md` from career-search repo (overlap false-positive bug, T-57)
- Added tasks T-55 (MCP migration, deferred), T-56 (add-task tool), T-57 (overlap bug Fix A)
- Wrote implementation plan: `~/.claude/plans/handoff-redesign-rename-on-ingest.md` (6 tasks, TDD order, verification script, pre-session reading list)
- Created branch `feature/handoff-redesign-stage-promote`; committed all session artifacts
- Updated `overlays/.memories/QUICK.md` + `KNOWLEDGE.md`

### Decisions Made
- `--payload` = **stage**: ingest (shutil.move to run dir, freeing well-known path) + validate-locate-verify in memory + write report + emit JSON handle
- `--id` = **promote**: find pending dir + recompute all values from current files + idempotency git-log check + apply + commit + rename dir suffix
- `--dry-run` flag **dropped** — it was vestigial (stage always writes 3 files)
- Run dir status suffix (`-pending`/`-success`/`-failed`) is the artifact system; `shutil.move` throughout for cross-device safety
- Promote is **idempotent**: checks git log before re-applying (prevents double-application if process dies between commit and dir-rename)
- JSON stdout is the output contract; model relays to user from parsed fields
- MCP migration deferred (T-55); structured schema per role deferred with it

### Next
- Execute `~/.claude/plans/handoff-redesign-rename-on-ingest.md` — 6 tasks (runlog → orchestrator → handoff.py → gitio → SKILL.md → overlay bump); consider fixing T-57 (overlap bug) in same session
- LTG track: rebase `feature/ltg-phase3-anchors` onto master, write `retrieval/anchors.py` TDD

---

