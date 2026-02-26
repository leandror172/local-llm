# Session Log

**Current Layer:** Layer 5 — Expense Classifier (pre-work complete)
**Current Session:** 2026-02-26 — Session 32: Layer 5 design + ollama-bridge logging + distillation plan
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`

---

## 2026-02-26 - Session 32: Layer 5 Design + Distillation Strategy

### Context
Layer 4 fully complete. Session focused on designing Layer 5 (expense classifier) and
the broader distillation/learning infrastructure. No code was written for expense-reporter
itself — session was architecture + pre-work.

### What Was Done
- **Layer 5 deep design:** Read all expense-reporter source (Go v2.1.0, 190+ tests) and
  all auto-category analysis artifacts (694-expense training set, algorithm spec, correction
  rules). Established domain boundary: classification logic in expense-reporter (product),
  MCP thin wrapper in llm repo (platform).
- **Distillation strategy designed:** Full plan for using Claude/local model interaction
  logs as training data. SFT from accepted responses, DPO from (Claude-improved, local-rejected)
  triples. DPO caveat documented: personal local use vs Anthropic ToS. Fine-tuning scope
  clarified: fixes mechanical patterns, can't raise 8B reasoning ceiling.
- **RAG with embeddings explained:** nomic-embed-text via Ollama, vector similarity retrieval,
  deferred to Layer 7 (not needed at current scale — 90% accuracy with keyword matching already).
- **Prompt pre-processor concept:** Local model compresses/enriches context before Claude calls.
  Added as Layer 7.10.
- **ollama-bridge JSONL logging (5.0a):** `config.py` (CALL_LOG_PATH, LOG_FULL_CONTENT env vars) +
  `client.py` (_log_call method). Appends JSON Lines to `~/.local/share/ollama-bridge/calls.jsonl`
  after every successful chat() call. Full content by default. Silent failure. Zero new dependencies.
- **CLAUDE.md updated (5.0b):** Layer 5+ local-model-first instruction. Try local for boilerplate,
  evaluate response (ACCEPTED/IMPROVED/REJECTED), record verdict. Creates distillation training data.
- **plan-v2.md updated:** Layer 5 fully redesigned (pre-work tasks, domain boundary note, 5.1–5.8).
  Layer 7 renamed + expanded (7.1–7.11 including SFT, DPO, QLoRA, prompt pre-processor).
- **tasks.md updated:** Layer 5 section with all pre-work done + 5.1–5.8 pending.
- **Vision docs created:** `docs/vision/expense-classifier-vision.md` (verbatim user scenario +
  5-phase iterative plan), `docs/vision/expense-classifier-data-inventory.md` (all artifact files,
  what to read for each phase).

### Next
- Begin Layer 5.1: port `feature_dictionary_enhanced.json` + `training_data_complete.json`
  into expense-reporter `data/` directory (read files first, understand format).
- Then 5.2: `classify` command in Go (Ollama HTTP client, structured output, feature dict context).
- Use local models for boilerplate during this work — logging is now active.

---

## 2026-02-25 - Session 31: Phase 1 Validators + Prompt Decomposition

### Context
Resumed from session 30. javac confirmed installed by user at session start — unblocked Java validator work.

### What Was Done
- **Python Phase 1 syntax validator:** `validate_python()` using built-in `compile()` (in-process, ~3ms/file, no subprocess, no temp files). `syntax_valid` criterion added to `code-python.yaml` (phase 1, weight 3.0). New scoring branch in `evaluate.py`. 5 test fixtures: `valid-complete.py`, `valid-snippet.py`, `invalid-syntax.py`, `invalid-indent.py`, `invalid-unclosed.py`. All pass/fail as expected.
- **Java Phase 1 compile validator:** `validate_java()` using `javac` subprocess with scaffolding (class-name→filename matching, bare-snippet wrapper). Two-pass `missing_dependency` classifier: Spring/Jakarta import failures → warnings (score 3), not errors (score 1). `compiles` criterion reused in `code-java.yaml` — no `evaluate.py` change needed. 5 test fixtures: `valid-standalone.java` (clean, score 5), `valid-spring-snippet.java` (missing-dep warnings, score 3), plus 3 invalid (syntax/type/undefined, score 1). Confirmed with javac 25.0.2.
- **sh-01/sh-02 decomposition:** Both prompts exceeded 8B ~400-token output budget at any timeout. Split into 4 focused sub-tasks: `01a-log-stats.md` (stats 1–5), `01b-log-histogram.md` (histogram only), `02a-backup-create.md` (mktemp+trap), `02b-backup-rotate.md` (keep-N rotation). Each targets ~150–250 tokens. Findings doc follow-up items marked complete.
- **Default timeout bump:** `benchmark.py` `DEFAULT_TIMEOUT` 300s → 600s (empirically required from session 29 data).
- **4 commits on `feature/phase1-code-validators`**, PR #8 opened and merged to master.
- **`.claude/index.md`** updated: validate-code.py description now lists all 4 languages.

### Decisions Made
- **Python uses `compile()` not `py_compile`:** Built-in compile() is cleaner — no .pyc side effects, catches all SyntaxError subclasses, in-process speed.
- **Java `missing_dependency` = warning not error:** Scopes Phase 1 to JDK syntax only; correct Spring Boot code scores 3 (not 1) when deps are absent from classpath.
- **`compiles` criterion reused for Java:** No evaluate.py change needed — the existing branch already handles the 5/3/1 scoring via error/warning counts.
- **Decomposed prompts keep `decomposed_from:` frontmatter field** linking back to original — preserves traceability without renaming the originals.

### Next
- **All Layer 4 deferred items complete.** Next: read `.claude/plan-v2.md` to identify Layer 5 scope and discuss first tasks.

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

