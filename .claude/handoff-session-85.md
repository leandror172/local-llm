# Session 85 Handoff — Session-Handoff Pipeline (B3 milestone complete)

**Date:** 2026-06-05 · **Branch:** `feature/session-handoff-pipeline` (stacked on `feature/ltg-phase3-anchors`; rebase onto master before any PR) · **Layer:** Tooling side-track (NOT LTG)

> Emergency one-file handoff (session limit ~91%), same pattern as session 84.
> Next session: read this top-to-bottom, apply the tracking updates (§5), re-create
> the to-do list (§6), then resume the build at **B4.1** (§7-8). All code is committed;
> the full suite is **53/53 green**. No code commit pending. (Leave this file in place —
> the user asked NOT to delete the session-84 handoff; do the same here unless told.)

---

## 1. What this session (84→85) did

1. **Folded the session-84 handoff** into the tracking files via a Haiku subagent acting as a
   pure mechanical applier (Claude authored every exact `old→new` splice; subagent applied).
   Commit `013031e`. (This is a small live rehearsal of the F2-Placer vs F3-Applier split.)
2. Built the rest of the **B3 milestone** of the session-handoff pipeline (Scope A = register-driven,
   deterministic, NO local model). Design frozen session 83; spec in
   `docs/plans/session-handoff-pipeline-design.md` (`ref:handoff-pipeline-design`).

## 2. Commits on the branch (this session)

- `013031e` chore: fold session-84 handoff into tracking files
- `84d7b0a` feat: **B3.1** F5 Mechanics + 9 tests (`mechanics.py`, `test_mechanics.py`)
- `ccc4484` feat: **B3.3** per-run logging + 7 tests (`runlog.py`, `test_runlog.py`)
- `a6f43cf` feat: **B3.2** F6 Orchestrator + git adapter + 6 tests (`orchestrator.py`, `gitio.py`, `test_orchestrator.py`); also added deferred task **T-53**

All code in `overlays/session-tracking/files/handoff/` (installs to `.claude/tools/handoff/` via the
overlay `files:` mechanism). **Full suite 53/53 green** (locator 15 + applier 8 + verifier 8 +
mechanics 9 + runlog 7 + orchestrator 6). Run: `cd` into the handoff dir, then
`python3 -m pytest -q > /tmp/p.txt 2>&1; echo exit=$?; tail -6 /tmp/p.txt` (the inline `| tail` glitches).

## 3. What each new module does

- **`mechanics.py`** (F5, no model). `next_session_number` (max `## …Session N…`+1, **bootstraps to 1**
  on a fresh repo — deliberate, not a raise); `today(clock=)`; `compute_header_values(...)` composes
  `Current Session` = `"<date> — Session <N>: <title>"` + passes `current_layer` through;
  `header_field_edits` locates the two **nomodel** header fields → `(Region, value)` edits for F4;
  `apply_field` = the nomodel replace splice the payload applier deliberately refuses;
  `rotate(repo_root, keep=3)` = thin invoker of `rotate-session-log.sh`. Local model verdict 1.
- **`runlog.py`** (B3.3). `create_run_dir(repo_root, session_number, *, clock)` →
  `.claude/local/handoff-runs/session-<N>-<ts>/` (gitignored); `write_input` (verbatim = recovery
  artifact); `RunReport`/`RegionEdit` dataclasses (the F6→logging data contract); `format_report`
  (presence-tested markdown: committed/rolled-back+reason/verify/per-region role+mode+before→after);
  `write_report`. Local model verdict 1 (added missing reason line).
- **`gitio.py`** (B3.2). `SubprocessGit(repo_root)` injectable adapter: `is_clean(paths)`, `add`,
  `commit`, `checkout` (rollback primitive), `status_short`.
- **`orchestrator.py`** (F6, **Claude-authored** — multi-module + git side-effects = local-model
  carve-out). `HandoffPayload` (provisional F7 shape) + `run_handoff(repo_root, register, payload, *,
  git, rotate=, clock=)`. Algorithm: (1) clean-tree precondition on tracking files → abort if dirty;
  (2) write `input.md`; (3) stage — locate every edit against ONE cached original per file; (4) apply
  right-to-left (nomodel→`apply_field`, else→`applier.apply`); (5) `verify` each file's COMBINED
  payload+mechanics edit set (the "F4 verifies F3+F5" requirement); (6-8) write → rotate → git
  add+commit, with `git checkout` as the rollback net on any failure; (9) write `report.md`.
  **Two safety layers:** in-memory verify-then-write (bad bytes never hit disk) + git checkout for
  post-write failures (rotate/commit). 6 tests incl. **2 real-git integration tests** (commit +
  rollback-restore).

## 4. Decisions locked this session (F6, all user-approved)

- Git side-effects behind an **injected adapter** (testable with a fake; one real-git integration test).
- Failure model = **in-memory verify → write only if all pass**, with **git checkout** as the second net.
- **Abort** (not warn) if any tracking file is dirty at start — protects the rollback.
- **Rotation inside** the committed transaction (commit includes trimmed log + new archive), but
  **outside the verify window** (rotation legitimately moves bytes; it's a trusted separate script).
- F6 is **payload-driven + register-driven**: it applies exactly the roles present in the payload, so
  the old "which files in the first apply-cut" open question dissolves.
- **NEW deferred task T-53 (B5.1 preflight check):** surface unmet preconditions (dirty tree) BEFORE
  the heavy handoff call (skill instructions / preflight tool / hook-injected context) so a failure
  doesn't cost a payload-assembly round-trip. Recorded in `tasks.md`.

## 5. Tracking updates to apply next session (the normal handoff would do these)

**`.claude/session-context.md`** → `ref:current-status`: add a **Session 85** bullet after the
Session 84 bullet and rewrite `**Next:**`. Suggested bullet: "**Session 85** (2026-06-05) —
Handoff-pipeline **B3 milestone COMPLETE**: F5 Mechanics (B3.1, `84d7b0a`, 9 tests, verdict 1),
per-run logging (B3.3, `ccc4484`, 7 tests, verdict 1), F6 Orchestrator + git adapter (B3.2,
`a6f43cf`, 6 tests incl. 2 real-git integration). 53 tests green. Deterministic Scope A spine
functionally complete; remaining = B4 (F7 schema + SKILL rewrite). Added deferred T-53 (preflight
check). Session-84 handoff folded via Haiku applier subagent." Set `**Next:**` → "Two tracks —
(LTG) `retrieval/anchors.py` TDD; (handoff-pipeline) **B4.1 define F7 payload schema** next, then
B4.2 SKILL rewrite. B1–B3 done." Also update the `session-reading-guide` Handoff-pipeline row note
to "B1–B3 done (53 tests); **B4.1 F7 schema next**." Optionally append to the session-83
active-decisions bullet: the F6 decisions in §4.

**`.claude/session-log.md`** → add a `## 2026-06-05 - Session 85: Session-handoff pipeline — B3
milestone (F5/F6/logging)` entry (Context / What Was Done / Decisions Made / Next from §1-4 here).
Bump `**Current Session:**` → "2026-06-05 — Session 85: handoff pipeline B3 milestone" and
`**Current Layer:**` → "Tooling side-track — Session-handoff pipeline (B3 done; B4 next). LTG Phase 3
still pending."

**`.claude/tasks.md`** → in the pipeline section: check off `(T-05) B3.1`, `(T-06) B3.2`,
`(T-07) B3.3` → `[x]`; mark the **B3 milestone** done. (T-53 already added.)

**QUICK / KNOWLEDGE files** → DONE at session-85 close (do NOT re-apply): root `.memories/QUICK.md`
Session 85 line added; `overlays/.memories/QUICK.md` status bumped; `overlays/.memories/KNOWLEDGE.md`
gained a "Session-Handoff Pipeline Architecture (2026-06)" entry (register + F1–F6 + F4 trust boundary).

*(Reuse the session-start pattern: Claude authors exact `old→new` splices, a Haiku subagent applies
them — keeps the churn out of main context.)*

## 6. Re-create the to-do list (in-session task tool does NOT persist)

B1, B2, **B3 (B3.1/B3.2/B3.3) are DONE**. Live remaining:
- **B4 — SKILL.md rewrite (milestone)** — blockedBy [B4.1, B4.2]
- **B4.1 — Define F7 payload schema** (startable): the payload Claude emits. See §7 design below.
- **B4.2 — Rewrite `.claude/skills/session-handoff/SKILL.md`** (blockedBy B4.1): decide content,
  emit the F7 payload, invoke the pipeline as ONE Bash call — no file reads, no per-section Edits.
- **Manifest wiring** (B3/B4-adjacent chore): add `registry.yaml` + `files/handoff/*.py` to
  `overlays/session-tracking/manifest.yaml` `files:` — they are NOT yet listed.
- **T-53 B5.1 preflight check** (future).

## 7. B4.1 design sketch (F7 schema) — captured, not built

**Make the payload file Claude emits BE `input.md` — one artifact, two jobs.**
- Format (lean): YAML frontmatter (`session_title`, `current_layer`, `checkoffs: [..]`) + `## role:
  <name>` markdown sections for each authored block. Parses into the existing `HandoffPayload`, and
  `raw` = the whole file verbatim → no drift between structured payload and recovery artifact (same
  no-two-representations principle as F4's recompute-and-compare).
- `payload.py`: `parse(text) -> HandoffPayload` + `validate(payload, register) -> errors`
  (unknown role / missing scalar / malformed task id). Validation = the natural home for T-53 preflight.
- **Open decision — runtime registry load:** the handoff dir is currently **stdlib-only**; loading
  `registry.yaml` needs PyYAML or a tiny loader. Decide before/within B4.1.
- Roles in scope (authored mode only; `intent` mode deferred to the enhancement): `log-entry`
  (prepend), `current-status` / `active-decisions` / `user-prefs` / `reading-guide` (replace),
  `tasks-append` (append), `tasks-checkoff` (via `checkoffs:` ids), header fields (via `session_title`
  + `current_layer` scalars, nomodel).

## 8. Files to READ to rebuild context (in order)

1. `docs/plans/session-handoff-pipeline-design.md` (`ref:handoff-pipeline-design`) — Scope A spec, F1–F7.
2. `overlays/session-tracking/registry.yaml` — the register (10 roles, 4 locator kinds, modes).
3. `overlays/session-tracking/files/handoff/{locator,applier,verifier,mechanics,runlog,gitio,orchestrator}.py`
   + their `test_*.py` — what's built (skim; §3 summarizes APIs).
4. `overlays/session-tracking/manifest.yaml` — install mapping; NOTE the gap (§6 manifest wiring).
5. `.claude/tools/rotate-session-log.sh` — what F5's `rotate()` invokes.
6. `.claude/skills/session-handoff/SKILL.md` — the skill B4.2 rewrites.
7. `.claude/overlays/local-model-conventions.md` (`ref:local-model-conventions`) — verdict/retry rules.

## 9. How to behave / proceed

- **WORKFLOW (hard):** Explanatory output style + `★ Insight` boxes. **Interactive pacing — pause after
  each subtask; do NOT auto-advance.** Propose before side-effecting commands. Build incrementally.
- **Local model:** local-first for leaf modules (verdict 0/1/2 each call); KEEP load-bearing contracts
  (registry, F7 schema, F6 orchestration) Claude-authored. `warm_model qwen2.5-coder:14b` at start. On
  timeout: wait-then-retry, don't escalate. Reread the local-model feedback memories before delegating.
- **Pytest:** run from the handoff dir (flat imports); redirect to a file then tail (inline `| tail` glitches).
- **Advisor:** ask permission before `advisor()` in main session. (Was UNAVAILABLE at session-85 close.)
- **Git:** stay on `feature/session-handoff-pipeline`; rebase onto master before any PR (stacked on
  LTG branch). Use `rtk` for all git/shell. `.claude/settings.json` (dirty) + `expense-reporter/`
  (untracked) are NOT ours — leave them.
- **First actions next session:** (a) apply §5 tracking updates (Haiku-applier pattern); (b) re-create
  §6 to-do list; (c) THEN pause and ask: proceed to **B4.1** (handoff pipeline) or switch to **LTG
  Phase 3 `anchors.py`**. Do not delete this handoff file.
- **Stretch idea (optional, only if budget allows):** dog-food F6 to write a real handoff — the
  tracking files are clean, the register was verified session 83, so `run_handoff` could apply the §5
  updates itself (rollback-protected). Risky without B4 plumbing; author the payload by hand if attempted.
