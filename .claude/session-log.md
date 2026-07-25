# Session Log

**Current Layer:** "Layer 5 — Expense Classifier (oficina P2 track active)"
**Current Session:** 2026-07-25 — Session 129: T-112 input-fit guard + T-120 previous-attempt diff (PR #85); T-118/T-119/T-121 filed; run-provenance safety net + verdict corrections

---
## 2026-07-25 - Session 129: T-112 input-fit guard + T-120 previous-attempt diff (PR #85); T-118/T-119/T-121 filed; run-provenance safety net + verdict corrections

### Context

Resumed with PR #84 (T-114 + T-115) already merged. Discussed T-112's scope, settled its design questions with live evidence, built T-112 and the user's own T-120 proposal end-to-end via TDD + local-model delegation, and opened PR #85. After a compaction, closed out the session: confirmed PR #85's merge, hardened run provenance for the session's live-acceptance run branches, cleaned up stale branches, and corrected two under-reported verdicts the user flagged mid-session.

### What Was Done

- Merged PR #84 (T-114 edit-iteration default + T-115 refactoring-conventions promotion).
- Settled T-112's open design questions with live evidence: probed that Ollama evicts the oldest prompt tokens rather than bounding generation at `num_ctx` (refuting a plausible-but-wrong story that overflow explained T-114's retry-blindness); wrote `docs/findings/oficina-ctx-overflow-2026-07-24.md`.
- Built and shipped T-112 (input-fit guard — `_context_overflow`, `ContextBudgetError`, `ContextLimitUnknown`, `model_context_limit` reading the persona's live `/api/show` ctx) and T-120 (previous-attempt-as-diff — `_previous_attempt_view` + `difflib` against the committed edit baseline), through stubs-then-Ollama delegation after two rejected full-delegation attempts. Suite 332→340.
- Live-accepted the guard both ways: refused a real overflow in 0.72s with zero GPU calls; a normal run's chars/4 size estimate landed within 1.3% of the true token count.
- Found and filed T-119: a whole-file edit run pasted ~110 lines of the acceptance tests into the source module and still reported `passed`/`auto_verdict: 2`/Delivered — discovered by reading the diff of a run that reported green, not by trusting the signal.
- Filed T-118 (run provenance — squash message + trailers + `refs/oficina/<run_id>`, R-D1–R-D6 proposed, not frozen) from a user question about what `submit_run`'s merges actually preserve, and T-121 (the `ref:KEY` marker grammar has five implementations and zero written spec).
- Opened and merged PR #85 (T-112 + T-120).
- Wrote the `feedback_verdicts_assess_patterns` memory after re-auditing this session's own verdicts and finding two that cited only functional defects while silently fixing pattern violations.
- Corrected those two verdicts' `reason` fields in place in `calls.jsonl` (`19d4ddf0edac`, `144600f2d4e2`), pulling the pattern-violation detail from the pre-compaction transcript rather than reconstructing it; kept a `.bak-2026-07-25` copy.
- Applied T-118's R-D2 in isolation: pinned the three live-acceptance run branches under `refs/oficina/<run_id>` before deleting them, so their bytes stay reachable outside `refs/heads/*`.
- Deleted the stale, already-merged `feature/oficina-t114-t115` branch (local + origin) — a convention violation flagged at session start and left uncleaned until now.

### Decisions Made

- T-112 D3: fail loud, not downshift — downshifting would leave less room than the file needs, reopening exactly the mid-file truncation E-D9 already guards against.
- T-112 D1: read the ctx ceiling live from `/api/show`, not `LanguagePack` or `registry.yaml` — Ollama is the source of truth for what a persona actually runs at; the registry records intent, not reality (the T-113 gap).
- T-120 (the user's own proposal) supersedes the earlier "just drop `previous_attempt`" framing and doesn't reopen the s126 M2 reversal — a diff is produced deterministically and only read, so the model still never emits an edit language.
- Verdicts must weigh pattern adherence alongside functional correctness — silently fixing a structural violation while the recorded reason cites only the bug teaches the DPO corpus the structure was fine.
- Adopted R-D2 (pin `refs/oficina/<run_id>` before deleting a run branch) now, in isolation, ahead of R-D1/R-D3 (squash + trailers) — cheap and safety-critical on its own; the fuller convention can wait for a dedicated pass.

### Next

- Decide T-119's detection mechanism (three candidates filed: reject `def test_` in a non-test target; diff against materialized test files for copied spans; size heuristic on insertions vs. objective size).
- Decide T-118's remaining scope: adopt squash-for-message + trailers (R-D1/R-D3), or leave R-D2 (now live) as the whole fix.
- Axis B kinds reconsideration (E-D8 `kind` rename + dead `acceptance.validators` removal) — carried over from session 128, still not started.
- Triage T-113 (ctx-footprint re-probe) and T-116 (ref-integrity baseline note, stale since the session 126–127 drift).

### Gotchas

- GitHub's server-side merge produces its own commit hash — a locally-created merge commit's oid will not appear on `origin/master` after the PR merges; verify by content (the code being present), not by hash equality.
- `git branch -D` only removes the ref; the commit stays reachable (and un-GC'd) as long as any other ref points to it or a descendant — that is the entire mechanism behind pinning `refs/oficina/*` before deleting a run branch.
