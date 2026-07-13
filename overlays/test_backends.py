"""Tests for lib.backends — num_ctx sizing + wall-clock deadline (T-81 Part 2).

Plain sync pytest, hermetic (urllib is monkeypatched — no network).

Run from overlays/:
    python3 -m pytest test_backends.py -q
"""

import json
import sys
from pathlib import Path

# Ensure overlays/ is on path so `from lib.backends import ...` resolves.
sys.path.insert(0, str(Path(__file__).parent))

from lib.backends import OllamaApiBackend, fit_num_ctx


# ── fit_num_ctx: pure function ──────────────────────────────────────────────


def test_fit_num_ctx_small_prompt_uses_smallest_bucket():
    """~500-char prompt: 500//4 + 1024 = 1149 → smallest bucket 4096."""
    assert fit_num_ctx(500) == 4096, "small prompt should use the 4096 bucket"


def test_fit_num_ctx_claude_md_class_input_grows_past_4096():
    """The CLAUDE.md-class input that used to overflow.

    16384//4 + 1024 = 5120 → bucket 8192. The `!= 4096` assertion is the RC1
    regression guard: the old fixed constant truncated exactly this input.
    """
    result = fit_num_ctx(16384)
    assert result == 8192, f"~16 KB prompt should size to 8192, got {result}"
    assert result != 4096, "RC1 regression guard: must not stay at the 4096 constant"


def test_fit_num_ctx_caps_at_ceiling():
    """Enormous prompt caps at the probed 14B ceiling (32768), never higher."""
    assert fit_num_ctx(100_000_000) == 32768, "must cap at the 32768 VRAM ceiling"


# ── mock plumbing ───────────────────────────────────────────────────────────


class _FakeResp:
    """Context-manager + line-iterable stand-in for a urllib streaming response.

    The real OllamaApiBackend.call iterates `for line in resp` over byte lines,
    so the fake must be iterable (not `.read()`-based) and support `with`.
    """

    def __init__(self, lines):
        self._lines = list(lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(self._lines)


def _done_line():
    return b'{"message":{"content":"{}"},"done":true}\n'


# ── call(): num_ctx is computed from the prompt, independent of fmt ──────────


def test_call_computes_ctx_from_prompt_not_constant(monkeypatch):
    """call() must size num_ctx from prompt length, INDEPENDENT of `fmt`.

    Kills the old `num_ctx = 4096 if fmt is not None else 8192` branch: same
    prompt → same num_ctx whether or not a format schema is passed.
    """
    import urllib.request

    backend = OllamaApiBackend({
        "id": "x",
        "address": "http://localhost:11434/api/chat",
        "model": "qwen3:14b",
    })

    captured = []

    def fake_urlopen(req, *args, **kwargs):
        # Capture the ACTUAL payload the backend built (not a fabricated one).
        captured.append(json.loads(req.data.decode()))
        return _FakeResp([_done_line()])

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    prompt = "x" * 8000
    expected = fit_num_ctx(len(prompt))

    # fmt=None
    out_none = backend.call(prompt, fmt=None)
    assert out_none == "{}", "should return the joined message content"
    assert captured[0]["options"]["num_ctx"] == expected, (
        f"num_ctx should be fit_num_ctx(len(prompt))={expected}, "
        f"got {captured[0]['options']['num_ctx']}"
    )

    # fmt set → num_ctx must be IDENTICAL (independent of fmt)
    backend.call(prompt, fmt={"type": "object"})
    assert captured[1]["options"]["num_ctx"] == expected, (
        "num_ctx must not depend on fmt — same prompt must yield the same ctx"
    )
    assert captured[0]["options"]["num_ctx"] == captured[1]["options"]["num_ctx"]


# ── call(): overall wall-clock deadline returns None (no exception) ──────────


def test_call_returns_none_on_wall_clock_deadline(monkeypatch):
    """An expired merge deadline aborts the stream and returns None.

    A timeout is not a quality failure — the caller (planner) treats None as
    "add manually". Assert: returns None, no exception, no partial content.
    """
    import urllib.request

    backend = OllamaApiBackend({
        "id": "x",
        "address": "http://localhost:11434/api/chat",
        "model": "qwen3:14b",
        "merge_timeout_s": -1,  # already-expired deadline trips on first iteration
    })

    def fake_urlopen(req, *args, **kwargs):
        # Streams content chunks but never a done:true — forces the loop to
        # keep going so the wall-clock check is what stops it.
        return _FakeResp([
            b'{"message":{"content":"partial-1"},"done":false}\n',
            b'{"message":{"content":"partial-2"},"done":false}\n',
        ])

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = backend.call(prompt="hi", fmt=None)
    assert result is None, "an expired wall-clock deadline must return None"
