## 2026-06-30 - Session 96: Land session-97 batch (PRs #56/#57) to master + cleanup + overlay test runner + git-add guard

### Context

Continuation of the session-97 batch. Reviewed and fixed PR #63 (T-42), then landed the whole stack to master — Phase 2.5 (#56) as its own merge, then the 6-task umbrella (#57) — cleaned up every branch/worktree, and added two pieces of repo tooling (overlay test runner, git-add guard).

### What Was Done

- **PR #63 (T-42) review fix:** rewrote the ref-lookup test **fully hermetic** (builds its own fixture corpus via `--root`, no repo coupling; deleted the `baseline-*.txt` snapshots), relocated it into the overlay source (`overlays/ref-indexing/files/tests/`, manifest v3→v4), and dropped the installed `.claude/tools/tests/` copy as a generated artifact. New `overlays/Makefile` with `make test`. Reviewer comment resolved.
- **Landed the session-97 stack to master:** merged #56 (Phase 2.5) as its own commit (`ca1acec`), then #57 (6 tasks + fan-out infra, `245fc95`) — clean SHA-dedup via the shared `af3fea4` boundary. Rewrote #57 title/body to reflect task-batch scope (via REST `PATCH` — `gh pr edit` hit a projectCards GraphQL deprecation bug).
- **Cleanup:** closed review PRs #58–64; deleted all session-97 branches (local + remote) + 2 worktrees + the merged base/review-base; verified nothing lost — `range-diff` proved `worktree-agent-a3fb6f15` fully redundant (3 patch-identical + 2 content-identical, only Phase-2.5 context shifts).
- **Overlay test runner:** extended `overlays/Makefile` to run all 3 suites (**196 tests** = ref-indexing 9 + session-tracking 174 + installer 13) via new `overlays/scripts/` runners + `run-all-tests.sh` aggregator; `ARGS='-k x'` pytest pass-through. `test-merge-plan.py` excluded (manual Ollama diagnostic, not a suite).
- **git-add bulk-stage guard:** `PreToolUse(Bash)` hook (`.claude/hooks/guard-git-add-all.py`) + committed hookify rule (`.claude/hookify.block-bulk-git-add.local.md`) + CLAUDE.md Git Safety rule. Denies `git add -A`/`.`/`--all`, allows explicit paths + `git add -u`.

### Decisions Made

- Phase 2.5 lands as its **own merge before** the umbrella, **merge-not-squash** so #57's shared commits dedup by SHA (squash would re-duplicate Phase 2.5 on master).
- Overlay tests are **hermetic and ship with the overlay source**; the installed `.claude/tools/` copy is a generated artifact (not committed) — but pre-existing installed *script* copies are left alone (source-only rule is for new artifacts).
- Makefile **delegates to `scripts/`** — per-suite cwd/interpreter quirks belong in scripts (reusable from shell/CI), Makefile stays a thin index.
- git-add guard regex is **anchored to a command position** (`^` or after `; & | newline ( {`, optional `rtk ` prefix) — so a commit message / grep that merely *mentions* the pattern is allowed; only real invocations are blocked. (First draft matched anywhere and blocked its own commit message.)

### Next

- **LTG Phase 4 — graph + communities** on the fresh 1018-row full-corpus index: `alias_of` lists → edge table; anchor↔anchor edges from `index.md` cross-refs. Unchanged top priority — Phase 2.5 and the task batch are now all on master.

### Gotchas

- `gh pr edit` is **broken** against this repo: it issues a GraphQL query including `projectCards` (Projects Classic, being sunset) and aborts the mutation while reporting only a warning — title/body silently unchanged. Use `gh api repos/{owner}/{repo}/pulls/N -X PATCH -f title=… -F body=@file` instead.
- **WSL2 over the Windows fs does not carry the exec bit into git's index** — `chmod +x` works locally but git stages `100644`; use `git add --chmod=+x` or scripts land non-executable (make/CI can't run them).
- The new **git-add guard blocks any bash command** with `git add -A/./--all` at a command position. When a command must contain the literal (it no longer blocks *mentions*, but to be safe) assemble the pattern at runtime or commit via `git commit -F <file>`.
- The **cozempic plugin auto-bumps `.claude/settings.json`** hook-schema every session (v12→v13 this session) — perpetual uncommitted churn; it rode along in the guard commit.
