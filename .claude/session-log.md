# Session Log

**Current Layer:** Deferred infra (clearing backlog — items 2, 3, 4 complete this session)
**Current Session:** 2026-03-07 — Session 39: Verdict capture fixes + deferred infra sweep
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`

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
- Push `feature/ref-integrity-checker` and open PR → master
- Commit CRLF normalization + session-log update
- Optional: fix expense repo issues found by checker (run with `--root ~/workspaces/expenses/code`)
- Optional: `git config core.hooksPath .githooks` to activate pre-commit hook locally
- Remaining open deferred tasks: hook-based auto-resume, user-config backup,
  Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix

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

## 2026-02-28 - Session 37: Recontextualization + ref_lookup inference observation

### Context
First session in expense-reporter after scaffolding bootstrap. No code changes — session was
diagnostic/reflective. Effort level: medium.

### Observed behavior: emergent cross-repo inference via ref_lookup

During recontextualization, Claude called three tools in parallel:
1. `Read` → memory file (didn't exist yet)
2. `Bash` → `resume.sh` (expense repo's current status)
3. `mcp__ollama-bridge__ref_lookup("current-status")` ← the interesting one

**The inference chain that led to call 3:**
- CLAUDE.md (expense repo) flags a two-repo setup: "MCP thin wrapper lives in the LLM infra repo"
- The `ollama-bridge` MCP server is described as the LLM repo's tooling
- Therefore: calling `ref_lookup` via that MCP server = querying the LLM repo's index
- Therefore: `current-status` from that tool = "the other repo's view of cross-repo state"

The inference was directionally correct and the call returned useful triangulating data.
**But it was fragile:** it only worked because the LLM repo's `current-status` block happened
to contain notes about the expense repo (written during session 36). If that convention
weren't maintained, the call would have returned purely LLM-repo-internal state.

**The real limitation:** `ref_lookup` is intra-repo by design. Cross-repo usefulness was
a side effect of content, not tool capability. Logged as deferred task in tasks.md:
`ref_lookup` could accept an optional `path` param to make cross-repo lookups explicit.

**Why this matters for training data / agent design:**
The inference pattern (MCP server identity → repo scope → content scope) is a legitimate
form of context-window reasoning about tool semantics. The fragility is worth noting:
agents that reason about tool scope from indirect signals (server name, CLAUDE.md mentions)
can produce correct-but-lucky results. Making the tool's scope explicit in its description
would eliminate the ambiguity.

### Next
- No tasks advanced this session
- Next in THIS repo: 5.8 (MCP thin wrapper) — blocked until 5.1–5.7 complete in expense repo
- Tasks 5.1–5.7 are tracked here but executed in `~/workspaces/expenses/code/`

---

## 2026-02-27 - Session 36: Portable Scaffolding + Expense Repo Bootstrap

### Context
Resumed from session 35 (all Layer 5 blockers resolved). Before starting 5.1, implemented the
two-repo workflow plan: make this repo's `.claude/` scaffolding portable, then bootstrap the
expense-reporter repo with it as the first consumer. Full plan executed across both repos.

### What Was Done

**Phase 1 — LLM repo (branch: `feature/portable-scaffolding`, commit: `cab902c`):**
- `resume.sh`: replaced hardcoded key hints with dynamic `ref-lookup.sh list` discovery.
  Any new `<!-- ref:KEY -->` block auto-appears with zero maintenance.
- `docs/scaffolding-template.md`: created reusable 10-step bootstrap guide describing directory
  structure, file purposes, ref:KEY two-tier convention, session log format, tool dependencies.
- `~/.claude/.mcp.json`: global MCP config — ollama-bridge now available in every Claude Code
  project, not just this repo. LLM repo `.mcp.json` kept as harmless redundancy.
- `tasks.md`: added two-repo workflow note under Layer 5 header.
- `session-context.md`: updated `current-status` ref block for session 36.

**Phase 2 — Expense repo scaffolding (branch: `feature/claude-code-scaffolding`, commit: `7c49e75`):**
- `.claude/tools/`: copied resume.sh, ref-lookup.sh, rotate-session-log.sh (fully portable).
- `.claude/skills/session-handoff/SKILL.md`: copied session-handoff skill.
- `CLAUDE.md`: project identity, Go structure, workflow rules, local model rules (try-local-first),
  domain facts (BR date/decimal format), resume guide.
- `.claude/index.md`: knowledge index with ref:go-structure, ref:testing, ref:classification,
  ref:indexing-convention blocks; classification data table, archive table, tools table.
- `.claude/session-context.md`: ref blocks for user-prefs, current-status, resume-steps,
  active-decisions (domain boundary, classification strategy, Go conventions).
- `.claude/session-log.md`: Session 1 entry with pre-history summary (Phases 1–11, 190+ tests).
- `.claude/tasks.md`: Layer 5 tasks 5.1–5.8 verbatim from plan-v2.md + pre-work status.
- Verified: `resume.sh` in expense repo finds 7 ref keys dynamically, zero config required.

**Phase 3 — Expense repo data & doc migration (same branch, commit: `ed055a1`):**
- `data/classification/`: 8 algorithm docs copied from `~/workspaces/expenses/auto-category/`
  (tracked); 15 personal data JSONs/CSVs also copied (gitignored).
- `docs/archive/`: 21 Desktop-era planning docs moved via git rename (history preserved).
- `docs/archive/transients/`: 12 root transient files moved (gitignored subfolder, per user).
- `.claude/settings.local.json`: backed up Windows Git Bash permissions to `.claude/local/`;
  replaced with WSL2-appropriate permissions (go test/build/run/vet, resume.sh, ref-lookup.sh).
- `.gitignore`: added `data/classification/*.json|csv`, `.claude/local/`, `docs/archive/transients/`.
- Verified: `git add -n data/classification/` confirms only 8 docs staged (no personal data).
- Verified: `cd expense-reporter && go test ./...` — all 190+ tests still passing.

### Decisions Made
- **Two-repo workflow is now live:** Feature work (5.1–5.7) in expense repo; MCP wrapper (5.8) in this repo.
- **Global MCP config pattern:** `~/.claude/.mcp.json` is the right place for tools needed in all projects; project-level `.mcp.json` kept for project-specific overrides.
- **Transient files → gitignored subfolder:** `docs/archive/transients/` pattern — move one-time scripts/reports there instead of tracking them or deleting them.
- **`confusion_analysis.json` gitignored** — user couldn't confirm whether it contains real expense descriptions; safe default.
- **`~/workspaces/expenses/auto-category/` left in place** — `data/classification/` is a copy, not a move.

### Next
- **Layer 5.1 (expense repo):** Verify `feature_dictionary_enhanced.json` + `training_data_complete.json`
  are in `data/classification/`; document their JSON schema in `.claude/index.md`
- **Layer 5.2 (expense repo):** `classify` command — 3-field input → Ollama HTTP → structured JSON → top-N subcategories
- **PRs to merge:** `feature/portable-scaffolding` (LLM repo) + `feature/claude-code-scaffolding` (expense repo)

---

