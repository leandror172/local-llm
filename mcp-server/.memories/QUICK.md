# mcp-server/ — Quick Memory

*Working memory for the MCP bridge server. Keep under 30 lines.*

## Status

Operational, system-wide availability. **18 tools** exposed to Claude Code (verified
2026-07-21 by decorator site, not by `grep -c "@mcp.tool"` — that returns 19 because one
hit is a docstring). **408 tests green** (`make test`); live P4 judge-gate acceptance is a
separate, deliberate non-test target — `make accept-p4`, real Ollama calls.
All tools verified, call logging active. Server is the integration layer for all 3 repos.

## Architecture

Python/FastMCP server, stdio transport (JSON-RPC 2.0 over stdin/stdout).
Claude Code spawns it as a subprocess — no network ports, pure local IPC.
Single async HTTP client (httpx) with connection pooling via lifespan pattern.

## Persona Routing (for MCP development work)

Use `my-mcp-q25c14` for MCP tool modifications (signatures, docstrings, return contracts).
Use `my-python-q25c14` for pure Python helpers (data flow, async patterns, path logic).
Both share `qwen2.5-coder:14b` base — no warm_model call needed when switching between them.

## Tool Catalog

ask_ollama, generate_code, summarize, classify_text, translate,
list_models, warm_model, query_personas, detect_persona, build_persona,
create_persona, copy_persona, ref_lookup, patch_file,
submit_run, run_status, run_result, cancel_run
(18 total; last 4 = oficina async runs; CLI parity via `oficina` entry point + `watch-run.sh`)

## Key Patterns

- **Server-side file context** — reads files on server, injects into prompt (zero Claude token cost)
- **Ref context injection** — `refs: list[str]` + `refs_root: str | None` on ask_ollama and generate_code; server resolves ref keys via ref-lookup.sh, prepends as `<refs>` block (zero Claude token cost; any folder with `<!-- ref:KEY -->` markers accepted)
- **Output to file** — `output_file: str | None` on ask_ollama and generate_code; writes response to disk (relative paths from REPO_ROOT); `output_only=True` returns compact status instead of content (defers verdict to file inspection)
- **patch_file** — server-side exact string replace on a file; same semantics as Edit tool (uniqueness check, replace_all flag); zero Claude read cost; atomic write via tmp+rename
- **Language routing** — auto-selects best persona per language from registry
- **Call logging** — every call → JSONL, keyed by `call_id` + `tool` (T-105); `prompt_hash` is a content address, NOT an identity. New fields appear only after the bridge subprocess restarts. Detail: KNOWLEDGE.md § "Call Logging for DPO"
- **Cold-start management** — warm_model pre-loads into VRAM, in-flight tracking prevents mid-request eviction
- **Debug logging** — opt-in structured JSONL at `/tmp/ollama-bridge.jsonl`, gated by `OLLAMA_BRIDGE_LOG_LEVEL` env var (DEBUG/INFO/WARNING/ERROR); per-process `client_id` so multiple bridges can share one log file; `scripts/which-bridge.sh` lists live bridges with banner info

## oficina/ submodule (P1–P4)

`src/ollama_mcp/oficina/` — detached local-model run substrate. **Module map: the source tree
in `README.md`**, which is current and names every module's job. Vision, phase history and
as-built invariants: `docs/vision/coding-delegate/` (QUICK § "How we got here" + KNOWLEDGE).

mcp-server-side facts that live nowhere else:

- **The `client.py` seam.** `chat` mints `call_id` onto `ChatResponse`, and gained
  `num_predict` (T-91) and `fetch_model_descriptor` (POST `/api/show`, T-112). Identity rules
  and the restart caveat: KNOWLEDGE.md § "Call Logging for DPO".
- **`worker.py` is deliberately not the home for shared machinery** — KNOWLEDGE.md
  § "What `worker.py` is not".
- `service.py` is ONE impl layer under both the 4 MCP tools and the `oficina` CLI.
- Loop and worker tests use the executable-spec DSL (`ref:test-executable-spec`).
- `.claude/tools/ollama-cache-report.py` — per-run prefix-reuse report over `calls.jsonl`
  (duration-not-count rule).

Suite 408; live gate `make accept-p4` (currently T-129/T-130 → PR #87).

## Deeper Memory -> KNOWLEDGE.md

- **Transport Choice** — stdio over HTTP, rationale
- **File Context Design** — why server reads files instead of Claude
- **Call Logging Format** — JSONL schema, `call_id`/`tool` identity, DPO data connection
- **In-Flight Safety** — warm_model eviction guards
- **Debug Logging Design** — JSONL schema, reserved-fields filter, banner shape, where it's wired in
- **What `worker.py` is not** — why transport and report own their own modules
- **oficina conventions** — atomic writes, `run_id` in calls.jsonl, P2 deferral resolutions
