"""Async HTTP client for the Ollama /api/chat endpoint.

This module wraps Ollama's REST API in a clean Python interface. It's used
by the MCP server's tool functions but is also importable on its own for
testing or scripting.

Key design choices:
- Uses httpx.AsyncClient for non-blocking HTTP (MCP server is async)
- Single shared client instance for connection pooling (reuses TCP connections)
- Returns a structured dict, not raw JSON, so callers get consistent fields
"""

import datetime
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import httpx

from ollama_mcp.config import (
    CALL_LOG_PATH,
    DEFAULT_MODEL,
    DEFAULT_THINK,
    DEFAULT_TIMEOUT,
    LOG_FULL_CONTENT,
    OLLAMA_BASE_URL,
)


# ---------------------------------------------------------------------------
# Response dataclass
# ---------------------------------------------------------------------------

@dataclass
class ChatResponse:
    """Structured response from an Ollama /api/chat call.

    Attributes:
        content: The model's text reply (thinking tokens are stripped by Ollama).
        model: Which model actually handled the request.
        prompt_eval_count: Tokens consumed by the input prompt (input tokens).
        eval_count: Total tokens generated (includes hidden thinking tokens for Qwen3).
        eval_duration_ms: Time spent generating tokens, in milliseconds.
        total_duration_ms: Wall-clock time for the entire request, in milliseconds.
    """
    content: str
    model: str
    prompt_eval_count: int
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
        self._http = httpx.AsyncClient(base_url=self._base_url, timeout=None)

        # In-flight request tracking. Counts active requests per model.
        # Used by warm_model to avoid evicting a model mid-generation.
        # Designed for easy extraction to directory-based coordination
        # (Option 2) — swap these 3 methods to use file ops instead.
        self._inflight: dict[str, int] = {}

    # -- In-flight tracking (Option 1: in-process dict) --------------------
    # Future extraction point: replace dict ops with directory lock files
    # per docs/ideas/ollama-coordination-layer.md

    def mark_inflight(self, model: str) -> None:
        """Register an in-flight request for the given model."""
        self._inflight[model] = self._inflight.get(model, 0) + 1

    def mark_complete(self, model: str) -> None:
        """Deregister an in-flight request for the given model."""
        count = self._inflight.get(model, 0)
        if count <= 1:
            self._inflight.pop(model, None)
        else:
            self._inflight[model] = count - 1

    def is_busy(self, model: str | None = None) -> bool:
        """Check if a model (or any model) has in-flight requests."""
        if model is not None:
            return self._inflight.get(model, 0) > 0
        return any(v > 0 for v in self._inflight.values())

    def get_inflight(self) -> dict[str, int]:
        """Return a copy of the in-flight request counts."""
        return dict(self._inflight)

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
            "think": think,
            "options": {},
        }
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        if format is not None:
            payload["format"] = format

        # Track in-flight requests so warm_model can check before evicting.
        self.mark_inflight(model)
        try:
            # Use a fresh client per call to avoid stale connection state from
            # previously cancelled or timed-out requests.  The TCP handshake
            # overhead is negligible relative to model generation time (30–150s).
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=None
            ) as fresh_client:
                response = await fresh_client.post(
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
        finally:
            self.mark_complete(model)

        # Check for HTTP errors. Ollama returns 404 when a model isn't found.
        if response.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model '{model}' not found in Ollama. "
                f"Available models: ollama list"
            )
        response.raise_for_status()

        # Parse the response JSON into our structured dataclass.
        data = response.json()
        result = ChatResponse(
            content=data["message"]["content"],
            model=data.get("model", model),
            prompt_eval_count=data.get("prompt_eval_count", 0),
            eval_count=data.get("eval_count", 0),
            eval_duration_ms=data.get("eval_duration", 0) / 1_000_000,
            total_duration_ms=data.get("total_duration", 0) / 1_000_000,
        )

        # Log the call for distillation / training data collection.
        self._log_call(prompt, system, model, temperature, think, format is not None, result)

        return result

    def _log_call(
        self,
        prompt: str,
        system: str | None,
        model: str,
        temperature: float | None,
        think: bool,
        had_format: bool,
        response: "ChatResponse",
    ) -> None:
        """Append a JSONL record for this call to CALL_LOG_PATH.

        Runs synchronously — file I/O is fast (~1ms) vs the Ollama call (~1s),
        so the overhead is negligible. Failures are silently swallowed so a
        log error never breaks the actual tool call.

        The log is the raw material for future distillation / fine-tuning:
        - prompt_hash allows deduplication without storing sensitive text
        - Full prompt/response stored by default (LOG_FULL_CONTENT=true)
        - Set OLLAMA_LOG_FULL_CONTENT=false to store 200-char previews only
        - Set OLLAMA_CALL_LOG="" to disable logging entirely
        """
        if not CALL_LOG_PATH:
            return
        try:
            log_path = Path(CALL_LOG_PATH)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]

            # Rough estimate of how many Claude API tokens the same task would cost.
            # Formula: (prompt + system + response chars) / 4 — the standard
            # chars-per-token approximation for English/code content. Intentionally
            # imprecise; good enough for ballpark ACCEPTED/IMPROVED savings reports.
            system_chars = len(system) if system else 0
            claude_tokens_est = (
                len(prompt) + system_chars + len(response.content)
            ) // 4

            entry = {
                "ts": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                "model": response.model,
                "prompt_hash": prompt_hash,
                "prompt": prompt if LOG_FULL_CONTENT else prompt[:200],
                "system": (
                    system if LOG_FULL_CONTENT else (system[:100] if system else None)
                ),
                "response": (
                    response.content if LOG_FULL_CONTENT else response.content[:200]
                ),
                "prompt_chars": len(prompt),
                "response_chars": len(response.content),
                "prompt_eval_count": response.prompt_eval_count,
                "eval_count": response.eval_count,
                "eval_duration_ms": round(response.eval_duration_ms),
                "total_duration_ms": round(response.total_duration_ms),
                "claude_tokens_est": claude_tokens_est,
                "temperature": temperature,
                "think": think,
                "had_format": had_format,
            }

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Never let logging break a tool call

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

    async def list_running(self) -> list[dict]:
        """Fetch models currently loaded in Ollama's VRAM.

        Returns:
            List of model info dicts from /api/ps (name, size, size_vram,
            expires_at, details). Empty list if none loaded.

        Raises:
            OllamaConnectionError: Can't reach Ollama.
        """
        try:
            response = await self._http.get("/api/ps", timeout=10)
        except httpx.ConnectError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            )
        response.raise_for_status()
        return response.json().get("models", [])

    async def unload_model(self, model: str) -> None:
        """Unload a model from VRAM by sending keep_alive: 0.

        Uses the /api/chat endpoint with empty messages array and
        keep_alive: 0, which tells Ollama to release the model immediately.

        Raises:
            OllamaConnectionError: Can't reach Ollama.
        """
        try:
            response = await self._http.post(
                "/api/chat",
                json={"model": model, "messages": [], "keep_alive": 0},
                timeout=30,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            )

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._http.aclose()

    # Async context manager support: `async with OllamaClient() as client:`
    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
