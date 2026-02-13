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

import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp.server.fastmcp import FastMCP

from ollama_mcp.client import OllamaClient, OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError
from ollama_mcp.config import DEFAULT_MODEL, MODELS, TEMPS

# ---------------------------------------------------------------------------
# Language → persona routing for generate_code
# ---------------------------------------------------------------------------

# Maps programming languages to the best-fit persona. Languages not listed
# here fall through to the general-purpose my-codegen-q3 persona.
LANGUAGE_ROUTES: dict[str, str] = {
    "java": "my-coder-q3",
    "go": "my-coder-q3",
    "golang": "my-coder-q3",
    "html": "my-creative-coder-q3",
    "javascript": "my-creative-coder-q3",
    "js": "my-creative-coder-q3",
    "css": "my-creative-coder-q3",
    "svg": "my-creative-coder-q3",
}

_DEFAULT_CODEGEN_MODEL = "my-codegen-q3"

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

    # Non-blocking health probe — log Ollama status at startup for diagnostics.
    # Tools handle errors individually, so failure here doesn't block the server.
    try:
        models = await _client.list_models()
        print(
            f"[ollama-bridge] Ollama connected — {len(models)} model(s) available",
            file=sys.stderr,
        )
    except OllamaConnectionError:
        print(
            "[ollama-bridge] Warning: Ollama is not reachable. "
            "Tools will return friendly errors until Ollama starts.",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"[ollama-bridge] Warning: Health probe failed: {e}",
            file=sys.stderr,
        )

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

    General-purpose tool for explanations, Q&A, brainstorming, and analysis.
    For specialized tasks, prefer the dedicated tools:
    - generate_code: code generation (auto-routes to language-specific personas)
    - summarize: text summarization (bullet points)
    - classify_text: text classification (structured JSON output)
    - translate: language translation

    Args:
        prompt: The question or instruction for the model.
        model: Ollama model to use. Available: my-coder, my-coder-q3,
               my-creative-coder, my-creative-coder-q3, my-codegen-q3,
               my-summarizer-q3, my-classifier-q3, my-translator-q3.
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


# ---------------------------------------------------------------------------
# Shared error handler
# ---------------------------------------------------------------------------

def _format_error(e: Exception) -> str:
    """Convert Ollama exceptions to user-friendly error strings."""
    if isinstance(e, OllamaConnectionError):
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )
    if isinstance(e, OllamaModelNotFoundError):
        return (
            f"Error: Model not found. "
            f"Available models: {', '.join(MODELS)}"
        )
    if isinstance(e, OllamaTimeoutError):
        return (
            "Error: Ollama timed out. The model may be loading (cold start). "
            "Try again in a few seconds."
        )
    return f"Error: {e}"


# ---------------------------------------------------------------------------
# Specialized tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def generate_code(
    prompt: str,
    language: str | None = None,
    model: str | None = None,
) -> str:
    """Generate code using a local Ollama model with smart persona routing.

    Automatically selects the best persona based on the target language:
    - Java, Go → my-coder-q3 (backend specialist)
    - HTML, JavaScript, CSS → my-creative-coder-q3 (browser/Canvas specialist)
    - All other languages → my-codegen-q3 (general-purpose code generator)

    An explicit model parameter overrides the automatic routing.

    Args:
        prompt: What code to generate (e.g., "binary search function").
        language: Target programming language (e.g., "python", "rust").
                  Used for persona routing and prepended as a hint to the prompt.
                  If omitted, the model infers the language from context.
        model: Override automatic persona routing with a specific model name.

    Returns:
        Generated code (typically in a fenced code block). Returns an error
        message string if Ollama is unreachable.
    """
    client = _get_client()

    # Determine which persona to use: explicit override > language route > default
    if model is not None:
        chosen_model = model
    elif language is not None:
        chosen_model = LANGUAGE_ROUTES.get(language.lower(), _DEFAULT_CODEGEN_MODEL)
    else:
        chosen_model = _DEFAULT_CODEGEN_MODEL

    # Prepend language hint so the persona knows what to generate
    if language:
        full_prompt = f"[Language: {language}]\n{prompt}"
    else:
        full_prompt = prompt

    try:
        response = await client.chat(
            prompt=full_prompt,
            model=chosen_model,
            think=False,
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)


@mcp.tool()
async def summarize(
    text: str,
    max_points: int | None = None,
    model: str = "my-summarizer-q3",
) -> str:
    """Summarize text into concise bullet points using a local Ollama model.

    The summarizer preserves facts, numbers, and conclusions from the source.
    Output is bullet points by default.

    Args:
        text: The text to summarize.
        max_points: Maximum number of bullet points. If omitted, the model
                    decides based on content length.
        model: Ollama model to use. Default: my-summarizer-q3.

    Returns:
        Bullet-point summary. Returns an error message string if Ollama
        is unreachable.
    """
    client = _get_client()

    # Build prompt with optional constraint
    if max_points is not None:
        prompt = f"Summarize the following text in at most {max_points} bullet points:\n\n{text}"
    else:
        prompt = f"Summarize the following text:\n\n{text}"

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            think=False,
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)


@mcp.tool()
async def classify_text(
    text: str,
    categories: list[str],
    model: str = "my-classifier-q3",
) -> str:
    """Classify text into one of the provided categories using a local Ollama model.

    Uses grammar-constrained decoding (Ollama's format parameter) to guarantee
    valid JSON output with the category restricted to the provided list.

    Args:
        text: The text to classify.
        categories: List of valid category names (e.g., ["food", "transport", "housing"]).
                    The model must pick exactly one.
        model: Ollama model to use. Default: my-classifier-q3.

    Returns:
        JSON string with keys: category, confidence (0.0-1.0), reasoning.
        Returns an error message string if Ollama is unreachable.
    """
    client = _get_client()

    # Build dynamic JSON schema — the enum constrains the model's output
    # to only the provided categories via grammar-constrained decoding.
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": categories,
            },
            "confidence": {
                "type": "number",
            },
            "reasoning": {
                "type": "string",
            },
        },
        "required": ["category", "confidence", "reasoning"],
    }

    prompt = (
        f"Classify the following text into one of these categories: "
        f"{', '.join(categories)}.\n\n{text}"
    )

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            format=schema,
            think=False,
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)


@mcp.tool()
async def translate(
    text: str,
    target_language: str,
    source_language: str | None = None,
    model: str = "my-translator-q3",
) -> str:
    """Translate text to a target language using a local Ollama model.

    The translator preserves meaning, tone, and formatting. Outputs only the
    translated text with no preamble or explanation.

    Args:
        text: The text to translate.
        target_language: Language to translate into (e.g., "Spanish", "Japanese").
        source_language: Language of the input text. If omitted, the model
                         auto-detects the source language.
        model: Ollama model to use. Default: my-translator-q3.

    Returns:
        Translated text only. Returns an error message string if Ollama
        is unreachable.
    """
    client = _get_client()

    # Build prompt with language pair info
    if source_language:
        prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}"
    else:
        prompt = f"Translate the following text to {target_language}:\n\n{text}"

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            think=False,
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)
