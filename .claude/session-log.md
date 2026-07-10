# Session Log

**Current Layer:** Layer 5 — Expense Classifier
**Current Session:** 2026-07-09 — Session 111: session-tracking v11 — resume.sh becomes config, the pipeline becomes a package (PR #71)

---
## 2026-07-09 - Session 111: session-tracking v11 — resume.sh becomes config, the pipeline becomes a package (PR #71)

### Context

Opened on T-80 (make the `customizable:` reset warning discriminate). The user reframed it — "what resume.sh brings up could be configurable" — which dissolved half of T-80 and exposed a chain of defects beneath it. Everything below descends from that reframe.

### What Was Done

- **Discriminating signals (T-80a):** `manual_if_exists` records `SAME` when byte-identical; `handle_customizable` records `INFO … no-op` vs `WARN-CLOBBER`. The T-80 spec was unimplementable as written (decision-3 fires when there are NO markers, so there is no installed interior to compare) — the answerable question is whether the overlay default is present verbatim. Polarity is deliberate: silence only on proof of safety.
- **Packaging flip (R-D7 + R-D9):** ten loose `.py` files → `src/sessiontracking/{register,handoff,resume}` with entry points `st-handoff` / `st-resume`. `register/` is a layer-0 primitive both products import; neither imports the other. `always_user_files:` removed. Distribution option D ADOPTED.
- **`resume.yaml` step interpreter (R-D1/2/3):** six hardcoded bash sections → a step list. Fixed vocabulary (`text`/`region`/`log_next`/`git_log`/`git_status`) + a `run:` escape hatch. `region:` steps name a **register role**, resolved through the same `locate()` the handoff writes with — wiring the read side the register has asked for since session 83.
- **Schema validation:** `registry.yaml`'s `version:` key was read and ignored in five repos; `load_register` now refuses an unsupported schema (exit 2).
- **`--verify` rebuilt (T-82):** three questions, one per kind of ownership, plus a new **locator contract** (`verify_locators:`) asserting every register role resolves. It found four real bugs on its first run.
- **Migrated all five repos to v11** and committed in each; `--verify` exit 0 everywhere. career-search's "What to read first" variant survived, as two lines of its own `resume.yaml`.
- **Bookkeeping:** T-43 closed (absorbed), T-80 closed (a done, b cancelled), T-82 closed, T-58/T-60 annotated, `tasks.md` line-40 open decision answered. T-81 and T-83 filed.
- **#7 done:** every repo now invokes the handoff identically — no `--registry`. Also removed llm's project-level `SKILL.md` shadow, three overlay versions stale.
- **Report:** `docs/reports/session-111-report.md`. **Plans:** `docs/plans/resume-config-steps.md` (R-D1–R-D10), `docs/plans/overlay-install-baseline.md` (T-83, B-D1–B-D8, unfrozen).

### Decisions Made

- **Code ships as a package; config ships as an overlay.** The installer's remaining job is `registry.yaml`, `resume.yaml`, templates, `CLAUDE.md`, `SKILL.md` — files no package manager should own.
- **R-D7 and R-D9 are one decision.** Extracting the `register/` primitive looked expensive only because the flat directory had no package semantics. Packaging is what makes the extraction cheap.
- **Three version facts, never conflate:** package `--version` (machine-global) ≠ `registry.yaml: version:` (per-file schema contract) ≠ CLAUDE.md `<!-- overlay:session-tracking vN -->` (per-repo config generation). The marker disentangles; it does not dissolve.
- **A step earns a fixed kind when the overlay owns the invariant it depends on.** `log_next` parses session-log structure; `git_log` pins plain `git`. `run:` is for what only the repo knows — executable config at Makefile trust level, adopted knowingly.
- **`--verify` asks a different question per ownership.** Byte-equality is meaningless for a file the repo owns; what must hold is the locator contract. Write roles gate (`BROKEN`), read-only advise (`ABSENT`).
- **T-80(b) CANCELLED** — it repaired a workaround R-D5 deleted. `customizable:` keeps zero call-sites; that is the healthy steady state for an escape hatch, and the category stays.
- **T-54 is NOT done.** It asks for a `--force-manual` override, still unbuilt. Three commits this session mislabel the identical-file fix as T-54; corrected in `tasks.md` and both QUICK memories. Sequence T-54 after T-83 — with a baseline it likely shrinks to `--theirs`.
- **llm is a normal consumer of its own overlay.** CLAUDE.md markers, a real register copy, `quick-pointers` moved out of `index.md`. Three "home repo is special" behaviours fell; none was defended on its merits.

### Next

- **MERGE PR #71 before llm leaves `feature/resume-config-steps`.** The editable install resolves through llm's working tree, and `overlays/session-tracking/src/` does not exist on master — `git checkout master` would break `st-resume` in four consumer repos.
- **Verify the next `resume.sh` run** (see the reading-guide row) — this handoff writes regions that `st-resume` reads through the same register, so the first post-handoff resume is the real acceptance test for both.
- Then: **T-83** (freeze B-D1–B-D8, half a session; build + propagate, one session). **T-53** preflight is now mostly a working `--verify`. **T-81** `--mode ai` plan-then-apply. **T-54** re-scoped after T-83.
- LTG Phase 6 MCP server (L-01) continues in the sibling `latent-topic-graph` repo.

### Gotchas

- **`--mode ai` cannot be previewed.** `--dry-run` never calls the model — it only reports that it would. Two real attempts on llm's 12.4 KB CLAUDE.md: 9-minute timeout, then ~20 minutes and zero bytes. That is a `TIMEOUT`, not a verdict 0. Hand-merge per `APPLY.md` instead; a correct hand-merge makes `--dry-run` report `[SKIP] CLAUDE.md — already installed vN`, which is a stronger check than reading a plan.
- **`SKILL.md` installs via `user_files` = skip-if-present**, so a project-level copy shadows the global one and silently stops updating. llm's was three versions stale. Do not create one unless the repo genuinely needs a different skill.
- **`grep -c` prints `0` AND exits 1** when nothing matches, so `|| echo 0` prints a second zero. Bit the `run:` count step; `|| true` keeps grep's own count.
- **Three tests this session encoded the bug as the contract** (`test_11` asserting the non-discriminating `WARN`, `test_template_diff_gates_exit` asserting T-58's decision, and my own `_extract_next_section` expectation). Only the byte-identity diff and the locator contract caught them — both compare against something the implementation did not author.
- **The old bash footer hardcoded `ref:deferred-infra` in every repo**, including the three whose block is `ref:deferred`. It had been pointing at a nonexistent key.
- Three consumers were still running a **v8-era `handoff-harvest.sh`**; the v11 install finally delivered T-59. Residue of session 108's overclaimed "v9 synced cross-repo".
