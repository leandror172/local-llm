#!/usr/bin/env python3
"""
ollama_client.py — Synchronous Ollama /api/chat client.

Thin wrapper using stdlib urllib (no external deps).
Designed for use by personas/ scripts that need LLM calls
without pulling in httpx or asyncio.

Used by:
  - personas/build-persona.py (Task 3.5 conversational builder)
"""

import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_TIMEOUT = 120  # seconds — covers cold starts


def ollama_chat(
    prompt: str,
    *,
    model: str = "my-coder-q3",
    system: str | None = None,
    temperature: float | None = None,
    think: bool = False,
    format_schema: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Send a chat request to Ollama and return the response.

    Args:
        prompt: User message.
        model: Ollama model name.
        system: Optional system prompt.
        temperature: Sampling temperature (None = model default).
        think: Enable Qwen3 thinking mode.
        format_schema: JSON schema dict for structured output.
        timeout: Max seconds to wait.

    Returns:
        Dict with keys: content (str), model (str), eval_count (int),
        total_duration_ms (float).

    Raises:
        ConnectionError: Ollama not reachable.
        TimeoutError: Ollama didn't respond in time.
        RuntimeError: Ollama returned an error (e.g., model not found).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"think": think},
    }
    if temperature is not None:
        payload["options"]["temperature"] = temperature
    if format_schema is not None:
        payload["format"] = format_schema

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "Name or service not known" in str(e):
            raise ConnectionError(
                f"Cannot connect to Ollama at {OLLAMA_URL}. Is Ollama running?"
            ) from e
        raise RuntimeError(f"Ollama request failed: {e}") from e
    except TimeoutError:
        raise TimeoutError(
            f"Ollama did not respond within {timeout}s. Model may be loading."
        )

    if "error" in body:
        raise RuntimeError(f"Ollama error: {body['error']}")

    return {
        "content": body["message"]["content"],
        "model": body.get("model", model),
        "eval_count": body.get("eval_count", 0),
        "total_duration_ms": body.get("total_duration", 0) / 1_000_000,
    }
