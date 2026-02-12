"""Async HTTP client for the Ollama /api/chat endpoint.

This module wraps Ollama's REST API in a clean Python interface. It's used
by the MCP server's tool functions but is also importable on its own for
testing or scripting.

Key design choices:
- Uses httpx.AsyncClient for non-blocking HTTP (MCP server is async)
- Single shared client instance for connection pooling (reuses TCP connections)
- Returns a structured dict, not raw JSON, so callers get consistent fields
"""

from dataclasses import dataclass

import httpx

from ollama_mcp.config import DEFAULT_MODEL, DEFAULT_THINK, DEFAULT_TIMEOUT, OLLAMA_BASE_URL


# ---------------------------------------------------------------------------
# Response dataclass
# ---------------------------------------------------------------------------

@dataclass
class ChatResponse:
    """Structured response from an Ollama /api/chat call.

    Attributes:
        content: The model's text reply (thinking tokens are stripped by Ollama).
        model: Which model actually handled the request.
        eval_count: Total tokens evaluated (includes hidden thinking tokens).
        eval_duration_ms: Time spent generating tokens, in milliseconds.
        total_duration_ms: Wall-clock time for the entire request, in milliseconds.
    """
    content: str
    model: str
    eval_count: int
    eval_duration_ms: float
    total_duration_ms: float


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class OllamaConnectionError(Exception):
    """Raised when we can't reach the Ollama server at all."""


class OllamaModelNotFoundError(Exception):
    """Raised when the requested model isn't available in Ollama."""


class OllamaTimeoutError(Exception):
    """Raised when Ollama takes too long to respond."""


# ---------------------------------------------------------------------------
# Client class
# ---------------------------------------------------------------------------

class OllamaClient:
    """Async client for Ollama's /api/chat endpoint.

    Usage:
        client = OllamaClient()
        response = await client.chat("Explain Python decorators in 3 sentences.")
        print(response.content)

    The client maintains a persistent httpx.AsyncClient for connection pooling.
    Call close() or use as an async context manager when done.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL) -> None:
        # httpx.AsyncClient reuses TCP connections across requests, which
        # avoids the overhead of a new TLS/TCP handshake per call.
        self._base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(base_url=self._base_url)

    async def chat(
        self,
        prompt: str,
        *,                          # Everything after * must be passed as keyword args
        model: str = DEFAULT_MODEL,
        system: str | None = None,
        temperature: float | None = None,
        think: bool = DEFAULT_THINK,
        format: dict | None = None,  # JSON schema for structured output
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ChatResponse:
        """Send a chat completion request to Ollama.

        Args:
            prompt: The user message to send.
            model: Ollama model name (e.g., "my-coder-q3").
            system: Optional system prompt prepended to the conversation.
            temperature: Sampling temperature (0.0-1.0). None = model default.
            think: Enable Qwen3 thinking mode. False disables hidden reasoning.
            format: JSON schema dict for structured output. None = free text.
            timeout: Max seconds to wait for a response.

        Returns:
            ChatResponse with the model's reply and performance metrics.

        Raises:
            OllamaConnectionError: Can't reach Ollama (not running?).
            OllamaModelNotFoundError: The requested model isn't pulled/created.
            OllamaTimeoutError: Ollama didn't respond within the timeout.
        """
        # Build the messages list. Ollama's /api/chat expects an array of
        # {"role": "...", "content": "..."} objects, similar to OpenAI's format.
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Build the request payload. "stream: false" means Ollama returns
        # the complete response in one JSON blob instead of streaming tokens.
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"think": think},
        }
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        if format is not None:
            payload["format"] = format

        # Make the HTTP request with error handling for each failure mode.
        try:
            response = await self._http.post(
                "/api/chat",
                json=payload,
                timeout=timeout,
            )
        except httpx.ConnectError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            )
        except httpx.TimeoutException:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {timeout}s. "
                "The model may be loading (cold start) — try again."
            )

        # Check for HTTP errors. Ollama returns 404 when a model isn't found.
        if response.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model '{model}' not found in Ollama. "
                f"Available models: ollama list"
            )
        response.raise_for_status()

        # Parse the response JSON into our structured dataclass.
        data = response.json()
        return ChatResponse(
            content=data["message"]["content"],
            model=data.get("model", model),
            eval_count=data.get("eval_count", 0),
            eval_duration_ms=data.get("eval_duration", 0) / 1_000_000,
            total_duration_ms=data.get("total_duration", 0) / 1_000_000,
        )

    async def list_models(self) -> list[dict]:
        """Fetch the list of models available in Ollama.

        Returns:
            List of model info dicts with at least a "name" key.

        Raises:
            OllamaConnectionError: Can't reach Ollama.
        """
        try:
            response = await self._http.get("/api/tags", timeout=10)
        except httpx.ConnectError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            )
        response.raise_for_status()
        return response.json().get("models", [])

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._http.aclose()

    # Async context manager support: `async with OllamaClient() as client:`
    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
