# Session Log

**Current Layer:** "Layer 5+ — oficina (P2 evaluated loop, post-slice)"
**Current Session:** 2026-07-17 — Session 123: "oficina P2 deferrals T-96–T-98 resolved — PR #77 (suite 260)"

---
## 2026-07-17 - Session 123: "oficina P2 deferrals T-96–T-98 resolved — PR #77 (suite 260)"

### Context

PR #76 (P2 first slice) merged to master before the session; picked the T-96–T-98 review-deferral cleanup pass over immediate widening, on the fresh branch `feature/oficina-p2-deferrals`.

### What Was Done

- **T-96 RESOLVED (b)+(c)** — `server._ref_lookup_script()` call-time fallback chain (`OFICINA_REF_LOOKUP` → `LLM_REPO_ROOT` → package-relative, mirroring `evaluator._validate_code_script`) + fail-loud `RefsDropped {run_id, refs, reason}` worker-ledger event on unresolved `context.refs` (frozen run-event registry untouched). 9 tests (`test_refs_resolution.py`).
- **T-97 RESOLVED** — retention sweep gained a `workspace` prune class (spec.json → rev-parse → `worktree remove --force` + `prune`, mirroring `Workspace.teardown`); repo-gone still reclaims disk with `git_pruned=False` recorded; TTL staleness moved to run-dir mtime (empty-artifacts crashed runs now visible). 7 git-integration tests (`test_retention_worktrees.py`).
- **T-98 RESOLVED** — canonical failure-path spelling = worktree-relative: parser keeps pytest nodeid prefixes, evaluator stamps compile failures with `target_relpath`, `scope_of`/`diff_touches_test_files`/loop `target_files` compare normpath'd relpaths. Both confirmed review collision scenarios pinned as regressions.
- Decision records appended in place to `ref:oficina-p2-review-deferred`; tasks checked off; mcp-server QUICK/KNOWLEDGE memories updated (new invariants section).
- **PR #77 opened + pushed** (one commit per task + docs commit). Suite 241 → 260.
- `mcp-server/Makefile` gained `make test` / `make test-oficina` (+ `ARGS=` passthrough); registered in `ref:bash-wrappers`.

### Decisions Made

- T-96 option (a) (spawn-env propagation) rejected as primary: a plain-shell `oficina submit` has no `LLM_REPO_ROOT` to propagate either — the call-time fallback fixes both spawn surfaces.
- The fail-loud note is a WORKER-ledger event (`RefsDropped`, RetentionPruned precedent), not a run event — the frozen run-event registry stays untouched.
- T-97 repo-gone rule (user call): workspace tree always reclaimed, git prune skipped-but-recorded — refusing to prune would re-leak the disk.
- Local-model delegation flipped per artifact class: test bodies delegated for hermetic tests (T-96), implementation delegated for single-file behavioral change (T-97), hand-written for git-integration tests + surgical multi-site edits (T-98, per the test_workspace.py precedent).

### Next

- **PR #77 merge decision** (small, 3 fixes + docs — lean: merge, then branch fresh for widening).
- **oficina P2 post-slice widening** (P2-D1): more kinds/validators, escalation ladder (P2-D9), tiny-model classifier (P2-D4 — pairs with the M-P1b/P2 classifier benchmark).
- **T-93 measurement is now unblocked** (T-96 fixed the CLI-worker refs drop) — measure the mermaid-as-context verdict via a real loop delegation.

### Gotchas

- `RetentionPruned`'s TTL policy previously measured artifacts-dir mtime AND skipped empty-artifacts runs — a hard-crashed worktree run was invisible twice over. If a sweep behaves oddly on old stores, stale run-dir mtimes are now the trigger.
- `oficina watch` still breaks on run_ids starting with `-` (minor item in `ref:oficina-p2-review-deferred`, still open).
