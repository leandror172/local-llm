# test_runlog.py
#
# Contract tests for B3.3 per-run logging: the shared run-dir keyed by
# session-N + timestamp, verbatim input.md (recovery artifact), and the
# formatted report.md (audit artifact). Presence-based assertions so the
# format can evolve without breaking the content contract.
#
# Flat imports — run from inside the handoff dir or pass absolute file paths.

import datetime

import pytest

from runlog import (
    create_run_dir,
    write_input,
    write_report,
    format_report,
    RunReport,
    RegionEdit,
    find_pending_run,
    promote_run_dir,
    mark_run_failed,
    count_runs_by_status,
    RunNotFoundError,
)

FIXED = datetime.datetime(2026, 6, 5, 14, 30, 0)
CLOCK = lambda: FIXED


# ---- create_run_dir ---------------------------------------------------------

def test_create_run_dir_path_shape(tmp_path):
    """Run dir lives under .claude/local/handoff-runs/ named session-<N>-<ts>-<status> and exists."""
    d = create_run_dir(tmp_path, 85, status="pending", clock=CLOCK)
    assert d.parent == tmp_path / ".claude" / "local" / "handoff-runs"
    assert d.name == "session-85-20260605-143000-pending"
    assert d.is_dir()


def test_create_run_dir_uses_injected_clock(tmp_path):
    """The timestamp in the dir name comes from the injected clock."""
    d = create_run_dir(tmp_path, 7, status="pending", clock=CLOCK)
    assert "20260605-143000" in d.name


# ---- write_input ------------------------------------------------------------

def test_write_input_persists_payload_verbatim(tmp_path):
    """input.md holds Claude's exact F7 payload, byte-for-byte (recovery artifact)."""
    d = create_run_dir(tmp_path, 85, status="pending", clock=CLOCK)
    payload = "role: current-status\n\nSome **authored** block — verbatim.\n"
    p = write_input(d, payload)
    assert p == d / "input.md"
    assert p.read_text() == payload


# ---- format_report ----------------------------------------------------------

def test_format_report_committed_shows_regions():
    """A committed report names the session, status, and each region's role+mode+before/after."""
    report = RunReport(
        session_number=85, committed=True, rolled_back=False, reason="",
        verify_ok=True,
        edits=[RegionEdit(role="current-status", mode="replace",
                          before="old interior", after="new interior")],
    )
    out = format_report(report)
    assert "Session 85" in out
    assert "committed" in out.lower()
    assert "current-status" in out and "replace" in out
    assert "old interior" in out and "new interior" in out


def test_format_report_rolled_back_shows_reason():
    """A rolled-back report states rollback and the failure reason."""
    report = RunReport(
        session_number=85, committed=False, rolled_back=True,
        reason="verify failed: marker mismatch", verify_ok=False, edits=[],
    )
    out = format_report(report)
    assert "rolled back" in out.lower()
    assert "verify failed: marker mismatch" in out


# ---- write_report -----------------------------------------------------------

def test_write_report_writes_formatted_file(tmp_path):
    """report.md is written into the run dir and contains the formatted report."""
    d = create_run_dir(tmp_path, 85, status="pending", clock=CLOCK)
    report = RunReport(
        session_number=85, committed=True, rolled_back=False, reason="",
        verify_ok=True, edits=[],
    )
    p = write_report(d, report)
    assert p == d / "report.md"
    assert "Session 85" in p.read_text()


# ---- shared run dir ---------------------------------------------------------

def test_input_and_report_share_run_dir(tmp_path):
    """input.md and report.md land in the same session-N+timestamp dir."""
    d = create_run_dir(tmp_path, 85, status="pending", clock=CLOCK)
    ip = write_input(d, "x")
    rp = write_report(d, RunReport(85, True, False, "", True, []))
    assert ip.parent == rp.parent == d


# ---- create_run_dir with status ---------------------------------------------

def test_create_run_dir_with_status_appends_suffix(tmp_path):
    """Dir name ends with -<status> when status is provided."""
    d = create_run_dir(tmp_path, 85, clock=CLOCK, status="pending")
    assert d.name.endswith("-pending")


# ---- find_pending_run -------------------------------------------------------

def test_find_pending_run_returns_correct_dir(tmp_path):
    """Returns the path to <handle>-pending/ when it exists."""
    runs_folder = tmp_path / ".claude" / "local" / "handoff-runs"
    runs_folder.mkdir(parents=True, exist_ok=True)
    handle = "session-85-20260605-143000"
    pending_dir = runs_folder / f"{handle}-pending"
    pending_dir.mkdir()
    result = find_pending_run(tmp_path, handle)
    assert result == pending_dir


def test_find_pending_run_raises_on_missing_handle(tmp_path):
    """Raises RunNotFoundError when no dir matches the handle."""
    with pytest.raises(RunNotFoundError):
        find_pending_run(tmp_path, "nonexistent-handle")


def test_find_pending_run_raises_on_multiple_matches(tmp_path):
    """Raises RunNotFoundError with 'ambiguous' when multiple -pending dirs share the handle prefix."""
    runs_folder = tmp_path / ".claude" / "local" / "handoff-runs"
    runs_folder.mkdir(parents=True, exist_ok=True)
    handle = "session-85-20260605-143000"
    (runs_folder / f"{handle}-pending").mkdir()
    (runs_folder / f"{handle}-v2-pending").mkdir()
    with pytest.raises(RunNotFoundError, match="ambiguous"):
        find_pending_run(tmp_path, handle)


# ---- promote_run_dir --------------------------------------------------------

def test_promote_run_dir_renames_pending_to_success(tmp_path):
    """Renames <handle>-pending/ to <handle>-success/ and returns the new path."""
    runs_folder = tmp_path / ".claude" / "local" / "handoff-runs"
    runs_folder.mkdir(parents=True, exist_ok=True)
    handle = "session-85-20260605-143000"
    pending_dir = runs_folder / f"{handle}-pending"
    pending_dir.mkdir()
    success_dir = promote_run_dir(pending_dir)
    assert success_dir.name == f"{handle}-success"
    assert success_dir.exists()
    assert not pending_dir.exists()


def test_promote_run_dir_raises_if_not_pending(tmp_path):
    """Raises ValueError when the dir does not end in -pending."""
    with pytest.raises(ValueError):
        promote_run_dir(tmp_path / "some-random-dir")


# ---- mark_run_failed --------------------------------------------------------

def test_mark_run_failed_renames_pending_to_failed(tmp_path):
    """Renames <handle>-pending/ to <handle>-failed/ and returns the new path."""
    runs_folder = tmp_path / ".claude" / "local" / "handoff-runs"
    runs_folder.mkdir(parents=True, exist_ok=True)
    handle = "session-85-20260605-143000"
    pending_dir = runs_folder / f"{handle}-pending"
    pending_dir.mkdir()
    failed_dir = mark_run_failed(pending_dir)
    assert failed_dir.name == f"{handle}-failed"
    assert failed_dir.exists()
    assert not pending_dir.exists()


# ---- count_runs_by_status ---------------------------------------------------

def test_count_runs_by_status_returns_correct_counts(tmp_path):
    """Returns dict with correct counts for pending/success/failed; missing statuses get 0."""
    runs_folder = tmp_path / ".claude" / "local" / "handoff-runs"
    runs_folder.mkdir(parents=True, exist_ok=True)
    for i in range(2):
        (runs_folder / f"session-85-20260605-14300{i}-pending").mkdir()
    for i in range(3):
        (runs_folder / f"session-85-20260605-14300{i}-success").mkdir()
    (runs_folder / "session-85-20260605-143000-failed").mkdir()
    result = count_runs_by_status(tmp_path)
    assert result == {"pending": 2, "success": 3, "failed": 1, "aborted": 0}
