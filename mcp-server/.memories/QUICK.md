# mcp-server/ — Quick Memory

*Working memory for the MCP bridge server. Keep under 30 lines.*

## Status

Operational, system-wide availability. 12 tools exposed to Claude Code.
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
ref_lookup, patch_file, submit_run, run_status, run_result, cancel_run
(last 4 = oficina async runs; CLI parity via `oficina` entry point + `watch-run.sh`)

## Key Patterns

- **Server-side file context** — reads files on server, injects into prompt (zero Claude token cost)
- **Ref context injection** — `refs: list[str]` + `refs_root: str | None` on ask_ollama and generate_code; server resolves ref keys via ref-lookup.sh, prepends as `<refs>` block (zero Claude token cost; any folder with `<!-- ref:KEY -->` markers accepted)
- **Output to file** — `output_file: str | None` on ask_ollama and generate_code; writes response to disk (relative paths from REPO_ROOT); `output_only=True` returns compact status instead of content (defers verdict to file inspection)
- **patch_file** — server-side exact string replace on a file; same semantics as Edit tool (uniqueness check, replace_all flag); zero Claude read cost; atomic write via tmp+rename
- **Language routing** — auto-selects best persona per language from registry
- **Call logging** — every call → JSONL (prompt, response, model, latency, tokens)
- **Cold-start management** — warm_model pre-loads into VRAM, in-flight tracking prevents mid-request eviction
- **Debug logging** — opt-in structured JSONL at `/tmp/ollama-bridge.jsonl`, gated by `OLLAMA_BRIDGE_LOG_LEVEL` env var (DEBUG/INFO/WARNING/ERROR); per-process `client_id` so multiple bridges can share one log file; `scripts/which-bridge.sh` lists live bridges with banner info

## oficina/ submodule (P1 async substrate)

`src/ollama_mcp/oficina/` — detached local-model run substrate (vision:
`docs/vision/coding-delegate/`). Primitives done (T1–T5): `ledger` (event-sourced JSONL,
offset=line-index, repair-on-append), `ids`+`store` (run-dir layout under an injected
root; default `~/.local/share/oficina/` wired later), `intake` (pydantic schema + named
rejection rules), `fifo` (disk queue `queue/<epoch-ms>-<run_id>`), `workerproc` (pidfile
arbitration + detached spawn), `worker` (lazy-daemon loop), `service` (ONE impl layer
under both the 4 MCP tools and the CLI), `retention`, `cli`, `config` (`OFICINA_ROOT`
override; default `~/.local/share/oficina/`). Tests: `tests/oficina/`. **P1 complete —
live acceptance 6/6 (2026-07-12).** pydantic is now an explicit dep.
**P2 evaluated loop (session 120, PR #76):** `parser`/`prompt`/`workspace`/`evaluator`/`loop`
modules for `kind:function`. **Reviewed + hardened session 121** (10 correctness fixes;
invariants + deferred T-95–T-99 in the coding-delegate KNOWLEDGE.md + `ref:oficina-p2-review-deferred`).
**Simplified session 122** (suite 241): `errors.TriadError` base (Assembly/Evaluation errors),
`workspace.target_relpath`, table-driven intake unknown-keys, Budgets-from-schema, `run()`
decomposed. **T-95/T-99 RESOLVED (b):** per-call transport = `worker._chat_generation` +
`_cold_start_grace` (shared by single-shot + `loop.default_coder`; `spec.timeout_s` honored);
`auto_verdict` is LEDGER-only — P4 DPO joins ledger↔`calls.jsonl` on `run_id`.
Loop tests use the executable-spec DSL (`ref:test-executable-spec`).
**Session 123: T-96/T-97/T-98 RESOLVED** (branch `feature/oficina-p2-deferrals`, suite 260):
refs fallback chain + fail-loud `RefsDropped`; retention `workspace` prune class (TTL =
run-dir mtime); worktree-relative path scoping. Decision records: `ref:oficina-p2-review-deferred`.

## Deeper Memory -> KNOWLEDGE.md

- **Transport Choice** — stdio over HTTP, rationale
- **File Context Design** — why server reads files instead of Claude
- **Call Logging Format** — JSONL schema, DPO data connection
- **In-Flight Safety** — warm_model eviction guards
- **Debug Logging Design** — JSONL schema, reserved-fields filter, banner shape, where it's wired in
