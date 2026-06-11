# test_handoff_cli.py
#
# End-to-end tests for the handoff.py CLI entrypoint, driven as a subprocess on a
# real tmp git repo (same pattern as test_orchestrator's integration tests).
# Reuses _setup / _git_init from test_orchestrator for the tracking-file scaffold.
#
# Flat imports — run from inside the handoff dir.

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from test_orchestrator import _setup, _git_init  # tracking-file + git scaffolding

HANDOFF_DIR = Path(__file__).resolve().parent

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

    ## 2026-06-05 - Session 85: CLI test

    new entry body

    ---
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
    # The CLI runs the real rotate step; the tmp repo needs an executable no-op,
    # just as a real repo carries .claude/tools/rotate-session-log.sh.
    rotate = root / ".claude/tools/rotate-session-log.sh"
    rotate.parent.mkdir(parents=True, exist_ok=True)
    rotate.write_text("#!/bin/sh\nexit 0\n")
    rotate.chmod(0o755)
    payload_file = tmp_path / "payload.md"
    payload_file.write_text(payload_text)
    return root, reg, payload_file


def _run_cli(root, reg, payload_file, *extra):
    return subprocess.run(
        [sys.executable, "handoff.py", "--payload", str(payload_file),
         "--repo-root", str(root), "--registry", str(reg), *extra],
        cwd=HANDOFF_DIR, capture_output=True, text=True,
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_cli_real_run_commits(tmp_path):
    root, reg, payload_file = _scaffold(tmp_path)
    _git_init(root)

    result = _run_cli(root, reg, payload_file)

    assert result.returncode == 0, result.stderr
    log = subprocess.run(["git", "log", "--oneline"], cwd=root,
                         capture_output=True, text=True).stdout
    assert "session 85" in log.lower()
    assert "new status here" in (root / ".claude/session-context.md").read_text()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_cli_dry_run_writes_nothing(tmp_path):
    root, reg, payload_file = _scaffold(tmp_path)
    _git_init(root)
    before = (root / ".claude/session-context.md").read_text()

    result = _run_cli(root, reg, payload_file, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert (root / ".claude/session-context.md").read_text() == before
    assert not (root / ".claude/local/handoff-runs").exists()
    count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    assert count == "1"  # no new commit


def test_cli_validation_error_exits_nonzero_without_running(tmp_path):
    root, reg, payload_file = _scaffold(tmp_path, payload_text=BAD_PAYLOAD)
    # No git init: validation must fail before run_handoff is ever reached.

    result = _run_cli(root, reg, payload_file)

    assert result.returncode != 0
    assert "bogus-role" in (result.stderr + result.stdout)
    assert not (root / ".claude/local/handoff-runs").exists()
