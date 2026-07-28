"""Characterization tests for `OllamaClient._log_call`'s call identity (T-105).

Written BEFORE the P4-T3 refactor that moves where `call_id` is minted, so they pin
what a caller observes TODAY and stay green across the change
(`ref:patterns-refactoring-characterize-first`). `call_id` had zero test coverage
before this file — a suite that never exercises the code proves nothing about it.

Structural/wiring tests: bespoke imperative per the executable-spec taxonomy
(`ref:test-executable-spec`) — each varies the `given`, not an input sequence.
"""

import json

from ollama_mcp.client import OllamaClient


class _FakeResponse:
    """Stands in for a ChatResponse; only the attributes `_log_call` reads."""

    content = "response content"
    model = "model-used"
    prompt_eval_count = 10
    eval_count = 20
    eval_duration_ms = 30.5
    total_duration_ms = 40.75
    prompt_eval_duration_ms = 5.25


def _log_one(client, log_path, monkeypatch, prompt):
    """Log one call against a throwaway log file, never the real calls.jsonl."""
    monkeypatch.setattr("ollama_mcp.client.CALL_LOG_PATH", str(log_path))
    client._log_call(
        prompt=prompt,
        system=None,
        model="model-used",
        temperature=None,
        think=False,
        had_format=False,
        response=_FakeResponse(),
        run_id=None,
        tool="test",
    )


def _records(log_path):
    """Every JSONL record written to `log_path`, in order."""
    with open(log_path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_call_id_is_twelve_lowercase_hex_chars(tmp_path, monkeypatch):
    """The id shape is load-bearing: verdict-capture matched `[a-f0-9]+`, so a
    non-hex call_id would have been rejected silently rather than loudly."""
    log_path = tmp_path / "calls.jsonl"

    _log_one(OllamaClient(), log_path, monkeypatch, prompt="a prompt")

    call_id = _records(log_path)[0]["call_id"]
    assert len(call_id) == 12
    assert all(c in "0123456789abcdef" for c in call_id)


def test_identical_prompts_get_distinct_call_ids(tmp_path, monkeypatch):
    """call_id identifies a CALL; prompt_hash is a content address that collides by
    design (one hash covered 24 calls across 8 models). Same prompt, different ids."""
    log_path = tmp_path / "calls.jsonl"
    client = OllamaClient()

    _log_one(client, log_path, monkeypatch, prompt="the same prompt")
    _log_one(client, log_path, monkeypatch, prompt="the same prompt")

    first, second = _records(log_path)
    assert first["prompt_hash"] == second["prompt_hash"]
    assert first["call_id"] != second["call_id"]
