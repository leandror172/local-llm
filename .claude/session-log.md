# Session Log

**Current Layer:** MCP server feature execution (ollama-bridge Plans 1-3) — side track before LTG Phase 2
**Current Session:** 2026-05-22 — Session 63: MCP Plan 1 executed (refs param + personas + constraints)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`

---

## 2026-05-22 - Session 63: MCP Plan 1 executed (refs param + personas + constraints)

### Context
Resumed on `feature/ollama-bridge-refs-param` branch (created this session). Plans 1-3 were written in session 62. This session executed Plan 1 (refs param) in full TDD cycle, created `my-mcp-q25c14` persona, added SOLID + scope constraints to 14B coding personas, updated Plans 2+3 with session findings, and completed all memory updates.

### What Was Done
- **Plan 1 (refs param) — fully executed:**
  - `pyproject.toml` updated with pytest + pytest-asyncio dev deps
  - `mcp-server/tests/conftest.py` written (repo_root, ref_dir, mock_ollama fixtures)
  - `mcp-server/tests/test_refs.py` — 10 tests (unit + integration), all green
  - `_resolve_ref_key` + `_build_refs_block` helpers added to `server.py`
  - `refs`/`refs_root` params added to `ask_ollama` and `generate_code` (signature + docstring + body)
  - Live acceptance tests passed: `ltg-embedding`, `ltg-extractor`, missing-key fail-fast, combined refs+context_files
  - Minor fix: error message uses stdout (not stderr) from `ref-lookup.sh` on non-zero exit
- **New persona `my-mcp-q25c14`** — qwen2.5-coder:14b with MCP-specific system prompt; created via skill
- **SOLID + scope constraints** added to `my-mcp-q25c14`, `my-python-q25c14`, `my-python-q3-14b` Modelfiles + re-registered with Ollama
- **Deferred task:** backfill same constraints to all remaining coding personas → `docs/tasks/backfill-persona-constraints.md`
- **Plans 2+3 updated** with session findings: `_resolve_output_path` shared helper (Step 1 of Plan 2), atomic write via `os.replace`, pre-validate before Ollama call, few-shot sibling prompting pattern for Step 3, `my-mcp-q25c14` persona routing noted
- **Memory updates:** `mcp-server/.memories/QUICK.md` (persona routing), `mcp-server/.memories/KNOWLEDGE.md` (refs param design), root `.memories/QUICK.md` (session 63 status), cross-session memory (few-shot sibling pattern, warm_model same-base rule)
- **Local model verdicts this session:** conftest 1, test_refs 1, `_resolve_ref_key` 2, `_build_refs_block` 1, `ask_ollama` modification 0/0/0 (all 3 models failed → wrote directly), `generate_code` modification 1 (my-mcp-q25c14, fixed `if refs and refs_root` → `if refs`)

### Decisions Made
- **MCP vs Python persona split:** `my-mcp-q25c14` for tool signature/docstring/return contract; `my-python-q25c14` for pure helpers (controller/service analogy)
- **No warm_model when switching same-base personas** — `my-mcp-q25c14` and `my-python-q25c14` share qwen2.5-coder:14b; switching evicts and reloads the same model
- **Few-shot sibling pattern** — when two parallel tools need the same change, do the first manually then pass it as context for the second local model call; validated: jumped from verdict-0 to verdict-1
- **Scope-creep constraint** — "MUST NOT modify code outside explicitly requested scope" added to all 14B coding personas after observing all three models drop surrounding logic when asked for targeted additions
- **`_resolve_output_path` extracted as shared helper** in Plan 2 (Step 1) so Plan 3 doesn't inline divergent logic

### Next
- **Continue `feature/ollama-bridge-refs-param` branch — execute Plan 2** (`output_file` param): read `ref:mcp-output-file-advisor-notes`, implement `_resolve_output_path` + `_write_output_file`, TDD (`test_output_file.py`), then modify `ask_ollama` + `generate_code`. Plan: `docs/plans/ollama-bridge-output-file.md`.
- **Then Plan 3** (`patch_file` tool): `docs/plans/ollama-bridge-patch-file.md`.
- **Then LTG Phase 2** — `docs/plans/ltg-phase2-implementation.md` (`ref:ltg-phase2-plan`).

---

## 2026-05-22 - Session 62: ollama-bridge 3-feature plans

### Context
Side session before executing LTG Phase 2. User proposed augmenting `generate_code`/`ask_ollama` with a `refs` parameter that resolves `<!-- ref:KEY -->` markers server-side (zero Claude token cost). This grew into a set of three related MCP server features planned together.

### What Was Done
- **Designed and wrote 3 implementation plans** (all in `docs/plans/`, all with TDD test specs and ref markers):
  1. `ollama-bridge-refs-param.md` — `refs: list[str]` + `refs_root: str | None` params on `ask_ollama` and `generate_code`; server runs `ref-lookup.sh` per key via subprocess, prepends as `<refs>…</refs>` block. Any folder with `<!-- ref:KEY -->` markdown markers qualifies as `refs_root`.
  2. `ollama-bridge-output-file.md` — `output_file: str | None` + `output_only: bool` params; server writes response to disk (relative paths from `REPO_ROOT`); `output_only=True` returns compact status instead of content; verdict still required.
  3. `ollama-bridge-patch-file.md` — new `patch_file` MCP tool; server-side exact string replace (Python `str.replace`); same semantics as Edit tool (uniqueness check, `replace_all` flag); zero Claude read cost.
- **Added TDD specs to all plans:** pyproject.toml dev deps (`pytest`, `pytest-asyncio`, `asyncio_mode = "auto"`), shared `conftest.py` fixture spec (repo_root, ref_dir, mock_ollama), and 8–9 per-plan test cases with explicit assertions.
- **Added `<!-- ref:KEY -->` markers** to every major section of all 3 plans, with shared prefixes: `mcp-refs-param-*`, `mcp-output-file-*`, `mcp-patch-file-*`. Wildcard fetch (`ref:mcp-patch-file-*`) returns the full plan. Verified 21 new keys visible via `ref-lookup.sh --list`.
- **Plan 3 cross-references Plan 2:** `mcp-patch-file-reading` refs `mcp-output-file-decisions` — demonstrates inter-plan ref lookup working as designed.

### Decisions Made
- **`refs_root` = any folder** (not repo-specific) — any folder with `*.md` files using `<!-- ref:KEY -->` markers qualifies; `ref_lookup` tool already had `path` param, consistent.
- **Fail-fast on missing ref keys** — same contract as `context_files` path errors; partial injection would be worse than no injection.
- **`output_only=True` defers verdict, doesn't skip it** — Claude must still give a 0/1/2 verdict after inspecting the written file.
- **`patch_file` uses Python `str.replace` server-side** — no subprocess, no regex; same exact-string semantics as the Edit tool; file read → replace → write, all in-process.
- **TDD across all 3 plans** — test files written before implementation; key non-tautological tests include: `test_resolve_ref_key_root_is_respected` (proves `--root` actually forwarded), `test_build_refs_block_fails_fast_on_missing_key` (proves no partial block returned), `test_multiline_old_string` (guards against naive single-line implementation).

### Next
- **Execute the 3 plans** — start with Plan 1 (refs param); implement TDD: setup pyproject.toml + conftest.py, write tests, run red, implement, run green. Plans ready: `ref:mcp-refs-param-*`, `ref:mcp-output-file-*`, `ref:mcp-patch-file-*`.
- **Then execute LTG Phase 2** — `docs/plans/ltg-phase2-implementation.md` (`ref:ltg-phase2-plan`); unchanged from session 61.

---

## 2026-05-20 - Session 61: VRAM probe + Phase 2 implementation plan

### Context
Resumed with all prior PRs merged (master clean). Two goals: clear the Phase 2 gate (VRAM co-residence probe for bge-m3 + qwen3:14b) and write a detailed Phase 2 implementation plan ready to execute next session.

### What Was Done
- **Updated tracking files:** Corrected stale open-PR references in `ref:current-status` and `.memories/QUICK.md`; retrieval QUICK.md stale "freeze pending" line fixed.
- **VRAM co-residence probe:** Wrote `retrieval/run-vram-probe.sh` (4-stage script: preflight, sequential load, co-residence check, 5-round interleaved stress). Fixed `set -euo pipefail` + SIGPIPE bug in preflight (grep exits early on first match → `ollama list` gets SIGPIPE → pipefail propagates 141; fix: capture output first, grep the variable).
- **Probe result:** WARN verdict — bge-m3 evicts qwen3:14b at load time (11,384 + 1,200 MiB > 12,288 MiB), but 0 query-time evictions across 4 warm rounds, avg infer 3,559 ms. **bge-m3 locked. Sequential constraint established.**
- **Stored probe findings:** Updated `retrieval/DECISIONS.md` (`ref:ltg-embedding` probe marked complete with actual VRAM figures); updated root `.memories/QUICK.md` and `retrieval/.memories/QUICK.md`.
- **Created `retrieval/.memories/KNOWLEDGE.md`:** New semantic memory file with 3 ref blocks: `ref:ltg-vram-probe` (full probe findings + SIGPIPE gotcha), `ref:ltg-phase1-summary` (consolidated extractor findings), `ref:ltg-phase0-decisions-index` (all 8 Phase 0 decisions in summary table). QUICK.md trimmed to pointer + "Deeper Memory" section.
- **Discussed Phase 2 implementation choices:** Corpus validation scope (8-file first), input source (reuse Phase 1 JSONL, filter to winning models), embedding text (description-only; A/B deferred), script structure (3 separate scripts + wrappers).
- **Wrote `docs/plans/ltg-phase2-implementation.md`:** Full execution plan with: required reading (7 files in order), decisions in force, Phase 1 JSONL input format + routing rule, LanceDB schema (with `"vector"` naming rationale), per-script CLI/logic/API spec for embed.py + store.py + inspect.py, bash wrapper pattern, 4-probe acceptance test table, `.gitignore` additions, post-completion memory update checklist, deferred items table.
- **Registered:** plan in `.claude/index.md`; `retrieval/` added to `ref:memory-files`; Retrieval/LTG Tools table in `ref:bash-wrappers` updated.
- **Committed:** `feature/ltg-phase2-plan` branch, commit `16a9483`, 10 files.

### Decisions Made
- **8-file validation first** (Option A) before full corpus expansion — validates pipeline on trusted, scored extractions before widening scope.
- **Reuse Phase 1 JSONL** (filter to winning models) rather than re-extracting — the scored outputs are the ground truth; fresh extraction is unreviewed and takes ~10 min.
- **Description-only embedding** to start; A/B test (description+spans) deferred as explicit future task with trigger: probe query underperforms.
- **3 separate scripts** (`embed.py`, `store.py`, `inspect.py`) with individual bash wrappers — composable, independently runnable.
- **bge-m3 locked** — sequential constraint (no parallel embed+infer) applies to embed.py only; indexing pipeline is inherently sequential anyway.

### Next
- **Execute `docs/plans/ltg-phase2-implementation.md`** — start by reading the Required Reading section (7 files listed in order). Then write `embed.py`, `store.py`, `inspect.py` and their bash wrappers. Run the 4-probe acceptance test to close Phase 2.

### Notable
- **`set -euo pipefail` + `grep -q` SIGPIPE trap:** `cmd | grep -q pattern` fails when grep exits on first match and sends SIGPIPE to `cmd`. With pipefail, the pipe returns 141 (SIGPIPE), not grep's 0. Appears as a false negative on the first matching entry in the output. Fix: `OUT=$(cmd); echo "$OUT" | grep -q pattern`. A generic bash gotcha worth remembering for any probe/filter script.

---

## 2026-05-16 - Session 60: Consolidate Ollama directives into ollama-scaffolding overlay

### Context
Side-track from the LTG line. User observed that the expense and web-research repos carry Ollama-usage directives in their feedback memories that are absent from the `ollama-scaffolding` overlay master files. Goal: promote the selected directives into the overlay so every repo it installs into shares them. Work done on a new branch `feature/ollama-scaffolding-directives`.

### What Was Done
- **Six directives consolidated** into `ollama-scaffolding` from expense/web-research feedback memories: D1 prompt style (describe behavior, not implementation), D2 always-attempt (never skip on past `0` verdicts), D3 serialization (serial by default; 3+ parallel exceeds VRAM; different-model parallel worst), D4 retry budget (3-4 attempts before escalating), D5 caller inclusion in `context_files`, D6 few-shot-before-delete.
- **Mechanism conversion:** the retry-patterns reference doc moved from a `templates:` entry (created once, never propagates) to a `files:` entry (hash-based COPY/SKIP/overwrite — re-installs deliver updates).
- **Renamed** `local-model-retry-patterns` → `local-model-conventions` (ref key + file) to reflect the broader before/after-call scope; doc restructured into "Before you call" / "After you call". All references updated, including this repo's own `ref:` block in `session-context.md` and `CLAUDE.md`.
- **Two installer bugs fixed in `overlays/lib/actions.py`:** (1) `handle_files` forced `executable=True` — replaced with extension-based detection (`_is_executable_payload`) + explicit `_apply_mode`, because the `/mnt/i` drvfs mount reports every file as 777 so mode-preservation is unreliable; (2) `handle_merge_sections` round-tripped through `read_text`/`write_text`, silently normalizing a CRLF target to LF — added `_read_text_eol`/`_write_text_eol` to preserve line endings.
- **Propagated** to expense (`4ed7a89`) and web-research (`4bd07d5`, amended to restore CRLF after the bug was found+fixed). Both got the v1→v2 overlay marker update deterministically — no AI mode.
- **3 commits:** llm branch `feature/ollama-scaffolding-directives` — `3c0e2f4` (consolidation) + `548ca07` (line-ending fix); expense/web-research one each.

### Decisions Made
- **`files:` over markers for the overlay doc** — it is 100% overlay-owned with zero per-repo customization, so the template "user-managed" contract bought nothing; `files:` propagates on re-install with no version bump. A standalone marked-file mechanism was considered and deferred.
- **Renamed the ref key** — the doc outgrew "retry patterns" once pre-call directives were added; `local-model-conventions` covers calling + verdict + retry.
- **chmod by extension, not filesystem mode** — drvfs makes the executable bit meaningless; extension is the only reliable signal without a git dependency.
- **Amended the web-research commit** (user-approved) rather than a follow-up commit — it was unpushed and the EOL-normalization noise would otherwise complicate merges with in-progress work in that repo.

### Next
- Resume the LTG Phase 2 line — VRAM co-residence probe (qwen3:14b + bge-m3 ≈ 12 GB). This session did not touch LTG.
- New deferred items added to `ref:deferred-infra`: AI-merge-path CRLF preservation; ollama-scaffolding overlay review-for-improvements.
- Open PR for `feature/ollama-scaffolding-directives`.

### Notable
- **WSL drvfs gotcha:** Windows drives mounted in WSL (`/mnt/*`, 9p/drvfs) report every file as `-rwxrwxrwx` and ignore `chmod`. Any tool that copies files off such a mount and trusts `os.access` or mode-preservation will mis-set permissions. `git ls-files -s` still shows the correct mode (git stores it).
- The deterministic v1→v2 marker replace in `handle_merge_sections` is mode-independent — AI mode is only used for *first* insertion when no marker exists. "Don't use AI mode" was satisfied automatically for both target repos.

---

