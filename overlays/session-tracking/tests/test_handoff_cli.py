# test_handoff_cli.py
#
# End-to-end tests for the new --payload (stage) / --id (promote) CLI.
# Driven as subprocesses on a real tmp git repo. JSON stdout is the
# observable contract — all assertions parse result.stdout as JSON.
#
# Flat imports — run from inside the handoff dir.

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from test_orchestrator import _setup, _git_init

# Subprocess CLI tests run the packaged module from the src root, so `-m` resolves.
SRC_DIR = Path(__file__).resolve().parent.parent / "src"

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

PAYLOAD = textwrap.dedent("""\
    ---
    session_title: CLI test
    current_layer: New layer text
    checkoffs: [T-99]
    ---
    ## role: log-entry

    ### context
    resumed from prior session

    ### what_was_done
    - tested the CLI stage/promote flow

    ### next
    - run full suite

    ## role: current-status

    new status here
""")

BAD_PAYLOAD = textwrap.dedent("""\
    ---
    session_title: X
    current_layer: Y
    ---
    ## role: bogus-role

    content
""")


def _scaffold(tmp_path, payload_text=PAYLOAD):
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


def _run_id(root, reg, handle):
    return subprocess.run(
        [sys.executable, "-m", "sessiontracking.handoff.cli", "--id", handle,
         "--repo-root", str(root), "--registry", str(reg)],
        cwd=SRC_DIR, capture_output=True, text=True,
    )


# ---- --payload: stage -------------------------------------------------------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_payload_creates_pending_dir_moves_file_emits_json(tmp_path):
    """--payload: creates -pending run dir, moves file off well-known path, emits stage_ok JSON."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)

    result = _run_payload(root, reg, well_known)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "stage_ok"
    assert "handle" in out and out["handle"]
    assert not well_known.exists()  # moved by shutil.move
    run_dir = Path(out["run_dir"])
    assert run_dir.exists() and run_dir.name.endswith("-pending")
    assert (run_dir / "input.md").exists()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_payload_validation_failure_no_run_dir_file_stays(tmp_path):
    """--payload: validation failure leaves file at well-known path and creates no run dir."""
    root, reg, well_known = _scaffold(tmp_path, payload_text=BAD_PAYLOAD)
    _git_init(root)

    result = _run_payload(root, reg, well_known)

    assert result.returncode != 0
    out = json.loads(result.stdout)
    assert out["status"] == "validation_failed"
    assert well_known.exists()  # NOT moved — model can re-edit in place
    assert not (root / ".claude" / "local" / "handoff-runs").exists()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_payload_json_has_required_fields(tmp_path):
    """--payload stage_ok JSON contains all fields the model needs to parse."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)

    result = _run_payload(root, reg, well_known)

    out = json.loads(result.stdout)
    for field in ("handle", "status", "session_number", "regions", "run_dir",
                  "report_path", "reason", "run_counts"):
        assert field in out, f"missing field: {field}"
    assert isinstance(out["run_counts"], dict)
    for key in ("pending", "success", "failed"):
        assert key in out["run_counts"]


# ---- --id: promote ----------------------------------------------------------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_id_promotes_commits_and_renames_dir(tmp_path):
    """--id: applies, commits, renames -pending → -success, emits committed JSON."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)

    stage = json.loads(_run_payload(root, reg, well_known).stdout)
    assert stage["status"] == "stage_ok"
    handle = stage["handle"]

    result = _run_id(root, reg, handle)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "committed"
    git_log = subprocess.run(["git", "log", "--oneline"], cwd=root,
                             capture_output=True, text=True).stdout
    assert "session 85" in git_log.lower()
    run_dir = Path(out["run_dir"])
    assert run_dir.name.endswith("-success")
    assert "new status here" in (root / ".claude/session-context.md").read_text()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_id_idempotent_commit_exists_but_dir_still_pending(tmp_path):
    """Crash-recovery: --id reconciles to -success and returns committed when commit is
    already in git log but dir is still -pending (died between commit and rename)."""
    root, reg, well_known = _scaffold(tmp_path)
    _git_init(root)

    # Stage
    stage_out = json.loads(_run_payload(root, reg, well_known).stdout)
    handle = stage_out["handle"]
    pending_dir = Path(stage_out["run_dir"])

    # Promote (commits + renames to -success)
    promote_out = json.loads(_run_id(root, reg, handle).stdout)
    success_dir = Path(promote_out["run_dir"])
    assert success_dir.name.endswith("-success")

    # Simulate crash: rename dir back to -pending
    shutil.move(str(success_dir), str(pending_dir))
    assert pending_dir.exists()

    # Second --id: commit already in git log, dir is -pending → reconcile + return committed
    result = _run_id(root, reg, handle)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "committed"
    count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    assert count == "2"  # init + 1 handoff (no double-commit)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_id_missing_handle_exits_nonzero(tmp_path):
    """--id with a handle that has no pending dir exits nonzero."""
    root, reg, _ = _scaffold(tmp_path)
    _git_init(root)

    result = _run_id(root, reg, "session-99-nonexistent")

    assert result.returncode != 0


# ---- mutual exclusivity / arg errors ----------------------------------------

def test_payload_and_id_are_mutually_exclusive(tmp_path):
    """Passing both --payload and --id is a CLI error."""
    root, reg, well_known = _scaffold(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "sessiontracking.handoff.cli", "--payload", str(well_known),
         "--id", "some-handle", "--repo-root", str(root), "--registry", str(reg)],
        cwd=SRC_DIR, capture_output=True, text=True,
    )
    assert result.returncode != 0
