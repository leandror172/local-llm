## 2026-06-26 - Session 95: Cache-warmed subagent fan-out + 6-task batch (PRs #57-64)

### Context

Autonomous multi-agent batch session: designed a cache-warmed planner→implementer fan-out pattern, exercised it on 6 deferred tasks, and assembled the results into stacked PRs on top of Phase 2.5 (PR #56). Mostly run unattended via remote control.

### What Was Done

- Designed + documented the **cache-warmed subagent fan-out pattern** (`docs/patterns/cache-warmed-subagent-fanout.md`, `ref:cache-warmed-fanout`) + two tier agent types (`.claude/agents/plan-warm.md` Opus/medium, `impl-warm.md` Sonnet/high). Memory: `reference_cache_warmed_fanout.md`. Resolved subagent-effort mechanism (frontmatter `effort:` only — no per-spawn Agent param) and the turn-boundary-breakpoint cache rationale.
- Ran 5 Opus planners → detailed per-task plans (`scratchpad/plan-T*.md`), then 6 implementers for **T-26, T-59, T-30, T-19, T-58, T-42**. All green: T-26 (28 personas incl 2 inactive gemma3-27b), T-59 (174), T-30 (257), T-19 (21), T-58 (13+174), T-42 (10).
- Opened **8 PRs**: #57 `batch/session-97-base`→master (umbrella = Phase 2.5 + all 6 tasks + infra, "everything merged"); #58–64 per-task review PRs → `batch/s97-review-base` (Phase-2.5 baseline ref). #64 = fan-out infra + T-66.
- Salvaged two base-branch mistakes: implementers' `isolation:worktree` shared ONE worktree (no per-agent isolation) AND were based on stale master; re-homed every task commit onto the Phase-2.5 tip (af3fea4) via cherry-pick (clean except a resolved `retrieval/.memories/QUICK.md` merge).

### Decisions Made

- T-58 `--verify`: SAME = EOL-normalized (not byte-exact); 3b=(a) — templates/`manual_if_exists` DIFF+MISSING also gate the exit code.
- T-26: included the 2 inactive gemma3-27b coding personas (skip-list covers archived/benchmark, not inactive).
- PR topology: per-task PRs target a Phase-2.5 baseline ref; umbrella #57 carries everything. The two requests ("children PR into BASE" + "BASE shows everything merged") are git-incompatible as one stacked target, so split.

### Next

- Review + merge the 8 PRs (children #58–64, then umbrella #57 → master). Then run the T-26 rebuild checklist (`scratchpad/rebuild-checklist-T26.md`, 28 serial `ollama create`).
- LTG Phase 4 (graph + communities) on the merged full-corpus index.
- T-66: validate the fan-out pattern + revisit protocol-embedding — note the multi-turn warm→inject flow was NOT exercised (single-shot only this session).

### Gotchas

- `isolation:worktree` does NOT isolate concurrent background agents — they shared one worktree, stacking scoped commits (recoverable). For true parallel isolation, pre-create worktrees off the right base and spawn plain agents.
- Two heavy-I/O implementers (T-26, T-19) hit "Prompt is too long" but had committed their scoped work first — overflow cost the report, not the code.
- Backups tagged `backup/s97-*`; recovery notes in `scratchpad/worktree-entanglement-recovery.md`. This handoff committed onto `batch/session-97-base` (rides in PR #57).
