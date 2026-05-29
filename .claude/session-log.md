# Session Log

**Current Layer:** LTG Phase 3 — Anchor Integration
**Current Session:** 2026-05-29 — Session 74: M-P0a benchmark — DeepCoder-14B vs qwen2.5-coder:14b
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-25-to-2026-05-25.md`, `.claude/archive/session-log-2026-05-26-to-2026-05-26.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`

---

## 2026-05-29 - Session 74: M-P0a benchmark — DeepCoder-14B vs qwen2.5-coder:14b

### Context
Started by running `resume.sh`. All PRs from session 73 merged. Moved to M-P0a — the pending model upgrade benchmark. Discovered `qwen3.6-coder:14b` (original M-P0a target) does not exist on Ollama; the tag was from unverified secondary sources. Pivoted to DeepCoder-14B as the strongest verified 14B coder candidate (HumanEval+ 92.6%, LiveCodeBench 60.6%, same 9GB footprint). All work on branch `feature/m-p0a-deepcoder-benchmark`.

### What Was Done
- **Tag verification:** Confirmed `qwen3.6-coder:14b` does not exist. `qwen3.6` = 27B/35B general model. `qwen3-coder` = 30B MoE only (already pulled). No 14B coder in Qwen3.x generation exists on Ollama.
- **DeepCoder research:** Fetched HuggingFace card, agentica/rllm GitHub, Ollama library page. Key finding: no think-suppression mechanism documented anywhere; model recommends `max_tokens=64000` minimum (CoT traces can consume entire budget). Fine-tuned from DeepSeek-R1-Distilled-Qwen-14B via RL.
- **Benchmark prompts:** Added two new benchmark prompts (04-python-async-pipeline.md, 05-mcp-file-stats.md). Tightened existing go prompt (`context.Context` stop signal, `go run -race` requirement). Prompts reviewed by Opus 4.8 subagent — applied all actionable feedback (exception scope, run_in_executor spec, MCP extension filter contract, grading checklists).
- **Persona setup:** Added `deepcoder:14b` to `models.yaml`. Created 6 personas via skill (`copy_persona` for constrained Go/Python/MCP; hand-written Modelfiles for vanilla variants with model-recommended settings temp=0.6, top_p=0.95, no system prompt).
- **Benchmark runs (9 total):** Ran sequentially grouped by base model (minimize VRAM swaps). Results:
  - go-q25c14: ✅ 212.9s, 1370tok, 6.4tok/s
  - python-q25c14: ✅ 111.3s, 760tok, 6.8tok/s
  - mcp-q25c14: ✅ 123.5s, 845tok, 6.8tok/s
  - go-deepcoder: ❌ TIMEOUT (500s)
  - python-deepcoder: ✅ 194.8s, 1326tok, 6.8tok/s (think block present)
  - mcp-deepcoder: ❌ TIMEOUT (500s)
  - go-deepcoder-vanilla: ❌ TIMEOUT (500s)
  - python-deepcoder-vanilla: ❌ TIMEOUT (500s)
  - mcp-deepcoder-vanilla: ❌ TIMEOUT (500s)
- **Evaluation:** Sonnet 4.6 (primary) + Opus 4.8 subagent (independent, before seeing primary verdicts). Both evaluators agreed on all 9 verdicts. Opus empirically verified Go bugs via scratch harness (`go run -race` fires 10–13 race reports; cleanExpired removed 0 of 4 expired entries; 5 Puts yield 4 tracked entries due to corrupt list).
- **Verdict summary:** go-q25c14=1, python-q25c14=1, mcp-q25c14=0 (wrong FastMCP API — production bug), python-deepcoder=2 (best output, correct @dataclass + fuller async), all others=0 (timeout).
- **Decision: NO SWAP.** DeepCoder structurally unfit for RTX 3060 12GB. 5/6 timeout; no think-suppression; latency unpredictable (constrained variant completed while vanilla timed out — system prompt shortens CoT but not reliably). The Python quality win is real but a 2-line fix to q25c14 is cheaper than absorbing 2× latency.
- **Side finding:** `my-mcp-q25c14` uses wrong FastMCP API (wrong import, dispatcher pattern). Added as P1 fix task.
- **Report:** `docs/findings/deepcoder-benchmark-2026-05-29.md` (7 `ref:KEY` sections, Opus eval verbatim).

### Next
- **Fix `my-mcp-q25c14` persona** (P1 — wrong FastMCP API exposed by benchmark)
- **LTG Phase 3** — anchor integration (anchor nodes, Phase 1 JSONL → anchor table, `relate()` with anchor overlay)
- **M-P0a cleanup** — retire 6 deepcoder benchmark personas when no longer needed (deferred task added)

## 2026-05-28 - Session 73: M-P0b VRAM probe + embedding upgrade (bge-m3 → qwen3-embedding:8b)

### Context
Started by running `resume.sh`. PR#42 (`feature/ltg-phase2-implementation` → master) was already open. Moved directly to M-P0b — the VRAM co-residence probe for `qwen3-embedding:8b` + `qwen3:14b`, which was unblocked now that Phase 2 was complete. All session work committed to new branch `feature/ltg-embedding-upgrade-qwen3`.

### What Was Done
- **M-P0b VRAM probe:** Re-used `retrieval/run-vram-probe.sh` with `EMBED_MODEL=qwen3-embedding:8b`. Fixed the script first — `EMBED_MODEL="bge-m3"` was hardcoded (env override silently ignored); changed to `${EMBED_MODEL:-bge-m3}` idiom. Probe verdict: **WARN** (same as bge-m3) — load-time eviction, zero query-time evictions, avg infer 4.2s (vs 3.5s with bge-m3).
- **Decision: re-embed before Phase 3 (Option A):** Re-embedding cost is small (69 topics, ~3s); deferring would multiply the re-embed scope each phase (corpus + anchors vs corpus only). Embedding upgraded immediately.
- **config.yaml updated:** `model: bge-m3 → qwen3-embedding:8b`, `embed_dim: 1024 → 4096`.
- **embed.py fixed:** Hardcoded `embed_dim=1024` in two `main()` call sites replaced with `cfg_dim` from `load_config(CONFIG_PATH)`. Also imports `ModelClient, load_config` from `model_client`.
- **store.py fixed:** `SCHEMA` constant → `build_schema(embed_dim: int)` function. `rows_to_arrow_table` infers `embed_dim` from first input row's field. `main()` reads `rows[0]["embed_dim"]` for `validate_table`.
- **Pipeline re-run:** `run-embed.sh` → 69 topics, 2.9s, 4096-dim. `run-store.sh` → 69 rows, old index auto-backed up to `index.bak`. Acceptance: R1/R3/R4 ✅, R2 ⚠️ same corpus gap, P1 relate improved 0.663→0.697.
- **Docs/memories updated:** `retrieval/DECISIONS.md` (`ref:ltg-embedding` rewritten, schema table updated), `retrieval/.memories/QUICK.md`, `retrieval/.memories/KNOWLEDGE.md` (new `ref:ltg-m-p0b-probe`), `.memories/QUICK.md`, `docs/findings/model-updates-2026-05.md` (M-P0b row marked complete, embedding table updated).
- **2 commits** on `feature/ltg-embedding-upgrade-qwen3`: `a0f1e92` (code + probe + artifacts) + `5f04a4e` (memories + docs). **61 tests green.**

### Decisions Made
- **Re-embed before Phase 3** — Option A chosen; cost is small and avoiding it multiplies re-embed scope at every future phase.
- **N-criteria threshold recalibration deferred to Phase 3** — original `> 1.0` threshold was bge-m3 1024-dim calibrated. Noise queries at 0.84–0.98 in 4096-dim are proportionally equivalent; recalibrate when Phase 3 anchors join corpus.
- **embed.py config-driven** — model + embed_dim now come from `config.yaml`; future model swaps require only one config edit.
- **store.py schema-dynamic** — `build_schema(embed_dim)` replaces `SCHEMA` constant; dimension flows from input JSONL, not from code.

### Next
- **Open PR** for `feature/ltg-embedding-upgrade-qwen3` (branches off `feature/ltg-phase2-implementation` — coordinate merge order with PR#42)
- **LTG Phase 3** — anchor integration (anchor nodes, Phase 1 JSONL → anchor table, `relate()` with anchor overlay)
- **M-P0a** — still pending: pull + benchmark `qwen3.6-coder:14b` vs `qwen2.5-coder:14b`

---

## 2026-05-28 - Session 72: LTG Phase 2 Tasks 7–9 (ltg_inspect.py, acceptance, docs)

### Context
Continuation of Phase 2 implementation. Resumed from `.claude/prompt-ltg-phase2-continuation.md`. Branch: `feature/ltg-phase2-implementation`. Tasks 7–9 of 9 completed this session. Phase 2 fully closed.

### What Was Done
- **Orientation audit:** Discovered missed `test_embed.py` read + `ref:ltg-extractor` / `ref:ltg-phase1-summary` needed; completed additional reads before starting implementation.
- **Task 7 — `retrieval/ltg_inspect.py`:** 5-mode CLI (--list, --stats, --query, --relate, --acceptance). Tests first: Ollama timed out 3× on `qwen2.5-coder:14b`; escalated to `qwen3:14b` (300s timeout). Generated test scaffold manually, delegated 14 test functions to Ollama, applied 3 inline fixes (double capsys.readouterr, missing ModelClient mock, wrong search assertion). 14/14 green. `run-inspect.sh` wrapper added.
- **Key rename:** `inspect.py` → `ltg_inspect.py` — `inspect.py` shadows Python stdlib `inspect` module via `sys.path[0]`, breaking `httpx` and `pyarrow` imports in all other scripts. Discovered during `run-embed.sh` pipeline test.
- **Task 8 — Acceptance run:** Full pipeline: embed (69 topics, 8 files, 5.2s) → store (1.1s) → inspect --acceptance (2.3s, target <5s). Results: R1/R3/R4 ✅, R2 borderline (`.memories/QUICK.md` topics don't surface "session memory" explicitly), N1/N2 ✅ (L2 > 1.0), P1 relate ✅ (mean cosine 0.663). Fixed 3 runtime bugs: store.py undefined `logger`, relate_mode crash on empty corpus file, acceptance_mode output_md as dir not file.
- **Task 9 — Doc updates:** 6 files updated: `retrieval/DECISIONS.md` (Phase 2 note in `ref:ltg-embedding`, `inspect.py→ltg_inspect.py`, new `ref:ltg-phase2-schema`), `retrieval/.memories/QUICK.md` (Phase 2 complete status), `retrieval/.memories/KNOWLEDGE.md` (new `ref:ltg-phase2-findings`), `.claude/session-context.md` (session 72 entry + Next advanced), `.claude/index.md` (4 new LTG wrappers), v1 plan (session 72 expansion note).

### Decisions Made
- **`ltg_inspect.py` not `inspect.py`** — stdlib shadow is a hard blocker; documented in `ref:ltg-phase2-findings` as gotcha.
- **R2 borderline → document and proceed** — only 1 underperforming query (plan threshold is 2+); A/B with `description_plus_spans` remains deferred.
- **LanceDB uses L2 distance** (not cosine) — `L2 = sqrt(2*(1-cos))` for unit-normalised vectors; acceptance threshold "cosine < 0.55" → L2 > 0.949. Documented in `ref:ltg-phase2-findings`.
- **`qwen2.5-coder:14b` unusable at current context size** — 3 consecutive timeouts with 300s budget (both full prompt and split prompt). Escalated to `qwen3:14b`. Worth re-testing M-P0a swap sooner.

### Next
- **Create PR** for `feature/ltg-phase2-implementation` → master
- **LTG Phase 3** — anchor integration (anchor nodes, Phase 1 JSONL → anchor table, relate() with anchor overlay)
- **M-P0b** — VRAM probe for `qwen3-embedding:8b` + qwen3:14b (now unblocked)

---

## 2026-05-27 - Session 71: LTG Phase 2 Tasks 3–6 (model_client, preflight, embed, store)

### Context
Continuation of Phase 2 implementation (session 70 was design-only). Resumed from `.claude/prompt-ltg-phase2-continuation.md`. Branch: `feature/ltg-phase2-implementation`. Tasks 3–6 of 9 completed this session.

### What Was Done
- **Task 3 — model_client.py:** `load_config()` + `ModelClient` (embed_dim, embed_texts) isolation layer. 13 tests green. Ollama verdict 1 — async/await on sync httpx.post (2-site fix).
- **Task 4 — preflight.sh + run-preflight.sh:** 5-check fail-fast script (python deps, Ollama reachable, bge-m3 pulled, Phase 1 JSONL exists, disk space). All 5 checks pass. Ollama verdict 2.
- **Task 5 — embed.py + run-embed.sh:** Reads Phase 1 JSONL, routes to winning extractor (code vs prose), batches embed via bge-m3 `/api/embed`, writes 16-field embedding JSONL. Includes sequential constraint header comment. 23 tests green. Ollama generated helpers at verdict 1 (4 fixes: unique_slugs -1→-2, wrong join, utcnow→timezone.utc, missing json import). main() written by Claude after 4 Ollama attempts (3 cold-start timeouts + 1 rejected for wrong generator/list handling).
- **Task 6 — store.py + run-store.sh:** 16-field PyArrow SCHEMA, load_embedding_jsonl, rows_to_arrow_table (fixed-size float32 list), backup_index (shutil.move, replace prior backup), open_or_create_table (mode=overwrite), validate_table, write_run_log, main(). 11 tests green. Ollama verdict 1 — missing shutil/datetime imports + LanceTable.column() doesn't exist (use .to_arrow().column()).
- **4 commits pushed** to `feature/ltg-phase2-implementation`.

### Decisions Made
- **Ollama prompts:** behavioral intent only, not code stubs — confirmed by user correction mid-session. Sending function stubs as prompts defeats the purpose of delegation.
- **Tests should also go to Ollama** when they contain non-trivial logic — not just implementations.
- **Prompt splitting:** large prompts (>2000 chars + 3 large context files) time out on 14B; split helpers-first + main()-second.

### Gotchas Discovered
- **httpx async slip:** qwen2.5-coder generates `async def`/`await httpx.post` even when context is sync. Fix prompt: explicitly say "use `httpx.post(url, json=payload, timeout=120.0)` — NOT async."
- **LanceTable API:** `.column("vector")` does not exist on LanceTable; use `.to_arrow().column("vector").to_pylist()`.
- **generate_code timeout pattern:** Not cold start — model loaded but 14B + large context = real timeout. Split context or reduce prompt size.

### Next
- **Task 7:** `inspect.py` — 5 modes: `--query` (ANN top-k), `--list`, `--stats`, `--relate` (pairwise cosine preview), `--acceptance` (runs all 7 probe queries, writes markdown to `retrieval/probes/`). TDD + Ollama. See v2 plan lines 393–469.
- **Task 8:** Run acceptance — embed Phase 1 JSONL → store → inspect --acceptance. 4 recall + 2 negative + 1 relate-preview queries. Latency target: <5s for all 7 queries.
- **Task 9:** Post-completion doc updates (DECISIONS.md, .memories/, session-context.md, index.md).
- **Read before starting Task 7:** v2 plan lines 393–469 (inspect.py spec) + 567–606 (acceptance test definitions).
- **Reminder for next session:** delegate test-writing to Ollama too; use behavioral prompts not code stubs.

---

## 2026-05-27 - Session 70: LTG Phase 2 design decisions (no implementation yet)

### Context
All PRs merged (treated as merged per user instruction: #37 Plans 1+2, #38 Plan 3+logging, #39 model survey). Session focused entirely on design decisions for LTG Phase 2 before any code is written. A context-bloat incident (advisor call doubled context past 100K) truncated the session mid-design; key decisions were recovered from an extracted session file and decisions committed to the plan doc.

### What Was Done
- **Oriented on Phase 2 state:** plan ready, Phase 1 JSONL exists (8 files × 4 models), bge-m3 + qwen3:14b pulled, lancedb/pyarrow not yet installed, .gitignore missing two entries.
- **Decided embedding model path:** bge-m3 for Phase 2 as planned; VRAM probe for qwen3-embedding:8b deferred to *after* Phase 2 completes (not a gate for Phase 2 start). Confirmed changing models later = 2 config lines only (model name + embed_dim).
- **model_client.py isolation layer designed:** scripts never touch httpx or provider URLs; all model calls go through `ModelClient(config)`. Interface: `embed()`, `embed_batch()`, `embed_dim()`, `generate()`. Ollama-only for Phase 2; provider branches extensible later.
- **config.yaml shape decided:** flat/inline for Phase 2 (one role: `embedding`). Comment in file documents two-level upgrade path. Upgrade trigger: ≥2 roles share same base model with different params, OR ≥3 roles total.
- **embed_dim validation:** Option B — assert `len(vector) == config.embed_dim` on first embed call; fail with message pointing to config key. Lazy (not at init), no extra network cost.
- **extract_topics.py:** untouched for Phase 2; retrofit to model_client.py is a deferred task.
- **Naming convention for registered models:** `{provider}-{model-slug}-{key-params}` e.g. `ollama-bge-m3-dim-1024`, `ollama-qwen3-14b-no-think`. Append only differentiating properties.
- **New file:** `docs/ideas/ltg-model-registry-design.md` — full two-level design, naming convention, load_config() resolution pseudocode, note on parallel registry + LTG repo separation.
- **Updated:** `docs/plans/ltg-phase2-implementation.md` — added model_client.py + config.yaml to scope, Decisions In Force table (3 new rows), Required Reading table (1 new row), post-completion checklist.
- **Updated:** `.claude/tasks.md` — replaced old ModelCaller Protocol stub with concrete retrofit task; added LTG config two-level upgrade task.
- **Updated:** `.claude/index.md` — entry for `docs/ideas/ltg-model-registry-design.md`.

### Decisions Made
- **bge-m3 for Phase 2** (probe qwen3-embedding:8b after Phase 2, not before)
- **model_client.py is new Phase 2 scope** alongside embed.py/store.py/inspect.py
- **embed_dim: assert on first embed** (Option B, lazy)
- **config.yaml: flat inline for Phase 2;** two-level design at Phase 3+ trigger
- **LTG likely moving to own repo** before Phase 3+ integration (noted in registry design doc)

### Next
- **Start LTG Phase 2 implementation.** Read before coding (in order):
  1. `retrieval/.memories/QUICK.md`
  2. `retrieval/.memories/KNOWLEDGE.md` (`ref:ltg-vram-probe` + `ref:ltg-phase1-summary`)
  3. `docs/plans/ltg-phase2-implementation.md` — full spec (authoritative)
  4. `docs/ideas/ltg-model-registry-design.md` — model_client.py interface + config.yaml shape
  5. `retrieval/DECISIONS.md` (`ref:ltg-embedding`, `ref:ltg-vector-store`, `ref:ltg-storage-layout`)
  6. `retrieval/extract_topics.py` — JSONL format + dependency pattern (httpx, no pyproject.toml)
  7. First 5 lines of `retrieval/runs/20260416-181839.jsonl` — see actual Phase 1 data
  8. `.memories/QUICK.md` — repo-level status
- **Pre-implementation checklist before writing any code:**
  - `pip install 'lancedb>=0.20,<0.30' pyarrow` (httpx already present)
  - Add `retrieval/index/` and `retrieval/embeddings.jsonl` to `.gitignore`
- Build order: config.yaml → model_client.py → embed.py → store.py → inspect.py → bash wrappers → acceptance test

---

