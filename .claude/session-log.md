# Session Log

**Current Layer:** LTG Phase 2 — Embedding + Storage
**Current Session:** 2026-05-27 — Session 70: LTG Phase 2 design decisions (no implementation yet)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`

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

## 2026-05-26 - Session 67: patch_file acceptance testing + error-handling analysis

### Context
Resumed from session 66 handoff. MCP server had been fully restarted (computer reboot). Goal: live-verify the `~` expansion fix and run the full acceptance suite for the `patch_file` tool.

### What Was Done
- **Verified bridge freshness:** `server_start` banner in `/tmp/ollama-bridge.jsonl` confirmed git SHA `238873a` — new code running.
- **Tilde expansion fix — live end-to-end:** `generate_code(output_file="~/workspaces/tmp/p.py")` wrote to `/home/leandror/workspaces/tmp/p.py` (not `<repo>/~/...`); `patch_file("~/...")` resolved and patched correctly; error messages for missing files show the resolved absolute path (fix order confirmed correct).
- **6 original acceptance scenarios:** all pass — basic replace + content verification, not-found error string, non-unique error with count, `replace_all=True`, relative path from REPO_ROOT, missing file error.
- **3 user-requested complex scenarios:**
  1. **Multi-line + correction loop:** ISO-8601 duration parser — local model produced correct core regex but missed `P1W` week format. Fixed via `patch_file` (week fast-path + `not any(match.groups())` guard). Smoke test 5/5 cases pass.
  2. **Add functionality via `context_files` + `output_file`:** Added `format_duration(seconds) -> str` to the same file. `context_files` preserved all prior patches verbatim. Zero-duration edge case broken (`format_duration(0)` raised ValueError → should return `"PT0S"`); fixed via `patch_file`. 8/8 smoke tests pass incl. round-trips.
  3. **Complex generation + surgical patch_file fix:** LRU cache via OrderedDict — correct LRU semantics, but key type hardcoded to `str`. Three `patch_file` calls changed key type to `Hashable` and removed unused imports. 6/6 behavioral assertions pass incl. tuple key.
- **All 5 `generate_code` verdicts:** all `1` (improved) — consistent pattern: correct core logic, unrequested `logging.basicConfig()` side effect + catch-log-reraise noise.
- **Error-handling analysis discussion:** identified two Python antipatterns in local model output, then extended to Java and Go equivalents. User confirmed this is language-specific and worth a dedicated session.
- **`docs/ideas/persona-error-handling-conventions.md`** — full analysis: what triggers the antipatterns, why each is wrong per language, proposed Modelfile directive language for Python/Java/Go, implementation plan, and where delegation is and isn't trustworthy.
- **`docs/plans/ollama-bridge-patch-file-acceptance-results.md`** — complete test results: 10/10 scenarios, per-scenario smoke test tables, verdicts, corrections made.
- **Updated `.claude/index.md`** with entries for both new docs.
- **Updated `.claude/tasks.md`** with new deferred task: per-language error handling + logging conventions for persona Modelfiles.
- **Updated PR #38** with full test plan including live acceptance results, tilde fix, and link to results doc.
- **2 commits this session:** `53c8566` (error handling doc + task) and `e3405b3` (acceptance results + index).

### Decisions Made
- **Per-language error-handling conventions:** flagged as a dedicated session (not done inline). Python rule: `getLogger(__name__)` only, no `basicConfig()`, no catch-log-reraise same type. Java: no catch-log-rethrow. Go: `fmt.Errorf("context: %w", err)`, no log-and-return mid-library. See `docs/ideas/persona-error-handling-conventions.md`.
- **"Programming by proxy" limit acknowledged:** the directive should eliminate noise, not prescribe which errors to handle — that remains the model's judgment call.
- **Pair error-handling Modelfile work with backfill-persona-constraints session** — same class of Modelfile audit work.

### Local Model Verdicts
All 5 calls to `qwen2.5-coder:14b` via `my-python-q25c14`:
- ISO-8601 parser: **1** (~700 est. Claude tokens saved) — missing week support, unused imports
- `format_duration`: **1** (~1200 est. Claude tokens saved) — zero-duration bug, dead code
- LRU cache: **1** (~650 est. Claude tokens saved) — key type too narrow, unused imports
- Scenario 1 seeding (`get_answer`): **1** (~150 est. Claude tokens saved) — logging boilerplate only
- Scenario 3 seeding (`foo/bar`): **2** (~150 est. Claude tokens saved) — output_only write, accepted

### Next
- **Push the 2 session-67 commits** (ahead of origin on `feature/ollama-bridge-patch-file-impl`).
- **Merge PR #37** (Plans 1+2: refs param + output_file) into master.
- **Merge PR #38** (pre-work fixes + Plan 3 patch_file + logging + ~ fix + acceptance results) into master. Base is `feature/ollama-bridge-output-file` — merge #37 first.
- **LTG Phase 2** — `docs/plans/ltg-phase2-implementation.md` (`ref:ltg-phase2-plan`). Read Required Reading section (7 files) first, then implement `embed.py`, `store.py`, `inspect.py` + bash wrappers.

---

## 2026-05-25 - Session 66: MCP debug logging + ~ expansion fix

### Context
Restart after session 65 handoff. Goal: live-test the new `patch_file` MCP tool from Plan 3. First `patch_file` call hung for minutes with no diagnostic surface (pure file I/O wedged unexplained), so the session pivoted into building optional structured logging — then used that logging on the next attempt to find and fix an unrelated `~`-expansion bug in `_resolve_output_path`.

### What Was Done
- **Structured debug logging infra** (`feat(mcp): structured debug logging for tool-call hang diagnosis`, `1af8542`):
  - `mcp-server/src/ollama_mcp/debug_log.py` — env-driven (`OLLAMA_BRIDGE_LOG_LEVEL`, `OLLAMA_BRIDGE_LOG_FILE`); JSONL formatter with reserved-fields filter (`t/level/ev/client_id/pid` cannot be shadowed by user fields); per-process `client_id` (random hex) + `pid` stamped on every record; `fields`-dict-over-`**kwargs` at the emit boundary so user keys can never collide with positional params.
  - `_lifespan` emits stderr banner (`pid/ppid/git/branch/client_id/log_level/log_file`) and INFO `server_start`/`server_stop` events.
  - Instrumented (explicitly, no decorator — user chose Option B) `patch_file`, `generate_code`, `ask_ollama` with DEBUG `tool_enter`/`tool_exit` events; `client.py:chat()` brackets the httpx POST with `http_post_start/http_post_done/http_post_error`.
  - `run-server.sh` defaults `OLLAMA_BRIDGE_LOG_LEVEL=INFO`; both `.mcp.json` files (repo + `~/.claude/.mcp.json`) bump to DEBUG via `env` block.
  - `mcp-server/scripts/which-bridge.sh` — lists live bridges with banner info (python3-based, no jq dependency).
  - Docs: README (env vars table, "Debug Logging" subsection, hang-diagnostic playbook in Troubleshooting); `.memories/QUICK.md` (Key Patterns bullet + Deeper Memory pointer); `.memories/KNOWLEDGE.md` (full design-decision section with rationale, key choices, deliberate-scope note).
- **Make/watch helpers** (`feat(mcp): make logs target + watch-logs.sh prettifier`, `3bb2e46`):
  - `mcp-server/Makefile` — `help/logs/logs-raw/bridges` targets; `make logs CLIENT=abcd1234` filters to one bridge; `LOG_FILE=/path` overrides location.
  - `mcp-server/scripts/watch-logs.sh` — `tail -F` + Python prettifier that columnizes time/level/event and shows per-event fields inline.
  - README updated to recommend `make logs` over raw `tail -F`.
- **`~` expansion fix** (`fix(mcp): expand ~ in _resolve_output_path`, `f48c3ca`):
  - Live-test surfaced: `generate_code(output_file="~/workspaces/tmp/p.py")` + `patch_file("~/...")` were treating `~` as a literal directory character (Claude passes strings unprocessed by any shell, so no expansion happens), silently writing to `<repo>/~/workspaces/tmp/p.py`.
  - Fix: `Path(path).expanduser()` at top of `_resolve_output_path`; also fixed the REPO_ROOT-join branch to use the *expanded* `p` rather than re-using the raw `path` string (a latent bug that would have re-dropped any expansion).
  - TDD: wrote red regression test in `test_patch_file.py`, ran (red), applied fix, ran (green). Then added analogous test to `test_output_file.py` for symmetry. Both call sites share `_resolve_output_path`, so one fix covers both.
  - 21/21 tests green across `test_patch_file.py` + `test_output_file.py`.
- **Live hang verification:** the original `patch_file` hang did NOT reproduce on the fresh, debug-logged bridge. Strongly suggests it was specific to whichever stale bridge served the prior session, not structural — but we now have the instrumentation to catch it if it returns.
- **Handoff doc:** `.claude/handoff-session-66.md` (161 lines) with verification checklist, resume-testing plan, file-reading priorities, and the user's three additional testing scenarios quoted verbatim.

### Decisions Made
- **Log levels**: Python stdlib `DEBUG/INFO/WARNING/ERROR` (skipped TRACE per user "we might not need that many"). All levels structurally available; only `debug/info/error` helpers exposed since `warning` had no current call site.
- **Option B explicit logging** over `@traced_tool` decorator (user chose) — tool body shows exactly when logs fire; small `_done()` closure pattern in `patch_file`/`ask_ollama` dedupes the timing field without adding magic.
- **Shared log file across bridges, demultiplex by `client_id`** — POSIX `O_APPEND` guarantees atomic writes up to `PIPE_BUF` (4 KB); our ~200-400 byte JSON lines are well inside. No file locking needed, no per-PID file rotation.
- **Reserved-fields filter on the JSONL formatter** — `t/level/ev/client_id/pid` are pinned to formatter-authoritative values; user fields with the same name are silently dropped. Belt and suspenders alongside renaming the banner's `level → log_level` to avoid the original collision.
- **Default INFO in `run-server.sh`, DEBUG via `.mcp.json` env block** — bridge always records the startup banner + Ollama errors; cranking to DEBUG (per-tool timing) is a one-file edit.
- **Deliberately narrow instrumentation** — only the three tools involved in the hang got `tool_enter`/`tool_exit`. The other nine MCP tools are uninstrumented; add coverage when a specific tool needs investigation rather than preemptively.
- **`~/.claude/.mcp.json` edited in place** — out of any git tree; user-level DEBUG env applies whenever Claude Code falls back to user config. User aware; can revert manually.

### Local Model Verdicts
- `generate_code(prompt="Write a Python function foo() that returns 1...")` during the live-test seeding: verdict **2** (~60 est. Claude tokens saved) — exact function requested, no extras.

### Next
- **Reconnect the `ollama-bridge` MCP server** so a fresh bridge picks up the `~` expansion fix (the in-memory bridge code is still stale).
- **Live-verify the fix**: re-run `generate_code(output_file="~/workspaces/tmp/p.py")` + `patch_file("~/workspaces/tmp/p.py", ...)`; confirm both resolve under `/home/leandror/workspaces/tmp/` and no `<repo>/~/` directory is created.
- **Run the original 6 acceptance scenarios** from `docs/plans/ollama-bridge-patch-file.md` (`ref:mcp-patch-file-acceptance`).
- **Run the user's three additional scenarios** (quoted verbatim in `.claude/handoff-session-66.md`): multi-line generation + correction loop; adding functionality to an existing file via `context_files` + `output_file`; complex generation then `patch_file` surgical fix.
- **PR #38** — three commits ahead of origin (`1af8542`, `3bb2e46`, `f48c3ca`); user will push manually.

---

### Context
Continued from session 64 on branch `feature/ollama-bridge-output-file`. Goal: execute Plan 2 advisor pre-work fixes, then implement Plan 3 (`patch_file` tool). User also chose Option A for fence-stripping (auto-strip markdown fences in `generate_code` output).

### What Was Done
- **Read advisor review files** before starting: `docs/plans/advisor-review-session-64.md`, `docs/plans/ollama-bridge-plans-advisor-notes.md`, `.claude/overlays/local-model-conventions.md`.
- **Pre-work commit `fc48526`** on `feature/ollama-bridge-patch-file` (new branch off `feature/ollama-bridge-output-file`):
  - Deleted stray `retrieval/test_output.py` (never committed, wrong dir — LTG artifact area)
  - Fixed double path resolution: `ask_ollama`/`generate_code` now pass pre-resolved `_pre` (Path) directly to `_write_output_file`, avoiding a second `_resolve_output_path` call
  - `_resolve_output_path` no longer calls `.resolve()` prematurely; `.resolve()` now happens inside `_write_output_file` AFTER `mkdir()` for accurate canonicalization of symlinked parents
  - `_write_output_file` updated to accept `pathlib.Path | str` (fast path for pre-resolved callers)
  - Test 2: restored `assert result == "mocked-model-output"` as first assertion
  - Test 4: replaced `any(ch.isdigit() ...)` with `assert "Written" in result` + `assert str(output_file) in result` + `assert str(len("mocked-model-output".encode())) in result`
  - Test 9: added `assert "[Language: python]" in mock_ollama.chat.call_args.kwargs["prompt"]`
  - 19/19 tests green
- **Plan 3 branch** `feature/ollama-bridge-patch-file-impl` (off pre-work branch):
  - `_strip_code_fences()` helper added to `server.py` (strips ` ```lang\n` opening and `\n``` ` closing fences from model output); applied to `generate_code` only (not `ask_ollama`)
  - `test_patch_file.py` generated via `my-mcp-q25c14` local model (verdict 1 — fixed read-before-write order bug in tests 3+4); fence artifacts stripped + corrections applied directly
  - `patch_file` MCP tool implemented via `my-mcp-q25c14` (verdict 2 — accepted as-is); inserted at end of `server.py`
  - 10 new tests: basic replace, count in return, not-found, non-unique error with "found 2 times", replace_all × 2 occurrences, replace_all × 1 occurrence, multiline old_string, missing file, relative path, UTF-8 round-trip
  - 29/29 tests green
  - Docs: `mcp-server/.memories/QUICK.md` (tool count 10→12, catalog, key patterns); `overlays/ollama-scaffolding/files/local-model-conventions.md` + `.claude/overlays/local-model-conventions.md` (output_file + patch_file sections added)
  - Commit `d206e6e`. PR #38 created (base: `feature/ollama-bridge-output-file`).

### Decisions Made
- **Auto-strip fences in `generate_code`** (Option A) — `generate_code` always writes code files; fences are never valid. Implemented as `_strip_code_fences()` using `splitlines(keepends=True)` to preserve line endings.
- **Haiku handoff file instead of direct session-handoff** — user running on extra usage; session 65 handoff delegated to a cheaper Haiku session via this instruction file.

### Local Model Verdicts
- `test_patch_file.py` generation: `TIMEOUT_COLD_START` × 2 (not verdicts), then verdict **1** (improved — read-before-write order bug in tests 3+4 fixed inline + markdown fences stripped; ~2000 est. Claude tokens saved)
- `patch_file` implementation: verdict **2** (accepted as-is; ~1250 est. Claude tokens saved)

### Next
- **Merge PR #37 (Plans 1+2) and PR #38 (pre-work + Plan 3) into master.**
- **LTG Phase 2** — `docs/plans/ltg-phase2-implementation.md` (`ref:ltg-phase2-plan`). Read Required Reading section (7 files) first, then implement `embed.py`, `store.py`, `inspect.py` + bash wrappers.

---

