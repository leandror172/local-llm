# Session 66 Handoff — MCP debug logging + ~ expansion fix

*Branch: `feature/ollama-bridge-patch-file-impl`. Three commits ahead of origin.*

## What happened this session

Started by re-running the `patch_file` acceptance test from session 65. The first attempt **hung for minutes with no diagnostic surface**, so we built optional structured logging so the next hang has somewhere to land. The investigation also surfaced an unrelated bug: `_resolve_output_path` never expanded `~`, silently writing files under `<repo>/~/...`.

### Commits landed (in order)

| SHA-ish | Subject |
|---|---|
| `1af8542` | feat(mcp): structured debug logging for tool-call hang diagnosis |
| (new) | feat(mcp): make logs target + watch-logs.sh prettifier |
| (new) | fix(mcp): expand ~ in _resolve_output_path |

Run `git -C /mnt/i/workspaces/llm log --oneline -5` to see exact SHAs.

### Files changed (cumulative)

- `mcp-server/src/ollama_mcp/debug_log.py` — **new**. Env-driven JSONL logger; per-process `client_id`; reserved-fields filter.
- `mcp-server/src/ollama_mcp/server.py` — `_lifespan` banner + `server_start`/`server_stop`; `tool_enter`/`tool_exit` on `patch_file`, `generate_code`, `ask_ollama`. `_resolve_output_path` now calls `.expanduser()`.
- `mcp-server/src/ollama_mcp/client.py` — `chat()` brackets the httpx `/api/chat` call with `http_post_start`/`http_post_done`/`http_post_error`.
- `mcp-server/run-server.sh` — defaults `OLLAMA_BRIDGE_LOG_LEVEL=INFO`, `OLLAMA_BRIDGE_LOG_FILE=/tmp/ollama-bridge.jsonl`.
- `mcp-server/Makefile` — **new**. `make help|logs|logs-raw|bridges`.
- `mcp-server/scripts/which-bridge.sh` — **new**. Lists live bridges with banner info.
- `mcp-server/scripts/watch-logs.sh` — **new**. `tail -F` + Python prettifier.
- `mcp-server/tests/test_patch_file.py` + `tests/test_output_file.py` — `test_tilde_in_path_expands_to_home` / `test_tilde_in_output_file_expands_to_home` regressions.
- `.mcp.json` (repo) + `~/.claude/.mcp.json` (user-level) — `env` block bumps log level to `DEBUG` for the bridge.
- `mcp-server/README.md` + `mcp-server/.memories/QUICK.md` + `mcp-server/.memories/KNOWLEDGE.md` — docs.

### Open follow-ups

- **`~/.claude/.mcp.json` is not under git.** It was edited in place with the same DEBUG env block as the repo's `.mcp.json`. If you want DEBUG only in this project, revert the user-level file manually.
- **Stale literal-`~` directory.** The earlier buggy test wrote `/mnt/i/workspaces/llm/~/workspaces/tmp/p.py`. User said they'd clean it up via Windows Explorer; check with `ls /mnt/i/workspaces/llm/~/ 2>/dev/null` — if it still exists, ask before deleting.
- **PR #37 and PR #38** (Plans 1+2 and Plan 3) were already open at session-65 handoff; this work is on the same branch. Don't push without checking with user.

---

## Verification checklist (run these first)

A fresh bridge is required to exercise the new code — the bridge running when you arrive may still be on stale code.

```bash
# 1. Confirm the last three commits are present locally.
git -C /mnt/i/workspaces/llm log --oneline -5

# 2. Run the test suite — all should be green (21 tests across patch_file + output_file).
cd /mnt/i/workspaces/llm/mcp-server && uv run --project . pytest tests/test_patch_file.py tests/test_output_file.py -v

# 3. List live bridges. The session's own bridge should appear with a real
#    client_id and a git SHA matching the latest commit. If it shows
#    "(no banner — restart with OLLAMA_BRIDGE_LOG_LEVEL=INFO)", the user
#    has not reconnected the MCP server yet — ask them to do so before testing.
make -C /mnt/i/workspaces/llm/mcp-server bridges

# 4. Start log watching in a side terminal:
make -C /mnt/i/workspaces/llm/mcp-server logs
```

If `make bridges` shows the bridge git SHA matches the head of `feature/ollama-bridge-patch-file-impl`, the bridge is current and you can proceed. If not, ask the user to reconnect the `ollama-bridge` MCP server (or restart Claude Code).

---

## Resume testing where we left off

We had run **Test 1 from `docs/plans/ollama-bridge-patch-file.md` acceptance section** and discovered the `~` expansion bug. With the fix in place, the original six scenarios in that plan still need running end-to-end against a fresh bridge.

### Original scenarios (from the plan)

Located in `docs/plans/ollama-bridge-patch-file.md` under `<!-- ref:mcp-patch-file-acceptance -->`:

1. Basic replacement — `generate_code` → `patch_file("return 1" → "return 42")`. Verify file content actually changed.
2. Not found → error string starting with `"Error:"`.
3. Non-unique → error with count in the message.
4. `replace_all=True` — all occurrences replaced.
5. Relative path resolves from `REPO_ROOT`.
6. File does not exist → error, not crash.

Also re-run **the tilde-expansion live test** that surfaced the bug:
- `generate_code(output_file="~/workspaces/tmp/p.py")` then `patch_file("~/workspaces/tmp/p.py", ...)`. After the fix, both should resolve to `/home/<user>/workspaces/tmp/p.py`. Confirm no `<repo>/~/` directory gets created.

### User's additional scenarios (quoted verbatim from this session)

The user's instruction that landed mid-investigation, to be exercised once the basic scenarios pass:

> In addition to your scenarios, run also tests with more complicated scenarios — complicated code that generates multiple lines (and likely to be wrong on 1st run), then asking to correct; also, test asking to add functionality to a code file; then, test getting complicated code generated, then you use the new patch MCP to fix the issues

Concretely, three scenario shapes to design tests around:

1. **Multi-line generation + correction loop.** Ask `generate_code` for something non-trivial (e.g., "a Python function that parses an ISO-8601 duration string into seconds, handling weeks/days/hours/minutes/seconds, with input validation"). Inspect the result. If wrong (likely on first run for a 7-8B local model), pass it back as `context_files=[generated]` with a correction prompt. Evaluate via the standard verdict scale (2/1/0) and record `~tokens-saved` estimate inline.
2. **Add functionality to existing file.** Take a file that already exists (preferably one of our just-written ones), pass it via `context_files`, ask for a new function to be appended or an existing function to be extended. Use `output_file` to overwrite. Then verify by reading the file (with `rtk read`, not Read tool, per user preference).
3. **Generate complicated, then `patch_file` to fix surgical issues.** Generate something multi-line and intentionally-likely-flawed. Identify *one specific* problem (e.g., wrong return type, missing edge case, off-by-one). Use `patch_file` (not `generate_code` again) to fix just that — exercising the "zero Claude read cost" claim. Verify the fix landed in the file via `rtk read`.

**For all three:** the user has memory `feedback_local_model_test_context.md` — when generating pytest files, pass `pyproject.toml` as context so the local model picks up `asyncio_mode=auto` instead of defaulting to `@pytest.mark.asyncio`.

### What to watch in `make logs`

For each scenario, the expected event chain (with the new DEBUG logging) should be:

```
tool_enter  generate_code  (output_file=..., language=python, ...)
http_post_start  model=...  url=/api/chat
http_post_done   model=...  status=200  body_bytes=N  ms=N
tool_exit   generate_code  ok=True  content_chars=N  ms=N
tool_enter  patch_file     (path=..., replace_all=False, ...)
tool_exit   patch_file     ok=True  resolved=/abs/path  count=1  ms=<1
```

Diagnostic rule from `mcp-server/.memories/KNOWLEDGE.md` (Debug Logging section):

- `tool_enter` without matching `tool_exit` → hang inside the tool body
- No `tool_enter` after a prior `tool_exit` → hang in MCP stdio or Claude Code's client (not the bridge)
- `http_post_start` without `http_post_done` → Ollama wedged on the request

---

## Files to read for context (priority order)

| Priority | File | Why |
|---|---|---|
| 1 | `mcp-server/.memories/QUICK.md` | Working-memory index for the bridge |
| 2 | `mcp-server/.memories/KNOWLEDGE.md` § "Debug Logging — Structured JSONL (2026-05, session 65)" | Design rationale + reserved-fields filter, banner shape |
| 3 | `mcp-server/Makefile` + `mcp-server/scripts/watch-logs.sh` + `mcp-server/scripts/which-bridge.sh` | The diagnostic toolbox |
| 4 | `docs/plans/ollama-bridge-patch-file.md` § `mcp-patch-file-acceptance` | Original six acceptance scenarios |
| 5 | `mcp-server/src/ollama_mcp/debug_log.py` | ~100-line module, reads quickly |
| 6 | `mcp-server/src/ollama_mcp/server.py:155-175` | The fixed `_resolve_output_path` |
| 7 | `~/.claude/projects/-mnt-i-workspaces-llm/memory/MEMORY.md` | Cross-session user preferences (rtk read, ~/workspaces/tmp for scratch, verdict scoring, etc.) |

---

## Test environment notes

- **Scratch files:** Use `~/workspaces/tmp/`, never `/tmp/` (per `feedback_use_workspaces_tmp.md`).
- **File reading during tests:** Use `rtk read <file>` not the Read tool or `cat` (per `feedback_use_rtk_read.md`).
- **Verdict scoring after `generate_code` calls:** record verdict 0/1/2 + reason + `~N est. Claude tokens saved` per the `local-model-conventions` pattern. Hooks expect this format.
- **Persona for MCP work:** `my-mcp-q25c14` (tool signatures, docstrings) vs `my-python-q25c14` (helpers); both share `qwen2.5-coder:14b` base — no `warm_model` needed when switching. See `project_few_shot_sibling_prompting.md`.

---

## Commands cheat-sheet

```bash
# Watch logs (start in a side terminal before running tests)
make -C /mnt/i/workspaces/llm/mcp-server logs

# Filter to one bridge once you know its client_id
make -C /mnt/i/workspaces/llm/mcp-server logs CLIENT=abcd1234

# List live bridges
make -C /mnt/i/workspaces/llm/mcp-server bridges

# Run the full bridge test suite
cd /mnt/i/workspaces/llm/mcp-server && uv run --project . pytest -v

# Read a file (token-efficient)
rtk read /mnt/i/workspaces/llm/mcp-server/src/ollama_mcp/debug_log.py

# Check this branch's commits ahead of origin
git -C /mnt/i/workspaces/llm log --oneline origin/feature/ollama-bridge-patch-file-impl..HEAD
```
