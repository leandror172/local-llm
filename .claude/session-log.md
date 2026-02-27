# Session Log

**Current Layer:** Layer 5 — Expense Classifier (pre-work complete, ready to build)
**Current Session:** 2026-02-26 — Session 34: Model audit, new model pulls, comparison tooling
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`

---

## 2026-02-26 - Session 34: Model Audit, New Pulls, Multi-Model Comparison Tooling

### Context
Pre-Layer 5 model audit. User had explored LM Studio (WSL version causes BSoD; Windows app is fine),
discovered VRAM+RAM hybrid loading. Session focused on researching new models, pulling them, building
multi-model comparison tooling, and establishing qwen2.5-coder:14b as preferred codegen model for Layer 5.

### What Was Done
- **Model audit:** Researched 2026 model landscape. Found Qwen3.5 (released 2026-02-17/24), Qwen3-Coder:30b,
  Qwen3:30b-a3b. Updated CLAUDE.md and index.md model selection tables with current + future candidates.
- **Pulled 3 new base models:**
  - `qwen2.5-coder:14b` (9.0GB Q4_K_M) — fits in VRAM, code-specialized
  - `qwen3:8b-q8_0` (8.9GB Q8) — same model, higher quantization fidelity
  - `qwen3:30b-a3b` (19GB Q4_K_M MoE) — 30B total / 3B activated, hybrid VRAM+RAM
- **Re-pulled `qwen3:8b`** — already current (manifest-only download)
- **Created 3 Modelfiles + personas:**
  - `my-go-q25c14` (`go-qwen25c14.Modelfile` → `qwen2.5-coder:14b`) — comparison partner
  - `my-go-q3-q8` (`go-qwen3-q8.Modelfile` → `qwen3:8b-q8_0`) — quantization comparison
  - `my-go-q3-30b` (`go-qwen3-30b.Modelfile` → `qwen3:30b-a3b`, num_ctx=8192) — quality ceiling
- **Updated registry files:**
  - `personas/registry.yaml` — new "comparison personas" section + future model notes (qwen3.5:35b-a3b, qwen3-coder:30b) as YAML comments
  - `personas/models.py` — added code-14b, code-30b, code-q8 entries; new MODEL_TAG_TO_SUFFIX/Q_SUFFIX entries
- **Built multi-model comparison tooling:**
  - `benchmarks/lib/compare-models.py` + `run-compare-models.sh` — same prompt → N models → side-by-side output → verdict → JSONL
  - `benchmarks/lib/record-verdicts.py` + `run-record-verdicts.sh` — post-hoc verdict collection for non-interactive runs; `--list`/`--entry N` flags
  - `personas/lib/ollama_client.py` — added `keep_alive` param (set to `"0"` in comparison calls to evict models between runs)
- **Ran 3 comparison tests** (cold, warm, 4-model with eviction); results in `benchmarks/results/compare-runs.jsonl`
- **Recorded verdicts for 4-model run:**
  - `my-go-q3` → REJECTED (timed out at 600s — Qwen3 thinking spiral)
  - `my-go-q3-q8` → IMPROVED (correct, but missing json tags/field comments)
  - `my-go-q25c14` → ACCEPTED (best: json tags, file header, idiomatic `errors.New`, field comments)
  - `my-go-q3-30b` → REJECTED (dropped `id` field from constructor — silent logic error)

### Decisions Made
- **`my-go-q25c14` (qwen2.5-coder:14b) is preferred for Go codegen in Layer 5** — best output quality; ~32s is acceptable given zero token cost
- **Speed philosophy confirmed:** "Some speed loss acceptable for correctness and free local tokens" — user's explicit view
- **qwen3:30b-a3b underperforms on focused tasks** — larger model doesn't mean better; 14B code-specialized beats 30B general on constructor generation
- **Future model watch list in registry.yaml:** qwen3.5:35b-a3b (too new + tight memory), qwen3-coder:30b (same size as 30b-a3b, pull after 30b-a3b validated)
- **Model duplication noted:** Models listed in CLAUDE.md, index.md, registry.yaml, models.py — user flagged for future consolidation

### Open / Unresolved (must fix before Layer 5)
- **`think: false` via `options{}` not working** — qwen3:8b timed out at 600s on trivial prompt (thinking spiral). Token counts 1960-1995 for 25-line output confirm massive hidden thinking. May need `think` at top level of payload, not inside `options`. **Fix this first next session.**
- **`num_ctx=16384` in `go-qwen25c14.Modelfile` causes KV cache overflow** — 14B at 16K ctx needs ~15GB (9GB weights + 6GB KV cache), overflows 12GB VRAM. Reduce to 8192 (cuts KV cache to ~3GB → better speed consistency).

### Next
- Fix `think: false` placement in `ollama_client.py` (top-level vs `options{}`) — test both, verify token counts drop
- Reduce `num_ctx` in `go-qwen25c14.Modelfile` from 16384 → 8192
- **Then start Layer 5:** task 5.1 (port training data), 5.2 (`classify` command in Go)
- For Layer 5 classification model: benchmark `my-go-q25c14` (qwen2.5-coder:14b) vs `my-classifier-q3` (qwen3:8b) on expense inputs

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

