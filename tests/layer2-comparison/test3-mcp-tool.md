# Test 3: Add MCP Tool — `count_tokens`

Add a new tool called `count_tokens` to the existing MCP server at `mcp-server/src/ollama_mcp/server.py`.

## Requirements

The tool should estimate the token count of a given text string, useful for checking if text will fit within a model's context window before sending it.

**Function signature:**
```python
async def count_tokens(text: str, model: str = DEFAULT_MODEL) -> str
```

**Behavior:**
- Call Ollama's `/api/embed` endpoint with the given text and model to get the actual embedding, then count the token count from the response
- If `/api/embed` is unavailable or fails, fall back to a simple character-based estimate (1 token ≈ 4 characters for English text)
- Return a human-readable string like: `"Token count estimate for model 'my-coder-q3': 1,247 tokens (from 4,988 characters)"`
- Use the shared `_get_client()` pattern and `_format_error()` for error handling, consistent with existing tools
- Use `think=False` (not applicable for embed, but follow the pattern for any chat calls)

**Integration:**
- Add the tool with the `@mcp.tool()` decorator, following the existing code style
- Add a new method to `OllamaClient` in `client.py` for the `/api/embed` call
- Include a proper docstring matching the style of existing tools (with Args/Returns sections)

**Do not modify any existing tools** — only add new code.
