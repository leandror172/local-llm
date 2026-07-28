"""Characterization tests for call identity across the chat→log seam (T-105, P4-T3).

`call_id` had ZERO test coverage before this file, so the P4-T3 refactor that moves
where it is minted had no regression net (`ref:patterns-refactoring-characterize-first`
rule 3: a suite that never exercises the code proves nothing about it).

**Anchored at the HTTP boundary on purpose.** An earlier draft faked the `response`
object and broke on the refactor — mocking the boundary you ARE changing (rule 4). The
transport is what P4-T3 does not touch, so stubbing httpx keeps both the minting and the
logging inside the tested region. That is what lets the middle test below state the
invariant the field exists for: **the id the caller receives is the id in the log.**

Structural/wiring tests: bespoke imperative per the executable-spec taxonomy
(`ref:test-executable-spec`) — each varies the `given`, not an input sequence.
"""

import json

import httpx

from ollama_mcp.client import OllamaClient

_OLLAMA_BODY = {
    "message": {"content": "hi"},
    "model": "m",
    "prompt_eval_count": 1,
    "eval_count": 2,
    "eval_duration": 3_000_000,  # ns in the wire format; the client divides by 1e6
    "total_duration": 4_000_000,
    "prompt_eval_duration": 5_000_000,
}


class _FakeHttpResponse:
    """The subset of an httpx response that `chat` reads."""

    status_code = 200
    content = b"{}"

    def json(self):
        return _OLLAMA_BODY

    def raise_for_status(self):
        return None


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient — the boundary P4-T3 does NOT change."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, *args, **kwargs):
        return _FakeHttpResponse()


def _records(log_path):
    """Every JSONL record written to `log_path`, in order."""
    with open(log_path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


async def _chat_once(log_path, monkeypatch, prompt):
    """Run one chat call against the stubbed transport and a throwaway log."""
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr("ollama_mcp.client.CALL_LOG_PATH", str(log_path))
    return await OllamaClient().chat(prompt, tool="test")


async def test_call_id_is_twelve_lowercase_hex_chars(tmp_path, monkeypatch):
    """The id shape is load-bearing: verdict-capture matched `[a-f0-9]+`, so a non-hex
    call_id would have been rejected silently rather than loudly."""
    log_path = tmp_path / "calls.jsonl"

    await _chat_once(log_path, monkeypatch, prompt="a prompt")

    call_id = _records(log_path)[0]["call_id"]
    assert len(call_id) == 12
    assert all(c in "0123456789abcdef" for c in call_id)


async def test_response_call_id_matches_the_logged_record(tmp_path, monkeypatch):
    """THE JOIN KEY. Without a shared id the only common column is run_id, which is
    per-RUN — so per-iteration matching would be positional, the fallback T-105 banned
    ("when identity is unknown, stay silent; mislabeled is worse than missing")."""
    log_path = tmp_path / "calls.jsonl"

    response = await _chat_once(log_path, monkeypatch, prompt="a prompt")

    assert response.call_id
    assert response.call_id == _records(log_path)[0]["call_id"]


async def test_identical_prompts_get_distinct_call_ids(tmp_path, monkeypatch):
    """call_id identifies a CALL; prompt_hash is a content address that collides by
    design (one hash covered 24 calls across 8 models). Same prompt, different ids."""
    log_path = tmp_path / "calls.jsonl"

    await _chat_once(log_path, monkeypatch, prompt="the same prompt")
    await _chat_once(log_path, monkeypatch, prompt="the same prompt")

    first, second = _records(log_path)
    assert first["prompt_hash"] == second["prompt_hash"]
    assert first["call_id"] != second["call_id"]
