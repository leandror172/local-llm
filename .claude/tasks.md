# Task Progress

**Last Updated:** 2026-06-04 (session 83)
**Active Layer:** Layer 5 — Expense Classifier
**Full history:** `.claude/archive/phases-0-6.md`, `.claude/archive/layer-0-findings.md`

---

## Session-Handoff Pipeline (Scope A) — ACTIVE (session 83)

Register-driven deterministic rewrite of the `session-handoff` skill. Design frozen session 83.
Spec: `docs/plans/session-handoff-pipeline-design.md` (`ref:handoff-pipeline-design`).
Deferred model layer: `docs/plans/session-handoff-placer-enhancement.md` (`ref:handoff-placer-enhancement`).
Branch: `feature/session-handoff-pipeline` (stacked on `feature/ltg-phase3-anchors`; rebase onto master before any PR).
Home: `overlays/session-tracking/` (propagate via overlay install).

**Task-ID convention (B1.2):** every open `- [ ]` task carries a unique `(T-NN)` id (document order) so the pipeline can check off by id. Existing short labels (`B1.2`, `M-P0a`, …) stay as human labels alongside; new tasks take the next free id.

**B1 — Register + task IDs** (milestone)
- [x] **B1.1** — author `overlays/session-tracking/registry.yaml` (10 roles, locators verified). DONE session 83, commit `b18aba9`.
- [x] (T-01) **B1.2** — add stable `(T-NNx)` task IDs to this file so checkoff is deterministic (flip `[ ]`→`[x]` by id). Normalize the bold-label tasks (`**3.5-B:**`, `**M-P0a:**`) with IDs. Lone new in-file element. DONE session 84 (commit `a1f985d`).

**B2 — Deterministic safety core** (milestone; TDD; local-first per `ref:local-model-conventions`) — DONE session 84 (31 tests green)
- [x] (T-02) **B2.1 F1 Locator** — for each register entry find its region (ref_block / structural / field / checklist) + mode + current interior; self-check "exactly one match → else abort + fall back". DONE session 84 (`e6d4615`, 15 tests).
- [x] (T-03) **B2.2 F3 Applier** — splice authored content per mode (replace / prepend / append / checkoff-by-id); must not touch bytes outside the region. DONE session 84 (`71979e6`, 8 tests).
- [x] (T-04) **B2.3 F4 Verifier** — hash everything outside register regions before/after; assert unchanged + locators still resolve + mode honored. Pass/fail gate (trust boundary). DONE session 84 (`f0c4822`, 8 tests).

**B3 — Orchestrator + per-run logging** (milestone)
- [ ] (T-05) **B3.1 F5 mechanics** — deterministic header-field bumps (Current Session / Current Layer, nomodel); next session-N derivation (reuse the `## 20` grep in `rotate-session-log.sh`); date; call `rotate-session-log.sh`.
- [ ] (T-06) **B3.2 F6 Orchestrator** — stage files → apply → verify-all → commit-or-rollback (`git checkout` on fail) → summary + uncommitted-git warning + idempotency guard.
- [ ] (T-07) **B3.3 Per-run logging** — `.claude/local/handoff-runs/<session-N+ts>/` with `input.md` (Claude's exact payload) + `report.md` (what was applied).

**B4 — SKILL.md rewrite** (milestone)
- [ ] (T-08) **B4.1 F7 schema** — the payload Claude emits: per-role authored blocks (Scope A = authored mode only; `intent` mode = deferred enhancement).
- [ ] (T-09) **B4.2 SKILL rewrite** — rewrite `.claude/skills/session-handoff/SKILL.md` to decide content, emit the F7 payload, invoke the pipeline as one Bash call — no file reads, no per-section Edits. Preserve pre-flight git/date context.

**B5 — Preflight precondition check** (FUTURE; surfaced session 85)
- [ ] (T-53) **B5.1 Preflight check** — a cheap pre-handoff check the skill (or a hook) runs BEFORE invoking the full pipeline, reporting unmet preconditions (e.g. dirty tracking files that would trip F6's clean-tree guard) so they're resolved up front instead of discovered via a failed F6 run → rework → re-call. Mechanism options: (a) skill instructions to run the check first; (b) a dedicated preflight tool/script returning the unmet conditions; (c) a hook fired when the skill is read that auto-injects the unmet-precondition context. Decide mechanism when building B4.2 (SKILL rewrite). Rationale: F6 aborts on dirty tracking files (decision session 85); failing inside the tool wastes a payload-assembly round-trip. **Plan:** `docs/plans/handoff-b5.1-preflight.md`.

**Open decisions to settle when relevant:** run-artifact placement (lean `.claude/local/handoff-runs/`); whether `report.md` also appends to committed `session-log.md`; whether `session-context.md` is in the first apply-cut or `tasks.md`+`session-log` only; whether `resume.sh` is refactored onto the shared register now or later (lean: later).

---

## Completed (summary)

- **Phases 0-6:** Infrastructure setup complete (Ollama, models, Docker, verification, docs)
- **Layer 0:** Foundation upgrades complete (12/12) — Qwen3 models, benchmarks, structured output, thinking mode strategy, decomposition, runtime validation, few-shot examples
- **Layer 1:** MCP Server complete (7/7 + MCP-1/2/3/4) — FastMCP server, 9 tools, persona-aware routing, system-wide availability
- **Layer 2:** Local-first CLI complete — Aider (primary) + OpenCode (comparison); decisions → `.claude/archive/decisions-layers-1-3.md`; findings → `docs/findings/layer2-tool-comparison.md`

---

## Layer 3: Persona Creator — COMPLETE

All tasks (3.1–3.6 + refactoring + 3.5-A) complete. Decisions → `.claude/archive/decisions-layers-1-3.md`. Full catalog → `personas/personas-reference.md`. Future candidates → `personas/ideas.md`.

- [ ] (T-10) **3.5-B:** Implement Option 3 multi-round conversation loop — deferred, not blocking Layer 4

<!-- ref:layer4-status -->
## Layer 4: Evaluator Framework — COMPLETE

Core tasks (4.1–4.4) + shell rubric + Java/Python validators + prompt decomposition all complete. Key design decisions → `docs/plans/2026-02-21-layer4-discussion-context.md`.

### Open stragglers
- [ ] (T-11) **4.x Phase 3 frontier judge:** Extension point designed in `docs/plans/2026-02-21-layer4-discussion-context.md` — Claude API call for subjective/ambiguous cases.
- [ ] (T-12) **4.6 Claude Desktop insights tool:** Standalone `tools/claude-desktop-insights.py` (split out from original Layer 4 scope).

---

<!-- /ref:layer4-status -->

<!-- ref:deferred-infra -->
## Deferred Infrastructure / Tooling

Completed items → `.claude/archive/deferred-completed.md`

- [x] **Re-probe 14B num_ctx after KV cache quant (q8_0):** DONE (session 76, 2026-05-30). All 4 models probed at 16K/24K/32K. Upgraded to 32768: qwen3:14b (1,051 MiB free), qwen2.5-coder:14b (2,790 MiB free), deepseek-r1:14b (2,783 MiB free). deepseek-coder-v2:16b → 24576 (32K tight at 574 MiB). 8 personas rebuilt. Script: `scripts/run-ctx-probe.sh`. Results: `retrieval/probes/ctx-probe-2026-05-30.md`.
- [ ] (T-13) **RECHECK num_ctx three-way divergence before Phase 2.5 corpus expansion:** Frozen Phase 1 spec + `sweep_extractors.py` = 16384 (validated operating point); production `config.yaml` extractors = 32768 (drifted from session 75/76 ctx-ceiling upgrades). Decision (c) session 81: keep both deliberately — harmless on the 8-file corpus (all fit in 16K). Trigger: when Phase 2.5 adds documents >16384 tokens, decide (a) align both to 32768 + re-run sweeps, or (b) drop production to 16384. See `retrieval/DECISIONS.md` ref:ltg-extractor num_ctx note.
- [ ] (T-14) **Hook-based auto-resume:** `UserPromptSubmit` hook injects `resume.sh` output on session start. Needs `.claude/local/session-started` flag to gate (fires every message, not just first).
- [ ] (T-15) **Qwen3-Coder-Next feasibility study (80B MoE, 3B active):** ~24GB at 3-bit quant. Needs VRAM headroom profiling + native Linux eval. Not priority until 30B models proven insufficient.
- [ ] (T-16) **expense-reporter config reader: replace runtime.Caller with os.Executable:** `internal/config/config.go` uses `runtime.Caller(0)` — breaks on deployment. Fix: `os.Executable()` + walk up. Low priority until binary deployed.
- [ ] (T-17) **Overlay wizard — interactive install inside an AI CLI:** Context: `docs/ideas/overlay-wizard.md`. Three steps: `/install-overlay` skill → wizard pattern generalization → portable TUI.
- [ ] (T-18) **Upgrade WSL2 Python from 3.10 to 3.12:** `uv python install 3.12` alongside 3.10. Do before writing new standalone Python scripts.
- [ ] (T-19) **`create-persona.py`: accept raw temperature values:** Currently named choices only. Should also accept numeric (e.g., `0.1`, `0.7`).
- [ ] (T-20) **Refactor `server.py` — separation of concerns:** Extract `_is_model_loaded`, `_check_busy_models`, `_evict_all`, `_load_model` helpers. Split into logical modules.
- [ ] (T-21) **File-based Ollama coordination layer (Option 2):** Watch Ollama PR #9392 first (`ACTIVE` field in `/api/ps`). Build trigger: VRAM thrash observed AND #9392 hasn't shipped. Design: `docs/ideas/ollama-coordination-layer.md`.
- [x] **ollama-metrics proxy — systemd unit:** Done 2026-05-30. `/etc/systemd/system/ollama-metrics.service`, `After=ollama.service`, auto-starts on boot.
- [ ] (T-22) **Prometheus+Grafana stack — systemd/docker unit:** `make stack` still manual. Consider `docker compose` systemd unit if monitoring proves long-term useful.
- [ ] (T-23) **Watch Ollama native `/metrics` PR #11159:** OTel-based endpoint (eval/prompt/load/total duration + token counts, per model label). 41+ commits, actively rebased since June 2025, not yet merged. When merged: port-swap proxy (Option A) becomes unnecessary — switch to native endpoint directly. PR: https://github.com/ollama/ollama/pull/11159
- [ ] (T-24) **Extract `create-persona.py` into importable library:** MCP tools currently shell out via subprocess. Extract to `personas/lib/persona_builder.py`.
- [ ] (T-25) **MCP server: hot-reload persona registry:** New personas invisible until restart. Add `reload_registry` tool or file-watcher.
- [x] **ollama-scaffolding overlay: repo-file-as-context guidance:** Include existing repo files as few-shot context. Add to overlay source for downstream repos. Done — D5 (caller inclusion) + D6 (few-shot-before-delete) added to `local-model-conventions.md`.
- [ ] (T-26) **Backfill SOLID + scope constraints to all coding personas:** Add 5 constraint lines (SOLID + "MUST NOT modify outside scope") to all coding Modelfiles not already updated. Detail + grep command: `docs/tasks/backfill-persona-constraints.md`.
- [ ] (T-27) **Per-language error-handling + logging conventions for persona system prompts:** Analysis session needed. Observations: local model consistently adds `logging.basicConfig()` (Python module-level side effect antipattern) + catch-log-reraise same type (noise, not handling). Rule varies by language — Python: `getLogger(__name__)` only, no catch-log-reraise; Java: no catch-log-rethrow same type; Go: `fmt.Errorf("context: %w", err)` instead of log-and-return. Action: audit all coding persona Modelfiles, add language-specific error-handling directives. Pair with backfill session above.
- [ ] (T-28) **ollama-scaffolding overlay — review for improvements:** Audit the overlay now that directives are consolidated. Candidate improvements: (1) re-sync directive content against the source feedback memories in the expense / web-research repos as they evolve — the overlay is a point-in-time snapshot and those memories drift; (2) add a ref-block integrity check for `local-model-conventions.md` (balanced `<!-- ref: -->` markers), reusing `ref-indexing`'s `check-ref-integrity.py`; (3) stamp the producing overlay version into the installed doc so downstream repos can tell which version they have (the `files:` mechanism is hash-based, with no version trace); (4) consider a standalone marked-file install mode if any overlay doc ever needs per-repo customization — `files:` currently overwrites wholesale.
- [ ] (T-29) **install-overlay: preserve line endings in the AI-merge path:** `handle_merge_sections`' deterministic v1→v2 update now preserves CRLF (`_read_text_eol`/`_write_text_eol` in `overlays/lib/actions.py`), but the AI-merge branch (`ai_merge` in `overlays/lib/planner.py`) still round-trips through `read_text`/`write_text` and will normalize a CRLF target to LF. Thread the EOL flag through `ai_merge` / `apply_plan`.
- [x] **`extract_topics.py` retrofit + `config.yaml` two-level upgrade:** DONE (sessions 78–81). 148 tests green, parity verified, close-out punch-list cleared (session 81). Branch `feature/ltg-extractor-retrofit`, PR open. Design was settled (session 77). Branch: `feature/ltg-extractor-retrofit`. Plan: `docs/plans/ltg-extractor-retrofit.md` (full spec + TDD guidance per task). Summary: `extract_topics.py` → 2-arm production runner; `sweep_extractors.py` new benchmark file; `routing.py` + `schemas.py` new leaf modules; `ModelClient` gains `extract_prose()`, `extract_code()`, `call()`, `_chat()`, `ChatResult`; `config.yaml` gets `models:` + `roles:` two-level shape with `timeout_s`, `options:` sub-dict, `think` top-level key. `retrieval/tests/test_routing.py` written (14 tests, confirmed red). Start at Task 1.
- [x] **MCP server — `refs` + `refs_root` params on `ask_ollama` + `generate_code` (TDD):** Completed session 63. 10 green tests. Live acceptance tested. Branch: `feature/ollama-bridge-refs-param`.
- [x] **MCP server — `output_file` + `output_only` params on `ask_ollama` + `generate_code` (TDD):** Completed session 64. 9 green tests. Live acceptance tested (basic write, relative path, output_only, edit loop). Branch: `feature/ollama-bridge-output-file`.
- [x] **MCP server — `patch_file` tool (TDD):** Completed session 65. 10 green tests (29 total). Atomic write via tmp+rename, uniqueness check, replace_all flag, UTF-8 round-trip. Also added `_strip_code_fences()` to `generate_code`. Branch: `feature/ollama-bridge-patch-file-impl`. PR #38 (base: feature/ollama-bridge-output-file).
- [x] **LTG Phase 2 — model_client.py + config.yaml:** Done session 71. 13 tests green.
- [x] **LTG Phase 2 — preflight.sh + run-preflight.sh:** Done session 71. 5/5 checks pass.
- [x] **LTG Phase 2 — embed.py + run-embed.sh:** Done session 71. 23 tests green. Sequential constraint header included.
- [x] **LTG Phase 2 — store.py + run-store.sh:** Done session 71. 11 tests green. 16-field schema, auto-backup, mode=overwrite.
- [x] **LTG Phase 2 — ltg_inspect.py + acceptance run + post-completion docs:** Tasks 7–9 complete session 72. 14/14 tests green. Acceptance 7/8 pass (R2 borderline), 2.3s. Renamed from inspect.py (stdlib shadow). See `ref:ltg-phase2-findings`.
- [x] **LTG Phase 2 — delegate test-writing to Ollama:** Applied session 72 — scaffold written manually, 14 test function bodies delegated to qwen3:14b (qwen2.5-coder:14b timed out 3×; escalation to tier 2 confirmed working).
- [ ] (T-30) **`embed_texts(role=)` → named wrapper cleanup:** `embed_texts(texts, role="embedding")` predates the named-methods pattern and has an established test surface in `test_inspect.py`. Future cleanup: add named `embed_query(texts)` wrapper delegating to `embed_texts(texts, role="embedding")`. Do not break existing test surface. Trigger: when adding a second embedding role (e.g., anchor embedding). Out of scope for extractor retrofit (session 77).
- [ ] (T-31) **`embed.py embed_batch_with_retry` → ModelClient unification:** `embed.py` has its own HTTP batch path (`embed_batch_with_retry`) that bypasses `ModelClient.embed_texts()`. Future cleanup: unify under `ModelClient` with retry logic moved inside or wrapped. Trigger: when a second embed.py-style pipeline consumer needs embedding. Out of scope for extractor retrofit (session 77).
- [ ] (T-32) **LTG Phase 3 — anchor integration (DECISIONS FROZEN session 82 — write `anchors.py` next):** All decisions frozen in `retrieval/DECISIONS.md` (`ref:ltg-phase3-decisions`). Full discussion: `docs/plans/ltg-phase3-decisions-discussion.md` (`ref:ltg-phase3-discussion`). Architecture: dual-path (alias-link, repo-wide anchors, `mechanical+key` descriptions, M:N `alias_of` JSON list, `confidence` 0.7 node-provenance not upgraded on alias, `node_kind` drops `merged`). Next: write `retrieval/anchors.py` TDD on branch `feature/ltg-phase3-anchors` (rebase onto master after retrofit PR merges). See `ref:ltg-phase3-decisions` for full spec.
- [ ] (T-33) **LTG Phase 6 gate — evaluate repo separation before implementing MCP tool:** Before writing `retrieve_context` / `relate_files` into ollama-bridge, decide whether `retrieval/` should become its own repo. By Phase 6 the schema is stable and the first cross-repo consumer exists — that's the right time. Separation cost: ~1 session (`git subtree split`, corpus-path parameterization, per-repo `.mcp.json`). Rationale: session 76 architectural note.
- [ ] (T-34) **LTG acceptance — recalibrate N-criteria threshold for 4096-dim:** Original `> 1.0` L2 threshold was calibrated for bge-m3 (1024-dim). After qwen3-embedding:8b upgrade, noise queries land at 0.84–0.98 (proportionally equivalent). Recalibrate based on observed score distribution once Phase 3 anchors join corpus. Update `acceptance_mode` in `ltg_inspect.py`.
- [ ] (T-35) **LTG Phase 2 — A/B: description-only vs description+spans embedding:** Deferred from session 61. Embed topic description only (current) vs description + concatenated span text. Measure recall difference on the 4 probe queries. Trigger: any probe query underperforms dense-only. See `ref:ltg-embedding` "sparse signal option".
- [ ] (T-36) **LTG Phase 2.5 — full corpus expansion:** After 8-file acceptance test passes, run `extract_topics.py` on full MVP corpus (`docs/research/`, `docs/ideas/`, `.claude/`, `.memories/`) with the frozen 2-arm routing, embed all output, populate index. Deferred from session 61.
- [ ] (T-37) **Subagent MCP server integration discoverability:** See `docs/findings/mcp-subagent-integration.md`. Short-term: `~/.claude/agents/ollama-worker.md` template.
- [ ] (T-38) **LTG Phase 1 — specialized-extractor routing study:** Add 3-5 more code files to corpus; test routing (coder on code, qwen3:14b on prose) vs single-model. See `ref:ltg-phase1-insights` + `ref:ltg-phase1-routing-hypothesis`.
- [ ] (T-39) **LTG Phase 1 — prompt iteration: topic-count floor + containment-only overlap:** (1) `max(5, major_section_count)` floor; (2) containment-only overlap (no crossed partial spans). See `ref:ltg-phase1-insights` findings #4 and #5.
- [ ] (T-40) **LTG Phase 1 — cross-reference-index 3rd-arm routing hypothesis:** Deferred from Branch C reconciliation. Re-evaluate when: determinism re-run on `smart-rag-index.md` × qwen3:14b, or corpus n≥3 cross-ref files, or MoE evaluated. See `ref:ltg-phase1-routing-hypothesis`.
- [ ] (T-41) **LTG Phase 1 — per-topic rubric JSON as Phase 2 input:** 648 per-topic scores in `ltg-rater-20260416-181839-20260430-215756Z.json`. Could disambiguate 3rd-arm hypothesis without new sweep.
- [x] **`retrieval/viz_sweep.py` — bash wrapper:** `run-extract-topics.sh` + `run-sweep-extractors.sh` added (session 80). `run-viz-sweep.sh` still pending (low priority, one-off tool).
- [ ] (T-42) **`ref-lookup.sh` — add `--paths` flag to emit source file paths alongside key names:** `--list` currently outputs key names only (verified session 82); `anchors.py` ingestion uses a raw repo grep instead. A `--paths` flag (or `--list-with-paths`) would make the script usable as the ingestion source directly and expose file paths for the `.claude/local/` safety filter. Before implementing, check `rtk find` output format — if rtk wraps find output differently, the path parsing may need to account for that.
- [ ] (T-43) **resume.sh — ref tag audit + structural fixes:** Add `ref:quick-pointers` (high priority) and `ref:active-decisions` (medium, now compact); add open-deferred count one-liner. Fix 3 bugs: `head -20` truncation on current-status, user-prefs flattened to unreadable single line, key list unreadable. Full plan: `docs/plans/resume-sh-ref-audit.md`.
- [ ] (T-54) **install-overlay: opt-in override for `manual_if_exists`:** Today `manual_if_exists` (e.g. session-tracking's `registry.yaml`) always flags-on-update and never overwrites — safe default, but there is no first-class way to push the canonical version through when a repo genuinely wants it. Add a `--force-manual` / `--overwrite-manual` flag (global or per-path), or a per-entry manifest hint; must back up (`do_backup`) before overwriting and stay idempotent. Lives in `overlays/lib/actions.py` `handle_manual_if_exists` + `install-overlay.py` arg parsing. Surfaced session 86 (handoff-pipeline dog-food, Option-C register delivery). **Plan:** `docs/plans/overlay-manual-if-exists-override.md`.
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
- [ ] (T-44) **M-watch — Long-context small model:** Watch for ≤15GB model with genuine 32K+ *synthesis* context (not just retrieval). Candidates: future Qwen3.5 long-context variant, or any model beating qwen3:8b on Fiction.liveBench at 128K+ while fitting 12GB VRAM.
- [ ] (T-45) **M-watch — MiMo-7B-RL (Xiaomi, MIT) — 7B reasoning upgrade candidate:** MATH-500 95.8%, AIME 2024 68.2% (vs deepseek-r1:7b 55.5% — meaningful gap at same size). MIT license, Ollama GGUF available, ~5GB Q4. Uses Multiple-Token Prediction (MTP) for speculative decoding at 90% acceptance rate — faster than standard 7B. **Trigger:** any task where deepseek-r1:14b is overkill on VRAM/speed — benchmark against deepseek-r1:7b first. Full analysis: `docs/findings/model-updates-2026-05.md` § "Reasoning / Code — MiMo-7B-RL".
- [ ] (T-46) **M-watch — Qwen3.6-27B (LTG Phase 3+ quality arm + vision capability):** Dense hybrid (Gated DeltaNet), Apache 2.0, AIME 2026 94.1%, SWE-bench 77.2%. Ollama: `qwen3.6:27b` (17GB Q4_K_M → 12GB VRAM + ~5GB RAM offload; ~5–10 tok/s). Also has vision encoder — first multimodal model in stack. **Coding variant inaccessible on RTX 3060** (NVFP4/MLX only; no 14B Qwen3.6 exists). 35B variant (`qwen3.6:35b`, 24GB, likely MoE A3B) — verify architecture before pulling. **Trigger:** Phase 3 corpus expansion — benchmark on 2-3 long extraction tasks vs qwen3:14b. Use as quality arm for offline batch runs if justified; too slow for interactive MCP. Full analysis: `docs/findings/model-updates-2026-05.md` § "Long-Context + High-Quality".
- [ ] (T-47) **M-watch — Long-context extraction arm (LTG Phase 3+ trigger):** Two candidates for corpus files >20K tokens without chunking — addresses LTG non-contiguous topic recognition on large docs. **Trigger:** Phase 3 corpus expansion adds long-document files — benchmark then, not before. (1) `mistral-nemo:12b` — Apache 2.0, 128K ctx, ~7.7GB Q4, MMLU 68%, `ollama pull mistral-nemo`. (2) Nemotron-Nano-8B (`nvidia/Llama-3.1-Nemotron-Nano-8B-v1`) — NVIDIA Open+Llama3.1 license (commercial OK), 128K ctx, ~5GB Q4, thinking mode on/off, MT-Bench 7.9; 21 GGUF quants on HF. Mistral-Nemo preferred on quality; Nemotron-Nano if VRAM is tighter. Full analysis: `docs/findings/model-updates-2026-05.md` § "Long-Context Extraction".
- [ ] (T-48) **M-update — models.yaml:** Add pulled models as they are verified locally. Deprecate `qwen2.5-coder:14b` only after M-P0a benchmark confirms replacement; deprecate `llama3.1:8b` (covered by qwen3:8b non-think). Verify each tag at `ollama.com/library/<tag>` before adding.
- [ ] (T-49) **M-P0a cleanup — Retire DeepCoder benchmark personas:** 6 personas registered with `status: benchmark` (my-go-deepcoder, my-go-deepcoder-vanilla, my-python-deepcoder, my-python-deepcoder-vanilla, my-mcp-deepcoder, my-mcp-deepcoder-vanilla). When no longer needed for reference: (a) `ollama rm` each, (b) archive or remove their Modelfiles, (c) set `status: archived` in registry.yaml, (d) optionally `ollama rm deepcoder:14b` to free 9GB VRAM. Defer until DeepCoder think-suppression is confirmed non-existent (no watch period needed) or a new experiment is planned.
- [ ] (T-50) **M-watch — DeepSeek R2 32B:** Watch for stable q2_K/q3_K Ollama tag (~11GB). Would upgrade reasoning ceiling. Check monthly.
- [ ] (T-51) **web-research: audit Anthropic vs local model routing — identify local substitution candidates:** Motivation: MiMo-7B-RL and qwen3:14b are capable enough to handle reasoning/extraction tasks currently routed to Claude, reducing Anthropic API spend. Action: (1) review Dispatcher routing in web-research repo — which agent roles call Claude vs Ollama MCP bridge; (2) for each Claude-routed role, assess if qwen3:14b (extraction/reasoning) or MiMo-7B-RL (math/code reasoning, ~5GB, MIT) could substitute at acceptable quality; (3) add explicit "local model" routing option or persona per role where viable. Track in web-research repo once audit is done. Likely covered by the `local-model-conventions.md` overlay already installed (session 60) — verify it's being used.
- [ ] (T-52) **M-watch — Claude-distilled Qwen3.5-9B:** Watch `Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2` for independent benchmarks. Do not pull until benchmarks confirm meaningful gain AND ToS situation clarifies.

---

## Layer 5: Expense Classifier — ACTIVE (expense-reporter repo)

All tasks 5.1–5.8 done as of 2026-05-29. 439 tests passing. Work tracked in `~/workspaces/expenses/code/`.
Note: MCP wrapper (5.8) ended up in expense-reporter's own `mcp-server/`, not this repo.
Deferred work (5.R1 TF-IDF, 5.R2 embeddings, RUI-3 apply, RUI-4 3-level path) tracked there.
Cross-repo status + implications → `.claude/adjacent-projects.md`
