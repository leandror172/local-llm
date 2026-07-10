# test_harvest.py
#
# Contract tests for handoff-harvest.sh (P3 — git-log harvest).
# Drives the bash script via subprocess against a temp git repo that mirrors
# the installed layout:
#   tmp/.claude/tools/handoff-harvest.sh  (copy of script under test)
#
# The temp repo is initialised OUTSIDE the llm repo tree so git commands inside
# the script see only the test commits, not the real project history.
#
# Key invariants under test:
# - Normal path: commits AFTER the newest chore(session-handoff): commit are printed
# - The handoff commit itself and older commits are excluded
# - No-handoff-commit fallback: falls back gracefully (non-zero output or fallback note
#   to stderr), exits 0
# - Empty range (HEAD IS the handoff commit): prints nothing to stdout, exits 0

import os
import shutil
import subprocess
import pytest
from pathlib import Path

SCRIPT_SOURCE = Path(__file__).parent.parent / "files" / "handoff-harvest.sh"


def _setup(tmp_path: Path) -> Path:
    """Mirror installed layout: script at tmp/.claude/tools/handoff-harvest.sh."""
    tools_dir = tmp_path / ".claude" / "tools"
    tools_dir.mkdir(parents=True)
    script_path = tools_dir / "handoff-harvest.sh"
    shutil.copy(SCRIPT_SOURCE, script_path)
    script_path.chmod(0o755)
    return script_path


def _git(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(tmp_path), *args],
        capture_output=True, text=True, check=True
    )


def _init_repo(tmp_path: Path) -> None:
    """Initialise a git repo with local user config and an initial commit."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    # Make the initial commit so the repo is non-empty
    (tmp_path / "README.md").write_text("repo\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "chore: init repo")


def _commit(tmp_path: Path, subject: str) -> str:
    """Create a commit with given subject; return its SHA."""
    _git(tmp_path, "commit", "--allow-empty", "-m", subject)
    result = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    script = tmp_path / ".claude" / "tools" / "handoff-harvest.sh"
    return subprocess.run(
        [str(script)],
        capture_output=True, text=True
    )


# ---- normal path: only post-handoff commits appear -------------------------

def test_normal_path_subjects_after_handoff(tmp_path):
    """Commits after the last chore(session-handoff): commit are printed; handoff and earlier are excluded."""
    _setup(tmp_path)
    _init_repo(tmp_path)
    _commit(tmp_path, "initial commit")
    _commit(tmp_path, "feat: add something")
    _commit(tmp_path, "chore(session-handoff): session 88 — previous session")
    _commit(tmp_path, "fix: bug fix after handoff")
    _commit(tmp_path, "feat: new feature")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    stdout = result.stdout
    # Post-handoff subjects must appear
    assert "fix: bug fix after handoff" in stdout
    assert "feat: new feature" in stdout
    # Handoff commit and earlier must NOT appear
    assert "chore(session-handoff):" not in stdout
    assert "initial commit" not in stdout
    assert "feat: add something" not in stdout


def test_normal_path_excludes_older_handoffs(tmp_path):
    """When multiple handoff commits exist, only commits after the NEWEST one are printed."""
    _setup(tmp_path)
    _init_repo(tmp_path)
    _commit(tmp_path, "initial commit")
    _commit(tmp_path, "chore(session-handoff): session 87 — older handoff")
    _commit(tmp_path, "feat: between handoffs")
    _commit(tmp_path, "chore(session-handoff): session 88 — newest handoff")
    _commit(tmp_path, "fix: after newest handoff")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    stdout = result.stdout
    assert "fix: after newest handoff" in stdout
    # Both handoff commits and the inter-handoff commit must be absent
    assert "chore(session-handoff):" not in stdout
    assert "between handoffs" not in stdout
    assert "older handoff" not in stdout


# ---- empty range: HEAD is the handoff commit --------------------------------

def test_empty_range_head_is_handoff_commit(tmp_path):
    """If HEAD is the handoff commit, nothing is printed to stdout; exits 0."""
    _setup(tmp_path)
    _init_repo(tmp_path)
    _commit(tmp_path, "initial commit")
    _commit(tmp_path, "chore(session-handoff): session 88 — this session")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    # stdout should be empty (possibly just a newline from the note)
    assert "chore(session-handoff):" not in result.stdout
    assert "initial commit" not in result.stdout


# ---- no handoff commit in history: fallback ---------------------------------

def test_no_handoff_commit_fallback(tmp_path):
    """When no chore(session-handoff): commit exists, script falls back gracefully and exits 0."""
    _setup(tmp_path)
    _init_repo(tmp_path)
    _commit(tmp_path, "initial commit")
    _commit(tmp_path, "feat: first feature")
    _commit(tmp_path, "fix: first fix")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    # Should emit a note to stderr about the fallback
    assert result.stderr != "" or result.stdout != ""
    # Must not crash or print an error that looks like a git error
    assert "fatal" not in result.stderr.lower()


def test_no_handoff_commit_fallback_prints_recent_commits(tmp_path):
    """Fallback path emits some commits (not silent) so caller can still populate what_was_done."""
    _setup(tmp_path)
    _init_repo(tmp_path)
    for i in range(3):
        _commit(tmp_path, f"feat: commit {i}")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    # At least some commit subjects should be visible
    combined = result.stdout + result.stderr
    assert "feat: commit" in combined


# ---- prefix specificity: bare chore(session-handoff): without 'session ' is NOT a boundary ---------

def test_prefix_reuse_commit_is_not_a_boundary(tmp_path):
    """A commit matching 'chore(session-handoff):' but NOT 'chore(session-handoff): session '
    must not be treated as a session boundary — it should appear in the harvest output,
    not silently truncate the range.

    History:
      chore(session-handoff): session 95 — real handoff  <-- true boundary
      feat: work A
      chore(session-handoff): tweak manifest              <-- prefix reuse, NOT a boundary
      feat: work B

    Expected: work A, tweak manifest, work B in stdout; session 95 line excluded.
    With the loose grep '^chore(session-handoff):' the 'tweak manifest' commit is
    mistakenly picked as the newest boundary, causing work A and tweak manifest itself
    to be dropped from output (RED).  With the tighter grep
    '^chore(session-handoff): session ' only the real handoff is the boundary (GREEN).
    """
    _setup(tmp_path)
    _init_repo(tmp_path)
    _commit(tmp_path, "chore(session-handoff): session 95 — real handoff")
    _commit(tmp_path, "feat: work A")
    _commit(tmp_path, "chore(session-handoff): tweak manifest")
    _commit(tmp_path, "feat: work B")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    stdout = result.stdout
    # All three post-boundary commits must appear
    assert "feat: work A" in stdout, f"work A missing from stdout:\n{stdout}"
    assert "chore(session-handoff): tweak manifest" in stdout, (
        f"tweak manifest missing from stdout (was wrongly treated as boundary):\n{stdout}"
    )
    assert "feat: work B" in stdout, f"work B missing from stdout:\n{stdout}"
    # The real handoff commit IS the boundary and must NOT appear
    assert "session 95 — real handoff" not in stdout, (
        f"real handoff commit should be excluded (it is the boundary):\n{stdout}"
    )
