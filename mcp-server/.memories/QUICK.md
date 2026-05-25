# mcp-server/ — Quick Memory

*Working memory for the MCP bridge server. Keep under 30 lines.*

## Status

Operational, system-wide availability. 10 tools exposed to Claude Code.
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
list_models, warm_model, query_personas, detect_persona, build_persona

## Key Patterns

- **Server-side file context** — reads files on server, injects into prompt (zero Claude token cost)
- **Ref context injection** — `refs: list[str]` + `refs_root: str | None` on ask_ollama and generate_code; server resolves ref keys via ref-lookup.sh, prepends as `<refs>` block (zero Claude token cost; any folder with `<!-- ref:KEY -->` markers accepted)
- **Language routing** — auto-selects best persona per language from registry
- **Call logging** — every call → JSONL (prompt, response, model, latency, tokens)
- **Cold-start management** — warm_model pre-loads into VRAM, in-flight tracking prevents mid-request eviction

## Deeper Memory -> KNOWLEDGE.md

- **Transport Choice** — stdio over HTTP, rationale
- **File Context Design** — why server reads files instead of Claude
- **Call Logging Format** — JSONL schema, DPO data connection
- **In-Flight Safety** — warm_model eviction guards
