# Session Log

**Current Layer:** LTG Phase 1 — topic extractor spike
**Current Session:** 2026-04-15 — Session 53: ref-lookup prefix search + Phase 1 extractor spike (runner built)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`

---

## 2026-04-15 - Session 53: ref-lookup prefix search + Phase 1 extractor spike (runner built)

### Context
Resumed on `feature/ltg-phase0` (PR open for review). Two quick deferred items first, then Phase 1 spike work.

### What Was Done
- **ref-lookup prefix/glob search** (`feature/ref-lookup-prefix-search`, PR #30): `ref-lookup.sh` now accepts `KEY*` patterns; also fixed `--list` digit-key bug (`[a-z-]*` → `[a-z0-9-]*`) that was hiding `layer3-inventory`, `layer4-status`, and all 10 `ltg-plan-phase-*` keys. Overlay `ref-indexing` bumped to v2.
- **Phase 1 corpus selected**: 8 files (7 prose + 1 code) covering long research doc, short memory, cross-reference index, multi-topic plan, structured template, mixed content, architectural doc, Python code file.
- **`retrieval/prompts/extract.txt`**: extraction prompt template — 5 rules emphasising non-contiguous spans and semantic (not structural) topics.
- **`retrieval/extract_topics.py`**: sweep runner — 4 models × 8 corpus files, `FORMAT_SCHEMA` structured output via Ollama `format=` param, 6 mechanical rubric dims auto-computed (dims 1-4, 10-11), JSONL + summary table output, manual rubric template generated for dims 5-8.
- **MCP `client.py` fix** (two changes): (1) `AsyncClient(timeout=None)` — was using httpx's 5s default, overriding per-request timeouts silently; (2) `chat()` now uses `async with httpx.AsyncClient()` per call instead of reusing persistent client — fixes stale connection state after cancelled/timed-out requests.
- **Local model workflow**: q25c14 generated `parse_topics` (IMPROVED) and `call_ollama` (IMPROVED); gemma3:12b generated full completion of remaining functions (IMPROVED); Claude version chosen as final (richer comments, `MANUAL_RUBRIC_TEMPLATE` constant). Protocol deferred TODO added to `call_ollama`.
- **Deferred task added to `ref:deferred-infra`**: `ModelCaller` Protocol abstraction for `extract_topics.py` — decouples from Ollama HTTP, enables MCP bridge / OpenAI-compatible / mock.
- **Committed**: `feature/ltg-phase1-extractor-spike` (commit 80e7ebf).

### Decisions Made
- Claude version of runner chosen over gemma version — richer docs, cleaner template handling; gemma's IMPROVED logic merged in (utility functions from q25c14, execution from gemma3:12b).
- `async with httpx.AsyncClient()` per call is the right pattern for sequential, long-running Ollama calls; connection pool reuse is appropriate for concurrent/short calls, not 30-150s generation.
- Context-accumulation via `context_files` (WIP file) is the reliable strategy for generating large scripts with local models — keep each prompt's expected output under ~200 tokens.
- `cozempic` reports against 1.00M window; actual is 200K — multiply reported % by 5× for real usage.

### Next
- **Run the sweep**: `python3 retrieval/extract_topics.py` — 4 models × 8 files. Score dims 1-4 automatically; fill dims 5-8 manually in the generated rubric template.
- **Phase 2 VRAM co-residence probe**: qwen3:14b + bge-m3 simultaneously on 12GB card — required before locking embedding choice.
- **Open PR** for `feature/ltg-phase1-extractor-spike` after sweep results documented in `retrieval/spike-results.md`.
- **Still open**: PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers.
**Current Layer:** Layer 5+ / LTG Phase 0 frozen
**Current Session:** 2026-04-14 — Session 52: LTG Phase 0 decisions + plan re-indexed
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`

---

## 2026-04-14 - Session 52: LTG Phase 0 decisions + plan re-indexed

### Context
Resumed on master (clean) after session 51's smart-rag + LTG work merged in
commit e639b5e. User switched to Opus max effort for the Phase 0 decision
discussion — all 8 Phase 0 decisions required explicit resolution before
any code. New branch `feature/ltg-phase0`.

### What Was Done
- **Phase 0 decisions frozen** in `retrieval/DECISIONS.md` — 8 entries, each with
  decision / rationale / alternatives / revisit trigger. New top-level `retrieval/`
  directory created with `.memories/QUICK.md` following the per-folder convention.
- **Plan document re-indexed** with 19 narrow `ref:KEY` blocks replacing the single
  file-wide block per the single-responsibility rule. `plan-latent-topic-graph`
  now wraps only intro+goal; per-phase keys `ltg-plan-phase-0` through
  `ltg-plan-phase-9` plus `ltg-plan-{required-reading,deferred,relationship,
  integration,risks,estimate,success,handoff}`. Phase 0/1/2 blocks cross-reference
  the session 52 resolutions in DECISIONS.md.
- **`.claude/index.md` updated** with two new tables: "LTG Plan — Per-Section Ref Keys"
  (18 sub-keys) and "LTG Phase 0 Decisions" (8 decision keys).
- **Root `.memories/QUICK.md` updated** — added `retrieval/` to repo structure,
  advanced LTG status, added pointers to the narrow ref keys.
- **Feedback memory saved** (`feedback_batch_edits_on_opus.md`): batch multiple edits
  into one Write or parallel tool calls on Opus, not sequential Edits (cost).
- **Chore commits:** `.mcp.json` gains the web-research MCP entry; 3 `/copy` response
  snapshots saved to `docs/ideas/smart-rag-phase-0-response-*.md`.

### Decisions Made
Summary of frozen Phase 0 (full rationale in `retrieval/DECISIONS.md`):
- **Index scope** → per-repo, federation to Phase 9 (`ref:ltg-scope`)
- **Embedding** → `bge-m3` via Ollama (Ollama-native flipped the decision from
  nomic-embed-text); fallback chain mxbai → arctic → nomic. VRAM co-residence
  probe required in Phase 2 before locking. (`ref:ltg-embedding`)
- **Vector store** → LanceDB (`ref:ltg-vector-store`)
- **Graph lib** → networkx + leidenalg (`ref:ltg-graph-lib`)
- **Extractor** → empirical A/B in Phase 1, no pre-commit; 5-6 models × 8 files +
  long-file appendix, 11-dim rubric, two-stage variant for top 2, exit threshold
  ≥ 2.2 weighted quality (`ref:ltg-extractor`)
- **Placement** → new top-level `retrieval/` directory (`ref:ltg-placement`)
- **Storage layout** → pure LanceDB + JSON/YAML sidecars + `inspect.py` (rejected
  the SQLite+LanceDB split; adding SQLite later is a 2-hour add if ever needed).
  (`ref:ltg-storage-layout`)
- **Corpus** → curated subset + `docs/ideas/`; two finding-dependent branch points
  (code files, long files) to resolve after Phase 1 sweep (`ref:ltg-corpus`)

Non-default highlights: embedding choice hinged on `ollama pull bge-m3` succeeding;
extractor decision is explicitly "how we will decide" rather than "what we decided";
two-stage extraction variant added to sweep after discussion of attention-splitting
failure modes; long-file handling elevated to Phase 1 appendix after user flagged
the >1MB web-research MCP wiki file as a stress test that might reveal architectural
findings (file-as-unit vs segment-as-unit).

### Next
- **Phase 1 topic-extractor spike.** Write the structured-output extraction prompt
  + runner script. Warm models via `warm_model` MCP tool before batch. Run the
  sweep (5-6 models × 8 files + long-file appendix). Score against the 11-dim
  rubric. Pick winner. Document in `retrieval/phase1-results.md` and
  `retrieval/phase1-long-file-findings.md`. Do not advance to Phase 2 unless
  weighted quality ≥ 2.2.
- **Phase 2 VRAM co-residence probe** (qwen3:14b + bge-m3 on 12GB card) is required
  before locking the embedding choice; if eviction happens during query-time ops,
  drop to `mxbai-embed-large`.
- Open PR for `feature/ltg-phase0` → master.
- Still open: PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with
  LTG; read claude-code `services/mcp/normalization.ts` before next MCP refactor;
  Layer 4 stragglers; registry hot-reload; server.py refactor.

---

## 2026-04-13 - Session 51: Smart RAG research + Latent Topic Graph concept & plan

### Context
Resumed on `feature/gemma3-benchmark`, then branched to `feature/smart-rag-research`.
User wanted a shared content-linking substrate across 4 consumers (career chatbot,
Claude Code, web-research, llm repo) — not a one-size RAG.

### What Was Done
- **Research cluster (commit d51cb42):** 7 sources reviewed, per-file notes written
  under `docs/research/smart-rag-*.md` with ref keys `rag-*`; hub at
  `ref:smart-rag-research`. `.claude/index.md`, `.memories/{QUICK,KNOWLEDGE}.md` updated.
- **Latent Topic Graph (commit 38a5bad):** synthesized research into named construct.
  - Concept paper `docs/research/latent-topic-graph.md` (`ref:concept-latent-topic-graph`)
  - 10-phase plan `docs/plans/2026-04-13-latent-topic-graph-implementation.md`
    (`ref:plan-latent-topic-graph`) with plan-v2 integration table
  - plan-v2 task 7.11 promoted from "vanilla RAG" to cross-cutting LTG substrate
- Web-research MCP tested live (`research_url`, qwen3:14b, ~46s).

### Decisions Made
- **Files are containers, not nodes.** Topics are primary; file-to-file is derived aggregate.
- **Anchor stratification:** `ref:KEY` = confidence 1.0 anchors; LLM edges carry provenance.
- **Build once in llm repo; federate to consumers.** One retriever, per-domain wikis.
- **Do not implement in this session** — concept + plan only; next session executes Phase 0+1.

### Next
- Execute LTG plan Phase 0 (decisions) → Phase 1 (topic-extractor spike).
- Open PR for `feature/smart-rag-research` → master.
- Separate pending: PR for `feature/gemma3-benchmark`.

---

## 2026-04-09 - Session 50: Gemma 3 benchmark + Claude Code source research

### Context
Resumed on master (clean). User brought two news items: Claude Code source leaked via npm
sourcemap, and Google's Gemma 3 / TurboQuant. Session focused on investigating both and
storing findings durably.

### What Was Done
- **Research stored:** `docs/ideas/claude-code-python-port.md` — covers all 3 cloned repos
  (claude-code TS source, claude-code-sourcemap, open-multi-agent); key files to read flagged
- **Gemma models pulled:** `gemma3:12b` (8.1GB) and `gemma3:27b` (17GB) via Ollama
- **models.yaml:** added gemma3:12b + gemma3:27b entries (15 base models now)
- **Personas cloned** via copy_persona from my-go-q25c14 / my-python-q25c14:
  - `my-go-g3-12b`, `my-python-g3-12b` (active)
  - `my-go-g3-27b`, `my-python-g3-27b` (inactive — benchmarked, too slow)
- **Benchmarks (3 prompts, 2 languages):**
  - gemma3:12b: ~31 tok/s, IMPROVED on all; 3-4× faster than qwen2.5-coder:14b
  - gemma3:27b: 3.2 tok/s, timeout on ALL tasks even warmed
- **record-verdicts.py:** added `--verdicts A,I,R --notes "p1|p2|p3"` for non-interactive
  use (Claude Code terminal has no TTY; interactive `input()` hits EOFError)
- **Gemma 4:** not on Ollama as of 2026-04-09; revisit ~2 weeks
- **Deferred:** `add_model` MCP tool (automate models.yaml entry creation)
- **.memories/ updated:** QUICK (root, personas, benchmarks) + KNOWLEDGE (root, benchmarks)
- **Branch:** `feature/gemma3-benchmark`, 3 commits (feat + 2x chore)

### Decisions Made
- gemma3:12b = new speed tier: same IMPROVED quality as 14B, 3-4× faster; best for iterative tasks
- gemma3:27b = not viable on RTX 3060: dense partial offload slower than MoE at same total size
  (dense pays PCIe bandwidth on every layer; MoE only activates ~3B params per token)
- Claude Code `services/mcp/normalization.ts` → read before any MCP server refactor
- Claude Code `services/autoDream/consolidationPrompt.ts` → read before improving session-handoff quality
- open-multi-agent (MIT, 3 deps): defer until web-research multi-agent phase; local model pattern
  via `provider: 'openai', baseURL: 'http://localhost:11434/v1'` verified with Gemma 4 / Qwen 3

### Next
- Open PR for `feature/gemma3-benchmark` → master
- Phase 3 chatbot (source code awareness)
- Explore `claude-code/src/services/mcp/normalization.ts` before next MCP refactor
- Gemma 4 on Ollama: check availability ~2026-04-23
- Layer 4 stragglers (Phase 3 frontier judge, claude-desktop insights 4.6)

---

## 2026-04-03 - Session 49: Chatbot Phase 2 — LLM routing + error handling

### Context
Resumed on `feature/smart-chatbot`; created new branch `feature/chatbot-phase2` for all new work this session.

### What Was Done
- **Phase 2 LLM-as-router**: `_build_section_index()` parses all `*-knowledge.md` into flat sections; `_route_sections()` makes a non-streaming Groq call to select up to 3 relevant sections per question; `_enrich_prompt()` appends them to the system prompt
- **Test suite built**: 48 unit tests with synthetic fixtures (`tests/fixtures/context/`), `conftest.py` mocking HF/Gradio/Anthropic, `_make_hf_exc()` helper matching Groq's real nested `{"error": {...}}` format
- **Error handling overhaul**: `_parse_hf_error()` (structured, via `exc.response.json()`), `_retry_after()` (parses `Xh/Xm/Xs` wait formats, retries short waits only), `_classify_error()` (user-friendly messages with wait time for quota errors), `_with_retry()` wrapper used by both routing and main call
- **Groq rate-limit fixes**: TPD daily limit handling with human-readable wait ("about 2 hours"); Claude backend skips Groq routing entirely
- **Debug logging**: `[routing]` and `[respond_hf]` prints + `career_chat_log` alias for log tailing
- **PR #26** opened: `feature/chatbot-phase2` → master

### Decisions Made
- Routing capped at 3 sections (not 6) to stay under Groq's 12K TPM — routing call ~4K + enriched prompt ~9K would exceed limit
- `_with_retry`: one retry on `rate_limit_exceeded` with wait ≤ 60s; daily/hourly quota (long waits) returns None → user gets specific message instead
- Claude backend skips `_route_sections` — avoids burning Groq TPD quota, Claude doesn't need a separate routing call
- Section content truncated to 600 chars in `_enrich_prompt` to control token cost
- `_make_hf_exc` uses Groq's real nested format `{"error": {...}}` — discovered via production log (`body_keys=['error']`)

### Feedback captured (memory)
- Ollama retry protocol: REJECTED → improve prompt + second model, not straight to Claude
- Ollama workflow: always first; write tests first; send full files not slices
- Don't revisit previously validated decisions without new evidence

### Next
- Merge PR #26 to master
- Deploy to HF Spaces (`career_chat_upload_hf`) to test Phase 2 live
- Review `.memories/` PRs in expenses + web-research repos
- Merge PR #21 (persona MCP tools)
- Phase 3 chatbot: source code awareness (file index + targeted reads)

---

