import subprocess
import json
import os
import sys
from pathlib import Path

def _run_hook(stdin_text: str) -> tuple[int, str]:
    default = Path(__file__).parent.parent / "oficina-watch-hook.py"
    hook_path = Path(os.environ.get("HOOK_PATH", default))
    if not hook_path.exists():
        raise FileNotFoundError(f"Hook script not found at {hook_path}")
    
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=stdin_text,
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode, result.stdout

def _envelope(tool_name: str, tool_response: dict) -> str:
    return json.dumps({
        "session_id": "s1",
        "cwd": "/tmp",
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": {},
        "tool_response": tool_response
    })

def _assert_watch_output(stdout: str, run_id: str) -> None:
    parsed = json.loads(stdout)
    inner = parsed["hookSpecificOutput"]
    assert inner["hookEventName"] == "PostToolUse"
    assert run_id in inner["additionalContext"]
    assert "watch-run.sh" in inner["additionalContext"]

def test_submit_success_nested_escaped_json_emits_watch_instruction() -> None:
    tool_response = {"result": "{\"run_id\": \"E98GDtbLL-4MAEfo0mjctw\", \"watch_cmd\": \"oficina watch E98GDtbLL-4MAEfo0mjctw\", \"queue_position\": 1}"}
    stdin_text = _envelope("mcp__ollama-bridge__submit_run", tool_response)
    returncode, stdout = _run_hook(stdin_text)
    assert returncode == 0
    _assert_watch_output(stdout, "E98GDtbLL-4MAEfo0mjctw")

def test_submit_success_plain_dict_response_emits_watch_instruction() -> None:
    tool_response = {"run_id": "abc-DEF_123", "watch_cmd": "oficina watch abc-DEF_123"}
    stdin_text = _envelope("mcp__ollama-bridge__submit_run", tool_response)
    returncode, stdout = _run_hook(stdin_text)
    assert returncode == 0
    _assert_watch_output(stdout, "abc-DEF_123")

def test_error_response_emits_nothing() -> None:
    tool_response = {"result": "Error: invalid spec — missing objective"}
    stdin_text = _envelope("mcp__ollama-bridge__submit_run", tool_response)
    returncode, stdout = _run_hook(stdin_text)
    assert returncode == 0
    assert stdout.strip() == ""

def test_unparseable_stdin_exits_zero_silently() -> None:
    returncode, stdout = _run_hook("not json {{{")
    assert returncode == 0
    assert stdout.strip() == ""

def test_other_tool_name_emits_nothing() -> None:
    tool_response = {"run_id": "should-not-fire"}
    stdin_text = _envelope("mcp__ollama-bridge__generate_code", tool_response)
    returncode, stdout = _run_hook(stdin_text)
    assert returncode == 0
    assert stdout.strip() == ""

if __name__ == "__main__":
    test_functions = [
        test_submit_success_nested_escaped_json_emits_watch_instruction,
        test_submit_success_plain_dict_response_emits_watch_instruction,
        test_error_response_emits_nothing,
        test_unparseable_stdin_exits_zero_silently,
        test_other_tool_name_emits_nothing
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
