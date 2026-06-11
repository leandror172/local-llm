# test_runlog.py
#
# Contract tests for B3.3 per-run logging: the shared run-dir keyed by
# session-N + timestamp, verbatim input.md (recovery artifact), and the
# formatted report.md (audit artifact). Presence-based assertions so the
# format can evolve without breaking the content contract.
#
# Flat imports — run from inside the handoff dir or pass absolute file paths.

import datetime

from runlog import (
    create_run_dir,
    write_input,
    write_report,
    format_report,
    RunReport,
    RegionEdit,
)

FIXED = datetime.datetime(2026, 6, 5, 14, 30, 0)
CLOCK = lambda: FIXED


# ---- create_run_dir ---------------------------------------------------------

def test_create_run_dir_path_shape(tmp_path):
    """Run dir lives under .claude/local/handoff-runs/ named session-<N>-<ts> and exists."""
    d = create_run_dir(tmp_path, 85, clock=CLOCK)
    assert d.parent == tmp_path / ".claude" / "local" / "handoff-runs"
    assert d.name == "session-85-20260605-143000"
    assert d.is_dir()


def test_create_run_dir_uses_injected_clock(tmp_path):
    """The timestamp in the dir name comes from the injected clock."""
    d = create_run_dir(tmp_path, 7, clock=CLOCK)
    assert "20260605-143000" in d.name


# ---- write_input ------------------------------------------------------------

def test_write_input_persists_payload_verbatim(tmp_path):
    """input.md holds Claude's exact F7 payload, byte-for-byte (recovery artifact)."""
    d = create_run_dir(tmp_path, 85, clock=CLOCK)
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
    d = create_run_dir(tmp_path, 85, clock=CLOCK)
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
    d = create_run_dir(tmp_path, 85, clock=CLOCK)
    ip = write_input(d, "x")
    rp = write_report(d, RunReport(85, True, False, "", True, []))
    assert ip.parent == rp.parent == d
