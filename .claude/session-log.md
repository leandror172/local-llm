# Session Log

**Current Layer:** Overlay system — implementation complete, PR open
**Current Session:** 2026-03-11 — Session 40: Overlay system implementation
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`

---

## 2026-03-11 - Session 40: Overlay system implementation (Phases 1–4 complete)

### Context
Resumed from session 39b where the overlay system was designed but not implemented.
Branch: `feature/overlay-system`. All four phases executed in a single session.

### What Was Done

**Phase 1 — Directory structure + manifest:**
- `overlays/ref-indexing/` with `manifest.yaml`, `files/`, `templates/`, `sections/`, `prompts/`
- `sections/claude-md-ref-rules.md` — Scenario A (full content, not pointer)
- `templates/index.md.tmpl`, `sections/gitignore-lines.txt`, `APPLY.md`, `README.md`
- Decided: `§` heading pointer vs fuller content in CLAUDE.md → chose fuller (Scenario A)
- Decided: `.sh` wrappers redundant — `./script.py` is whitelistable in Claude Code directly

**Phase 2 — Installer (`install-overlay.py`):**
- All action handlers: files (sha256 diff), templates (no-overwrite), append_lines (idempotent), merge_sections (marker-driven versioning), manual_if_exists
- AI merge: prompt→schema→plan→apply pipeline; Ollama structured output (`format` param)
- Fixed: stream:false timeout (→ stream:true); num_ctx 4096→8192; XML prompt delimiters; EOFError on stdin; dry-run fires AI call (moved short-circuit before call)
- `--backup` / `--no-backup` flag (BooleanOptionalAction, default on)
- Refactored: prompts extracted to files (`merge-section.txt` → `merge-plan.txt`); JSON schema in `merge-plan-schema.json`
- Planner approach: AI returns `{insert_after_line, delete_ranges, reasoning}` — script applies deterministically, always adds markers itself
- `[WARN]` when AI inserts without deleting; `[DELETE]` record per range applied

**Backends — declarative config (`ai-backends.yaml`):**
- `BackendType` + `SchemaMode` enums (`str, Enum` mixin, Python 3.10 compat)
- `Backend` ABC with `is_available()` + `call()` abstract methods
- `OllamaApiBackend` (format_param, +think suffix), `CliBackend` (stdin, JSON envelope), `ClaudeApiBackend` (tool_use)
- `CliBackend`: CLAUDECODE env var detection (nested session guard); `--output-format json` envelope parsing; `_extract_json()` strips markdown fences
- `--backend ID` (by id from yaml or 'auto'), `--model` override, `--debug` flag

**Split into `lib/` package:** `report.py`, `backends.py`, `planner.py`, `actions.py`
Install entry point reduced to ~90 lines.

**Phase 3 — Tests:**
- overlay-test (fresh): all SKIP/COPY, idempotency confirmed
- expense repo (retrofit): qwen3:14b+think → correct merge with markers; claude-code (haiku) → perfect result (delete lines 5–9 exact, replace old section cleanly, interactive confirm worked)
- Model comparison (test-merge-plan.py): 7 variants tested; think:false → zero deletes; think:true → identifies delete range; 30b-a3b+think most accurate; haiku best via prompt_injection

**Phase 4 — Docs:** `overlays/README.md` authoring guide

**Deferred tasks added:** Python 3.10→3.12 upgrade via uv (enables StrEnum)

### Decisions Made
- `§` pointer vs fuller content in CLAUDE.md: chose fuller (Scenario A) — always-loaded rules are more reliable than "read on demand"
- Prompts in files, not code — independent git history, editable without touching Python
- JSON schema in separate file — same principle; passed to Ollama `format` param directly
- AI as planner (not file generator) — script owns markers and file writes; AI only decides WHERE
- Default AI model: `qwen3:14b+think` (Ollama); `haiku` (claude-code CLI)
- `str, Enum` mixin over `StrEnum` — Python 3.10 compat; upgrade deferred to tasks.md
- `lib/` split before PR — cleaner to review than monolith
- claude-code backend: prompt via stdin (not positional arg), `--output-format json` envelope, `_extract_json()` for markdown fence stripping

### Next
- Merge PR `feature/overlay-system` → master (PR opened this session)
- Merge pending PRs: #10 (token logging), #11 (verdict hooks→#10), #12 (context-files), #13 (ref-integrity)
- Resume Layer 5 in `~/workspaces/expenses/code/` (tasks 5.1–5.7: classify command pipeline)
- Overlay system follow-ups (low priority): Python 3.12 upgrade; `session-tracking` overlay candidate

---

## 2026-03-07 - Session 39: Verdict capture fixes + deferred infra sweep

### Context
Resumed from session 38. Completed verdict-capture pipeline testing (PostToolUse bug),
then swept three deferred infra tasks in one session.

### What Was Done

**Verdict capture hook pipeline — COMPLETE (PR #11):**
- Diagnosed `additionalContext` bug: PostToolUse requires `hookSpecificOutput` wrapper,
  not top-level key. Fixed `ollama-post-tool.py`.
- Diagnosed SubagentStop bug: `verdict-capture.py` used `transcript_path` (main session);
  subagent verdicts are in `agent_transcript_path`. Fixed with event-type detection.
- Hooks promoted to `~/.claude/settings.json` (user-level, fires in all Claude Code sessions).
- Deferred task added: backup `~/.claude/settings.json` + `.mcp.json` (not in any repo).
- Also discovered: `SubagentStart` hook can inject context into subagents; `updatedMCPToolOutput`
  can replace MCP tool output in PostToolUse; Claude Code docs confirmed `additionalContext`
  is documented for PostToolUse but requires correct JSON structure.
- PR #11: `feature/verdict-capture-hook` → `feature/ollama-token-logging`.

**context_files for generate_code/ask_ollama — COMPLETE (PR #12):**
- `ContextFile` Pydantic model, `_build_context_block()`, `context_files` param on both tools.
- Files read server-side; Claude pays zero tokens for file content. Absolute paths enforced.
- PR #12: `feature/context-files-param` → `master` (also includes ref_lookup cross-repo).

**ref_lookup cross-repo — COMPLETE (rides PR #12):**
- `ref-lookup.sh --root /abs/path` + `server.py ref_lookup(path=...)`.
- Validated against expense repo: finds that repo's keys, correct error on bad path.

**ref integrity checker — COMPLETE (branch: feature/ref-integrity-checker, PR pending):**
- `check-ref-integrity.py`: 4 checks (dangling refs, unclosed blocks, duplicate defs, orphans).
  Fence-aware (skips ``` blocks). Excludes `.git/`, `node_modules/`, `.venv/`. `--root` flag.
- `check-ref-integrity.sh`: thin bash wrapper.
- `.githooks/pre-commit`: gates on staged `*.md` files. Install: `git config core.hooksPath .githooks`.
- LLM repo: exit 0, 8 orphaned (expected). Expense repo: 1 dangling ref, 3 duplicate defs found.

**CRLF normalization (discovered during session-log edit):**
- `session-log.md` and other tracked `.md` files had CRLF despite `.gitattributes eol=lf`.
- Root cause: `--renormalize` only stages the LF version; doesn't update working tree.
- Fix: `sed -i 's/\r//'` to convert in-place. Applied to all tracked `.md` files.

### Decisions Made
- `hookSpecificOutput` wrapper required for PostToolUse `additionalContext` — not top-level
- User-level `~/.claude/settings.json` for hooks that must fire in all projects
- Absolute paths only for `context_files` (no cwd ambiguity)
- Repo root (not `.claude/` dir) for `--root` param — consistent with `PROJECT_ROOT` convention
- Python (not bash) for ref integrity checker — fence-aware parsing too fragile in bash pipes

### Next
- Push `feature/ref-integrity-checker` and open PR → master (done: PR #13)
- Optional: `git config core.hooksPath .githooks` to activate pre-commit hook locally
- Optional: fix expense repo issues found by checker
- Remaining open deferred tasks: hook-based auto-resume, user-config backup,
  Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix

---

## 2026-03-09 - Session 39b: Overlay system design

### Context
Continued from session 39 (same branch `feature/ref-integrity-checker`). The ref integrity
checker exposed that patterns developed in this repo (ref indexing, session tracking, ollama
scaffolding) need a portable packaging mechanism to apply to other repos like the expense reporter.

### What Was Done

**Overlay system design — COMPLETE (plan only, no implementation):**
- Defined the concept: "repo augmentation" / "project overlay" — packages of files, config
  sections, and AI-agent instructions that layer onto an existing repository
- Identified the hard problems: merge semantics for shared files (CLAUDE.md), idempotency
  via markers, detecting existing installations (retrofit), update versioning
- Designed three execution modes: manual (TODO list), AI-assisted interactive, AI-assisted
  unattended (with auto-detect backend: Ollama → `claude -p` → manual)
- Defined marker format: `<!-- overlay:NAME vN -->` / `<!-- /overlay:NAME -->` — verified
  no conflict with `<!-- ref:KEY -->` patterns in ref-lookup.sh and integrity checker
- Designed manifest format (YAML) with: files, templates, append_lines, merge_sections,
  manual_if_exists, agent_targets (Claude Code paths for v1)
- Designed structured report system: every action logged with rationale, stdout/file/JSON output
- Wrote full implementation plan: `docs/plans/overlay-system-plan.md` (4 phases)
- Chose ref-indexing as first overlay; expense repo as test target (retrofit/update case)

### Decisions Made
- `<!-- overlay:NAME vN -->` markers for managed sections in shared files (CLAUDE.md etc.)
- YAML manifest (pyyaml available; supports comments; Python installer anyway)
- Python installer (bash too fragile for parsing — ref integrity checker lesson)
- AI merge uses Ollama locally (free) with fallback to `claude -p`
- `agent_targets` block (renamed from "integrations") declares AI-tool config paths
- Files themselves are the unit for scripts (no in-file markers); markers only for sections
  injected into shared files

### Next
- **Execute the overlay system plan** (`docs/plans/overlay-system-plan.md`):
  - Phase 1: overlay directory structure + manifest + extract ref-indexing files
  - Phase 2: `install-overlay.py` with deterministic + AI-merge + report
  - Phase 3: test against expense repo (retrofit case)
  - Phase 4: document the template for future overlays

---

## 2026-03-07 - Session 38: Token logging + verdict capture hooks

### Context
Resumed from session 37 (recontextualization only). Two deferred infra items addressed:
token logging completeness (item 5) and a new PostToolUse+Stop hook pipeline for
structured verdict capture. All work on branch `feature/verdict-capture-hook`
(forked from `feature/ollama-token-logging`, which has PR #10 open to master).

### What Was Done

**Token logging (deferred item 5 — COMPLETE):**
- `ChatResponse` dataclass: added `prompt_eval_count` field (Ollama input tokens)
- `_log_call`: now records `prompt_chars`, `response_chars`, `prompt_eval_count`,
  `eval_count`, `claude_tokens_est` ((prompt+system+response chars)/4)
- `personas/lib/ollama_client.py`: return dict gains `prompt_eval_count`
- `CLAUDE.md` + `docs/scaffolding-template.md` + expense repo `CLAUDE.md`:
  verdict instruction updated — ACCEPTED/IMPROVED now require a rough mental
  chars/4 estimate inline; explicitly prohibits file reads or code execution to compute it
- Subagent test confirmed the instruction is interpreted correctly
- PR #10 open: `feature/ollama-token-logging` → master

**Branch/PR management:**
- Work branched off master: `feature/ollama-token-logging` (PR #10)
- Working branch forked from it: `feature/verdict-capture-hook` (current)
- Master has the two commits; PRs are the proper delivery path going forward

**Verdict capture hooks (PARTIALLY COMPLETE — needs testing):**
- `.claude/hooks/ollama-post-tool.py` (PostToolUse): fires after every
  `mcp__ollama-bridge__*` call; reads last `calls.jsonl` entry for `prompt_hash`;
  injects `[VERDICT prompt_hash=N]` template via `additionalContext`
- `.claude/hooks/verdict-capture.py` (Stop/SubagentStop): fires at turn end;
  scans transcript for filled VERDICT blocks; appends typed verdict records
  `{type:"verdict", prompt_hash, verdict, reason, est_claude_tokens}` to `calls.jsonl`;
  deduplicates by prompt_hash
- `.claude/settings.json`: wires PostToolUse (matcher: `mcp__ollama-bridge__.*`),
  Stop, and SubagentStop to the two scripts
- Subagent test revealed two issues: (1) SubagentStop was missing from settings.json
  (fixed in session), (2) unclear if PostToolUse `additionalContext` reaches subagent
  context — needs investigation

**tasks.md updated:**
- Deferred item 5 marked `[x]` complete
- New deferred item added: PostToolUse hook for verdict capture (this work)

### Decisions Made
- **Option C for verdict storage:** verdict records written as typed entries
  (`{type:"verdict", ...}`) in the existing `calls.jsonl` — append-only, no rewrites,
  join by `prompt_hash`. Splitting to a separate file is easy later if needed.
- **Stop + SubagentStop:** both hooks point to the same `verdict-capture.py` script.
  `SubagentStop` was added after the first subagent test revealed it was missing.
- **Token estimate in CLAUDE.md is "mental, no file reads":** subagent test confirmed
  the instruction works as intended after rewriting from "read the log" to "apply chars/4 mentally".
- **`/mcp reconnect` is the right restart path:** killing the Python process and using
  `/mcp reconnect` is the reliable way to reload server code changes; `/mcp disable`+`/mcp enable`
  does NOT kill the OS process.

### Next
- **Start by testing the hook pipeline on `feature/verdict-capture-hook`:**
  1. **Main session test (local):** call `mcp__ollama-bridge__generate_code` directly in
     the main session; verify (a) PostToolUse hook injects `[VERDICT prompt_hash=N]`
     template into context, (b) fill the template, (c) end the turn, (d) check
     `calls.jsonl` for a new `{type:"verdict", ...}` record.
  2. **Subagent test:** spawn a subagent that calls the ollama tool; verify whether
     `SubagentStop` fires and captures the verdict; separately determine if
     PostToolUse `additionalContext` reaches subagent context (it may not — if not,
     the subagent will use CLAUDE.md-trained narrative format, not the template).
  3. **Fix as needed:** if PostToolUse additionalContext doesn't reach subagents,
     decide whether to (a) accept narrative-only verdicts from subagents or (b) add
     explicit verdict instruction to subagent prompts when spawning them.
- **After hook pipeline confirmed working:** commit `settings.json` change (SubagentStop
  addition is uncommitted), push `feature/verdict-capture-hook`, open PR to
  `feature/ollama-token-logging` (not master — layered PRs).
- **Longer term:** `feature/ollama-token-logging` PR #10 → master can be merged once
  the hook work is validated.

---

