# test_rotate.py
#
# Contract tests for rotate-session-log.sh (P1 — latest-only topology).
# Drives the bash script via subprocess against a tmp dir that mirrors production layout:
#   tmp/.claude/tools/rotate-session-log.sh  (copy of script under test)
#   tmp/.claude/session-log.md               (fixture)
#   tmp/.claude/archive/                     (created by script)
#
# Key invariants under test:
# - Multiple spilled entries → each archived to its own slugged file
# - Slug is derived from the entry heading title
# - NO "Previous logs:" line is ever written
# - Default keep=1 leaves exactly the newest entry
# - --dry-run writes nothing
# - Idempotent: second run with same keep is a no-op

import os
import shutil
import subprocess
import pytest
from pathlib import Path

SCRIPT_SOURCE = Path(__file__).parent.parent / "files" / "rotate-session-log.sh"

# Three-entry fixture — newest first (same ordering as real session-log.md)
SESSION_LOG_THREE = (
    "# Session Log\n"
    "\n"
    "**Current Layer:** Layer 5\n"
    "**Current Session:** 2026-06-15 — Session 91: P1 Rotate Rewrite\n"
    "\n"
    "---\n"
    "\n"
    "## 2026-06-15 - Session 91: P1 Rotate Rewrite\n"
    "\n"
    "### Context\nNewest entry body.\n"
    "\n"
    "---\n"
    "\n"
    "## 2026-06-12 - Session 89: Handoff pipeline fixes P1-P5\n"
    "\n"
    "### Context\nMiddle entry body.\n"
    "\n"
    "---\n"
    "\n"
    "## 2026-06-11 - Session 88: Stage promote implementation\n"
    "\n"
    "### Context\nOldest entry body.\n"
    "\n"
    "---\n"
)

SESSION_LOG_ONE = (
    "# Session Log\n"
    "\n"
    "**Current Layer:** Layer 5\n"
    "**Current Session:** 2026-06-15 — Session 91: P1 Rotate Rewrite\n"
    "\n"
    "---\n"
    "\n"
    "## 2026-06-15 - Session 91: P1 Rotate Rewrite\n"
    "\n"
    "### Context\nOnly entry body.\n"
    "\n"
    "---\n"
)


def _setup(tmp_path: Path, log_content: str) -> tuple[Path, Path]:
    """Mirror production layout: script at tmp/.claude/tools/rotate-session-log.sh"""
    tools_dir = tmp_path / ".claude" / "tools"
    tools_dir.mkdir(parents=True)
    archive_dir = tmp_path / ".claude" / "archive"
    archive_dir.mkdir(parents=True)

    script_path = tools_dir / "rotate-session-log.sh"
    shutil.copy(SCRIPT_SOURCE, script_path)
    script_path.chmod(0o755)

    log_path = tmp_path / ".claude" / "session-log.md"
    log_path.write_text(log_content)

    return log_path, archive_dir


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    script = tmp_path / ".claude" / "tools" / "rotate-session-log.sh"
    return subprocess.run(
        [str(script), *args],
        capture_output=True, text=True
    )


# ---- no-op: single entry, keep=1 ------------------------------------------

def test_single_entry_no_rotation(tmp_path):
    """One entry with keep=1 → exit 0, no archive files, session-log unchanged."""
    log_path, archive_dir = _setup(tmp_path, SESSION_LOG_ONE)
    original = log_path.read_text()

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "no rotation needed" in result.stdout
    assert log_path.read_text() == original
    assert list(archive_dir.iterdir()) == []


# ---- two entries spill to one archive file ---------------------------------

def test_two_entries_keep1_archives_one(tmp_path):
    """Two entries with keep=1 → one archive file, log kept has only the newest."""
    two_entry_log = (
        "# Session Log\n"
        "\n"
        "**Current Layer:** L\n"
        "**Current Session:** 2026-06-15 — Session 91: Newest\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-15 - Session 91: Newest\n"
        "\n"
        "### Context\nNewest body.\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-12 - Session 89: Handoff pipeline fixes P1-P5\n"
        "\n"
        "### Context\nOlder body.\n"
        "\n"
        "---\n"
    )
    log_path, archive_dir = _setup(tmp_path, two_entry_log)

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    files = list(archive_dir.iterdir())
    assert len(files) == 1
    archived = files[0]
    assert archived.name == "session-log-2026-06-12-s89-handoff-pipeline-fixes-p1-p5.md"

    # Archived content includes the entry heading
    content = archived.read_text()
    assert "## 2026-06-12 - Session 89:" in content
    assert "Older body" in content

    # Kept file has only the newest entry, no pointer line
    kept = log_path.read_text()
    assert "## 2026-06-15 - Session 91: Newest" in kept
    assert "## 2026-06-12" not in kept
    assert "Previous logs:" not in kept


# ---- three entries: two spill to two separate archive files ----------------

def test_three_entries_keep1_archives_two(tmp_path):
    """Three entries with keep=1 → two separate archive files, newest kept."""
    log_path, archive_dir = _setup(tmp_path, SESSION_LOG_THREE)

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    files = {f.name for f in archive_dir.iterdir()}
    assert "session-log-2026-06-12-s89-handoff-pipeline-fixes-p1-p5.md" in files
    assert "session-log-2026-06-11-s88-stage-promote-implementation.md" in files
    assert len(files) == 2

    # Each archive has its entry content
    f89 = (archive_dir / "session-log-2026-06-12-s89-handoff-pipeline-fixes-p1-p5.md").read_text()
    assert "## 2026-06-12 - Session 89:" in f89
    assert "Middle entry body" in f89

    f88 = (archive_dir / "session-log-2026-06-11-s88-stage-promote-implementation.md").read_text()
    assert "## 2026-06-11 - Session 88:" in f88
    assert "Oldest entry body" in f88

    # Kept log has only session 91
    kept = log_path.read_text()
    assert "## 2026-06-15 - Session 91:" in kept
    assert "## 2026-06-12" not in kept
    assert "## 2026-06-11" not in kept
    assert "Previous logs:" not in kept


# ---- no "Previous logs:" line is ever written ------------------------------

def test_no_previous_logs_pointer_written(tmp_path):
    """The new rotate script must NEVER write a 'Previous logs:' line."""
    log_path, archive_dir = _setup(tmp_path, SESSION_LOG_THREE)

    _run(tmp_path)

    kept = log_path.read_text()
    assert "Previous logs:" not in kept
    for f in archive_dir.iterdir():
        assert "Previous logs:" not in f.read_text()


# ---- --dry-run writes nothing ----------------------------------------------

def test_dry_run_writes_nothing(tmp_path):
    """--dry-run prints what would happen but makes no filesystem changes."""
    log_path, archive_dir = _setup(tmp_path, SESSION_LOG_THREE)
    original_log = log_path.read_text()

    result = _run(tmp_path, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "[dry-run] No changes made." in result.stdout
    assert "Would archive" in result.stdout
    assert log_path.read_text() == original_log
    assert list(archive_dir.iterdir()) == []


# ---- idempotent: second run on rotated file is a no-op --------------------

def test_idempotent_second_run(tmp_path):
    """After rotation, a second run finds only one entry and exits early."""
    log_path, archive_dir = _setup(tmp_path, SESSION_LOG_THREE)

    _run(tmp_path)
    files_after_first = {f.name for f in archive_dir.iterdir()}

    result2 = _run(tmp_path)

    assert result2.returncode == 0, result2.stderr
    assert "no rotation needed" in result2.stdout
    files_after_second = {f.name for f in archive_dir.iterdir()}
    assert files_after_second == files_after_first  # no new archives


# ---- --keep 2 keeps two entries -------------------------------------------

def test_keep_2_leaves_two_entries(tmp_path):
    """--keep 2 with three entries archives only the oldest."""
    log_path, archive_dir = _setup(tmp_path, SESSION_LOG_THREE)

    result = _run(tmp_path, "--keep", "2")

    assert result.returncode == 0, result.stderr
    files = list(archive_dir.iterdir())
    assert len(files) == 1
    assert files[0].name == "session-log-2026-06-11-s88-stage-promote-implementation.md"

    kept = log_path.read_text()
    assert "## 2026-06-15 - Session 91:" in kept
    assert "## 2026-06-12 - Session 89:" in kept
    assert "## 2026-06-11" not in kept


# ---- slug truncation at 40 chars ------------------------------------------

def test_slug_truncated_at_40_chars(tmp_path):
    """Slugs longer than 40 characters are truncated."""
    long_title_log = (
        "# Session Log\n"
        "\n"
        "**Current Layer:** L\n"
        "**Current Session:** 2026-06-15 — Session 91: Short\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-15 - Session 91: Short\n"
        "body\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-12 - Session 89: A very long title that exceeds forty characters easily indeed\n"
        "body\n"
        "\n"
        "---\n"
    )
    log_path, archive_dir = _setup(tmp_path, long_title_log)

    _run(tmp_path)

    files = list(archive_dir.iterdir())
    assert len(files) == 1
    name = files[0].name
    # Remove prefix and extension to get the slug part
    slug_part = name.replace("session-log-2026-06-12-s89-", "").replace(".md", "")
    assert len(slug_part) <= 40


# ---- fallback slug when heading is unparseable ----------------------------

def test_fallback_slug_on_unparseable_heading(tmp_path):
    """If a heading has no 'Session N: title' pattern, fall back to sN form."""
    weird_log = (
        "# Session Log\n"
        "\n"
        "**Current Layer:** L\n"
        "**Current Session:** 2026-06-15 — Session 91: Normal\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-15 - Session 91: Normal\n"
        "body\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-12 weird heading with no session number\n"
        "body\n"
        "\n"
        "---\n"
    )
    log_path, archive_dir = _setup(tmp_path, weird_log)

    result = _run(tmp_path)

    # Must not crash
    assert result.returncode == 0, result.stderr
    files = list(archive_dir.iterdir())
    assert len(files) == 1
    # No crash; fallback filename uses date and s0
    assert files[0].name.startswith("session-log-2026-06-12-s0")


# ---- mechanics.rotate default keep=1 ---------------------------------------

def test_mechanics_rotate_default_keep_is_1():
    """mechanics.rotate() default keep parameter must be 1 (P1 topology)."""
    import inspect
    import sys
    # Add handoff dir to path for import
    handoff_dir = str(Path(__file__).parent)
    if handoff_dir not in sys.path:
        sys.path.insert(0, handoff_dir)
    from sessiontracking.handoff import mechanics
    sig = inspect.signature(mechanics.rotate)
    assert sig.parameters["keep"].default == 1, (
        f"mechanics.rotate keep default should be 1, got {sig.parameters['keep'].default}"
    )
