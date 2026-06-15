# test_t2_amend_abort.py
#
# End-to-end tests for new --amend and --abort CLI verbs in the handoff pipeline.
# Driven as subprocesses on a real tmp git repo. JSON stdout is the observable contract.

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from test_orchestrator import _setup, _git_init
from test_handoff_cli import _scaffold, _run_payload, _run_id

HANDOFF_DIR = Path(__file__).resolve().parent

# Payload that includes a replace-mode role (current-status) — forbidden in amend mode
AMEND_PAYLOAD_WITH_REPLACE = textwrap.dedent("""\
    ---
    session_title: amend test
    current_layer: Layer X
    checkoffs: [T-99]
    ---
    ## role: current-status

    new status here
""")

# Valid amend payload: checkoff-only (no block roles); empty session_title/current_layer.
# log-entry (prepend) is NOT included — prepend is forbidden in amend mode.
AMEND_PAYLOAD_OK = textwrap.dedent("""\
    ---
    session_title:
    current_layer:
    checkoffs: [T-99]
    ---
""")

# Payload with only a log-entry (structured slots) — must be rejected in amend mode
# (log-entry is prepend mode; amend is additive-only: append+checkoff only)
AMEND_PAYLOAD_PREPEND_ONLY = textwrap.dedent("""\
    ---
    session_title:
    current_layer:
    checkoffs: []
    ---
    ## role: log-entry

    ### what_was_done
    - appended entry body

    ### next
    - next thing

""")


def _amend_run(root, reg, payload_file):
    return subprocess.run(
        [sys.executable, "handoff.py", "--payload", str(payload_file),
         "--amend", "--repo-root", str(root), "--registry", str(reg)],
        cwd=HANDOFF_DIR, capture_output=True, text=True,
    )


def _abort_run(root, reg, handle):
    return subprocess.run(
        [sys.executable, "handoff.py", "--abort", handle,
         "--repo-root", str(root), "--registry", str(reg)],
        cwd=HANDOFF_DIR, capture_output=True, text=True,
    )


# ---- --amend: stage ---------------------------------------------------------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_stage_rejects_replace_role(tmp_path):
    """--amend rejects payloads with replace-mode roles."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_WITH_REPLACE)

    result = _amend_run(root, reg, well_known)

    assert result.returncode != 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "validation_failed"
    assert "amend mode is additive-only" in out["reason"]
    assert well_known.exists()  # file stays — author can re-edit


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_stage_rejects_prepend_role(tmp_path):
    """--amend rejects payloads with prepend-mode roles (log-entry); additive-only means append+checkoff."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_PREPEND_ONLY)

    result = _amend_run(root, reg, well_known)

    assert result.returncode != 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "validation_failed"
    assert "amend mode is additive-only" in out["reason"]
    assert well_known.exists()  # file stays — author can re-edit


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_stage_accepts_checkoff_only(tmp_path):
    """--amend accepts payloads with only checkoff roles (no block roles)."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_OK)

    result = _amend_run(root, reg, well_known)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "stage_ok"
    run_dir = Path(out["run_dir"])
    assert run_dir.exists() and run_dir.name.endswith("-pending")


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_stage_ignores_missing_scalars(tmp_path):
    """--amend accepts empty session_title and current_layer (scalars not required)."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_OK)  # has empty scalars

    result = _amend_run(root, reg, well_known)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "stage_ok"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_stage_session_number_is_current_not_next(tmp_path):
    """Amend stage: reported session_number == current committed N (84), not N+1 (85)."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_OK)

    result = _amend_run(root, reg, well_known)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "stage_ok"
    # Session log has session 84 as last entry; amend must report 84, not 85
    assert out["session_number"] == 84, f"expected 84, got {out['session_number']}"
    run_dir = Path(out["run_dir"])
    assert "session-84" in run_dir.name, f"run_dir should contain 'session-84': {run_dir.name}"
    assert "session-85" not in run_dir.name


# ---- --amend: promote -------------------------------------------------------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_promote_commit_has_amend_suffix(tmp_path):
    """Amend promote: commit message ends with '— amend' (no redundant parens)."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_OK)

    stage_out = json.loads(_amend_run(root, reg, well_known).stdout)
    assert stage_out["status"] == "stage_ok"
    handle = stage_out["handle"]

    result = _run_id(root, reg, handle)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "committed"

    git_log = subprocess.run(
        ["git", "log", "--oneline"], cwd=root, capture_output=True, text=True
    ).stdout
    assert "— amend" in git_log


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_promote_uses_current_session_number(tmp_path):
    """Amend promote: commit message references current session N, not N+1."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    well_known.write_text(AMEND_PAYLOAD_OK)

    stage_out = json.loads(_amend_run(root, reg, well_known).stdout)
    handle = stage_out["handle"]
    _run_id(root, reg, handle)

    git_log = subprocess.run(
        ["git", "log", "--oneline"], cwd=root, capture_output=True, text=True
    ).stdout
    # Session log has session 84 as last; amend should commit as 84 not 85
    assert "session 84" in git_log.lower()
    assert "session 85" not in git_log.lower()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_amend_promote_does_not_touch_header_fields(tmp_path):
    """Amend promote: Current Session and Current Layer header fields are unchanged."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)
    log_path = root / ".claude" / "session-log.md"
    header_before = log_path.read_text()

    well_known.write_text(AMEND_PAYLOAD_OK)
    stage_out = json.loads(_amend_run(root, reg, well_known).stdout)
    handle = stage_out["handle"]
    result = _run_id(root, reg, handle)
    assert result.returncode == 0, result.stderr

    header_after = log_path.read_text()
    # Extract the two header lines and compare
    def _header_lines(text):
        return [l for l in text.splitlines() if l.startswith("**Current")]
    assert _header_lines(header_before) == _header_lines(header_after)


# ---- --abort ----------------------------------------------------------------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_abort_renames_pending_to_aborted(tmp_path):
    """--abort renames -pending dir to -aborted and emits JSON status=aborted."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)

    stage_out = json.loads(_run_payload(root, reg, well_known).stdout)
    assert stage_out["status"] == "stage_ok"
    handle = stage_out["handle"]
    pending_dir = Path(stage_out["run_dir"])

    result = _abort_run(root, reg, handle)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "aborted"
    assert not pending_dir.exists()
    aborted_dir = Path(out["run_dir"])
    assert aborted_dir.name.endswith("-aborted")
    assert aborted_dir.exists()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_abort_fails_if_no_pending_run(tmp_path):
    """--abort with unknown handle exits nonzero with error status."""
    root, reg, _ = _scaffold(tmp_path)
    _git_init(root)

    result = _abort_run(root, reg, "session-99-nonexistent")

    assert result.returncode != 0
    out = json.loads(result.stdout)
    assert out["status"] == "error"
