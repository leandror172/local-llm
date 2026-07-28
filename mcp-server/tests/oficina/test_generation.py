"""Tests for the shared per-call generation transport (T-95 decision (b)).

``_chat_generation`` (transport) and ``_cold_start_grace`` (single retry) are the ONE
spelling of the per-call convention shared by the worker's single-shot ``GenerateFn``
default and the loop's per-iteration ``default_coder``.

Structural/wiring tests — bespoke imperative per the executable-spec taxonomy
(`ref:test-executable-spec`): each varies the `given` (a fake client, a flaky call),
not an input sequence.
"""

import pytest

from ollama_mcp.client import OllamaTimeoutError
from ollama_mcp.oficina.loop import NUM_PREDICT, default_coder
from ollama_mcp.oficina.worker import GenerationResult, _cold_start_grace


# --- _cold_start_grace: the single-retry convention --------------------------


def test_grace_retries_once_on_cold_start_timeout():
    """A first-call timeout (model loading into VRAM) is retried exactly once."""
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise OllamaTimeoutError("cold")
        return "warm"

    assert _cold_start_grace(flaky) == "warm"
    assert len(calls) == 2


def test_grace_propagates_a_second_timeout():
    """Two timeouts in a row are a real failure, not a cold start — no retry loop."""
    calls = []

    def always_cold():
        calls.append(1)
        raise OllamaTimeoutError("cold")

    with pytest.raises(OllamaTimeoutError):
        _cold_start_grace(always_cold)
    assert len(calls) == 2


def test_grace_does_not_retry_other_errors():
    """Only the cold-start timeout earns a retry; any other error propagates immediately."""
    calls = []

    def broken():
        calls.append(1)
        raise ValueError("not a cold start")

    with pytest.raises(ValueError):
        _cold_start_grace(broken)
    assert len(calls) == 1


# --- default_coder → _chat_generation: the call convention -------------------


class _FakeResponse:
    content = "```python\nx = 1\n```"
    model = "model-used"
    eval_count = 7
    total_duration_ms = 12.5
    call_id = "abc123def456"  # P4-T3: real ChatResponses always carry one


class _FakeClient:
    """Stands in for OllamaClient; records the chat kwargs for assertion."""

    captured: dict = {}

    async def chat(self, **kwargs):
        _FakeClient.captured = kwargs
        return _FakeResponse()

    async def close(self):
        pass


def test_default_coder_call_convention(monkeypatch):
    """The coder's chat call carries the whole shared convention: the T-91 num_predict
    floor/cap default when the budget passes None, the spec timeout (T-95), think=False,
    the run_id tag (calls.jsonl), and fence-stripped content."""
    monkeypatch.setattr("ollama_mcp.client.OllamaClient", _FakeClient)

    gen = default_coder(num_predict=None, timeout=123)("the prompt", "my-model", "run-1")

    kw = _FakeClient.captured
    assert kw["num_predict"] == NUM_PREDICT  # None → the T-91 floor/cap default
    assert kw["timeout"] == 123  # spec.timeout_s reaches the call (T-95)
    assert kw["think"] is False
    assert kw["run_id"] == "run-1"
    assert isinstance(gen, GenerationResult)
    assert "```" not in gen.content and "x = 1" in gen.content  # fences stripped
    assert gen.model == "model-used" and gen.eval_count == 7
    # P4-T3: the chat call's identity reaches the loop, so an iteration's ledger event
    # can name the exact calls.jsonl record that produced it instead of guessing by order.
    assert gen.call_id == "abc123def456"


def test_default_coder_explicit_num_predict_wins(monkeypatch):
    """A budgets.num_predict value passes through unchanged (not overridden by the default)."""
    monkeypatch.setattr("ollama_mcp.client.OllamaClient", _FakeClient)

    default_coder(num_predict=512, timeout=60)("p", "m", "run-2")

    assert _FakeClient.captured["num_predict"] == 512
