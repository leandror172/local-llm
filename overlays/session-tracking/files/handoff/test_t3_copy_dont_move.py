# test_t3_copy_dont_move.py
#
# Tests for T3 — copy-don't-move payload on failed stage.
# On success: original file removed (well-known path freed).
# On stage failure: original file stays, failed run dir gets input.md.

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from test_orchestrator import _setup, _git_init
from test_handoff_cli import _scaffold, REGISTRY_YAML

HANDOFF_DIR = Path(__file__).resolve().parent

# Payload that references a missing ref-block key → stage_and_apply will fail (locate error)
BROKEN_PAYLOAD = textwrap.dedent("""\
    ---
    session_title: stage fail test
    current_layer: Layer X
    checkoffs: []
    ---
    ## role: current-status

    <!-- ref:NONEXISTENT_KEY -->
    content that references missing markers
""")

# Registry with an extra role that will cause a locate failure when applied
# (the current-status block has bad content but the role is valid in registry)
REGISTRY_WITH_EXTRA_ROLE = textwrap.dedent("""\
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
      missing-block:
        file: .claude/session-context.md
        locator: {type: ref_block, key: NONEXISTENT_KEY}
        write_mode: replace
""")

PAYLOAD_WITH_MISSING_ROLE = textwrap.dedent("""\
    ---
    session_title: stage fail test
    current_layer: Layer X
    checkoffs: []
    ---
    ## role: missing-block

    some content
""")


def _scaffold_with_registry(tmp_path, registry_text, payload_text):
    root = _setup(tmp_path)
    reg = root / ".claude/handoff/registry.yaml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(registry_text)
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
        [sys.executable, "handoff.py", "--payload", str(payload_file),
         "--repo-root", str(root), "--registry", str(reg)],
        cwd=HANDOFF_DIR, capture_output=True, text=True,
    )


# ---- success case (existing behavior): file removed after stage_ok -----------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_success_stage_removes_original_file(tmp_path):
    """On stage_ok, original file at well-known path is removed (well-known path freed)."""
    from test_handoff_cli import _scaffold, PAYLOAD
    root, reg, well_known = _scaffold(tmp_path, payload_text=PAYLOAD)
    _git_init(root)

    result = _run_payload(root, reg, well_known)

    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["status"] == "stage_ok"
    assert not well_known.exists(), "Original file should be removed after successful stage"
    run_dir = Path(out["run_dir"])
    assert (run_dir / "input.md").exists()


# ---- failure case: file stays, failed run dir gets input.md -----------------

@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_failed_stage_original_file_stays(tmp_path):
    """On stage failure (locate error), original file remains at its original path."""
    root, reg, well_known = _scaffold_with_registry(
        tmp_path, REGISTRY_WITH_EXTRA_ROLE, PAYLOAD_WITH_MISSING_ROLE
    )
    _git_init(root)
    original_content = well_known.read_text()

    result = _run_payload(root, reg, well_known)

    assert result.returncode != 0
    out = json.loads(result.stdout)
    assert out["status"] == "stage_failed"
    # Original file must still exist at the original path
    assert well_known.exists(), "Original file must remain after failed stage"
    assert well_known.read_text() == original_content


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_failed_stage_run_dir_has_input_md(tmp_path):
    """On stage failure, the failed run dir still contains input.md (copy was made)."""
    root, reg, well_known = _scaffold_with_registry(
        tmp_path, REGISTRY_WITH_EXTRA_ROLE, PAYLOAD_WITH_MISSING_ROLE
    )
    _git_init(root)

    result = _run_payload(root, reg, well_known)

    assert result.returncode != 0
    out = json.loads(result.stdout)
    assert out["status"] == "stage_failed"
    runs_folder = root / ".claude" / "local" / "handoff-runs"
    failed_dirs = [d for d in runs_folder.iterdir() if d.name.endswith("-failed")]
    assert len(failed_dirs) == 1, "Should have exactly one -failed dir"
    assert (failed_dirs[0] / "input.md").exists(), "Failed run dir must have input.md"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_failed_stage_input_md_matches_original(tmp_path):
    """input.md in the failed run dir is a copy of the original payload content."""
    root, reg, well_known = _scaffold_with_registry(
        tmp_path, REGISTRY_WITH_EXTRA_ROLE, PAYLOAD_WITH_MISSING_ROLE
    )
    _git_init(root)
    original_content = well_known.read_text()

    _run_payload(root, reg, well_known)

    runs_folder = root / ".claude" / "local" / "handoff-runs"
    failed_dirs = [d for d in runs_folder.iterdir() if d.name.endswith("-failed")]
    assert failed_dirs
    assert (failed_dirs[0] / "input.md").read_text() == original_content
