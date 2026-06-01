# Session Log

**Current Layer:** LTG Phase 3 — Anchor Integration (prereq: extractor retrofit complete ✓)
**Current Session:** 2026-06-01 — Session 81: retrofit close-out + LTG Phase 3 anchor discovery (in progress)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-25-to-2026-05-25.md`, `.claude/archive/session-log-2026-05-26-to-2026-05-26.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-28-to-2026-05-28.md`, `.claude/archive/session-log-2026-05-29-to-2026-05-29.md`, `.claude/archive/session-log-2026-05-29-to-2026-05-29.md`

---

## 2026-06-01 - Session 81: Retrofit close-out + LTG Phase 3 anchor discovery

### Context
Resumed post-session-80 to open the retrofit PR and start LTG Phase 3. Entry point: read all Phase 3 prep docs (concept paper, full plan, DECISIONS) + the session-80 advisor review.

### What Was Done
- **Retrofit close-out (sonnet sub-agent):** cleared the advisor punch-list. Live-ran the sweep once (`status=ok`, non-zero tokens — Gap A closed); fixed stale `bge-m3` refs in `embed.py` + documented Invariant D (Gap B/D); added `test_config_yaml_contract` regression test. **148 tests** (was 147), independently re-verified. Commits `1572b39`, `2dc49b2`. Retrofit PR was already open; pushed.
- **num_ctx three-way finding:** frozen spec + sweep = 16384 (validated point); production `config.yaml` drifted to 32768 (session 75/76 ctx upgrades). **Decision (c):** keep both deliberately; RECHECK before Phase 2.5. Recorded in `sweep_extractors.py`, `DECISIONS.md`, `tasks.md`. Commit `d17f446`.
- **Workflows guide:** wrote `.claude/workflows-feature-guide.md` (+ index entry) — dynamic workflows = script-orchestrated subagents at scale, NOT a session tracker; when-to-use; repo candidates (Phase 3 design, persona backfill, model surveys). Commit `ce885df`.
- **LTG Phase 3 DISCOVERY (not frozen):** new branch `feature/ltg-phase3-anchors`. Full discovery doc `docs/plans/ltg-phase3-anchor-discovery.md`. Reframes: (1) configurable per-class **weights** generalize anchor stratification; (2) three-confidence concepts (retrieval weight / node provenance / edge confidence); (3) `node_kind` vs `source_class` as separate axes, taxonomy as a config projection of `(file_path, node_kind)`; (4) **dual-path RAG** — `ref:KEY` anchors as a *parallel* retrieval surface (span-topics / ref-keys / both), pushing merge toward an **alias-link** model; (5) empirical enumeration: only 2 of 138 ref keys live in the 8 extracted files (orphans carry no merge-noise). Advisor reviewed (D2 pushback to A + surfaced D5/D6). Commits `76cdc4a`, `6638320`.

### Decisions Made
- **num_ctx (c):** keep benchmark 16384 / production 32768 divergent; recheck at Phase 2.5.
- **Advisor permission rule:** ask before `advisor()` in the main session (context-dup bug); subagents may call freely. Saved to memory.
- **Phase 3 settled:** D1=C (capture fields, defer weight tuning), D3=C-heuristic (embed description not raw block), D4=yes (extend schema while re-index is ~3s).
- **Phase 3 OPEN (next session):** D2 (anchor scope — user leans B, advisor+empirical lean A), D5 (merge representation/multiplicity — lean alias-link, many-topics:one-anchor), D6 (acceptance retarget to 2 in-corpus refs), D7 (path-selection binding time — query vs build, lean query). Nothing frozen — user had not finished analysing §4 empirical finding.

### Next
- **Resume LTG Phase 3 discussion from `docs/plans/ltg-phase3-anchor-discovery.md` §4 onward.** Work through the empirical enumeration, confirm/decide D2/D5/D6/D7 (+ re-confirm D1/D3/D4 under the dual-path reframe), then freeze into a `ref:ltg-phase3-decisions` block in `DECISIONS.md`. Only then write `anchors.py` (TDD) in a later session.
- Retrofit PR (`feature/ltg-extractor-retrofit` → master) open; Phase 3 branch stacked on it — rebase onto master after retrofit merges.

---

## 2026-06-01 - Session 80: LTG extractor retrofit — full implementation

### Context
Continuation of sessions 78/79 (prior compact). Picked up from Task 5 with Tasks 1–4 already committed on `feature/ltg-extractor-retrofit`. All 8 tasks executed this session.

### What Was Done
- **Task 5 — `sweep_extractors.py`:** `cp extract_topics.py sweep_extractors.py`; removed `FORMAT_SCHEMA` + `call_ollama`; added `_build_benchmark_config(model)` helper (injects `think:false` for qwen3 variants only); `run_single` gains `client` param; `run_sweep` creates one `ModelClient` and threads it. 13 new tests. Commit `8fdfe0a`.
- **Task 6 — `extract_topics.py` rewrite:** Full rewrite as 2-arm production runner (~160 lines vs 440). `route_file()` delegates to `routing.route()`; `run_file()` dispatches to `client.extract_prose/extract_code` based on extension; JSONL contract (run_id, timestamp, model, file, file_role, status, parsed_topics). 11 new tests. Commit `321d1a5`.
- **Task 7 — Bash wrappers:** `run-extract-topics.sh` + `run-sweep-extractors.sh` (4-line pattern matching `run-embed.sh`). Both registered in `.claude/index.md` `bash-wrappers` table. Commit `6ba7e25`.
- **Task 8 — Parity check (no commit):** Ran `extract_topics.py` on `docs/research/smart-rag-repowise.md` (prose) + `personas/build-persona.py` (code). Then `embed.py` on output. Result: 2 files, 16 topics, 0 failed. `extractor_model` field confirmed `qwen3:14b` for prose, `qwen2.5-coder:14b` for code. No "WARNING: no winning row". Pipeline contract verified end-to-end.
- **Total tests:** 147 green (was 123 entering this session).
- **Ollama timeouts:** `my-python-q25c14` timed out 4× on full-file generation prompts for `sweep_extractors.py`. Resolved by writing implementation directly (user granted permission). Root cause: large context payload, not cold-start. Fix: use targeted slices in future, not full files as context.

### Decisions Made
- **`_build_benchmark_config` injects `think` key only for qwen3 variants** — checks `MODEL_EXTRA_PARAMS` dict; omits key entirely for gemma3/coder (correct Ollama behavior per `ref:thinking-mode`).
- **`run_single` takes `client` as parameter** (dependency injection) — `run_sweep` creates one client, threads it down. Makes testing clean without network calls.
- **`extract_topics.py` drops rubric/sweep entirely** — clean separation: production runner vs benchmark are now distinct tools.
- **`record["model"]` comes from `ChatResult.model`** (what Ollama actually used), not from the role name — survives future model renames in config.

### Gotchas Discovered
- `generate_code` with full-file context (350+ lines) reliably times out on `my-python-q25c14`. Use targeted `start_line`/`end_line` slices per context_files entry, or skip `output_file` and write surgically via Edit.
- `rel_path` passed to `run_single` must be `str`, not `PosixPath` — f-string `{path:<45}` format spec rejects Path objects with `TypeError`.

### Next
- **Open PR** for `feature/ltg-extractor-retrofit` → `master`. All 8 tasks complete, 147 tests green, parity verified.
- **After merge: LTG Phase 3 — anchor integration** (`retrieval/anchors.py`). Read `ref:ltg-plan-phase-3` + `retrieval/DECISIONS.md` first.
- **Deferred cleanup:** `embed_texts(role=)` → named wrapper; `embed_batch_with_retry` → ModelClient unification (both out-of-scope for this retrofit; tracked in tasks.md).

---

## 2026-05-30 - Session 77: LTG extractor retrofit — design complete

### Context
All PRs merged, master current. Entire session focused on design for the `extract_topics.py` → `model_client.py` retrofit (prereq for LTG Phase 3). Two advisor reviews. No implementation started — context hit 62% and a full plan was written for a fresh session.

### What Was Done
- **Extensive file reading:** `extract_topics.py`, `model_client.py`, `embed.py`, `config.yaml`, all test files, `ltg-model-registry-design.md`, `extract.txt` prompt, Phase 3 plan, `run-embed.sh`.
- **4 design Q&A settled:** ChatResult shape (`NamedTuple(content, model, prompt_tokens, eval_count)`), config YAML layout (YAML `options:` sub-dict + `think` as top-level sibling), role names (`extraction_prose`/`extraction_code`), schema location (`retrieval/schemas.py`).
- **Fork decision (two advisor passes):** Path B (production 2-arm runner) + `sweep_extractors.py` (benchmark). `extract_topics.py` keeps canonical name; `sweep_extractors.py` is the new file. Named methods (`extract_prose`/`extract_code`) for production; generic `call(prompt, model_config, schema)` for benchmark (dynamic-roles exception per pattern doc).
- **§1 pipeline contract identified:** `embed.py`'s `winning_extractor` + `select_winning_row` must agree with production runner's model name output. Fix: `routing.py` as single source of truth for `CODE_EXTENSIONS` + `route(path)→role`; `embed.py` imports from it.
- **`docs/patterns/code-design-conventions.md` written:** Language-agnostic pattern for named semantic methods (code as documentation). Python + Go examples. `ref:patterns-code-named-methods`. Added to `technology-conventions.md` index + `index.md`.
- **`feedback_code_as_documentation.md` saved to memory.**
- **`retrieval/tests/test_routing.py` written (TDD):** 14 tests for `routing.py`, confirmed red (ModuleNotFoundError). Committed on branch.
- **`docs/plans/ltg-extractor-retrofit.md` written:** Complete implementation guide — mandatory reading list, all settled decisions, per-task TDD guidance, local model call patterns (model: `my-python-q25c14`, timeout: 600), parity check criteria, out-of-scope items.
- **Branch `feature/ltg-extractor-retrofit` created.** 2 commits.
- **8-task list created** (session task tracker) covering routing.py → schemas.py → model_client.py → config.yaml → sweep_extractors.py → extract_topics.py → bash wrappers → parity check.

### Decisions Made
- **Fork B + sweep_extractors.py:** `extract_topics.py` → 2-arm production runner; benchmark sweep preserved in `sweep_extractors.py`.
- **ModelClient surface:** `extract_prose()`, `extract_code()` (named, production); `call(prompt, model_config, schema, timeout)` (generic, benchmark); `_chat()` private, owns all Ollama quirks.
- **`_chat` takes resolved config dict** (not role string) — named methods resolve role→dict; `call()` passes dict directly. Shared HTTP core.
- **ChatResult:** `NamedTuple(content, model, prompt_tokens, eval_count)`. Caller keeps wall-clock for tok/s.
- **config.yaml two-level:** `models:` + `roles:` with `options:` sub-dict for `num_ctx`/`temperature`; `think: false` as top-level sibling key (NOT inside `options{}`); `timeout_s` per model.
- **`schemas.py`:** `TOPIC_FORMAT_SCHEMA` moves to `retrieval/schemas.py` (leaf module). Imported by `model_client.py` + `sweep_extractors.py`.
- **Timeout:** config `timeout_s` default + caller override. 14B extractors: 600s. Never inherit `embed_texts`'s 120s.
- **Error handling:** `_chat`/`call` raise; caller classifies status taxonomy.
- **Code as documentation:** named methods over role strings — stored in memory + pattern doc.

### Next
- **Start implementation from `docs/plans/ltg-extractor-retrofit.md`** on branch `feature/ltg-extractor-retrofit`.
- **Read mandatory list first** (plan file § "Mandatory reading") — especially `.claude/overlays/local-model-conventions.md`.
- **Task 1 is ready:** `retrieval/tests/test_routing.py` exists (14 tests, confirmed red). Call `my-python-q25c14` with `timeout=600` to generate `routing.py`.

---

## 2026-05-30 - Session 76: 14B num_ctx re-probe + LTG architectural note

### Context
Started from feature/ollama-monitoring (tracking commits). Branched to feature/14b-num-ctx-reprobe for probe work. Context window was limited; session ended with cozempic cleanup.

### What Was Done
- **LTG repo-separation architectural evaluation:** Decided not to separate now (Phase 3 too early — data model still evolving, no consumers yet). Natural breakpoint: after Phase 5, before Phase 6. Extracted gate notes into two places:
  - `docs/plans/2026-04-13-latent-topic-graph-implementation.md` — blockquote at Phase 6 header
  - `.claude/tasks.md` — new deferred task "LTG Phase 6 gate — evaluate repo separation"
- **Pre-session reading guide:** Added `ref:session-reading-guide` block to `.claude/session-context.md` — compact table mapping each pending task to files/refs needed before starting. Wired into `resume.sh` as a new section between last-session and key-files blocks.
- **`scripts/run-ctx-probe.sh` written:** New reusable probe tool for context-window ceiling testing. Loads each model at configurable ctx sizes, measures VRAM + tok/s, prints summary table. Added to `index.md` under bash wrappers.
- **14B num_ctx re-probe — all models, 16K/24K/32K:** All pass at 32K with q8_0 KV enabled. Results:
  - qwen3:14b        → 32K: 11,237 MiB / 1,051 MiB free / 16.5 tok/s ✅
  - qwen2.5-coder:14b→ 32K:  9,498 MiB / 2,790 MiB free / 14.9 tok/s ✅
  - deepseek-r1:14b  → 32K:  9,505 MiB / 2,783 MiB free / 14.0 tok/s ✅
  - deepseek-coder-v2:16b → 24K: 11,554 MiB / 734 MiB free ✅ (32K tight at 574 MiB)
  - qwen3:8b-q8_0    → 32K: 11,674 MiB /  614 MiB free / 35.4 tok/s ✅ (tight PASS)
  - gemma3:12b       → 32K: 10,313 MiB / 1,975 MiB free / 41.2 tok/s ✅
- **11 personas upgraded and rebuilt:** personas/models.yaml, personas/registry.yaml (11 entries), 11 Modelfiles updated. `ollama create` run for all 11, verified via `ollama show`.
- **Stale references updated:** CLAUDE.md Key Technical Facts (14B ctx line), `.memories/KNOWLEDGE.md` VRAM Budget section, `session-context.md` ref:active-decisions num_ctx line, reading guide entry marked done.
- **Probe results doc:** `retrieval/probes/ctx-probe-2026-05-30.md` — full tables for both probe runs.
- **2 commits on feature/14b-num-ctx-reprobe:**
  - `42b9fa3` probe: 14B num_ctx re-probe post OLLAMA_KV_CACHE_TYPE=q8_0
  - `1ad9b72` probe: extend ctx-probe to qwen3:8b-q8_0 + gemma3:12b

### Decisions Made
- **LTG repo separation deferred to Phase 6 start:** Gate note placed in plan file + tasks.md. Extraction cost: ~1 session via `git subtree split`. Timing: after Phase 5 closes (stable schema + first cross-repo consumer).
- **All 14B models → 32768:** q8_0 KV cache makes 32K viable for all standard 14B models. deepseek-coder-v2:16b exception at 24576 (16B weights, tighter margin).
- **qwen3:8b-q8_0 → 32768:** 614 MiB headroom — tight but consistent with other PASS models.
- **gemma3:12b → 32768:** 1,975 MiB headroom — comfortable. GQA architecture scales KV more slowly than Qwen3 series.

### Next
- **Open PR** for `feature/14b-num-ctx-reprobe` → master (or merge feature/ollama-monitoring first if it's ahead)
- **Merge feature/ollama-monitoring** — contains tracking commits (LTG Phase 6 gate + reading guide)
- **LTG Phase 3 — anchor integration** (`retrieval/anchors.py`) — next primary LTG milestone; prereqs now cleared (14B re-probe done)
- **extract_topics.py → model_client.py retrofit** — do before Phase 3 integration
- **Classifier benchmark (M-P1b/P2)** — qwen3.5:0.8b, 2b, phi4-mini vs qwen3:4b-q8_0; models pulled and waiting
- **M-P0a cleanup** — retire 6 DeepCoder benchmark personas

---

