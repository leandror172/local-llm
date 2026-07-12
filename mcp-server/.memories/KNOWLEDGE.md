# mcp-server/ — Knowledge (Semantic Memory)

*MCP bridge server decisions. Read on demand.*

## stdio Transport Choice (2026-02)

Uses stdio (JSON-RPC 2.0 over stdin/stdout) instead of HTTP transport.
Claude Code spawns the server as a subprocess and pipes messages directly.

**Rationale:** No port conflicts, no authentication, no network overhead.
The server only serves one client (Claude Code), so HTTP's multi-client
benefits are unnecessary overhead.
**Implication:** Server lifecycle is tied to the Claude Code session.
Each session gets a fresh server process with clean state.

## Server-Side File Context (2026-02)

When tools accept `context_files` parameter, the server reads those files
itself and injects the content into the Ollama prompt. Claude never sees
the file content in its own context window.

**Rationale:** Sending file content through Claude's context and then into
the Ollama prompt would cost Claude tokens twice — once to receive, once
to forward. Server-side reading eliminates this entirely.
**Implication:** `generate_code` with 3 context files costs the same Claude
tokens as without — only Ollama sees the file content.

## Call Logging for DPO (2026-03)

Every Ollama call appended to `~/.local/share/ollama-bridge/calls.jsonl`.
Schema: timestamp, model, prompt (hashed + full), response, eval_count,
eval_duration_ms, total_duration_ms, temperature, think flag, format flag.
Estimated Claude token cost included: `(prompt_chars + response_chars) / 4`.

**Rationale:** DPO fine-tuning needs (prompt, response, quality_signal) triples.
The call log provides prompt + response; verdicts and evaluator scores provide
the quality signal. Passive collection during normal work.
**Implication:** Logging failures are silently swallowed — never break a tool call
for observability. Full content toggleable via `OLLAMA_LOG_FULL_CONTENT`.

## In-Flight Tracking for warm_model (2026-03)

warm_model evicts the current model to load a new one. But evicting while
another tool call is mid-generation would corrupt that response. An in-process
dict tracks which models have active requests (mark_inflight / mark_complete).

**Rationale:** Discovered via "evict then 404" bug — warm_model validated the
model existed, evicted the current one, but the new model wasn't loaded yet.
Fixed with `_check_model_exists()` pre-validation.
**Implication:** Single-session only (in-process dict). Cross-session coordination
(e.g., two Claude Code sessions sharing one GPU) would need file-based locking.

## Language Routing via Registry (2026-02)

generate_code auto-selects the best persona for a given programming language.
Routing scans the persona registry for keyword matches in role text + persona name.
Specialist (name match like "my-go-q3") beats generalist (role mentions "Go").
Qwen3-based personas preferred over Qwen2.5 on tie.

**Rationale:** Fast, offline, no LLM cost for routing. Works even if registry
file is missing (falls back to default model).
**Implication:** Adding a new language-specific persona automatically improves
routing — just register it with the right keywords.

## Refs Param Design — Server-Side Ref Resolution (2026-05, session 63)

`ask_ollama` and `generate_code` accept `refs: list[str]` and `refs_root: str | None`.
The server calls `_resolve_ref_key(key, root)` (subprocess to `ref-lookup.sh`) for each
key, gathers results in parallel via `asyncio.gather`, then wraps them in `<refs>…</refs>`
and prepends before the prompt. Zero Claude token cost — ref content never passes through
Claude's context.

**Prompt ordering:** `<refs>` → `<context_files>` → `[Language hint]` → user prompt.
Each layer wraps outward: content_files first, refs outermost.

**Key design choices:**
- `root=None` omits `--root` arg (lets shell script use its own default) — matches existing `ref_lookup` tool
- Non-absolute `refs_root` returns error immediately (fail-loud, not silent resolve)
- Fail-fast on missing key: `asyncio.gather` + exception wrapping; no partial block returned
- Shell script output includes HTML comment markers (`<!-- ref:KEY -->`); no extra labels added

**Implication:** Any folder with `*.md` files using `<!-- ref:KEY -->` convention works.
Not limited to the LLM repo. Validated in acceptance testing with `ltg-embedding` and `ltg-extractor`.

## Error Handling as Return Values (2026-02)

All tool functions catch exceptions and return error strings instead of raising.
Connection errors, model-not-found, timeouts — all become user-friendly messages.

**Rationale:** MCP tools that raise exceptions crash the server. Returning error
strings lets Claude handle the situation conversationally ("The model timed out,
let me try a different approach").
**Implication:** Claude never sees Python tracebacks — only human-readable error
descriptions. This is a deliberate UX choice, not defensive programming.

## Output File Design — Server-Side Write (2026-05, session 64)

`ask_ollama` and `generate_code` accept `output_file: str | None` and `output_only: bool = False`.
Path resolution via `_resolve_output_path` (shared helper, reused by `patch_file` in Plan 3).
Atomic write via `_write_output_file`: writes to `{path}.tmp`, then `os.replace` — never `write_text` directly.

**Key design choices:**
- Path pre-validated at top of function (before Ollama call) — fail-fast avoids wasting 5–30s GPU time on a bad path
- `_resolve_output_path` extracted as a standalone helper so Plan 3 (`patch_file`) reuses it without drift
- `output_only=True` returns `"Written N bytes to /abs/path"` — compact status for large files Claude doesn't need inline; verdict still required (read via `context_files` if needed)
- `output_only` without `output_file` is silently ignored — returns full content as normal
- Encoding: UTF-8 throughout, consistent with `_build_context_block` and all other file I/O

**Implication:** The edit loop pattern — `generate_code(output_file=...)` then `generate_code(context_files=[written_file])` — is now zero-overhead on both ends: write costs no extra Claude tokens, subsequent read passes through the server.

<!-- ref:mcp-keep-alive -->
## keep_alive Default for KV Prefix Reuse (2026-06)

`chat()` passes `keep_alive="15m"` in every Ollama payload. Inherited by all tools
(`generate_code`, `ask_ollama`, `summarize`, etc.) without per-tool changes.

**Rationale:** Ollama's default keep_alive is 5 minutes — too short for retry windows
(a 120s timeout + immediate retry can land outside 5m) and for multi-call sessions
where the same `context_files` or `refs` are passed repeatedly. llama.cpp automatically
reuses KV states for any leading prefix that matches the cached slot; `keep_alive`
controls how long that slot stays alive. 15 minutes covers normal interactive use.

**What this enables:**
- Retry after timeout: model still in VRAM → prefix (system prompt + stable docs)
  not recomputed — only the new/diverged tail is processed.
- Same `context_files` across two calls: identical leading bytes → cache hit on
  all doc tokens.

**What this does NOT do:** `keep_alive` does not pin tokens against sliding-window
eviction during a single long call (that's `num_keep`). For typical `generate_code`
workloads (32K ctx, output << 32K), sliding-window eviction does not occur.

Full research: `docs/findings/ollama-kv-prefix-cache-findings.md`
(`ref:ollama-kv-prefix-cache`, `ref:ollama-explicit-cache-api`)
<!-- /ref:mcp-keep-alive -->

## oficina Atomic-Write Conventions (2026-07-12, P1 T1–T5)

Two write disciplines coexist in `src/ollama_mcp/oficina/`, chosen per file role:
- **Append-only ledger (`events.jsonl`):** raw `"a"`-mode single-line writes — NOT
  tmp+replace. Torn-tail tolerance depends on partial lines being detectable in place;
  `_append` repairs the tail (byte truncate to last valid line) before every write.
- **Write-once files (`spec.json`) and queue markers:** tmp + `os.replace`/`os.rename`
  (the established `_write_output_file` pattern).

**Rationale:** a replace-based ledger write would lose the whole file on a crash between
tmp-write and replace of a large append; raw append bounds the damage to one torn line,
which the read/repair path already handles.
**Implication:** pydantic became an explicit `pyproject.toml` dep when T8 added the
`oficina` console entry point (2026-07-12).

## oficina run_id in calls.jsonl (2026-07-12, T6)

`OllamaClient.chat(run_id=...)` threads an additive, `dict.get()`-safe `run_id` field
into `_log_call` — present only for oficina runs, so the existing DPO readers
(`ollama-stats.py`, `ollama-verdicts.py`) ignore it. This is the ONE deliberate
`client.py` seam the substrate required (acceptance #6, verdict-protocol continuity);
revert = remove the param from both signatures + the 3-line conditional.

## Debug Logging — Structured JSONL (2026-05, session 65)

The server can emit a structured JSONL log to disk for hang diagnosis and
post-mortem inspection. Gated by `OLLAMA_BRIDGE_LOG_LEVEL` (one of `DEBUG`,
`INFO`, `WARNING`, `ERROR`) and `OLLAMA_BRIDGE_LOG_FILE` (defaults to
`/tmp/ollama-bridge.jsonl`). Implemented in `src/ollama_mcp/debug_log.py`,
called from `_lifespan` (banner + start/stop), `chat()` in client.py
(httpx start/done/error), and the bodies of `patch_file`, `generate_code`,
`ask_ollama` (tool_enter/tool_exit with per-tool fields).

**Rationale:** A multi-minute hang on `patch_file` (pure file I/O, no Ollama
involvement) revealed we had no way to localize the wedge — was it the tool
body, the FastMCP request loop, the stdio transport, or Claude Code's MCP
client? Stderr `print()` calls in `_lifespan` already existed but disappeared
into Claude Code's MCP subsystem; nothing was recorded per-tool. A small
structured log file changes "we don't know" into "the missing event tells you."

**Key design choices:**
- **Append-only shared file, demultiplexed by `client_id`.** Multiple bridges
  (one per Claude Code session) write to the same file. POSIX guarantees
  atomic writes up to `PIPE_BUF` (4 KB) on `O_APPEND` — our JSON lines are
  ~200-400 bytes, well inside that. No lock files, no rotation per process,
  just `grep '"client_id": "abcd1234"'` to filter.
- **Reserved-fields filter.** The JSONL formatter strips any user-supplied
  field that collides with reserved names (`t`, `level`, `ev`, `client_id`,
  `pid`). Without this, calling `info("server_start", level="DEBUG")` would
  have shown `level=DEBUG` instead of the record's actual severity. Belt and
  suspenders: the banner dict was also renamed `level → log_level` so the two
  concepts never share a word.
- **`fields` dict over `**kwargs` at the emit boundary.** Public helpers
  (`debug/info/error`) take `**fields`, but `_emit(level, event, fields)`
  takes a dict — so a user field named `level` or `event` can never collide
  with a positional parameter (the original splat-based design crashed
  immediately when banner was forwarded into `info`).
- **Lazy formatting via `logger.isEnabledFor(level)` short-circuit.** Field
  dicts are built unconditionally (cheap), but JSON serialization only runs
  when the level is enabled. Production cost at default `WARNING` is one
  level check per call.
- **Defaults set in `run-server.sh`, overridden via `.mcp.json` env block.**
  The script defaults `OLLAMA_BRIDGE_LOG_LEVEL=INFO` (banner + errors always
  recorded). The repo's `.mcp.json` env block bumps to `DEBUG` for live hang
  diagnosis; flip back by editing one file.

**Where it's wired (deliberately narrow):**
- `_lifespan` — `server_start` (with full banner: pid, ppid, git SHA, branch,
  client_id, log_level, log_file) and `server_stop`.
- `client.py:chat()` — `http_post_start` / `http_post_done` (with status and
  body bytes) / `http_post_error` (ERROR level).
- `server.py` — `tool_enter` / `tool_exit` on **only** `patch_file`,
  `generate_code`, `ask_ollama` (the three involved in the session-65 hang).
  The other 9 tools are deliberately uninstrumented — add coverage when a
  specific tool needs investigation, not preemptively.

**Implication:** `scripts/which-bridge.sh` reads back the banner from the
log to enrich `pgrep` output. The diagnostic playbook becomes mechanical:
`tail -f` the log, reproduce the bug, and the missing event tells you which
half wedged. `tool_enter` without `tool_exit` → server-side; no `tool_enter`
after a previous tool returned → MCP stdio or Claude Code's client.
