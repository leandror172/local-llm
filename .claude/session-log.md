# Session Log

**Current Layer:** LTG Phase 3 — Anchor Integration (prereq: extractor retrofit)
**Current Session:** 2026-05-30 — Session 77: LTG extractor retrofit design
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-25-to-2026-05-25.md`, `.claude/archive/session-log-2026-05-26-to-2026-05-26.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-28-to-2026-05-28.md`

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

## 2026-05-29 - Session 75: Infrastructure, model pulls, context-limit audit

### Context
Started with all PRs merged, master clean. Branched conversation (/btw) for a side question about context limits; both branches had work. Primary session focused on infrastructure (Ollama model store migration, KV cache quant), model pulls, and persona fixes. Branch covered context-limit doc audit.

### What Was Done
- **MCP persona fixes:** `my-mcp-q25c14` + `my-mcp-q3` — added CANONICAL EXAMPLE block with correct `from mcp.server.fastmcp import FastMCP` import. Also backfilled SOLID constraints to `my-mcp-q3`. Both rebuilt + smoke-tested.
- **Layer 5 status sync:** Queried expense-reporter repo; all 5.1–5.8 tasks complete (439 tests). Created `.claude/adjacent-projects.md` for loose cross-repo tracking. Updated tasks.md — Layer 5 ACTIVE (not COMPLETE; retrieval upgrades remain).
- **Ollama model store migrated C: → I:\\:** Moved 156GB blobs to `/mnt/i/ollama-models/`. Updated systemd override with `OLLAMA_MODELS=/mnt/i/ollama-models` + `Requires=mnt-i.mount`. 78/78 models verified. C:\\ no longer grows from model pulls (406GB free on I:\\). VHD compaction optional cleanup.
- **`OLLAMA_KV_CACHE_TYPE=q8_0` enabled system-wide:** Added to systemd override. Halves KV cache VRAM cost. Effect: 8B models → 32K effective ctx; 14B → 16K with headroom (re-probe pending).
- **Model pulls:** `qwen3.5:0.8b` (1.0GB), `qwen3.5:2b` (2.7GB), `phi4-mini` (2.5GB) pulled. `llama4:scout` pulled (67GB) then removed — not viable on 12GB (smallest quant 33.8GB needs 24GB VRAM; long-context reasoning quality also poor at 15.6% on Fiction.liveBench@128K).
- **M-P1a closed:** Opus subagent + web-research confirmed Scout not viable at any quant on this hardware. Closed as permanent; watch note added for future ≤15GB long-context synthesis model.
- **Context-limit audit (branched session):** Subagent identified 18 stale references to old limits (4K/10240). All 18 applied across CLAUDE.md, session-context.md, extract_topics.py, DECISIONS.md, models.yaml, mcp-server/README.md, persona-template.md, modelfile-reference.md, closing-the-gap.md, model-strategy.md, layer-0-runtime-refs.md, advisor-notes.md, README.md, portfolio mirrors.
- **`extract_topics.py` num_ctx:** 8192 → 16384 (direct LTG quality impact — was truncating files before extraction).
- **Deferred task added:** Re-probe 14B models at 24K–32K after q8_0 before committing to higher num_ctx.

### Decisions Made
- **Adjacent-projects pattern:** Other repos tracked loosely in `.claude/adjacent-projects.md` — not mirrored in tasks.md. Internal tracking stays in each repo.
- **Layer 5 status:** ACTIVE not COMPLETE — 5.R1 TF-IDF, 5.R2 embeddings, RUI-3/4 remain in expense-reporter.
- **Llama 4 Scout: permanently closed.** Hardware wall is absolute (33.8GB minimum, 24GB VRAM floor). Wrong model for synthesis use case regardless.
- **Long-context path forward:** `OLLAMA_KV_CACHE_TYPE=q8_0` + existing qwen3:8b at 32K is the right answer for document analysis. Chunk-and-retrieve via LTG beats single-model long-context dump.

### Next
- **LTG Phase 3** — anchor integration (`retrieval/anchors.py`, embed ref:KEY blocks, merge with extracted topics). See `docs/plans/2026-04-13-latent-topic-graph-implementation.md` § Phase 3.
- **Classifier benchmark (M-P1b/P2):** `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0`. Now that models are pulled.
- **14B num_ctx re-probe:** Deferred task. Run before any session needing >16K context on 14B.
- **M-P0a cleanup:** Retire 6 DeepCoder benchmark personas + `deepcoder:14b` base (still installed, 9GB on I:\\).

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

