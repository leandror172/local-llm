# Task Progress

**Last Updated:** 2026-02-27 (session 35)
**Active Layer:** Layer 5 — Expense Classifier
**Full history:** `.claude/archive/phases-0-6.md`, `.claude/archive/layer-0-findings.md`

---

## Completed (summary)

- **Phases 0-6:** Infrastructure setup complete (Ollama, models, Docker, verification, docs)
- **Layer 0:** Foundation upgrades complete (12/12) — Qwen3 models, benchmarks, structured output, thinking mode strategy, decomposition, runtime validation, few-shot examples
- **Layer 1:** MCP Server complete (7/7 + MCP-1/2/3/4) — FastMCP server, 9 tools, persona-aware routing, system-wide availability
- **Layer 2:** Local-first CLI complete — Aider (primary) + OpenCode (comparison); decisions → `.claude/archive/decisions-layers-1-3.md`; findings → `docs/findings/layer2-tool-comparison.md`

---

## Layer 3: Persona Creator — COMPLETE

All tasks (3.1–3.6 + refactoring + 3.5-A) complete. Decisions → `.claude/archive/decisions-layers-1-3.md`. Full catalog → `personas/personas-reference.md`. Future candidates → `personas/ideas.md`.

- [ ] **3.5-B:** Implement Option 3 multi-round conversation loop — deferred, not blocking Layer 4

<!-- ref:layer4-status -->
## Layer 4: Evaluator Framework — COMPLETE

Core tasks (4.1–4.4) + shell rubric + Java/Python validators + prompt decomposition all complete. Key design decisions → `docs/plans/2026-02-21-layer4-discussion-context.md`.

### Open stragglers
- [ ] **4.x Phase 3 frontier judge:** Extension point designed in `docs/plans/2026-02-21-layer4-discussion-context.md` — Claude API call for subjective/ambiguous cases.
- [ ] **4.6 Claude Desktop insights tool:** Standalone `tools/claude-desktop-insights.py` (split out from original Layer 4 scope).

---

<!-- /ref:layer4-status -->

<!-- ref:deferred-infra -->
## Deferred Infrastructure / Tooling

Completed items → `.claude/archive/deferred-completed.md`

- [x] **Re-probe 14B num_ctx after KV cache quant (q8_0):** DONE (session 76, 2026-05-30). All 4 models probed at 16K/24K/32K. Upgraded to 32768: qwen3:14b (1,051 MiB free), qwen2.5-coder:14b (2,790 MiB free), deepseek-r1:14b (2,783 MiB free). deepseek-coder-v2:16b → 24576 (32K tight at 574 MiB). 8 personas rebuilt. Script: `scripts/run-ctx-probe.sh`. Results: `retrieval/probes/ctx-probe-2026-05-30.md`.
- [ ] **Hook-based auto-resume:** `UserPromptSubmit` hook injects `resume.sh` output on session start. Needs `.claude/local/session-started` flag to gate (fires every message, not just first).
- [ ] **Qwen3-Coder-Next feasibility study (80B MoE, 3B active):** ~24GB at 3-bit quant. Needs VRAM headroom profiling + native Linux eval. Not priority until 30B models proven insufficient.
- [ ] **expense-reporter config reader: replace runtime.Caller with os.Executable:** `internal/config/config.go` uses `runtime.Caller(0)` — breaks on deployment. Fix: `os.Executable()` + walk up. Low priority until binary deployed.
- [ ] **Overlay wizard — interactive install inside an AI CLI:** Context: `docs/ideas/overlay-wizard.md`. Three steps: `/install-overlay` skill → wizard pattern generalization → portable TUI.
- [ ] **Upgrade WSL2 Python from 3.10 to 3.12:** `uv python install 3.12` alongside 3.10. Do before writing new standalone Python scripts.
- [ ] **`create-persona.py`: accept raw temperature values:** Currently named choices only. Should also accept numeric (e.g., `0.1`, `0.7`).
- [ ] **Refactor `server.py` — separation of concerns:** Extract `_is_model_loaded`, `_check_busy_models`, `_evict_all`, `_load_model` helpers. Split into logical modules.
- [ ] **File-based Ollama coordination layer (Option 2):** Watch Ollama PR #9392 first (`ACTIVE` field in `/api/ps`). Build trigger: VRAM thrash observed AND #9392 hasn't shipped. Design: `docs/ideas/ollama-coordination-layer.md`.
- [x] **ollama-metrics proxy — systemd unit:** Done 2026-05-30. `/etc/systemd/system/ollama-metrics.service`, `After=ollama.service`, auto-starts on boot.
- [ ] **Prometheus+Grafana stack — systemd/docker unit:** `make stack` still manual. Consider `docker compose` systemd unit if monitoring proves long-term useful.
- [ ] **Watch Ollama native `/metrics` PR #11159:** OTel-based endpoint (eval/prompt/load/total duration + token counts, per model label). 41+ commits, actively rebased since June 2025, not yet merged. When merged: port-swap proxy (Option A) becomes unnecessary — switch to native endpoint directly. PR: https://github.com/ollama/ollama/pull/11159
- [ ] **Extract `create-persona.py` into importable library:** MCP tools currently shell out via subprocess. Extract to `personas/lib/persona_builder.py`.
- [ ] **MCP server: hot-reload persona registry:** New personas invisible until restart. Add `reload_registry` tool or file-watcher.
- [x] **ollama-scaffolding overlay: repo-file-as-context guidance:** Include existing repo files as few-shot context. Add to overlay source for downstream repos. Done — D5 (caller inclusion) + D6 (few-shot-before-delete) added to `local-model-conventions.md`.
- [ ] **Backfill SOLID + scope constraints to all coding personas:** Add 5 constraint lines (SOLID + "MUST NOT modify outside scope") to all coding Modelfiles not already updated. Detail + grep command: `docs/tasks/backfill-persona-constraints.md`.
- [ ] **Per-language error-handling + logging conventions for persona system prompts:** Analysis session needed. Observations: local model consistently adds `logging.basicConfig()` (Python module-level side effect antipattern) + catch-log-reraise same type (noise, not handling). Rule varies by language — Python: `getLogger(__name__)` only, no catch-log-reraise; Java: no catch-log-rethrow same type; Go: `fmt.Errorf("context: %w", err)` instead of log-and-return. Action: audit all coding persona Modelfiles, add language-specific error-handling directives. Pair with backfill session above.
- [ ] **ollama-scaffolding overlay — review for improvements:** Audit the overlay now that directives are consolidated. Candidate improvements: (1) re-sync directive content against the source feedback memories in the expense / web-research repos as they evolve — the overlay is a point-in-time snapshot and those memories drift; (2) add a ref-block integrity check for `local-model-conventions.md` (balanced `<!-- ref: -->` markers), reusing `ref-indexing`'s `check-ref-integrity.py`; (3) stamp the producing overlay version into the installed doc so downstream repos can tell which version they have (the `files:` mechanism is hash-based, with no version trace); (4) consider a standalone marked-file install mode if any overlay doc ever needs per-repo customization — `files:` currently overwrites wholesale.
- [ ] **install-overlay: preserve line endings in the AI-merge path:** `handle_merge_sections`' deterministic v1→v2 update now preserves CRLF (`_read_text_eol`/`_write_text_eol` in `overlays/lib/actions.py`), but the AI-merge branch (`ai_merge` in `overlays/lib/planner.py`) still round-trips through `read_text`/`write_text` and will normalize a CRLF target to LF. Thread the EOL flag through `ai_merge` / `apply_plan`.
- [ ] **`extract_topics.py`: retrofit to `model_client.py`:** Replace inline `call_ollama()` + `DEFAULT_MODELS`/`MODEL_EXTRA_PARAMS` with `ModelClient` from `retrieval/model_client.py` (built in Phase 2). Thread through `run_single` / `run_sweep`. Upgrade before Phase 3+ integration. Design: `docs/ideas/ltg-model-registry-design.md`.
- [ ] **LTG `config.yaml`: upgrade to registered-models two-level design:** Upgrade `retrieval/config.yaml` from inline role configs to `models:` + `roles:` two-level dispatch. Trigger: ≥2 roles share same base model with different params, OR ≥3 roles total (expected at Phase 3 when extraction roles are added). Design: `docs/ideas/ltg-model-registry-design.md`.
- [x] **MCP server — `refs` + `refs_root` params on `ask_ollama` + `generate_code` (TDD):** Completed session 63. 10 green tests. Live acceptance tested. Branch: `feature/ollama-bridge-refs-param`.
- [x] **MCP server — `output_file` + `output_only` params on `ask_ollama` + `generate_code` (TDD):** Completed session 64. 9 green tests. Live acceptance tested (basic write, relative path, output_only, edit loop). Branch: `feature/ollama-bridge-output-file`.
- [x] **MCP server — `patch_file` tool (TDD):** Completed session 65. 10 green tests (29 total). Atomic write via tmp+rename, uniqueness check, replace_all flag, UTF-8 round-trip. Also added `_strip_code_fences()` to `generate_code`. Branch: `feature/ollama-bridge-patch-file-impl`. PR #38 (base: feature/ollama-bridge-output-file).
- [x] **LTG Phase 2 — model_client.py + config.yaml:** Done session 71. 13 tests green.
- [x] **LTG Phase 2 — preflight.sh + run-preflight.sh:** Done session 71. 5/5 checks pass.
- [x] **LTG Phase 2 — embed.py + run-embed.sh:** Done session 71. 23 tests green. Sequential constraint header included.
- [x] **LTG Phase 2 — store.py + run-store.sh:** Done session 71. 11 tests green. 16-field schema, auto-backup, mode=overwrite.
- [x] **LTG Phase 2 — ltg_inspect.py + acceptance run + post-completion docs:** Tasks 7–9 complete session 72. 14/14 tests green. Acceptance 7/8 pass (R2 borderline), 2.3s. Renamed from inspect.py (stdlib shadow). See `ref:ltg-phase2-findings`.
- [x] **LTG Phase 2 — delegate test-writing to Ollama:** Applied session 72 — scaffold written manually, 14 test function bodies delegated to qwen3:14b (qwen2.5-coder:14b timed out 3×; escalation to tier 2 confirmed working).
- [ ] **LTG Phase 6 gate — evaluate repo separation before implementing MCP tool:** Before writing `retrieve_context` / `relate_files` into ollama-bridge, decide whether `retrieval/` should become its own repo. By Phase 6 the schema is stable and the first cross-repo consumer exists — that's the right time. Separation cost: ~1 session (`git subtree split`, corpus-path parameterization, per-repo `.mcp.json`). Rationale: session 76 architectural note.
- [ ] **LTG acceptance — recalibrate N-criteria threshold for 4096-dim:** Original `> 1.0` L2 threshold was calibrated for bge-m3 (1024-dim). After qwen3-embedding:8b upgrade, noise queries land at 0.84–0.98 (proportionally equivalent). Recalibrate based on observed score distribution once Phase 3 anchors join corpus. Update `acceptance_mode` in `ltg_inspect.py`.
- [ ] **LTG Phase 2 — A/B: description-only vs description+spans embedding:** Deferred from session 61. Embed topic description only (current) vs description + concatenated span text. Measure recall difference on the 4 probe queries. Trigger: any probe query underperforms dense-only. See `ref:ltg-embedding` "sparse signal option".
- [ ] **LTG Phase 2.5 — full corpus expansion:** After 8-file acceptance test passes, run `extract_topics.py` on full MVP corpus (`docs/research/`, `docs/ideas/`, `.claude/`, `.memories/`) with the frozen 2-arm routing, embed all output, populate index. Deferred from session 61.
- [ ] **Subagent MCP server integration discoverability:** See `docs/findings/mcp-subagent-integration.md`. Short-term: `~/.claude/agents/ollama-worker.md` template.
- [ ] **LTG Phase 1 — specialized-extractor routing study:** Add 3-5 more code files to corpus; test routing (coder on code, qwen3:14b on prose) vs single-model. See `ref:ltg-phase1-insights` + `ref:ltg-phase1-routing-hypothesis`.
- [ ] **LTG Phase 1 — prompt iteration: topic-count floor + containment-only overlap:** (1) `max(5, major_section_count)` floor; (2) containment-only overlap (no crossed partial spans). See `ref:ltg-phase1-insights` findings #4 and #5.
- [ ] **LTG Phase 1 — cross-reference-index 3rd-arm routing hypothesis:** Deferred from Branch C reconciliation. Re-evaluate when: determinism re-run on `smart-rag-index.md` × qwen3:14b, or corpus n≥3 cross-ref files, or MoE evaluated. See `ref:ltg-phase1-routing-hypothesis`.
- [ ] **LTG Phase 1 — per-topic rubric JSON as Phase 2 input:** 648 per-topic scores in `ltg-rater-20260416-181839-20260430-215756Z.json`. Could disambiguate 3rd-arm hypothesis without new sweep.
- [ ] **`retrieval/viz_sweep.py` — bash wrapper:** Add `retrieval/run-viz-sweep.sh` + `retrieval/run-extract-topics.sh`. Low priority (one-off tools).
- [ ] **resume.sh — ref tag audit + structural fixes:** Add `ref:quick-pointers` (high priority) and `ref:active-decisions` (medium, now compact); add open-deferred count one-liner. Fix 3 bugs: `head -20` truncation on current-status, user-prefs flattened to unreadable single line, key list unreadable. Full plan: `docs/plans/resume-sh-ref-audit.md`.
<!-- /ref:deferred-infra -->

---

## Model Update Tasks (session 68, 2026-05-26)

Survey complete → `docs/findings/model-updates-2026-05.md`. Branch: `feature/model-survey-2026-05`.

- [x] **M-P0a — CLOSED: NO SWAP (2026-05-29).** `qwen3.6-coder:14b` does not exist on Ollama (tag was from unverified secondary sources). Benchmarked DeepCoder-14B as the strongest verified 14B coder alternative. Result: 5/6 DeepCoder runs timed out at 500s; no think-suppression mechanism exists; latency is unpredictable and intrinsic to R1-distill architecture. Quality on the one Python completion was verdict 2 (vs q25c14 verdict 1), but insufficient to justify 2× latency + 83% timeout rate. Full report: `benchmarks/results/deepcoder-benchmark-2026-05-28/report.md` (`ref:deepcoder-benchmark-decision`). **`qwen2.5-coder:14b` remains primary coder.** Watch: DeepCoder think-suppression or qwen3-coder 14B release.
- [x] **M-P0a followup — Fix `my-mcp-q25c14` + `my-mcp-q3` personas:** DONE (session 75). Added CANONICAL EXAMPLE block with correct `from mcp.server.fastmcp import FastMCP` import to both Modelfiles. Also backfilled SOLID constraints to `my-mcp-q3`. Both rebuilt and smoke-tested.
- [x] **M-P0b — Pull + VRAM probe + embedding upgrade:** COMPLETE (session 73). WARN verdict (load-time eviction only, zero query-time). Upgraded bge-m3 (1024-dim) → qwen3-embedding:8b (4096-dim). `embed.py`/`store.py` now config-driven. 61 tests green. Branch: `feature/ltg-embedding-upgrade-qwen3`. See `ref:ltg-m-p0b-probe`.
- [x] **M-P1a — CLOSED: NOT VIABLE (2026-05-29).** `llama4:scout` default tag is 67GB (q4_K_M of 109B MoE). Smallest quant anywhere is 33.8GB (unsloth UD-IQ1_S, 1.78-bit) — requires 24GB VRAM per Unsloth docs, double the available 12GB. MoE architecture does NOT reduce footprint (all 109B must be resident; only active params differ). Additionally, Scout's long-context *reasoning* quality is poor (15.6% on Fiction.liveBench at 128K); 10M context claim is retrieval-only, not synthesis. Wrong model for web-research/document-analysis use case. **Alternative: `OLLAMA_KV_CACHE_TYPE=q8_0` + raise `num_ctx` gives qwen3:8b 32–64K effective context at 5.2GB — already installed.** Watch: a ≤15GB model with genuine 32K+ synthesis context (not yet available).
- [x] **M-P1b — Pull tiny models:** DONE (session 75). `qwen3.5:0.8b` (1.0GB) + `qwen3.5:2b` (2.7GB) pulled. Add to `models.yaml` + benchmark for classifier co-residence pending.
- [x] **M-P2 — Pull phi4-mini:** DONE (session 75). `phi4-mini` (2.5GB) pulled. Add to `models.yaml` + benchmark vs `qwen3:4b-q8_0` for classification pending.
- [ ] **M-watch — Long-context small model:** Watch for ≤15GB model with genuine 32K+ *synthesis* context (not just retrieval). Candidates: future Qwen3.5 long-context variant, or any model beating qwen3:8b on Fiction.liveBench at 128K+ while fitting 12GB VRAM.
- [ ] **M-update — models.yaml:** Add pulled models as they are verified locally. Deprecate `qwen2.5-coder:14b` only after M-P0a benchmark confirms replacement; deprecate `llama3.1:8b` (covered by qwen3:8b non-think). Verify each tag at `ollama.com/library/<tag>` before adding.
- [ ] **M-P0a cleanup — Retire DeepCoder benchmark personas:** 6 personas registered with `status: benchmark` (my-go-deepcoder, my-go-deepcoder-vanilla, my-python-deepcoder, my-python-deepcoder-vanilla, my-mcp-deepcoder, my-mcp-deepcoder-vanilla). When no longer needed for reference: (a) `ollama rm` each, (b) archive or remove their Modelfiles, (c) set `status: archived` in registry.yaml, (d) optionally `ollama rm deepcoder:14b` to free 9GB VRAM. Defer until DeepCoder think-suppression is confirmed non-existent (no watch period needed) or a new experiment is planned.
- [ ] **M-watch — DeepSeek R2 32B:** Watch for stable q2_K/q3_K Ollama tag (~11GB). Would upgrade reasoning ceiling. Check monthly.
- [ ] **M-watch — Claude-distilled Qwen3.5-9B:** Watch `Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2` for independent benchmarks. Do not pull until benchmarks confirm meaningful gain AND ToS situation clarifies.

---

## Layer 5: Expense Classifier — ACTIVE (expense-reporter repo)

All tasks 5.1–5.8 done as of 2026-05-29. 439 tests passing. Work tracked in `~/workspaces/expenses/code/`.
Note: MCP wrapper (5.8) ended up in expense-reporter's own `mcp-server/`, not this repo.
Deferred work (5.R1 TF-IDF, 5.R2 embeddings, RUI-3 apply, RUI-4 3-level path) tracked there.
Cross-repo status + implications → `.claude/adjacent-projects.md`
