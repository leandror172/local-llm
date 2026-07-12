# ollama-bridge — MCP Server for Local LLM Delegation

An MCP (Model Context Protocol) server that lets Claude Code delegate simple tasks to local Ollama models running on GPU. Built with Python and [FastMCP](https://github.com/modelcontextprotocol/python-sdk).

**Pattern:** Frontier-first, delegates down — Claude decides when a task is simple enough for a local model, calls the appropriate tool, and uses the result directly.

## Architecture

```
Claude Code (frontier)
    │
    │  stdio (JSON-RPC 2.0)
    ▼
┌──────────────────────┐
│  ollama-bridge (MCP)  │
│  FastMCP + httpx      │
└──────────┬───────────┘
           │  HTTP POST /api/chat
           ▼
┌──────────────────────┐
│  Ollama (localhost)   │
│  RTX 3060 12GB VRAM  │
│  8 specialized        │
│  model personas       │
└──────────────────────┘
```

Claude Code spawns the MCP server as a subprocess on startup. The server maintains a persistent HTTP connection to Ollama and exposes tools that Claude can call autonomously.

## Tools

### `ask_ollama(prompt, model?, temperature?, persona?, context_files?, refs?, refs_root?, output_file?, output_only?)`
General-purpose Q&A, explanations, brainstorming. Default model: `my-coder-q3` (Qwen3-8B).
- `context_files`: inject file slices server-side (zero Claude token cost)
- `refs`: inject ref-marker documentation blocks (zero Claude token cost)
- `output_file`: write response to disk (relative paths anchor to `REPO_ROOT`)
- `output_only`: return compact status string instead of full content; defers verdict to file inspection

### `generate_code(prompt, language?, model?, context_files?, refs?, refs_root?, output_file?, output_only?)`
Code generation with smart persona routing:
- Java, Go → `my-coder-q3` (backend specialist)
- HTML, JavaScript, CSS → `my-creative-coder-q3` (browser/Canvas specialist)
- All other languages → `my-codegen-q3` (general-purpose)

An explicit `model` parameter overrides routing. Accepts the same `context_files`, `refs`, `output_file`, and `output_only` parameters as `ask_ollama`.

### `summarize(text, max_points?, model?)`
Summarizes text into concise bullet points. Default model: `my-summarizer-q3`.

### `classify_text(text, categories, model?)`
Classifies text into one of the provided categories. Uses grammar-constrained decoding (Ollama `format` parameter) to guarantee valid JSON output. Returns `{category, confidence, reasoning}`.

### `translate(text, target_language, source_language?, model?)`
Translates text with auto-detected source language. Default model: `my-translator-q3`.

### `list_models()`
Lists all models available in Ollama with sizes. Useful for checking what's pulled before calling other tools.

### `warm_model(model, force?)`
Pre-loads a model into VRAM to avoid a cold-start timeout on the next call. Refuses to evict a model with an in-flight request unless `force=True`. Skip when switching between same-base personas (they share weights).

### `query_personas(language?, domain?, tier?, name?)`
Queries the persona registry (`personas/registry.yaml`) by any filter combination. The offline complement to `list_models`: registry metadata (role, base model, status) rather than what's currently pulled.

### `detect_persona(path)`
Analyzes a codebase directory and returns ranked persona matches for working in it (language/framework detection against registry roles).

### `build_persona(description, codebase_path?)`
Proposes a new persona spec from a natural-language description (optionally informed by a codebase scan). Proposal only — creation goes through the persona-creator flow.

### `ref_lookup(key, path?)`
Looks up a named `<!-- ref:KEY -->` documentation block. Same resolution as the `refs` parameter, but returns the block to Claude instead of injecting it into an Ollama prompt.

### `patch_file(path, old_string, new_string, replace_all?)`
Exact-string file edit without reading the file into Claude's context — Edit-tool semantics (uniqueness check, atomic tmp+rename). For files the local model just generated; not a substitute for reading files you should understand.

### oficina — async deliverable runs (`submit_run`, `run_status`, `run_result`, `cancel_run`)

The async substrate around `generate_code`/`ask_ollama` semantics (P1 of the
coding-delegate vision — `docs/vision/coding-delegate/`). A run outlives the MCP call
*and the Claude session that created it*: a detached worker drains a disk FIFO, every
state change is an event in the run's ledger, and any session holding the `run_id` can
poll, cancel, or collect.

- `submit_run(spec)` → `{run_id, watch_cmd, queue_position}` — returns in <1s, never
  blocks on the GPU. Spec: `deliverable.kind: file|answer` (+ `target` for `file`),
  `objective`, optional `context.files`/`refs`, `model`, `timeout_s`. Malformed specs
  are rejected deterministically with a named rule (unknown keys fail loud).
- `run_status(run_id, since_offset?)` → state/phase folds + the event narrative since
  your last poll.
- `run_result(run_id)` → report + deliverable; errors discriminate unknown-id /
  not-terminal-yet / artifacts-pruned. The report survives retention pruning.
- `cancel_run(run_id)` — cooperative flag; the worker emits `Cancelled` at its next
  checkpoint (the command→event gap is visible in the ledger, by design).

Shell parity via the `oficina` CLI (`submit|status|result|cancel|watch|runs|prune`,
console entry point) and `./watch-run.sh <run_id>` to tail a run to terminal state.
Storage: `~/.local/share/oficina/` (override: `OFICINA_ROOT`). Every generation still
logs to `calls.jsonl` (plus a `run_id` field) — the verdict/DPO pipeline is unaffected.

## When to Delegate vs. Do Directly

**Good for delegation** (local model handles well):
- Boilerplate code generation (CRUD, utility functions, data classes)
- Text transformation (summarization, translation, classification)
- Simple explanations and Q&A
- Format conversion (JSON ↔ YAML, case conversion)

**Keep on Claude** (frontier model needed):
- Complex multi-file refactoring
- Architectural decisions and design reasoning
- Subtle bug analysis
- Tasks requiring full codebase context
- Anything requiring >16K context window (14B models) or >32K (7-8B models)

## Available Model Personas

| Persona | Base Model | Role | Temperature |
|---------|-----------|------|-------------|
| `my-coder` | Qwen2.5-Coder-7B | Fast coding (63-67 tok/s) | model default |
| `my-coder-q3` | Qwen3-8B | Coding with reasoning | model default |
| `my-creative-coder` | Qwen2.5-Coder-7B | Browser/Canvas/visual | model default |
| `my-creative-coder-q3` | Qwen3-8B | Creative coding | model default |
| `my-codegen-q3` | Qwen3-8B | General code generation | 0.1 |
| `my-summarizer-q3` | Qwen3-8B | Text summarization | 0.3 |
| `my-classifier-q3` | Qwen3-8B | Classification (JSON) | 0.1 |
| `my-translator-q3` | Qwen3-8B | Translation (100+ langs) | 0.3 |

All Qwen3 personas use `think: false` by default (simple tasks don't benefit from hidden reasoning, and it inflates latency 5-17x).

## Configuration

### Project-level (`.mcp.json` in repo root)

```json
{
  "mcpServers": {
    "ollama-bridge": {
      "command": "/mnt/i/workspaces/llm/mcp-server/run-server.sh"
    }
  }
}
```

### System-Wide Setup

To make ollama-bridge available in **every** Claude Code session (not just this repo), add it at the user level.

**Claude Code (user-level)** — add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "ollama-bridge": {
      "command": "/mnt/i/workspaces/llm/mcp-server/run-server.sh"
    }
  }
}
```

**Claude Desktop (Windows)** — add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ollama-bridge": {
      "command": "wsl",
      "args": ["--", "/mnt/i/workspaces/llm/mcp-server/run-server.sh"]
    }
  }
}
```

The `wsl --` prefix lets Claude Desktop (a Windows process) spawn the server inside WSL where Ollama and Python live.

**Startup behavior:** The server probes Ollama on startup and logs status to stderr. If Ollama is unreachable, the server starts anyway — tools return friendly error messages until Ollama becomes available.

### Environment Variables

**Claude Code side:**

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TIMEOUT` | `10000` | Max ms to wait for MCP tool response. Set to `120000` for Ollama cold starts. |

**Server side** (set in `.mcp.json` `env` block or shell):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `my-coder-q3` | Default model for `ask_ollama` |
| `OLLAMA_TIMEOUT` | `120` | Max seconds to wait for Ollama response |
| `OLLAMA_THINK` | `false` | Enable Qwen3 thinking mode globally |
| `OLLAMA_BRIDGE_LOG_LEVEL` | `INFO` (via `run-server.sh`) | Threshold for structured debug log. One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `OLLAMA_BRIDGE_LOG_FILE` | `/tmp/ollama-bridge.jsonl` | Where the structured log is appended. Safe to share across bridges (POSIX `O_APPEND` keeps per-line writes atomic). |

### Debug Logging

The server writes a structured JSONL log to disk for diagnosing tool hangs and
Ollama hiccups. Each line is a JSON object with `t` (UTC timestamp), `level`,
`ev` (event name), plus per-process `client_id` (random hex per bridge) and
`pid`. Multiple bridges can write to the same file safely — demultiplex by
`client_id`.

Levels in use:
- `INFO` — `server_start` (banner: git SHA, branch, log_level, log_file), `server_stop`
- `DEBUG` — `tool_enter` / `tool_exit` (with timing in ms) on `patch_file`, `generate_code`, `ask_ollama`; `http_post_start` / `http_post_done` on the Ollama `/api/chat` call
- `ERROR` — `http_post_error` (connect failures, timeouts)

To enable per-tool tracing during a hang investigation, add an env block to
`.mcp.json` and restart Claude Code:

```json
"ollama-bridge": {
  "command": "/mnt/i/workspaces/llm/mcp-server/run-server.sh",
  "env": {
    "OLLAMA_BRIDGE_LOG_LEVEL": "DEBUG",
    "OLLAMA_BRIDGE_LOG_FILE": "/tmp/ollama-bridge.jsonl"
  }
}
```

Diagnostic helpers (run from the repo root):

```bash
make -C mcp-server logs                       # tail + pretty-print, all bridges
make -C mcp-server logs CLIENT=ab12cd34       # filter to one bridge
make -C mcp-server logs-raw                   # raw JSONL for grep / jq
make -C mcp-server bridges                    # which-bridge.sh: PID/git/branch/...
make -C mcp-server help                       # list all targets
```

Filter a static log file without `make`:

```bash
grep '"client_id": "ab12cd34"' /tmp/ollama-bridge.jsonl
jq 'select(.client_id=="ab12cd34")' /tmp/ollama-bridge.jsonl   # if jq is installed
```

Diagnostic rule of thumb: if a tool hangs, look for the matching `tool_enter`
without a `tool_exit` (hang inside the tool body) or a missing `tool_enter`
entirely (hang in the MCP stdio transport or Claude Code's client).

## Running

```bash
# Standalone (for testing)
./mcp-server/run-server.sh

# Via Claude Code (automatic — reads .mcp.json on startup)
# Just start Claude Code in the project directory
```

The bash wrapper uses `uv run` to manage the virtual environment and dependencies automatically.

## Known Limitations

1. **Single GPU, single model at a time.** Ollama loads one model into VRAM. Switching between personas (e.g., `my-codegen-q3` → `my-summarizer-q3`) incurs a cold-start delay of ~10-30s while the new model loads. Same-base models (all Qwen3-8B) share weights, so Ollama may keep them hot.

2. **Context window.** 7-8B models handle ~32K tokens effectively. 14B models handle ~16K tokens on 12GB VRAM (OLLAMA_KV_CACHE_TYPE=q8_0 in effect). Prompts exceeding these limits produce degraded output without error.

3. **Quality ceiling.** Local 7-8B models fail at complex spatial reasoning, multi-step logic chains, and tasks requiring broad world knowledge. These should stay on Claude.

4. **Cold starts.** First request after Ollama has been idle may take 30-60s as the model loads into VRAM. `MCP_TIMEOUT=120000` accommodates this, but the calling Claude session will appear to hang during loading. **For long generations, this whole class is gone: use `submit_run` instead** — the MCP call returns in <1s, the worker retries once on a cold-start timeout, and `timeout_s` in the run spec (default 1800s) replaces the 120s MCP ceiling.

5. **No streaming.** Responses are returned in full (`stream: false`). Long generations may feel slow even though they're running at 51-67 tok/s.

6. **Qwen3 thinking overhead.** Even with `think: false`, there's a small overhead compared to Qwen2.5. If `think: true` is accidentally enabled, latency inflates 5-17x with no visible output difference (thinking tokens are stripped).

## Project Structure

```
mcp-server/
├── run-server.sh                    # Bash wrapper (project convention)
├── watch-run.sh                     # Tail an oficina run to terminal state
├── pyproject.toml                   # uv project config (+ `oficina` entry point)
├── scripts/
│   └── which-bridge.sh              # List live bridge processes with banner info
└── src/ollama_mcp/
    ├── __main__.py                  # Entry point (stdio transport)
    ├── config.py                    # Defaults + env var overrides
    ├── client.py                    # Async Ollama HTTP client
    ├── debug_log.py                 # Optional structured JSONL logging
    ├── server.py                    # FastMCP server + all tool definitions
    └── oficina/                     # Async deliverable-run substrate (P1)
        ├── service.py               # One impl layer under MCP tools + CLI
        ├── worker.py                # Detached lazy-daemon run loop
        ├── ledger.py                # Event-sourced JSONL run ledger
        ├── intake.py                # Deterministic spec validation
        ├── fifo.py / workerproc.py  # Disk queue / pidfile + detached spawn
        ├── store.py / ids.py        # Run-dir layout / run-ID minting
        └── retention.py / cli.py / config.py
```

## Troubleshooting

**"Cannot connect to Ollama"**
Ollama isn't running. Start it with `ollama serve` (or check if Docker Ollama is expected instead).

**"Model not found"**
The persona hasn't been created. Run `ollama create <persona-name> -f modelfiles/<persona>.Modelfile`.

**Tool call times out**
- Check `MCP_TIMEOUT` is set (`echo $MCP_TIMEOUT` — should be `120000`)
- Check Ollama is responsive: `curl http://localhost:11434/api/tags`
- May be a cold start — try again after model loads

**Claude doesn't use the tools**
- Check user-level config: `~/.claude.json` should have a top-level `mcpServers` entry
- For project-only setup: verify `.mcp.json` is in the repo root
- Run `/mcp` in Claude Code to check server status
- Restart Claude Code after config changes

**A tool call hangs (no result returned)**
- Run `./mcp-server/scripts/which-bridge.sh` to confirm which bridge is serving this session and that it's running post-logging code (git SHA column).
- `tail -f /tmp/ollama-bridge.jsonl` in another terminal while reproducing. The missing event tells you where the hang lives:
  - `tool_enter` but no `tool_exit` → hang inside the tool body
  - No `tool_enter` after a prior tool returned → hang in MCP stdio transport or Claude Code's client (not the bridge)
  - `http_post_start` but no `http_post_done` → Ollama itself is wedged on the request
- Multiple stale bridges from old sessions can accumulate; `kill <ppid>` from the `which-bridge.sh` output removes one cleanly (the `uv run` wrapper plus its Python child).
