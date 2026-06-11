# Session Log

**Current Layer:** Layer 5 — Expense Classifier
**Current Session:** 2026-06-11 — Session 88: Handoff stage/promote redesign — implementation (T1–T7) complete
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-25-to-2026-05-25.md`, `.claude/archive/session-log-2026-05-26-to-2026-05-26.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-28-to-2026-05-28.md`, `.claude/archive/session-log-2026-05-29-to-2026-05-29.md`, `.claude/archive/session-log-2026-05-29-to-2026-05-29.md`, `.claude/archive/session-log-2026-05-30-to-2026-05-30.md`, `.claude/archive/session-log-2026-05-30-to-2026-06-02.md`, `.claude/archive/session-log-2026-06-04-to-2026-06-04.md`, `.claude/archive/session-log-2026-06-04-to-2026-06-04.md`, `.claude/archive/session-log-2026-06-06-to-2026-06-06.md`

---

## 2026-06-11 - Session 88: Handoff stage/promote redesign — implementation (T1–T7) complete

### Context
Continuation of design+plan work from prior sessions. Picked up T3 (handoff.py) which had a broken local model output on disk from the prior session. T1 (runlog) and T2 (orchestrator) were already committed.

### What Was Done
- **T1 (runlog.py):** status suffix on run dirs (`-pending`/`-success`/`-failed`), `find_pending_run` / `promote_run_dir` / `mark_run_failed` / `count_runs_by_status` / `peek_session_number` — committed in prior session
- **T2 (orchestrator.py):** dropped `dry_run`, added `run_dir` IoC param (caller owns lifecycle), exposed `stage_and_apply` as public API — committed in prior session
- **T3 (handoff.py):** `--payload` (stage: validate → rename-on-ingest via `shutil.move` → in-memory apply → emit JSON, dir stays `-pending`) + `--id` (promote: idempotency by title suffix → `run_handoff` → rename dir). Local model 3× verdict 0 (truncation + semantic errors — stage path promoted when it shouldn't; reconstruction sort wrong); written directly. Key fix: idempotency check uses commit title suffix, not session number — after the first commit the header updates and `peek_session_number` returns N+1, causing a false miss on crash-recovery re-run
- **T4 (gitio.py):** `log_messages(n)` + 4 tests. Switched to `my-python-q25c14` (evicted `my-python-q3`); verdict 2 on first attempt with 14B model
- **T5 (SKILL.md):** Step 4 rewritten for two-call stage/promote flow with 3 recovery branches (validation_failed, stage_ok+promote_fail, crash-recovery idempotency)
- **T6 (manifest v3→v4):** overlay propagated to expenses/code, web-research, career-search via `install-overlay.py`
- **T7 (verifier.py):** `_effective_range` helper fixes tasks-append + tasks-checkoff false-positive; reconstruction sort fixed (`reversed(sorted_asc)` → `sorted(reverse=True)`) to match applier order for equal-start regions; regression test `test_append_and_checkoff_in_same_block_do_not_overlap` added
- **44 tests green.** PR #52 opened on `feature/handoff-redesign-stage-promote`.

### Decisions Made
- Idempotency check matches `" — {session_title}"` suffix rather than exact commit message — prevents N+1 false-miss after header update (discovered via test `test_id_idempotent_commit_exists_but_dir_still_pending`)
- `_effective_range` requires two coordinated fixes: the helper (overlap detection) AND `sorted(reverse=True)` in reconstruction (equal-start region ordering must match applier's stable-sort-descending behaviour)
- Model switch for T4: `my-python-q3` consistently truncated files >120 lines; `my-python-q25c14` solved on first try

### Next
- Merge PR #52 (stacked on `feature/ltg-phase3-anchors`; rebase onto master first if that branch is landing separately)
- LTG Phase 3: rebase `feature/ltg-phase3-anchors` onto master, write `retrieval/anchors.py` TDD per `ref:ltg-phase3-decisions`

---

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

## 2026-06-09 - Session 86: Flexible task ID checkoff + overlay distribution analysis

### Context
Continued from session 85–87 (Scope A complete, PR #50 open). Started by examining how the
handoff pipeline handles task checkoffs: accepted formats, locator mechanics, and the model's
role in specifying what to tick off. Evolved into a design session + implementation.

### What Was Done
- Analysed `_locate_checklist` (structural pattern) vs real tasks.md formats across 3 repos
  (expenses, career-search, web-research) — identified 2 touch points: locator pattern + ID
  validation regex
- Designed and implemented **checkbox-first locator**: enumerates `- [ ]` lines, filters by
  word-boundary ID match within first 40 chars; handles `(T-NN)`, `**ID**`, bare-numeric
  (`1.0`), and prefix-dash (`RUI-4`) formats without touching `applier.py` or `orchestrator.py`
- Broadened payload ID validation: `^T-\d+$` → `^[A-Za-z\d][A-Za-z\d.\-]*$`; hash IDs
  (`#035`) remain rejected (not pipeline task identifiers)
- Fixed test drift: existing `bogus` negative test updated to `#bogus` (bogus is now valid)
- 5 new locator tests + 6 new payload tests; **88 tests green** (was 77); overlay bumped to **v3**
- Synced `locator.py` + `payload.py` to all 3 installed repos (expenses, career-search,
  web-research) — separate commits per repo
- Updated `SKILL.md` (project-level + user-level): broadened ID format guidance
- Converted `(LLM repo)` task in web-research tasks.md → `(T-01)` pipeline-compatible format
- Wrote **overlay distribution options analysis** (9 options A–I) to
  `docs/findings/overlay-distribution-options.md` (`ref:overlay-distribution-options`)
- Updated `.memories/QUICK.md` + `overlays/.memories/QUICK.md` with session 88 status

### Decisions Made
- **Checkbox-first + 40-char positional limit:** task IDs always appear in the first ~40 chars
  of a `- [ ]` line; description text that references other IDs appears later — the limit is
  the semantic firewall. Word-boundary lookarounds prevent `T-1` matching `T-10`.
- **Hash IDs (`#035`) intentionally rejected:** they are application tracking numbers (external
  system refs), not pipeline task identifiers; the regex boundary encodes this distinction
- **Distribution options near-/medium-/long-term:** Option E (`--sync` installer mode) near-term;
  Option B (shared `~/.claude/tools/`) medium-term; Option G (dedicated MCP server) long-term;
  Option H (Claude Code plugin) if the pipeline needs to travel beyond this machine

### Next
- Two tracks: **(LTG)** rebase `feature/ltg-phase3-anchors` onto master, then write
  `retrieval/anchors.py` TDD; **(handoff-pipeline)** update PR #50 description (88 tests,
  flexible ID), then land it after the LTG PR merges

