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

### `ask_ollama(prompt, model?, temperature?)`
General-purpose Q&A, explanations, brainstorming. Default model: `my-coder-q3` (Qwen3-8B).

### `generate_code(prompt, language?, model?)`
Code generation with smart persona routing:
- Java, Go → `my-coder-q3` (backend specialist)
- HTML, JavaScript, CSS → `my-creative-coder-q3` (browser/Canvas specialist)
- All other languages → `my-codegen-q3` (general-purpose)

An explicit `model` parameter overrides routing.

### `summarize(text, max_points?, model?)`
Summarizes text into concise bullet points. Default model: `my-summarizer-q3`.

### `classify_text(text, categories, model?)`
Classifies text into one of the provided categories. Uses grammar-constrained decoding (Ollama `format` parameter) to guarantee valid JSON output. Returns `{category, confidence, reasoning}`.

### `translate(text, target_language, source_language?, model?)`
Translates text with auto-detected source language. Default model: `my-translator-q3`.

### `list_models()`
Lists all models available in Ollama with sizes. Useful for checking what's pulled before calling other tools.

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
- Anything requiring >4K context window (14B models) or >8K (7-8B models)

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

2. **Context window.** 7-8B models handle ~8K tokens effectively. 14B models are limited to ~4K tokens on 12GB VRAM. Prompts exceeding these limits produce degraded output without error.

3. **Quality ceiling.** Local 7-8B models fail at complex spatial reasoning, multi-step logic chains, and tasks requiring broad world knowledge. These should stay on Claude.

4. **Cold starts.** First request after Ollama has been idle may take 30-60s as the model loads into VRAM. `MCP_TIMEOUT=120000` accommodates this, but the calling Claude session will appear to hang during loading.

5. **No streaming.** Responses are returned in full (`stream: false`). Long generations may feel slow even though they're running at 51-67 tok/s.

6. **Qwen3 thinking overhead.** Even with `think: false`, there's a small overhead compared to Qwen2.5. If `think: true` is accidentally enabled, latency inflates 5-17x with no visible output difference (thinking tokens are stripped).

## Project Structure

```
mcp-server/
├── run-server.sh                    # Bash wrapper (project convention)
├── pyproject.toml                   # uv project config
└── src/ollama_mcp/
    ├── __main__.py                  # Entry point (stdio transport)
    ├── config.py                    # Defaults + env var overrides
    ├── client.py                    # Async Ollama HTTP client
    └── server.py                    # FastMCP server + all tool definitions
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
- Verify `.mcp.json` is in the repo root and Claude Code was started from that directory
- Run `/mcp` in Claude Code to check server status
- Restart Claude Code after config changes
