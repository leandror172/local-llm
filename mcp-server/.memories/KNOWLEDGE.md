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
