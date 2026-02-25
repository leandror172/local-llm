# Session Log

**Current Layer:** Layer 4 deferred — Java/Python Phase 1 validators next
**Current Session:** 2026-02-25 — Session 30: doc infrastructure, ref blocks, session tooling, context comparison
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`

---

## 2026-02-25 - Session 30: Doc Infrastructure + Context Comparison Experiment

### Context
Resumed from session 29 handoff. PRs #6 and #7 already merged to master. Session began with meta-work: auditing whether ref-lookup was being used, diagnosing session-log bloat, then building the infrastructure to fix both.

### What Was Done

**Ref lookup + session tooling (commit cf57a6e)**
- Extended `ref-lookup.sh` to scan all `*.md` project-wide (was `.claude/` only) + added `--list` flag (exits 0, MCP-friendly)
- Built `.claude/tools/resume.sh` — ~40-line session-start summary replacing reading 3+ files
- Built `.claude/tools/rotate-session-log.sh` — archives old entries, keeps last 3; ran immediately (1062 → 170 lines, 16 sessions archived to `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`)
- Built `.claude/tools/benchmark-status.sh` — rubrics/prompts/personas/results overview before benchmark sessions
- Added 5 new ref blocks (9 → 15 keys): `current-status`, `resume-steps`, `user-prefs`, `active-decisions` in session-context.md; `layer4-status`, `layer3-inventory`, `deferred-infra` in tasks.md; `indexing-convention` in index.md
- Added Documentation Rules to CLAUDE.md (hard requirements: new scripts → ref:bash-wrappers, new runtime docs → ref blocks, new files → index.md)
- Updated session-handoff skill: rotation step added before log entry
- Updated CLAUDE.md resume instruction to point to `resume.sh`

**MCP ref_lookup tool (commit cf57a6e)**
- Added `ref_lookup(key)` as 10th MCP tool in `server.py` — calls ref-lookup.sh via subprocess_exec (safe, same pattern as detect_persona). Enables Claude Desktop / non-CLI instances to query project knowledge by key.

**Context comparison experiment**
- Ran 3-way comparison (8B Ollama, 14B architect Ollama, Claude Sonnet subagents) with resume-only vs full-file context to measure information loss
- Key findings: (1) environment ground truth (`javac` not installed) beats all documentation; (2) full-file context better at mapping codebase changes (extend validate-code.py, not new file; reuse `compiles` branch); (3) resume-only loses codebase structure but recovers it by reading code; (4) jakarta.* gotcha in active-decisions but missed by both contexts — too buried
- Added `[ref:java-validator-design]` to tasks.md pre-implementation note with classpath decision, scaffolding strategy, 4-file change list, fixture convention

**Deferred items saved**
- Hook-based auto-resume and ref-integrity checker added to `[ref:deferred-infra]` in tasks.md

### Decisions Made
- **Session-log rotation:** rotate-session-log.sh called by session-handoff skill; keeps 3 most recent, archives rest
- **ref-lookup scope:** all `*.md` project-wide — ref blocks may live anywhere in the project, not just `.claude/`
- **Two-tier indexing confirmed:** `ref:KEY` for runtime lookups, `§ "Heading"` for navigation — documented in `[ref:indexing-convention]`
- **Documentation Rules (hard requirements):** new scripts → ref:bash-wrappers; new runtime docs → ref block; new files → index.md. Applies every session.
- **Java validator: Python first.** `py_compile` is unblocked (stdlib). Java needs `javac` installed + classpath design decision before coding.
- **Classpath strategy (decided):** scope Phase 1 to JDK-only syntax; classify Spring import failures as `missing_dependency` warnings, not errors.

### Next
- **Ask user to install javac:** `sudo apt-get install default-jdk-headless` (cannot run via Claude Code)
- **Python Phase 1 validator first** (unblocked): `validate_python()` in validate-code.py, `syntax_valid` criterion in code-python.yaml, case in evaluate.py, 5 fixtures in benchmarks/test-fixtures/python/
- **Java Phase 1 validator** (after javac confirmed): see `ref-lookup.sh java-validator-design` for full pre-implementation checklist
- **Default timeout bump:** 300s → 600s in `run-benchmark.sh`
- **sh-01/sh-02 decomposition** for 8B benchmarking

---

## 2026-02-24 - Session 29: Shell Rubric + shellcheck Phase 1 + Persona Hardening

### Context
Resumed from session 28 handoff. Plan approved (`~/.claude/plans/linear-growing-donut.md`), shellcheck confirmed installed (v0.8.0). Executed the plan, then ran three benchmark rounds, iterated on persona constraints, and restructured docs.

### What Was Done

**Task 4.x Shell rubric — COMPLETE (PR #7)**
- Created `evaluator/rubrics/code-shell.yaml` — 1 Phase 1 criterion (`shellcheck_clean`, w=3.0) + 5 Phase 2 criteria (correctness, best_practices, readability, completeness, edge_cases)
- Added `validate_shell()` to `benchmarks/lib/validate-code.py` — uses `shellcheck --format=json1`; error/warning severity → errors list, info/style → warnings list; `.sh` dispatch added
- Fixed `evaluator/lib/evaluate.py` — plan said "no changes needed" but the `else` branch returned `score: null`; added explicit `shellcheck_clean` case to `_score_from_validator_output()`
- Commit: `5be8e58`

**Three benchmark runs (2026-02-24)**
- T103037: first run, 300s timeout — 4/5 my-shell-q3 timeouts
- T123513: 600s timeout — all generations complete except sh-01 (both personas)
- T190133: 900s, prompts sh-01+sh-02 only — complementary timeouts (each persona completed one, timed on the other)
- Combined dataset: both personas averaged exactly 66.7% across 4 completed prompts each

**my-shell-q3 persona constraint hardening**
- Analysed shellcheck findings across all 10 benchmark outputs by SC code
- Added 6 new targeted constraints: `mapfile -t` array pattern, process substitution for loops, `find` over `ls`, direct exit-code checks (`if ! cmd`), single-quoted trap args, `${var:?}` rm guard, `local` scope rule
- Added global `MUST produce output that passes shellcheck with zero errors or warnings` as overarching intent
- Iterative smoke-testing (6 rounds): SC2207/SC2181/SC2012/SC2064/SC2168/SC2030 eliminated; residual SC2183/SC2154/SC1073 are logic errors — not fixable by constraints
- Commit: `574f915`

**Docs restructured**
- Created `docs/findings/` — canonical home for post-evaluation analysis
- Moved: `tests/layer2-comparison/findings.md` → `docs/findings/layer2-tool-comparison.md`
- Moved: `docs/model-comparison-hello-world.md` → `docs/findings/model-comparison-hello-world.md`
- Moved: `docs/plans/2026-02-24-shell-benchmark-findings.md` → `docs/findings/shell-benchmark-findings.md`
- `docs/plans/` now contains only pre-implementation design documents
- Updated 8 live references across index.md, session-context.md, tasks.md, closing-the-gap.md, vision-and-intent.md, generate-report.py
- Commits: `26a3905`, `4d73d8f`

**Prompt complexity finding documented and saved to memory**
- Expanded `docs/findings/shell-benchmark-findings.md` with generalizable principle: prompt complexity causes timeout + logic errors simultaneously — remedy is decomposition, not constraint tuning
- Empirical output budgets: 8B ~400 tokens, 14B ~800 tokens
- Added to `MEMORY.md` for cross-session recall
- Commit: `c92db7c`

### Decisions Made
- **Specialist hypothesis not confirmed at 8B scale:** both my-shell-q3 and my-coder-q3 averaged 66.7%; specialist wins on sh-04 (95.2% vs 68.6%) but tied overall
- **Constraint engineering scope:** MUST constraints fix mechanical patterns (SC codes), not logic errors (wrong printf args, unset vars, malformed regex). Logic errors require decomposition or larger model
- **sh-01/sh-02 are beyond 8B budget:** timeout at 300s/600s/900s — classified as 14B-tier prompts; should be decomposed or reserved for my-architect-q3
- **sed → Read tool reminder:** user caught use of `sed -n 'Xp'` for file reading; should always use Read tool with offset/limit instead
- **docs/findings/ structure:** `docs/plans/` for pre-implementation design only; `docs/findings/` for post-analysis. Both `tests/layer2-comparison/findings.md` and model-comparison doc moved accordingly

### Next
- Merge PR #7 (`feature/4x-shell-rubric` → `feature/layer4-evaluator-framework`) when ready
- **4.x Java/Python Phase 1 validators:** `javac` compile check for Java, `py_compile` for Python — next deferred evaluator task
- Increase default `--timeout` in `run-benchmark.sh` from 300s → 600s (per-domain defaults also worth considering)
- Trim or decompose `sh-01-log-analyzer` and `sh-02-backup-rotation` for 8B benchmarking

---

## 2026-02-23 - Session 28: Benchmark Runs + Evaluator Fixes

### Context
Layer 4 branch unmerged. Ran full benchmark suite (go, java, python, classification, shell) to validate the evaluator framework in practice. Two bugs surfaced and fixed.

### What Was Done

**Bug fix: evaluate.py — UnboundLocalError**
- `result` was only assigned inside the `try` block in `run_phase2()`; if `ollama_chat()` raised, the `if result is not None:` guard at line 362 hit `UnboundLocalError`
- Fix: initialize `result = None` before the `try` block
- Commit: `41a99ba`

**Bug fix: benchmark.py — invalid Markdown table separator**
- `generate_report()` was emitting `|-----------||---------|` (doubled `|`), producing broken report.md tables
- Fix: remove leading `|` from the repeated separator fragment
- Commit: `41a99ba`

**Feature: benchmark.py — `--resume RUN_ID` flag**
- Triggered by Go Phase 2 crash mid-run: all 30 raw generations were saved but 19 evals were missing
- Loads `raw/{slug}.json` to reconstruct `generation_results` without calling the model; loads `evals/{slug}-eval.json` to skip completed evaluations; runs only missing evals; rewrites `summary.json` + `report.md`
- Warmup skipped for fully-cached base_model groups and for judge when all evals present
- Commit: `41a99ba`

### Benchmark Results (5 domains, all run 2026-02-23)

| Domain | Winner | Avg% | Notes |
|--------|--------|------|-------|
| Java | my-java-q3 | 87.4% | +8.2% over coder; jakarta_namespace constraint paid off |
| Python | my-python-q3 | 88.2% | +0.2% over coder; specialist gap negligible |
| Classification | my-classifier-q3 | 100% | JSON schema (Phase 1) differentiates; coder 90.4% |
| Go | my-go-q3 | 78.7% | Timeout-heavy (6/10 for go-q3); 300s limit too tight |
| Shell | my-coder-q3 | 74.9% | Specialist loses due to timeouts + no shellcheck rubric |

### Key Findings
- **Specialist advantage strongest where hard constraints apply** (Java: jakarta.* namespace)
- **Timeout rate is the biggest data quality issue** — Go 14B (architect) hit 8/10 timeouts
- **`compiles` P1 gate score is consistently low** (~1.5-2.1/5 for Go) — most generated Go doesn't compile; what does compile always passes `go vet`
- **Classification Phase 1 (JSON schema) is doing real work** — my-coder-q3 failed json_valid for expense/sentiment
- **Shell results are misleading without shellcheck rubric** — `code-shell.yaml` task becomes priority

### Commits
- `41a99ba` fix: patch two benchmark bugs + add --resume flag to benchmark.py

### Next
- Plan + implement Task 4.x: `code-shell.yaml` rubric + shellcheck Phase 1 handler in evaluate.py

---

## 2026-02-23 - Session 27: Layer 4 — Evaluator Framework

### Context
Layers 0–3 and MCP-1/2/3/4 complete. Session began with architectural discussion (Opus), then switched to Sonnet for implementation. Key design constraints: (1) model flexibility — swappable later; (2) future "configurable pipeline" concept (declarative DAG). Chose Stance 3: Unix-style seams (standalone scripts with JSON I/O, model as parameter, no formal framework).

### What Was Done

**Task 4.1 — Rubrics (6 YAML files)**
- `evaluator/rubrics/code-go.yaml` — Phase 1: `compiles`(w=3.0) + `vet_clean`(w=1.0); Phase 2: correctness/idiomatic_go/readability/completeness
- `evaluator/rubrics/code-java.yaml` — Phase 2 only; targets jakarta.* (not javax.*), Spring constructor injection
- `evaluator/rubrics/code-python.yaml` — Phase 2 only; type hints, pythonic style
- `evaluator/rubrics/code-general.yaml` — Language-agnostic fallback
- `evaluator/rubrics/classification.yaml` — Phase 1: json_valid + confidence_range; Phase 2: category_correctness(w=4.0), calibration, reasoning
- `evaluator/rubrics/writing.yaml` — Phase 2 only: accuracy/clarity/structure/conciseness/completeness

**Task 4.2 — evaluate.py (~280 lines)**
- `evaluator/lib/evaluate.py` — Core scoring engine. Phase 1: subprocess to validate-code.py. Phase 2: one LLM call/criterion with `format_schema`, `temperature=0.1`, `think=False`
- `evaluator/run-evaluate.sh` — Whitelist-safe wrapper

**Task 4.3 — benchmark.py (~320 lines)**
- `evaluator/lib/benchmark.py` — Persona×prompt matrix orchestrator. Groups by `base_model` to minimize VRAM reloads. Defers Phase 2 judging until all generation complete
- `evaluator/run-benchmark.sh` — Whitelist-safe wrapper
- **Bugfix:** `ImportError: cannot import name 'ConnectionError' from 'ollama_client'` — fixed by using stdlib `ConnectionError = ConnectionError` instead of named import

**Task 4.4 — Prompt sets (40 files)**
- `evaluator/prompts/go/` — 10 prompts (easy×3, medium×4, hard×3): http-handler through event-bus
- `evaluator/prompts/java/` — 10 prompts: Spring Boot 3.x/jakarta.*, targeting known failure modes
- `evaluator/prompts/python/` — 10 prompts: FastAPI, asyncio, SQLAlchemy 2.0, type hints
- `evaluator/prompts/classification/` — 5 prompts: expense, sentiment, bug severity, language, topic
- `evaluator/prompts/shell/` — 5 prompts: log analyzer, backup, health check, git hook, deploy

**Documentation**
- `evaluator/README.md` — 213 lines: quick start, rubric format, prompt format, VRAM strategy, options reference, extension guide
- `docs/plans/2026-02-21-layer4-discussion-context.md` — Architectural discussion context preserved
- `docs/plans/2026-02-21-layer4-evaluator-framework.md` — Copy of approved plan

### Commits
- `4f074bf` feat: Layer 4 — Evaluator Framework (Tasks 4.1–4.4) [53 files, 2980 insertions]
- `e45169a` docs: add README.md for evaluator framework

### Decisions Made
- **Stance 3 (Unix seams):** No formal pipeline class — every component is a standalone script. Future DAG composes them via JSON I/O
- **VRAM grouping:** `group_by_base_model()` reads registry; my-go-q3 and my-java-q3 both use qwen3:8b so switching is free
- **Deferred Phase 2:** All generation runs first, then judge model loads once for entire batch — avoids ping-ponging
- **One criterion per LLM call:** 7-8B models more reliable at focused yes/no rubric evaluation than multi-criterion prompts
- **Rubrics as data:** Adding a domain requires only a new YAML + prompt directory, no Python changes
- **Task 4.6 deferred:** Claude Desktop insights → standalone `tools/claude-desktop-insights.py` (not part of Layer 4)

### Pending / Deferred
- PR creation + merge feature/layer4-evaluator-framework → master
- Live validation run (2 prompts × 1 persona as smoke test)
- Layer 5: Expense Classifier (next major layer per plan-v2.md)
- `tools/claude-desktop-insights.py` (Task 4.6 split out)
- Phase 3 frontier judge extension point (design documented in discussion-context.md)
- Java/Python Phase 1 validators (javac, py_compile) — deferred

---

