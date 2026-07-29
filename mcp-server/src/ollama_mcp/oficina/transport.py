"""The ONE per-call generation transport (T-95 decision (b)).

Every model call oficina makes goes through `_chat_generation`: the worker's single-shot
`GenerateFn` default, the loop's per-iteration `default_coder`, and the packaging judge. That
singularity is load-bearing rather than tidy — it is what puts each call in `calls.jsonl` with a
`run_id` and a `call_id`, which is the join the DPO pipeline is built on. P4 verified it: an
accepted run logs two call records, coder and judge, because the judge composes this rather than
the evaluator's own transport.

It lives here rather than in `worker.py` because it has three callers and the worker is merely
the first of them. Importing it from the worker dragged `Store`, `Fifo`, `WorkerProc`, retention
and the whole client chain into anything that wanted to make one model call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from ollama_mcp.client import OllamaTimeoutError


@dataclass
class GenerationResult:
    """Outcome of one generation stage."""

    content: str
    model: str
    eval_count: int
    duration_ms: float
    # The identity of the underlying chat call, echoed from ChatResponse (P4-T3).
    # This is what makes the ledger↔calls.jsonl join identity-based: without it the
    # only shared key is run_id, which is per-RUN, so matching an iteration to the call
    # that produced it would be ORDER-based — the positional fallback T-105 banned
    # (and anti-cheat iterations record a verdict without an evaluation, so the
    # positions do not even line up). Defaulted so injected fakes stay valid.
    call_id: str = ""


def _cold_start_grace(call: Callable[[], GenerationResult]) -> GenerationResult:
    """Run ``call``, retrying ONCE on a cold-start timeout (conventions doc).

    A first-call timeout is usually the model loading into VRAM — the retry hits a warm
    model. The single shared spelling of the grace convention (T-95): the worker's
    ``GenerateFn`` seam and every loop iteration's coder call both route through it.
    """
    try:
        return call()
    except OllamaTimeoutError:
        return call()


def _chat_generation(
    prompt: str,
    model: str,
    run_id: str,
    *,
    timeout: int,
    num_predict: Optional[int] = None,
    strip_fences: bool = True,
    # P4-T5: the judge is the third caller of this one transport (T-95 — per-call transport
    # is ONE spelling). It is the only one that needs a system prompt and a response schema,
    # so both are opt-in seams rather than a second transport that would miss calls.jsonl.
    system: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> GenerationResult:
    """One Ollama chat call → ``GenerationResult`` — the shared generation transport (T-95).

    Owns the call convention for BOTH the single-shot default and the loop's per-iteration
    coder: client lifecycle, ``think=False``, ``run_id`` tagging (calls.jsonl), bounded
    ``num_predict`` (T-91), fence stripping. Deliberately emits NO events — the single-shot
    path narrates via GenerationStarted/Finished, the loop via IterationStarted/Evaluated,
    and per-call telemetry lives in calls.jsonl joined on run_id (T-99 decision (b)).
    """
    import asyncio

    from ollama_mcp import server as srv
    from ollama_mcp.client import OllamaClient

    async def _call() -> Any:
        client = OllamaClient()
        try:
            return await client.chat(
                prompt=prompt,
                model=model,
                think=False,
                timeout=timeout,
                run_id=run_id,
                num_predict=num_predict,
                system=system,
                format=schema,
                # T-105: oficina does NOT route through the generate_code MCP tool —
                # this seam goes straight to the client, so it must self-attribute.
                # Verdicts for these are per-RUN (via run_result), not per-call.
                tool="oficina",
            )
        finally:
            await client.close()

    resp = asyncio.run(_call())
    content = srv._strip_code_fences(resp.content) if strip_fences else resp.content
    return GenerationResult(
        content=content, model=resp.model,
        eval_count=resp.eval_count, duration_ms=resp.total_duration_ms,
        call_id=resp.call_id,
    )


def model_context_limit(model: str) -> Optional[int]:
    """The model's effective context window in tokens, or None when undeterminable.

    The window is the ``num_ctx`` PARAMETER Ollama reports for the model. Absence is
    NOT "the architectural maximum" — the model would then run at Ollama's own unstated
    default — so an absent or unreadable value yields None rather than a guess: guessing
    high silently disables the caller's fit check, guessing low aborts valid work. Every
    failure (transport, status, shape, parse) lands on the same None channel; the ceiling
    is a value-or-absence, never a sentinel in the value channel (T-112).
    """
    descriptor = _fetch_model_descriptor(model)
    if not descriptor:
        return None
    return _num_ctx_from_parameters(descriptor.get("parameters", ""))


def _fetch_model_descriptor(model: str) -> Optional[Dict[str, Any]]:
    """The model's /api/show descriptor, or None if it cannot be retrieved."""
    import asyncio

    from ollama_mcp.client import OllamaClient

    async def _call() -> Any:
        client = OllamaClient()
        try:
            return await client.fetch_model_descriptor(model)
        finally:
            await client.close()

    try:
        return asyncio.run(_call())
    except Exception:  # noqa: BLE001 — an undeterminable ceiling is None, never a raise
        return None


def _num_ctx_from_parameters(parameters: str) -> Optional[int]:
    """Read ``num_ctx`` out of Ollama's ``name<whitespace>value`` parameter blob.

    The trailing space in the prefix match keeps a longer parameter that merely
    starts with the same letters from being mistaken for it.
    """
    for line in parameters.splitlines():
        if line.startswith("num_ctx "):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None
