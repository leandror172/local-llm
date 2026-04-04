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

## Error Handling as Return Values (2026-02)

All tool functions catch exceptions and return error strings instead of raising.
Connection errors, model-not-found, timeouts — all become user-friendly messages.

**Rationale:** MCP tools that raise exceptions crash the server. Returning error
strings lets Claude handle the situation conversationally ("The model timed out,
let me try a different approach").
**Implication:** Claude never sees Python tracebacks — only human-readable error
descriptions. This is a deliberate UX choice, not defensive programming.
