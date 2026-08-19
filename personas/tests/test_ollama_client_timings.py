"""
Unit tests for ollama_chat's timing fields (T-137).

Written RED, before the fields exist.

WHY THIS FILE EXISTS. `calls.jsonl` has recorded `eval_duration_ms` for every
bridge call since session 32, so generation tok/s has always been computable
*there*. It was never computable for the benchmarks, because they do not use the
bridge — `benchmarks/lib/writemodel_bench.py` imports `ollama_chat` from this
module, and this module dropped every duration except `total_duration`. s137
therefore had to bound the write-model benchmark's rate by wall clock.

The canonical field names are the ones `mcp-server/src/ollama_mcp/client.py`
writes into `calls.jsonl`. Two Ollama clients that name the same Ollama field
differently is the defect this file guards against, not a style question.
"""
import json
import urllib.request

import pytest

from lib.ollama_client import ollama_chat


# Ollama reports every duration in NANOSECONDS; every consumer here wants ms.
NS_PER_MS = 1_000_000


class _FakeResp:
    """Minimal stand-in for the object urlopen returns as a context manager."""

    def __init__(self, body: dict):
        self._payload = json.dumps(body).encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _body(**overrides) -> dict:
    """An /api/chat response body, shaped as Ollama actually returns it."""
    body = {
        "message": {"content": "ok"},
        "model": "my-python-q25c14-16k",
        "prompt_eval_count": 1500,
        "prompt_eval_duration": 2_000 * NS_PER_MS,
        "eval_count": 600,
        "eval_duration": 40_000 * NS_PER_MS,
        "load_duration": 15_000 * NS_PER_MS,
        "total_duration": 57_000 * NS_PER_MS,
    }
    body.update(overrides)
    return body


@pytest.fixture
def respond(monkeypatch):
    """Install a fake urlopen returning the given body; yields a call helper."""

    def _install(body: dict) -> dict:
        monkeypatch.setattr(
            urllib.request, "urlopen", lambda req, *a, **kw: _FakeResp(body)
        )
        return ollama_chat("prompt", model="my-python-q25c14-16k")

    return _install


class TestDurationFields:
    """Every duration Ollama returns must survive the wrapper, converted to ms."""

    # Distinct values per field, so a copy/paste that wires the wrong source
    # fails instead of coincidentally matching.
    @pytest.mark.parametrize("key,expected_ms", [
        ("eval_duration_ms", 40_000),
        ("prompt_eval_duration_ms", 2_000),
        ("load_duration_ms", 15_000),
        ("total_duration_ms", 57_000),
    ])
    def test_duration_is_converted_from_nanoseconds(self, respond, key, expected_ms):
        assert respond(_body())[key] == expected_ms

    def test_conversion_is_read_from_the_response_not_hardcoded(self, respond):
        # Halving the response must halve the reported figure. A field wired to a
        # constant passes the parametrized check above and fails this one.
        result = respond(_body(eval_duration=20_000 * NS_PER_MS))
        assert result["eval_duration_ms"] == 20_000

    @pytest.mark.parametrize("key", [
        "eval_duration_ms",
        "prompt_eval_duration_ms",
        "load_duration_ms",
        "total_duration_ms",
    ])
    def test_absent_duration_defaults_to_zero(self, respond, key):
        # Ollama omits load_duration on a warm model. Absence is normal and must
        # not raise — matching the .get(..., 0) contract the other fields use.
        bare = {"message": {"content": "ok"}, "model": "m"}
        assert respond(bare)[key] == 0


class TestComputedRate:
    """The point of the fields: a rate the log can be read for, not estimated."""

    def test_generation_tok_s_is_computable_from_the_returned_dict(self, respond):
        result = respond(_body())
        tok_s = result["eval_count"] / (result["eval_duration_ms"] / 1000)
        assert tok_s == pytest.approx(15.0)

    def test_load_time_is_separable_from_generation_time(self, respond):
        # T-131's discriminator: "slow because cold" vs "slow because contended"
        # is only answerable when load and generation are two numbers, not one.
        result = respond(_body())
        assert result["load_duration_ms"] != result["total_duration_ms"]
        assert result["load_duration_ms"] + result["eval_duration_ms"] < result["total_duration_ms"]


class TestFieldNamesMatchTheBridge:
    """The defect was two clients disagreeing, so the names are the contract."""

    # Exactly the keys mcp-server/src/ollama_mcp/client.py writes to calls.jsonl.
    # A rename on either side must break loudly here rather than produce two logs
    # that cannot be compared (ref:corpus-divergence-pattern).
    BRIDGE_TIMING_KEYS = {
        "prompt_eval_count",
        "prompt_eval_duration_ms",
        "eval_count",
        "eval_duration_ms",
        "total_duration_ms",
    }

    def test_returns_every_name_the_bridge_logs(self, respond):
        assert self.BRIDGE_TIMING_KEYS <= set(respond(_body()))
