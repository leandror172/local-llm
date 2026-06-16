# Session Log

**Current Layer:** Layer 5 — Expense Classifier
**Current Session:** 2026-06-12 — Session 89: Handoff pipeline — session-29 feedback fixes (P1–P5), --amend/--abort, overlay v5

---

## 2026-06-12 - Session 89: Handoff pipeline — session-29 feedback fixes (P1–P5), --amend/--abort, overlay v5

### Context
Expenses repo session 29 ran the new stage/promote pipeline in the field and hit 1 failed stage, 1 aborted stage, and 1 out-of-band manual edit; the executing agent left a feedback report (`~/workspaces/expenses/code/.claude/local/handoff-pipeline-feedback-session29.md`, P1–P5). This session analyzed it, then fixed everything via Sonnet subagents with main-session review.

### What Was Done
- **Root-cause analysis:** (a) commit 75886bb *claimed* the T5 SKILL.md rewrite but only touched manifest.yaml — every SKILL.md copy still taught the removed `--dry-run` (P1); (b) the v4 propagation to expenses was PARTIAL — stale `verifier.py` without `_effective_range` caused their P2 overlap failure on the already-fixed bug.
- **P-msg** (`f6d1116`): overlap errors name both regions `role(target)@file:line`; validation errors state WHY a field is required.
- **`--amend` + `--abort`** (`771ea5c`, `0fdb42f`): amend attaches additive-only runs (append+checkoff modes; prepend excluded to prevent duplicate session headings) to the last committed session — derived from git, scalars not required, no header write, idempotency skipped, commit suffix `— amend` (closes P4+P5). `--abort <handle>` renames pending→`-aborted` (no manual rm).
- **Copy-don't-move** (`bba6cce`): stage copies payload to `input.md` up front; unlink-original is the last op on success only — failed/crashed stage never consumes the author's file (closes P3).
- **SKILL.md recovery** (`979f66f`): genuine stage/promote rewrite + amend/abort + exact pre-flight one-liner; overlay/project/user copies byte-identical; fixed a wrong checkoff description in 2 of 3 copies (closes P1).
- **Overlay v5 propagated** to expenses, web-research, career-search — all 10 runtime modules + run-handoff.sh byte-verified with per-file `cmp`; registries untouched (`manual_if_exists`).
- **126 tests green** (was 44 claimed / 105 actual baseline). PR #52 body rewritten (REST API; gh GraphQL path broken by deprecated projectCards). README + index.md stale `--dry-run` refs fixed; overlays QUICK/KNOWLEDGE updated (also repaired corrupted lines in KNOWLEDGE.md stage/promote section).

### Decisions Made
- **Minimal `--amend` over `--session N`:** recovery path is strictly LESS powerful than the happy path — session number derived never typed (preserves the F5 nomodel-fence philosophy); worst amend mistake is a duplicate appended task.
- **Subagent workflow:** Sonnet subagents did implementation (authorized to use advisor()); main-session review re-derived invariants and caught 2 real bugs behind green tests (amend stage reported N+1 while promote committed N; prepend allowlist hole letting log-entry duplicate session headings).
- **Process learnings recorded in overlays KNOWLEDGE.md:** propagation needs a verify step; "done" claims in commits/memory are unverified; review must re-derive, not trust test counts.

### Next
- Merge PR #52 (rebase `feature/ltg-phase3-anchors` onto master first if landing separately)
- LTG Phase 3: rebase `feature/ltg-phase3-anchors` onto master, write `retrieval/anchors.py` TDD per `ref:ltg-phase3-decisions`

