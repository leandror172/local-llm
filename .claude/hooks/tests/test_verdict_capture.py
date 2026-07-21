#!/usr/bin/env python3
"""Tests for the verdict-capture harness (T-105).

Covers the producer→consumer seam, not just the parser. The 2026-03 build was
verified with a hand-authored fixture block fed straight to the regex; that test
passed for five months while the harness captured almost nothing, because nothing
checked that the *injected template* is what the *consumer* accepts. The
round-trip test here is the one that would have failed on day one — and it does
fail if either side's key name drifts (mutation-verified 2026-07-21).

Both hooks resolve their log via ``Path.home()`` module constants with no env
override, so every test runs the hook in a subprocess with HOME pointed at a
fresh temp dir.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
POST_TOOL = HOOKS_DIR / "ollama-post-tool.py"
CAPTURE = HOOKS_DIR / "verdict-capture.py"


# --- fixture helpers -------------------------------------------------------

def write_calls(home: Path, records: list) -> Path:
    """Write a fake calls.jsonl under `home`, one JSON object per line."""
    log = home / ".local/share/ollama-bridge/calls.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return log


def write_transcript(path: Path, text: str) -> Path:
    """Write a one-line transcript holding `text` as assistant output."""
    entry = {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }
    path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    return path


def block(key: str, value: str, verdict: int, reason: str, tokens: int = 100) -> str:
    """Build a filled verdict block keyed by `key` (call_id or prompt_hash)."""
    return (
        f"[VERDICT {key}={value}]\n"
        f"verdict: {verdict}\n"
        f"reason: {reason}\n"
        f"est_claude_tokens: {tokens}\n"
        "[/VERDICT]"
    )


def call(call_id: str, prompt_hash: str, response: str, tool: str = "generate_code") -> dict:
    return {
        "ts": "2026-07-21T00:00:00Z",
        "call_id": call_id,
        "tool": tool,
        "model": "m",
        "prompt_hash": prompt_hash,
        "response": response,
    }


def verdict_record(call_id: str, prompt_hash: str) -> dict:
    return {
        "type": "verdict",
        "ts": "2026-07-21T00:00:00Z",
        "call_id": call_id,
        "prompt_hash": prompt_hash,
        "verdict": 2,
        "reason": "first",
        "est_claude_tokens": 10,
    }


def _run(hook: Path, home: Path, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home)},
    )


def run_post_tool(home: Path, tool_name: str, returned: str):
    """Fire the PostToolUse hook; return the injected template text, or None."""
    proc = _run(
        POST_TOOL,
        home,
        {"tool_name": tool_name, "tool_response": json.dumps({"result": returned})},
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout or "{}")
    return out.get("hookSpecificOutput", {}).get("additionalContext")


def run_capture(home: Path, transcript: Path) -> None:
    proc = _run(
        CAPTURE, home, {"hook_event_name": "Stop", "transcript_path": str(transcript)}
    )
    assert proc.returncode == 0, proc.stderr


def read_verdicts(home: Path) -> list:
    log = home / ".local/share/ollama-bridge/calls.jsonl"
    out = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("type") == "verdict":
            out.append(rec)
    return out


# --- the seam --------------------------------------------------------------

def test_injected_template_is_parseable_once_filled():
    """Round-trip: what the injector emits must be what the consumer accepts."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(home, [call("aaa111bbb222", "beef00000001", "ALPHA")])
        template = run_post_tool(home, "mcp__ollama-bridge__generate_code", "ALPHA")
        assert template is not None, "no template injected for a judgeable tool"

        # Fill it exactly as an agent would: substitute the three placeholder lines.
        filled = template
        for placeholder, value in (
            ("verdict: 0 | 1 | 2", "verdict: 2"),
            ("reason: <one line>", "reason: clean"),
            ("est_claude_tokens: <number", "est_claude_tokens: 120"),
        ):
            line = next(ln for ln in filled.splitlines() if ln.startswith(placeholder))
            filled = filled.replace(line, value)

        write_transcript(home / "t.jsonl", filled)
        run_capture(home, home / "t.jsonl")

        verdicts = read_verdicts(home)
        assert len(verdicts) == 1, f"expected 1 verdict, got {len(verdicts)}"
        assert verdicts[0]["call_id"] == "aaa111bbb222"
        assert verdicts[0]["verdict"] == 2


# --- producer side ---------------------------------------------------------

def test_post_tool_skips_non_judgeable_tool():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(home, [call("aaa111bbb222", "beef00000001", "ALPHA")])
        assert run_post_tool(home, "mcp__ollama-bridge__summarize", "ALPHA") is None


def test_post_tool_matches_call_by_response_content():
    """The right record, not merely the last one."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(
            home,
            [
                call("aaa111bbb222", "hash00000001", "ALPHA"),
                call("ccc333ddd444", "hash00000002", "BETA"),
                call("eee555fff666", "hash00000003", "GAMMA"),
            ],
        )
        template = run_post_tool(home, "mcp__ollama-bridge__generate_code", "BETA")
        assert template is not None
        assert "call_id=ccc333ddd444" in template
        assert "eee555fff666" not in template, "tail record won over the content match"


def test_post_tool_stays_silent_when_nothing_matches():
    """A backgrounded call is not yet logged; naming the previous call would mislabel."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(home, [call("aaa111bbb222", "hash00000001", "ALPHA")])
        assert run_post_tool(home, "mcp__ollama-bridge__generate_code", "NOT LOGGED") is None


# --- consumer side ---------------------------------------------------------

def test_capture_writes_both_call_id_and_prompt_hash():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(home, [call("aaa111bbb222", "beef00000001", "ALPHA")])
        write_transcript(home / "t.jsonl", block("call_id", "aaa111bbb222", 2, "clean"))
        run_capture(home, home / "t.jsonl")

        verdicts = read_verdicts(home)
        assert len(verdicts) == 1
        assert verdicts[0]["call_id"] == "aaa111bbb222"
        assert verdicts[0]["prompt_hash"] == "beef00000001"
        assert verdicts[0]["tool"] == "generate_code"


def test_capture_accepts_legacy_prompt_hash_form():
    """Blocks written before T-105 still land, and resolve to the call's call_id."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(home, [call("eee555fff666", "1eaced000001", "GAMMA")])
        write_transcript(home / "t.jsonl", block("prompt_hash", "1eaced000001", 2, "legacy"))
        run_capture(home, home / "t.jsonl")

        verdicts = read_verdicts(home)
        assert len(verdicts) == 1
        assert verdicts[0]["call_id"] == "eee555fff666"


def test_capture_dedupes_on_call_id():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(
            home,
            [
                call("aaa111bbb222", "beef00000001", "ALPHA"),
                verdict_record("aaa111bbb222", "beef00000001"),
            ],
        )
        write_transcript(home / "t.jsonl", block("call_id", "aaa111bbb222", 0, "replay"))
        run_capture(home, home / "t.jsonl")

        assert len(read_verdicts(home)) == 1


def test_identical_prompts_get_independent_verdicts():
    """Regression: one prompt_hash covered 24 calls across 8 models.

    Deduping on prompt_hash meant that once any sibling was judged, none of the
    others could ever be — so a compare-models sweep could record exactly one
    verdict. Keying on call_id is what makes the siblings independent.
    """
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        write_calls(
            home,
            [
                call("aaa111bbb222", "dup00000hash", "ALPHA"),
                call("ccc333ddd444", "dup00000hash", "BETA"),
                verdict_record("aaa111bbb222", "dup00000hash"),
            ],
        )
        write_transcript(home / "t.jsonl", block("call_id", "ccc333ddd444", 1, "sibling"))
        run_capture(home, home / "t.jsonl")

        verdicts = read_verdicts(home)
        assert len(verdicts) == 2, f"sibling call was not independently judgeable: {verdicts}"
        assert {v["call_id"] for v in verdicts} == {"aaa111bbb222", "ccc333ddd444"}


if __name__ == "__main__":
    test_functions = [
        test_injected_template_is_parseable_once_filled,
        test_post_tool_skips_non_judgeable_tool,
        test_post_tool_matches_call_by_response_content,
        test_post_tool_stays_silent_when_nothing_matches,
        test_capture_writes_both_call_id_and_prompt_hash,
        test_capture_accepts_legacy_prompt_hash_form,
        test_capture_dedupes_on_call_id,
        test_identical_prompts_get_independent_verdicts,
    ]
    failed = False
    for test_func in test_functions:
        try:
            test_func()
            print(f"PASS {test_func.__name__}")
        except AssertionError as exc:
            print(f"FAIL {test_func.__name__}: {exc}")
            failed = True
    sys.exit(1 if failed else 0)
