# Session Log

**Current Layer:** Layer 5 — Expense Classifier (oficina P2 track active)
**Current Session:** 2026-07-25 — Session 130: T-119 recast — unearned confidence, not a missing detector (owner P4); T-122 + T-124 filed

---
## 2026-07-25 - Session 130: T-119 recast — unearned confidence, not a missing detector (owner P4); T-122 + T-124 filed

### Context

Resumed with PRs #83/#84/#85 all merged and master carrying the s129 handoff commit unpushed. A discussion/triage session by request — no build, no suite change. The whole session was one thread: re-grounding T-119 against the code, then against the user's challenge to its premise.

### What Was Done

- Loaded context (`ref-lookup.sh --paths`, `resume.sh`, both `.memories/` files); confirmed PRs #83/#84/#85 merged and master ahead-1 unpushed, not missing anything.
- **Measured the T-119 leak instead of reasoning about it.** `refs/oficina/dy-Bi1nMo5LIqnpzrtXRTw` (`cd852fa`) was still reachable — the s129 R-D2 pin paid for itself inside one session. The paste is **verbatim, not paraphrased**: 78 non-trivial generated lines appear in `test_prompt.py`, longest **contiguous** verbatim run **77 lines**. Legitimate baseline across all 14 `oficina/*.py` ↔ `tests/oficina/test_*.py` pairs on master: **max 4** (`workerproc.py`, a shared `import` header), 11 of 14 at 0–1. Separation ~20×.
- Corrected two of my own claims mid-thread: option (b) is **not** expensive plumbing (`_generate_with_snapshot` already holds `content`, `test_files`, `worktree`, `target_rel` one line above where `diff_touches_test_files` runs); and **there is no DPO-corpus poisoning** — `auto_verdict` is written to ledger events only (`loop.py:259,273`), the run's real training label is the per-run curated verdict via `run_result`, which H1 authored correctly.
- **Rewrote T-119** in `tasks.md` around the reframe, preserving the original three-detector framing as a triggered fallback rather than deleting it.
- Filed **T-122** (the feasibility band has no owner) and **T-124** (`check-ref-integrity.py` validates the working tree while every other consumer validates what git tracks).
- Pushed master; `origin/master` and `master` in sync.

### Decisions Made

- **T-119's defect is the confident report, not a missing detector.** A per-instance mechanical check is a ratchet: T-119 (tests added) and E-D6 (docstring deleted) are one family — unrequested change to the file. The split is the evaluator framework's own line: **the mechanical layer SURFACES drift, the judge/H1 CLASSIFIES it.** Magnitude is reference-checkable and free; "is this diff in scope" has no reference and is genuinely a judgment.
- **Owner is P4** (judge gate + delivery report), which already promises a diff summary and S17 judge-gates-DPO-labels — the seam `loop.py:251` names and nothing is wired to. T-119 is evidence for P4's priority, not a new mechanism.
- **Not the Phase-2 judge for leak detection specifically**, on three grounds: `code-python.yaml` as written would *pass* the leaked file; the judge tier is 7–8B and this is a 184-vs-137-line comparison, not a quality judgment; it needs both files in context when context is the binding constraint (T-112, T-122).
- **The three detectors demote to a fallback with a countable trigger — "a second leak observed in any run"** — per the recorded lesson that a deferral with a guessed trigger fires on a different trigger. (b) recorded as strongest at N=10 with today's measurement, so it needn't be re-derived.
- **P3-vs-P4 sequencing raised and deferred to next session by the user.** Phasing explicitly permits reordering (*"a phase may ship and sit"*), so P4-before-P3 is legal by design; P4 has no plan doc, which is the actual unit of work if it moves up.
- **The concurrent session's commit was left alone deliberately** — rewriting a commit created by a possibly-still-live session is destructive-git territory. Recorded instead of repaired; the user declined to file it as a task.

### Next

- **Discuss P3 vs P4 sequencing** — the one item the user explicitly deferred to next session.
- Decide T-118's remaining scope (R-D1/R-D3 squash-for-message + trailers, on top of the live R-D2).
- Axis B kinds reconsideration (E-D8 `kind` rename + dead `acceptance.validators` removal) — carried since s128, still not started.
- Triage T-113 (ctx-footprint re-probe), T-116 (ref-integrity baseline), T-124 (checker corpus gap, incl. the keep-or-drop call on three untracked paths).

### Gotchas

- **Two live Claude Code sessions on one working tree corrupt each other's commit boundaries.** A concurrent session (`session_01NuE6KnP73DCQqv3xMfbNEe`, 18:09) committed `docs(T-123)` with `.claude/tasks.md | 12 +++-` — twelve of those lines were **this** session's uncommitted T-119 recast and T-122. Verified after the fact: `git show HEAD:.claude/tasks.md | grep -c "unearned confidence"` = 1. Nothing lost; the history is simply wrong about who wrote what. **`guard-git-add-all.py` does not and cannot cover this** — the other session staged an *explicit path*, the recommended form; the hazard is that `git add <path>` stages whatever is in the tree at that path, including another process's in-flight edits. **The handoff pipeline has the same exposure** (its clean-tree guard tests dirtiness, not authorship). Deliberately not filed as a task.
- `rtk git add <path>` printing `ok (nothing to add)` is the tell that someone else already committed your working-tree change — it reads like a no-op, not like a collision.
- **The ref-marker grammar has no escape form, and the handoff pipeline enforces that the hard way.** Filing T-124 with the literal opening marker quoted as an example made the pipeline's marker-count verifier roll the entire transaction back (it reported one *gained* marker for that key) — a marker mentioned in prose is byte-identical to a marker that declares a block. Rewrite the mention without the literal and re-stage. Two follow-ons: this is a self-inflicted proof of T-121/R-D5 (spec is the deliverable), and the pipeline classified it **`internal_tool_bug`** ("likely a TOOL BUG; report with input.md") when it is a payload-content error — the rollback was correct, the diagnosis was not, and the skill's guidance for that status is "do not keep re-authoring", which would have been the wrong move here.
- A run branch deleted after merge is unreachable, but `refs/oficina/<run_id>` kept the T-119 evidence commit alive across a session boundary and made today's measurement possible. R-D2 justified itself faster than expected.
