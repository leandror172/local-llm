"""FastMCP server exposing Ollama models as tools for Claude Code.

This is the heart of the MCP server. It defines the tools that Claude Code
can discover and invoke. Each tool is a Python function decorated with
@mcp.tool() — FastMCP automatically:
  1. Generates a JSON schema from the function's type hints and docstring
  2. Validates incoming arguments against that schema
  3. Handles the JSON-RPC protocol over stdio

The server uses a "lifespan" pattern to manage the Ollama HTTP client:
- On startup: create a shared httpx client (connection pooling)
- On shutdown: close the client cleanly (release TCP connections)
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from ollama_mcp.client import OllamaClient, OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError
from ollama_mcp.config import DEFAULT_MODEL, MODELS, TEMPS

# ---------------------------------------------------------------------------
# Module-level client (set during server lifespan)
# ---------------------------------------------------------------------------

# This variable holds the shared OllamaClient instance. It's None until the
# server starts (lifespan __aenter__) and None again after shutdown (__aexit__).
# Tools call _get_client() to access it safely.
_client: OllamaClient | None = None


def _get_client() -> OllamaClient:
    """Get the shared Ollama client. Raises if server hasn't started yet."""
    if _client is None:
        raise RuntimeError("OllamaClient not initialized — server not running?")
    return _client


# ---------------------------------------------------------------------------
# Server lifespan (startup/shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastMCP) -> AsyncIterator[None]:
    """Manage the Ollama HTTP client lifecycle.

    This is an async context manager — Python's pattern for "setup, yield,
    teardown". The code before `yield` runs on startup, the code after runs
    on shutdown (even if an error occurred). FastMCP calls this automatically.
    """
    global _client
    _client = OllamaClient()
    try:
        yield
    finally:
        await _client.close()
        _client = None


# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

# This creates the MCP server object. The `name` appears in Claude Code's
# tool list. `instructions` helps Claude understand when to use these tools.
mcp = FastMCP(
    name="ollama-bridge",
    instructions=(
        "Local LLM gateway via Ollama. Use for simple tasks that don't need "
        "frontier-level intelligence: boilerplate code, text transformation, "
        "explanations, summaries. Models run on a local GPU — fast but less "
        "capable than Claude."
    ),
    lifespan=_lifespan,
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def ask_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
) -> str:
    """Ask a question to a local Ollama model.

    Use for simple tasks like generating boilerplate code, explaining concepts,
    text transformation, or quick Q&A. The model runs locally on GPU — fast
    response times but less capable than Claude.

    Args:
        prompt: The question or instruction for the model.
        model: Ollama model to use. Available: my-coder, my-coder-q3,
               my-creative-coder, my-creative-coder-q3.
               Default: my-coder-q3 (Qwen3-8B, good all-rounder).
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
                     Default: model's built-in default.

    Returns:
        The model's text response. If Ollama is unreachable, returns an error
        message instead of raising (so Claude can handle it gracefully).
    """
    client = _get_client()

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            temperature=temperature,
        )
        return response.content

    except OllamaConnectionError:
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )
    except OllamaModelNotFoundError:
        return (
            f"Error: Model '{model}' not found. "
            f"Available models: {', '.join(MODELS)}"
        )
    except OllamaTimeoutError:
        return (
            "Error: Ollama timed out. The model may be loading (cold start). "
            "Try again in a few seconds."
        )


@mcp.tool()
async def list_models() -> str:
    """List all models currently available in Ollama.

    Returns model names and sizes. Useful for checking which models are
    pulled and ready to use before calling ask_ollama.
    """
    client = _get_client()

    try:
        models = await client.list_models()
    except OllamaConnectionError:
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )

    if not models:
        return "No models found. Pull one with: ollama pull <model-name>"

    # Format each model as "name (size)" for easy reading.
    # The size comes in bytes from the API; convert to GB for readability.
    lines = []
    for m in models:
        name = m.get("name", "unknown")
        size_bytes = m.get("size", 0)
        size_gb = size_bytes / (1024 ** 3)
        lines.append(f"  - {name} ({size_gb:.1f} GB)")

    return "Available Ollama models:\n" + "\n".join(lines)
