# test_failure_clarity.py
#
# Contract guard: every failure exit must carry where + whose fault + what.
# Tests here prevent regression to bare, opaque error strings.
#
# Run from the handoff dir: python3 -m pytest test_failure_clarity.py -q

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from sessiontracking.handoff.verifier import verify, VerifyError
from sessiontracking.register.locator import Region, LocatorError, locate
from sessiontracking.handoff.orchestrator import stage_and_apply, _apply_all
from test_orchestrator import _setup, _git_init, REGISTER, _payload, CLOCK, TASKS

# Subprocess CLI tests run the packaged module from the src root, so `-m` resolves.
SRC_DIR = Path(__file__).resolve().parent.parent / "src"


# ---------------------------------------------------------------------------
# 1. Append+checkoff combo succeeds end-to-end
# ---------------------------------------------------------------------------

def test_append_checkoff_combo_verifies_end_to_end(tmp_path):
    """Integration: stage_and_apply must succeed when a payload has both tasks-append
    and a checkoff targeting a task inside the append region."""
    # Extend the standard REGISTER with a tasks-append role
    register = {
        **REGISTER,
        "tasks-append": {
            "file": ".claude/tasks.md",
            "locator": {"type": "ref_block", "key": "active-tasks"},
            "write_mode": "append",
        },
        "tasks-checkoff": {
            "file": ".claude/tasks.md",
            "locator": {"type": "checklist", "scope": "file"},
            "write_mode": "checkoff",
        },
    }

    tasks_content = (
        "# Tasks\n"
        "\n"
        "<!-- ref:active-tasks -->\n"
        "## Active\n"
        "- [ ] (T-01) existing task\n"
        "<!-- /ref:active-tasks -->\n"
    )

    root = _setup(tmp_path)
    (root / ".claude" / "tasks.md").write_text(tasks_content)

    from sessiontracking.handoff.mechanics import LogEntry
    from sessiontracking.handoff.orchestrator import HandoffPayload
    payload = HandoffPayload(
        session_title="combo test",
        current_layer="Layer X",
        blocks={"tasks-append": "- [ ] (T-02) new task\n"},
        log_entry=None,
        checkoffs=["T-01"],
        raw="verbatim",
    )
    # Must not raise
    stage_and_apply(root, register, payload, clock=CLOCK, amend=True)


# ---------------------------------------------------------------------------
# 2a. Internal equality-mismatch raise: inject divergence
# ---------------------------------------------------------------------------

def test_verifiy_mismatch_message_names_file_roles_and_byte(tmp_path):
    """VerifyError from a byte mismatch (line 81) names TOOL BUG, file, roles, byte."""
    original = (
        "<!-- ref:deferred-infra -->\n"
        "## Deferred\n"
        "- [ ] (T-05) something\n"
        "<!-- /ref:deferred-infra -->\n"
    )
    interior_start = original.index("## Deferred")
    interior_end = original.index("<!-- /ref:deferred-infra -->")
    region = Region(
        kind="ref_block", mode="append",
        start=interior_start, end=interior_end,
        interior=original[interior_start:interior_end],
        role="tasks-append", target="deferred-infra", file=".claude/tasks.md",
    )
    content = "- [ ] (T-06) new task\n"
    # Correct modified: insertion at region.end
    correct_modified = original[:region.end] + content + original[region.end:]
    # Corrupt it by flipping one byte to trigger the mismatch
    corrupt_modified = correct_modified[:10] + "X" + correct_modified[11:]

    edits = [(region, content)]
    with pytest.raises(VerifyError) as exc_info:
        verify(original, corrupt_modified, edits)

    err = exc_info.value
    msg = str(err)
    assert "TOOL BUG" in msg, f"Expected TOOL BUG in: {msg}"
    assert ".claude/" in msg, f"Expected file path in: {msg}"
    assert "roles" in msg, f"Expected 'roles' in: {msg}"
    assert "byte" in msg, f"Expected 'byte' in: {msg}"
    assert err.kind == "internal"


# ---------------------------------------------------------------------------
# 2b. Ref-marker mismatch raise
# ---------------------------------------------------------------------------

def test_verify_marker_mismatch_message_names_tool_bug_and_lost():
    """VerifyError from a marker gain (replace content introduces a new ref marker) names TOOL BUG and lost=.

    To reach line 91 (marker check), the byte check at line 81 must pass first, meaning
    expected == modified. We achieve this by making the replacement content itself introduce
    a new ref marker — the reconstruction also produces this marker (byte check passes),
    but the marker multiset now differs from the original (marker check fires).
    """
    original = (
        "<!-- ref:current-status -->\n"
        "old content\n"
        "<!-- /ref:current-status -->\n"
    )
    interior_start = original.index("old content")
    interior_end = original.index("<!-- /ref:current-status -->")
    region = Region(
        kind="ref_block", mode="replace",
        start=interior_start, end=interior_end,
        interior="old content\n",
        role="current-status", target="current-status", file=".claude/session-context.md",
    )
    # New content deliberately introduces an extra marker — byte check passes, marker check fires
    content = "<!-- ref:sneaky -->\nstuff\n<!-- /ref:sneaky -->\n"
    modified = original[:region.start] + content + original[region.end:]
    # modified now has 4 markers; original has 2 → marker multiset differs

    edits = [(region, content)]
    with pytest.raises(VerifyError) as exc_info:
        verify(original, modified, edits)

    err = exc_info.value
    msg = str(err)
    assert "TOOL BUG" in msg, f"Expected TOOL BUG in: {msg}"
    assert "lost=" in msg or "gained=" in msg, f"Expected lost=/gained= in: {msg}"
    assert err.kind == "internal"


# ---------------------------------------------------------------------------
# 3. Locator miss: message names task id and file, kind="payload"
# ---------------------------------------------------------------------------

def test_locator_miss_names_task_id_and_file():
    """LocatorError on a non-existent task id must carry kind=payload.

    The message-content assertions (task id + file path) are xfail because the locator
    message enrichment is Step 2.3, handled by Agent B. Once B enriches the message,
    these xfail markers should be removed.
    """
    role_def = {
        "locator": {"type": "checklist", "scope": "file"},
        "write_mode": "checkoff",
        "file": ".claude/tasks.md",
    }
    text = "- [ ] (T-01) existing task\n"
    with pytest.raises(LocatorError) as exc_info:
        locate(role_def, text, task_id="T-99")
    err = exc_info.value
    msg = str(err)
    assert err.kind == "payload"
    # xfail: message enrichment is Step 2.3 (Agent B). After B's pass, strip the xfail markers.
    if "T-99" not in msg:
        pytest.xfail("locator message not yet enriched with task id (Step 2.3 pending)")
    assert "T-99" in msg, f"Expected task id in: {msg}"
    if ".claude/tasks.md" not in msg:
        pytest.xfail("locator message not yet enriched with file path (Step 2.3 pending)")
    assert ".claude/tasks.md" in msg, f"Expected file path in: {msg}"


# ---------------------------------------------------------------------------
# 4a. CLI classification: payload_error for a checkoff miss
# ---------------------------------------------------------------------------

REGISTRY_YAML = textwrap.dedent("""\
    version: 1
    roles:
      log-entry:
        file: .claude/session-log.md
        locator: {type: structural, pattern: '^---$', occurrence: 1, position: after}
        write_mode: prepend
      header-current-session:
        file: .claude/session-log.md
        locator: {type: field, label: Current Session}
        write_mode: nomodel
      header-current-layer:
        file: .claude/session-log.md
        locator: {type: field, label: Current Layer}
        write_mode: nomodel
      current-status:
        file: .claude/session-context.md
        locator: {type: ref_block, key: current-status}
        write_mode: replace
      tasks-checkoff:
        file: .claude/tasks.md
        locator: {type: checklist, scope: file}
        write_mode: checkoff
""")

# Payload that checks off T-99 — but the tasks.md in _setup has T-99, so we use T-00 (absent)
PAYLOAD_CHECKOFF_MISS = textwrap.dedent("""\
    ---
    session_title: clarity test
    current_layer: Layer X
    checkoffs: [T-00]
    ---
    ## role: current-status

    new status
""")


def _scaffold(tmp_path, payload_text):
    root = _setup(tmp_path)
    reg = root / ".claude/handoff/registry.yaml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(REGISTRY_YAML)
    rotate = root / ".claude/tools/rotate-session-log.sh"
    rotate.parent.mkdir(parents=True, exist_ok=True)
    rotate.write_text("#!/bin/sh\nexit 0\n")
    rotate.chmod(0o755)
    well_known = root / ".claude" / "local" / "handoff-pending.md"
    well_known.parent.mkdir(parents=True, exist_ok=True)
    well_known.write_text(payload_text)
    return root, reg, well_known


def _run_payload(root, reg, payload_file):
    return subprocess.run(
        [sys.executable, "-m", "sessiontracking.handoff.cli", "--payload", str(payload_file),
         "--repo-root", str(root), "--registry", str(reg)],
        cwd=SRC_DIR, capture_output=True, text=True,
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_cli_payload_error_for_checkoff_miss(tmp_path):
    """CLI: a checkoff for a non-existent task id → status=payload_error."""
    root, reg, well_known = _scaffold(tmp_path, PAYLOAD_CHECKOFF_MISS)
    _git_init(root)

    result = _run_payload(root, reg, well_known)

    assert result.returncode != 0
    out = json.loads(result.stdout)
    assert out["status"] == "payload_error", f"Expected payload_error, got: {out}"


# ---------------------------------------------------------------------------
# 4b. CLI classification: internal_tool_bug via monkeypatched applier
# ---------------------------------------------------------------------------

PAYLOAD_VALID = textwrap.dedent("""\
    ---
    session_title: clarity test
    current_layer: Layer X
    checkoffs: []
    ---
    ## role: current-status

    new status
""")


def test_cli_internal_tool_bug_for_verify_mismatch(tmp_path, monkeypatch):
    """CLI stage path: a VerifyError(kind=internal) → status=internal_tool_bug with input.md mention.

    monkeypatch _apply_all to return corrupted text, drive _stage_path in-process.
    (subprocess cannot receive monkeypatching, so we call handoff._stage_path directly.)
    """
    from sessiontracking.handoff import orchestrator as _orch
    from sessiontracking.handoff import cli as _handoff
    import datetime

    original_apply_all = _orch._apply_all

    def corrupted_apply_all(text, items):
        result = original_apply_all(text, items)
        # Corrupt one byte so verify() raises VerifyError(kind="internal")
        if len(result) > 10:
            return result[:5] + "X" + result[6:]
        return result

    monkeypatch.setattr(_orch, "_apply_all", corrupted_apply_all)

    root, reg, well_known = _scaffold(tmp_path, PAYLOAD_VALID)
    _git_init(root)

    import io, contextlib
    from sessiontracking.register.registry_io import load_register
    from sessiontracking.handoff.gitio import SubprocessGit

    register = load_register(reg)
    git = SubprocessGit(root)

    # Capture stdout
    captured = []
    original_print = __builtins__["print"] if isinstance(__builtins__, dict) else print
    import builtins
    original_print = builtins.print

    printed_lines = []
    def capturing_print(*args, **kwargs):
        if args and isinstance(args[0], str):
            printed_lines.append(args[0])
        original_print(*args, **kwargs)

    monkeypatch.setattr(builtins, "print", capturing_print)

    # Build args namespace
    import argparse
    args = argparse.Namespace(
        payload=str(well_known),
        amend=False,
        repo_root=str(root),
        registry=str(reg),
    )

    rc = _handoff._stage_path(args, root, register, git)

    monkeypatch.setattr(builtins, "print", original_print)

    assert rc != 0, f"Expected non-zero return code"
    assert printed_lines, "Expected printed output"
    out = json.loads(printed_lines[0])
    assert out["status"] == "internal_tool_bug", f"Expected internal_tool_bug, got: {out}"
    assert "input.md" in out["reason"], f"Expected input.md in reason: {out['reason']}"
