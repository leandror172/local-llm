# Session Log

**Current Layer:** Layer 5 — Expense Classifier (design complete, ready to build)
**Current Session:** 2026-02-26 — Session 33: Layer 5 deep design + vision documentation
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`

---

## 2026-02-26 - Session 33: Layer 5 Deep Design + Vision Docs

### Context
Forked from Session 32 (rewound before distillation/Layer 7 discussion). Full read of existing external
artifacts (expense-reporter Go source + auto-category analysis) to properly scope Layer 5 before writing
any code. **Note:** Session 32 entry below covers the rest of the original conversation — ollama-bridge
logging (5.0a), CLAUDE.md local-model-first (5.0b), Layer 7 distillation expansion, and `docs/findings/LoRA.md`.

### What Was Done
- **Read all expense-reporter source:** Go v2.1.0, 190+ tests, Cobra CLI, excelize, hierarchical
  subcategory resolver, batch processor, installment expansion. Understood full architecture.
- **Read auto-category analysis artifacts:** FINAL_SUMMARY, classification_algorithm, classification_reasoning,
  algorithm_parameters, research_insights (partial). 694 training expenses, 90% HIGH confidence,
  229 keywords, 68 subcategories, correction rules (DME, Unimed, Layla, Anita, Algar).
- **Domain boundary finalized:** Classification logic → expense-reporter (product feature, LLM is impl detail).
  LLM repo → scaffolding/patterns for LLM-assisted dev, thin MCP wrapper only.
- **Long-term Telegram vision captured:** Full scenario (expense in chat → classify → inline keyboard
  → confirm → insert → reply) + queue behavior (oldest-first, offline backlog) documented verbatim.
- **Vision documents created:**
  - `docs/vision/expense-classifier-vision.md` — full scenario + 5-phase iterative plan
  - `docs/vision/expense-classifier-data-inventory.md` — file-by-file inventory of all external artifacts
  - `.claude/index.md` — both new docs indexed
- **RAG with embeddings explained:** keyword matching (Phase 1) vs embedding-based retrieval (Phase 5);
  Ollama `/api/embed` endpoint; deferred because 10% hard cases aren't fixable by better retrieval.
- **Expense persistence designed:** sha256[:12] of normalize(item+date+value) as ID, JSON Lines log,
  status lifecycle (pending→classifying→classified→confirmed→inserting→inserted), storage evolution
  (JSONL → SQLite → Redis). Added to vision doc.

### Decisions Made
- **Classification in expense-reporter** (not llm repo): subcategory is the interface; expense-reporter
  is product, LLM is impl detail hidden inside it
- **llm repo role:** Platform scaffolding — how to call Ollama from Go/Python tools (patterns, prompts,
  structured output schemas) reusable for future tools
- **Training data strategy confirmed:** Hybrid — feature dict + correction rules as system context,
  top-K keyword-matched examples as per-request few-shot
- **Hash ID:** sha256[:12] of normalized item+date+value (subcategory excluded; determined by pipeline)
- **Start with JSONL log** on successful insert; upgrade to SQLite when Telegram queue behavior needed

### Next
- Start Layer 5 implementation: read `feature_dictionary_enhanced.json` + `training_data_complete.json`
  to understand format, then port into expense-reporter `data/` directory (task 5.1)
- Build `classify` command in expense-reporter (task 5.2): Go HTTP call to Ollama, structured output
- Benchmark Qwen3-8B (`my-classifier-q3`) vs Qwen2.5-Coder-7B on sample expense classification

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

