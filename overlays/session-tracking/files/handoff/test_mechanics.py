# test_mechanics.py
#
# Contract tests for F5 (mechanics): next-session-number derivation, date,
# header-field value composition, and the nomodel field-edit path that must
# round-trip cleanly through F4 (verifier).
#
# Flat imports — run from inside the handoff dir or pass absolute file paths.

import datetime

from mechanics import (
    MechanicsError,
    next_session_number,
    today,
    compute_header_values,
    header_field_edits,
    apply_field,
)
from locator import Region
from verifier import verify


LOG = (
    "# Session Log\n"
    "\n"
    "**Current Layer:** Old layer text\n"
    "**Current Session:** 2026-06-04 — Session 84: Old topic\n"
    "\n"
    "---\n"
    "\n"
    "## 2026-06-04 - Session 84: B2 safety core\n"
    "body\n"
    "\n"
    "## 2026-06-02 - Session 82: anchors\n"
    "body\n"
)

ROLES = {
    "header-current-session": {
        "locator": {"type": "field", "label": "Current Session"},
        "write_mode": "nomodel",
    },
    "header-current-layer": {
        "locator": {"type": "field", "label": "Current Layer"},
        "write_mode": "nomodel",
    },
}


# ---- next_session_number ----------------------------------------------------

def test_next_session_number_from_newest_heading():
    """The newest entry is Session 84, so the next session is 85."""
    assert next_session_number(LOG) == 85


def test_next_session_number_takes_max_not_first():
    """Even if a lower-numbered entry appears first in file order, return max+1."""
    log = (
        "## 2026-06-01 - Session 80: x\n"
        "## 2026-06-04 - Session 84: y\n"
    )
    assert next_session_number(log) == 85


def test_next_session_number_defaults_to_one_when_empty():
    """A fresh repo with no Session-N headings bootstraps to Session 1 — no raise."""
    assert next_session_number("# Session Log\n\nno entries yet\n") == 1


# ---- today ------------------------------------------------------------------

def test_today_uses_injected_clock():
    """today() formats the injected clock as ISO YYYY-MM-DD."""
    fixed = lambda: datetime.date(2026, 6, 5)
    assert today(clock=fixed) == "2026-06-05"


# ---- compute_header_values --------------------------------------------------

def test_compute_header_values_composes_current_session():
    """current_session = '<date> — Session <N>: <title>' using next session number."""
    vals = compute_header_values(
        LOG, session_title="B3 mechanics", current_layer="Layer X", date="2026-06-05"
    )
    assert vals["current_session"] == "2026-06-05 — Session 85: B3 mechanics"


def test_compute_header_values_passes_layer_through():
    """current_layer is supplied by the skill and passed through unchanged."""
    vals = compute_header_values(
        LOG, session_title="t", current_layer="Layer X", date="2026-06-05"
    )
    assert vals["current_layer"] == "Layer X"


# ---- apply_field ------------------------------------------------------------

def test_apply_field_replaces_only_the_value():
    """apply_field swaps just the field value, leaving the '**Label:** ' prefix intact."""
    start = LOG.index("Old layer text")
    region = Region(
        kind="field", mode="nomodel",
        start=start, end=start + len("Old layer text"), interior="Old layer text",
    )
    out = apply_field(LOG, region, "New layer")
    assert "**Current Layer:** New layer" in out
    assert "Old layer text" not in out


# ---- header_field_edits -----------------------------------------------------

def test_header_field_edits_returns_two_nomodel_edits():
    """Locates both nomodel header fields and pairs each with its new value."""
    vals = compute_header_values(
        LOG, session_title="t", current_layer="L", date="2026-06-05"
    )
    edits = header_field_edits(LOG, ROLES, vals)
    assert len(edits) == 2
    assert all(region.mode == "nomodel" for region, _ in edits)


# ---- integration: mechanics edits round-trip through the verifier -----------

def test_mechanics_edits_pass_verify():
    """The nomodel header bumps, once applied, must satisfy F4's verify() — the
    safety contract between F5 (mechanics) and F4 (trust boundary)."""
    vals = compute_header_values(
        LOG, session_title="B3 mechanics", current_layer="New L", date="2026-06-05"
    )
    edits = header_field_edits(LOG, ROLES, vals)

    modified = LOG
    for region, value in sorted(edits, key=lambda e: e[0].start, reverse=True):
        modified = apply_field(modified, region, value)

    verify(LOG, modified, edits)  # must not raise
    assert "Session 85: B3 mechanics" in modified
    assert "**Current Layer:** New L" in modified
