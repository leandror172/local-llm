# Session Log

**Current Layer:** LTG Phase 2 — Embedding + Storage
**Current Session:** 2026-05-28 — Session 72: LTG Phase 2 Tasks 7–9 (ltg_inspect.py, acceptance, docs)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-25-to-2026-05-25.md`, `.claude/archive/session-log-2026-05-26-to-2026-05-26.md`

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

## 2026-05-27 - Session 69: Advisor review applied to model survey (session 68)

### Context
Session 68 produced `docs/findings/model-updates-2026-05.md` (model update survey) and the advisor reviewed it. The advisor identified source-quality issues: benchmark numbers and Ollama tag existence claims sourced from secondary blogs, not primary sources. This session applies 8 specific edits to the survey doc plus cascading updates to memory and tracking files.

### What Was Done
- **PR #39 details:** Existing open PR `feature/model-survey-2026-05` → `master`, 29 changed files, 2344 additions, clean/mergeable.
- **New branch `feature/model-survey-advisor-review`** off `feature/model-survey-2026-05`.
- **8 edits to `docs/findings/model-updates-2026-05.md`:**
  1. Methodology footnote added at top (secondary source warning)
  2. TL;DR P0 rows re-framed: "Swap" → "Pull + Benchmark" / "Pull + Probe"; swap made conditional
  3. Verification Status column added to TL;DR table with 5-value legend
  4. Qwen3.7 Max qualified: single-source, unusual naming, verify from official blog
  5. Benchmark numbers (~88%/~62% etc.) footnoted as secondary-source claims; ¹ notation added
  6. Embedding co-residence probe marked as hard gate (not follow-up) in LTG Phase 2 impact table
  7. Llama 4 Scout 10M context qualified: effective useful range ~200K–1M for RAG
  8. Independent benchmark Y/N column added to all 3 frontier-distilled tables
  9. "Changes Made in Response to Advisor Review" section added at doc bottom
- **`.memories/QUICK.md`:** Replaced "supersedes (~88%)" with "candidate to supersede (secondary source; not benchmarked; swap gated on M-P0a)"
- **`.memories/KNOWLEDGE.md`:** Qualified HumanEval/LiveCodeBench numbers as "from secondary sources, not independently verified"; marked embedding VRAM probe as hard gate
- **`.claude/tasks.md`:** M-P0a reframed as "Pull + benchmark; swap only if confirmed"; M-P0b: added "hard gate" language + "Do not start embed.py until probe passes"; M-update: deferred deprecation until local benchmark confirms
- **`.claude/session-context.md`:** Session 68 entry corrected (superseded → candidate to supersede); Session 69 entry added; Next pointer updated

### Decisions Made
- **Keep both coder models until M-P0a benchmark confirms** — premature deprecation of qwen2.5-coder:14b could disrupt active MCP work
- **Embedding VRAM probe = hard gate** — VRAM delta (0.6GB → ~5GB) is large enough that the old WARN verdict doesn't apply; new probe required before embed.py design
- **No changes to DECISIONS.md** — ref:ltg-extractor and ref:ltg-embedding remain unchanged; those are updated after benchmark/probe confirms, not before

### Next
- **Merge this PR** into `feature/model-survey-2026-05`, then merge #39 to master.
- **M-P0a** — pull `qwen3.6-coder:14b`, run local benchmark, swap if confirmed.
- **M-P0b** — pull `qwen3-embedding:8b`, run VRAM co-residence probe, update LTG Phase 2 plan if probe passes.
- **LTG Phase 2** — start `embed.py` only after M-P0b probe passes.

---

