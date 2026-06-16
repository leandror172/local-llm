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

