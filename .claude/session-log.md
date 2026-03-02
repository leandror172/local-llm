# Session Log

**Current Layer:** Layer 5 — Expense Classifier (scaffolding complete, ready for 5.1)
**Current Session:** 2026-02-27 — Session 36: Portable scaffolding + expense repo bootstrap
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`

---

## 2026-02-27 - Session 36: Portable Scaffolding + Expense Repo Bootstrap

### Context
Resumed from session 35 (all Layer 5 blockers resolved). Before starting 5.1, implemented the
two-repo workflow plan: make this repo's `.claude/` scaffolding portable, then bootstrap the
expense-reporter repo with it as the first consumer. Full plan executed across both repos.

### What Was Done

**Phase 1 — LLM repo (branch: `feature/portable-scaffolding`, commit: `cab902c`):**
- `resume.sh`: replaced hardcoded key hints with dynamic `ref-lookup.sh list` discovery.
  Any new `<!-- ref:KEY -->` block auto-appears with zero maintenance.
- `docs/scaffolding-template.md`: created reusable 10-step bootstrap guide describing directory
  structure, file purposes, ref:KEY two-tier convention, session log format, tool dependencies.
- `~/.claude/.mcp.json`: global MCP config — ollama-bridge now available in every Claude Code
  project, not just this repo. LLM repo `.mcp.json` kept as harmless redundancy.
- `tasks.md`: added two-repo workflow note under Layer 5 header.
- `session-context.md`: updated `current-status` ref block for session 36.

**Phase 2 — Expense repo scaffolding (branch: `feature/claude-code-scaffolding`, commit: `7c49e75`):**
- `.claude/tools/`: copied resume.sh, ref-lookup.sh, rotate-session-log.sh (fully portable).
- `.claude/skills/session-handoff/SKILL.md`: copied session-handoff skill.
- `CLAUDE.md`: project identity, Go structure, workflow rules, local model rules (try-local-first),
  domain facts (BR date/decimal format), resume guide.
- `.claude/index.md`: knowledge index with ref:go-structure, ref:testing, ref:classification,
  ref:indexing-convention blocks; classification data table, archive table, tools table.
- `.claude/session-context.md`: ref blocks for user-prefs, current-status, resume-steps,
  active-decisions (domain boundary, classification strategy, Go conventions).
- `.claude/session-log.md`: Session 1 entry with pre-history summary (Phases 1–11, 190+ tests).
- `.claude/tasks.md`: Layer 5 tasks 5.1–5.8 verbatim from plan-v2.md + pre-work status.
- Verified: `resume.sh` in expense repo finds 7 ref keys dynamically, zero config required.

**Phase 3 — Expense repo data & doc migration (same branch, commit: `ed055a1`):**
- `data/classification/`: 8 algorithm docs copied from `~/workspaces/expenses/auto-category/`
  (tracked); 15 personal data JSONs/CSVs also copied (gitignored).
- `docs/archive/`: 21 Desktop-era planning docs moved via git rename (history preserved).
- `docs/archive/transients/`: 12 root transient files moved (gitignored subfolder, per user).
- `.claude/settings.local.json`: backed up Windows Git Bash permissions to `.claude/local/`;
  replaced with WSL2-appropriate permissions (go test/build/run/vet, resume.sh, ref-lookup.sh).
- `.gitignore`: added `data/classification/*.json|csv`, `.claude/local/`, `docs/archive/transients/`.
- Verified: `git add -n data/classification/` confirms only 8 docs staged (no personal data).
- Verified: `cd expense-reporter && go test ./...` — all 190+ tests still passing.

### Decisions Made
- **Two-repo workflow is now live:** Feature work (5.1–5.7) in expense repo; MCP wrapper (5.8) in this repo.
- **Global MCP config pattern:** `~/.claude/.mcp.json` is the right place for tools needed in all projects; project-level `.mcp.json` kept for project-specific overrides.
- **Transient files → gitignored subfolder:** `docs/archive/transients/` pattern — move one-time scripts/reports there instead of tracking them or deleting them.
- **`confusion_analysis.json` gitignored** — user couldn't confirm whether it contains real expense descriptions; safe default.
- **`~/workspaces/expenses/auto-category/` left in place** — `data/classification/` is a copy, not a move.

### Next
- **Layer 5.1 (expense repo):** Verify `feature_dictionary_enhanced.json` + `training_data_complete.json`
  are in `data/classification/`; document their JSON schema in `.claude/index.md`
- **Layer 5.2 (expense repo):** `classify` command — 3-field input → Ollama HTTP → structured JSON → top-N subcategories
- **PRs to merge:** `feature/portable-scaffolding` (LLM repo) + `feature/claude-code-scaffolding` (expense repo)

---

## 2026-02-27 - Session 35: Fix Layer 5 Blockers + Java Workspace Setup

### Context
Resumed from session 34. Two blocking issues identified before Layer 5 could begin:
`think: false` not suppressing Qwen3 thinking (options{} placement), and `num_ctx=16384`
causing KV cache overflow on 12GB card. Also prepared a separate Spring Boot exercise workspace.

### What Was Done
- **Fixed `think: false` placement (5.0e):** Moved from `options{}` to top-level payload in both
  `personas/lib/ollama_client.py` and `mcp-server/src/ollama_mcp/client.py`. Verified with
  before/after tests: 701→124 tokens (82% reduction), 16.7s→2.6s (6.4x speedup), chars/token
  ratio normalized from 1.51→3.65 (matches Qwen2.5 baseline ~3.5). Root cause confirmed via
  Ollama docs: `think` is a top-level API parameter, silently ignored inside `options{}`.
- **Reduced `num_ctx` to 10240 (5.0f):** Changed `go-qwen25c14.Modelfile` from 16384→10240.
  User chose 10240 over 8192 for more context headroom. Confirmed: `num_ctx` does NOT require
  powers of 2 (arbitrary integers accepted). Rebuilt persona, tested successfully (no OOM).
- **Created `my-java-q25c14` persona:** New `modelfiles/java-qwen25c14.Modelfile` (qwen2.5-coder:14b,
  num_ctx=10240, Java 21 + Spring Boot 3.x constraints). Registered in `registry.yaml` and `index.md`.
  Smoke-tested: clean Spring Boot controller with jakarta.*, constructor injection, records.
- **Set up todaytix-test workspace:** `/home/leandror/workspaces/todaytix-test/` with git init,
  `.mcp.json` (ollama-bridge), and `CLAUDE.md` (local LLM usage instructions, Spring Boot conventions,
  mandatory review checklist for local model output).
- **Strengthened local model review instruction:** CLAUDE.md includes HARD REQUIREMENT for Claude
  to review model output (compile check, conventions check, correctness check) and state explicit
  ACCEPTED/IMPROVED/REJECTED verdict before writing to files.

### Decisions Made
- **`num_ctx` can be any integer** — not restricted to powers of 2. Chose 10240 (10K) as balance
  between context capacity and VRAM pressure on 12GB card.
- **Java persona on 14B only** — user chose `my-java-q25c14` (qwen2.5-coder:14b) over `my-java-q3`
  (qwen3:8b) for the exercise. Quality over speed for a learning exercise.
- **Local model output review is a HARD REQUIREMENT** — strengthened from passive "evaluate explicitly"
  to mandatory checklist + verdict before writing files. Better instruction-following behavior.
- **MCP bridge had same `think` bug** — fixed in both `personas/lib/ollama_client.py` (scripts) and
  `mcp-server/src/ollama_mcp/client.py` (MCP server). All Ollama callers now correct.

### Next
- **Layer 5.1:** Port training data into expense-reporter (all blockers now resolved)
- **todaytix-test:** User will open Claude Code in that folder for Spring Boot exercise (independent work)

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

