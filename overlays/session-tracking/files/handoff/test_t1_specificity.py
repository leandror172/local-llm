# test_t1_specificity.py
#
# Tests for T1 — error-message specificity improvements:
#   1. verifier.py: overlap errors must name both regions with role/target/file/line
#   2. payload.py:  scalar errors must state WHY (which header they feed)

import pytest

from verifier import verify, VerifyError
from locator import Region
from payload import parse, validate


# ---- helpers ----------------------------------------------------------------

def _line(original: str, pos: int) -> int:
    return original[:pos].count("\n") + 1


REGISTER = {
    "log-entry": {"write_mode": "prepend"},
    "current-status": {"write_mode": "replace"},
    "header-current-session": {"write_mode": "nomodel"},
    "tasks-checkoff": {"write_mode": "checkoff"},
}


# ---- 1. verifier overlap message specificity --------------------------------

def test_overlap_message_names_both_regions_with_metadata():
    """When regions carry role/target/file, error names both descriptors."""
    original = "0123456789abcdef"
    r1 = Region(kind="ref_block", mode="replace", start=0, end=10,
                interior=original[0:10], role="tasks-checkoff", target="RUI-WM1",
                file="tasks.md")
    r2 = Region(kind="ref_block", mode="replace", start=5, end=15,
                interior=original[5:15], role="tasks-append", target="ref:deferred",
                file="tasks.md")
    with pytest.raises(VerifyError) as exc_info:
        verify(original, original, [(r1, "x"), (r2, "y")])
    msg = str(exc_info.value)
    # Both region descriptors must appear
    assert "tasks-checkoff" in msg
    assert "RUI-WM1" in msg
    assert "tasks-append" in msg
    assert "ref:deferred" in msg
    assert "tasks.md" in msg


def test_overlap_message_includes_line_numbers():
    """Line numbers are derived from original text at region.start."""
    original = "line0\nline1\nline2\nline3\n"
    # r1 starts at byte 6 → line 2; r2 starts at byte 12 → line 3
    r1 = Region(kind="ref_block", mode="replace", start=6, end=11,
                interior="line1\n", role="roleA", target="tA", file="f.md")
    r2 = Region(kind="ref_block", mode="replace", start=9, end=17,
                interior="line1\nlin", role="roleB", target="tB", file="f.md")
    with pytest.raises(VerifyError) as exc_info:
        verify(original, original, [(r1, "x"), (r2, "y")])
    msg = str(exc_info.value)
    assert "2" in msg   # line of r1.start
    assert "roleA" in msg
    assert "roleB" in msg


def test_overlap_message_degrades_gracefully_without_metadata():
    """Regions without role/target/file still raise VerifyError (no crash)."""
    original = "0123456789abcdef"
    r1 = Region(kind="ref_block", mode="replace", start=0, end=10, interior=original[0:10])
    r2 = Region(kind="ref_block", mode="replace", start=5, end=15, interior=original[5:15])
    with pytest.raises(VerifyError) as exc_info:
        verify(original, original, [(r1, "x"), (r2, "y")])
    # Message must still be a non-empty string (graceful degradation)
    assert str(exc_info.value)


def test_no_overlap_still_passes_with_metadata():
    """Adding metadata fields to non-overlapping regions doesn't break verify."""
    original = "AAAAABBBBB"
    r1 = Region(kind="ref_block", mode="replace", start=0, end=5,
                interior="AAAAA", role="roleA", target="tA", file="f.md")
    r2 = Region(kind="ref_block", mode="replace", start=5, end=10,
                interior="BBBBB", role="roleB", target="tB", file="f.md")
    modified = "XXXXXYYYYY"
    verify(original, modified, [(r1, "XXXXX"), (r2, "YYYYY")])  # must not raise


# ---- 2. payload scalar error WHY --------------------------------------------

def test_scalar_error_session_title_names_header():
    """Empty session_title error must name the Current Session header."""
    text = "---\nsession_title:\ncurrent_layer: L\n---\n## role: current-status\nx\n"
    errors = validate(parse(text), REGISTER)
    assert any("Current Session header" in e for e in errors)


def test_scalar_error_current_layer_names_header():
    """Empty current_layer error must name the Current Layer header."""
    text = "---\nsession_title: T\ncurrent_layer:\n---\n## role: current-status\nx\n"
    errors = validate(parse(text), REGISTER)
    assert any("Current Layer header" in e for e in errors)


def test_scalar_errors_do_not_regress_valid_payload():
    """Valid scalars produce no errors."""
    text = "---\nsession_title: T\ncurrent_layer: L\n---\n## role: current-status\nx\n"
    errors = validate(parse(text), REGISTER)
    scalar_errors = [e for e in errors if "required" in e]
    assert not scalar_errors
