"""Contract tests for F1 Locator (session-handoff pipeline, Scope A).

The Locator resolves a register role + file text into a single Region describing
WHERE and HOW the pipeline may write. It performs an exactly-one-match self-check:
ambiguity or absence raises LocatorError (the orchestrator falls back to Claude).

Pure functions only: no file I/O, no YAML. The caller parses registry.yaml and
passes the role dict in; tests construct role dicts inline.
"""

import pytest

from locator import Region, LocatorError, locate


# --------------------------------------------------------------------------- #
# ref_block: span between <!-- ref:KEY --> and <!-- /ref:KEY -->
# --------------------------------------------------------------------------- #

REF_ROLE = {"locator": {"type": "ref_block", "key": "current-status"},
            "write_mode": "replace"}


def _ref_doc(interior):
    return (
        "# Heading\n\n"
        "<!-- ref:current-status -->\n"
        f"{interior}"
        "<!-- /ref:current-status -->\n"
        "trailing\n"
    )


def test_ref_block_returns_interior_between_markers():
    text = _ref_doc("OLD LINE 1\nOLD LINE 2\n")
    r = locate(REF_ROLE, text)
    assert isinstance(r, Region)
    assert r.kind == "ref_block"
    assert r.mode == "replace"
    assert r.interior == "OLD LINE 1\nOLD LINE 2\n"
    # bounds isolate exactly the interior; markers are outside the region
    assert text[r.start:r.end] == r.interior
    assert text[:r.start].endswith("<!-- ref:current-status -->\n")
    assert text[r.end:].startswith("<!-- /ref:current-status -->")


def test_ref_block_empty_interior():
    text = _ref_doc("")
    r = locate(REF_ROLE, text)
    assert r.interior == ""
    assert text[r.start:r.end] == ""


def test_ref_block_missing_open_marker_raises():
    text = "no markers here\n"
    with pytest.raises(LocatorError):
        locate(REF_ROLE, text)


def test_ref_block_missing_close_marker_raises():
    text = "<!-- ref:current-status -->\nbody\n"
    with pytest.raises(LocatorError):
        locate(REF_ROLE, text)


def test_ref_block_duplicate_open_marker_raises():
    text = _ref_doc("a\n") + _ref_doc("b\n")
    with pytest.raises(LocatorError):
        locate(REF_ROLE, text)


# --------------------------------------------------------------------------- #
# field: a single "**Label:** value" header line
# --------------------------------------------------------------------------- #

FIELD_ROLE = {"locator": {"type": "field", "label": "Current Session"},
              "write_mode": "nomodel"}


def test_field_returns_value_after_label():
    text = ("# Session Log\n\n"
            "**Current Layer:** LTG\n"
            "**Current Session:** 2026-06-02 — Session 82\n"
            "**Previous logs:** a, b\n")
    r = locate(FIELD_ROLE, text)
    assert r.kind == "field"
    assert r.mode == "nomodel"
    assert r.interior == "2026-06-02 — Session 82"
    assert text[r.start:r.end] == r.interior


def test_field_missing_raises():
    text = "**Other:** x\n"
    with pytest.raises(LocatorError):
        locate(FIELD_ROLE, text)


def test_field_duplicate_raises():
    text = "**Current Session:** one\n**Current Session:** two\n"
    with pytest.raises(LocatorError):
        locate(FIELD_ROLE, text)


# --------------------------------------------------------------------------- #
# structural: insertion anchor at the Nth occurrence of a line pattern
# --------------------------------------------------------------------------- #

LOG_ROLE = {"locator": {"type": "structural", "pattern": "^---$",
                        "occurrence": 1, "position": "after"},
            "write_mode": "prepend"}


def test_structural_insertion_anchor_is_zero_width_after_first_rule():
    text = ("# Header\n\n"
            "---\n"
            "## Session 82\n"
            "---\n"
            "## Session 81\n")
    r = locate(LOG_ROLE, text)
    assert r.kind == "structural"
    assert r.mode == "prepend"
    assert r.start == r.end          # zero-width insertion point
    assert r.interior == ""
    # insertion lands immediately after the FIRST '---\n', before '## Session 82'
    assert text[:r.start].endswith("---\n")
    assert text[r.start:].startswith("## Session 82")


def test_structural_position_before():
    role = {"locator": {"type": "structural", "pattern": "^---$",
                        "occurrence": 1, "position": "before"},
            "write_mode": "prepend"}
    text = "# Header\n\n---\nbody\n"
    r = locate(role, text)
    assert r.start == r.end
    assert text[r.start:].startswith("---\n")


def test_structural_occurrence_out_of_range_raises():
    role = {"locator": {"type": "structural", "pattern": "^---$",
                        "occurrence": 5, "position": "after"},
            "write_mode": "prepend"}
    text = "---\nonly one rule\n"
    with pytest.raises(LocatorError):
        locate(role, text)


# --------------------------------------------------------------------------- #
# checklist: a unique open task line matched by id (for check-off)
# --------------------------------------------------------------------------- #

CHECK_ROLE = {"locator": {"type": "checklist", "scope": "file"},
              "write_mode": "checkoff"}


def test_checklist_matches_open_task_by_id():
    text = ("- [ ] (T-04) **B2.3 F4 Verifier** — gate\n"
            "- [ ] (T-05) **B3.1 F5 mechanics** — bumps\n"
            "- [x] (T-06) **B3.2** — done already\n")
    r = locate(CHECK_ROLE, text, task_id="T-05")
    assert r.kind == "checklist"
    assert r.mode == "checkoff"
    assert "(T-05)" in r.interior
    assert r.interior.startswith("- [ ] (T-05)")
    assert text[r.start:r.end] == r.interior


def test_checklist_id_not_found_raises():
    text = "- [ ] (T-01) a\n"
    with pytest.raises(LocatorError):
        locate(CHECK_ROLE, text, task_id="T-99")


def test_checklist_already_checked_is_not_a_match():
    # id exists only as a completed task -> no OPEN task to check off -> error
    text = "- [x] (T-05) done\n"
    with pytest.raises(LocatorError):
        locate(CHECK_ROLE, text, task_id="T-05")


def test_checklist_duplicate_open_id_raises():
    text = "- [ ] (T-05) a\n- [ ] (T-05) b\n"
    with pytest.raises(LocatorError):
        locate(CHECK_ROLE, text, task_id="T-05")


def test_checklist_bold_id_format():
    text = ("- [ ] **5.R1** TF-IDF retrieval layer\n"
            "- [ ] **5.R2** Embedding retrieval layer\n")
    r = locate(CHECK_ROLE, text, task_id="5.R1")
    assert "5.R1" in r.interior
    assert r.interior.startswith("- [ ] **5.R1**")


def test_checklist_bare_numeric_id():
    text = ("- [x] 1.0 — Protocol definitions\n"
            "- [ ] 1.0a — variant task\n"
            "- [ ] 3.1 — CLI wrapper\n")
    r = locate(CHECK_ROLE, text, task_id="3.1")
    assert "3.1" in r.interior
    assert r.interior.startswith("- [ ] 3.1")


def test_checklist_prefix_dash_id():
    text = ("- [x] **RUI-1** review command\n"
            "- [ ] **RUI-4** emit full 3-level path\n")
    r = locate(CHECK_ROLE, text, task_id="RUI-4")
    assert "RUI-4" in r.interior


def test_checklist_word_boundary_no_substring_match():
    # T-1 must not match the T-10 line
    text = ("- [ ] (T-10) **task ten**\n"
            "- [ ] (T-1) **task one**\n")
    r = locate(CHECK_ROLE, text, task_id="T-1")
    assert r.interior.startswith("- [ ] (T-1) ")
    assert "T-10" not in r.interior


def test_checklist_id_in_description_of_other_task_not_matched():
    # T-01 appears in the description of T-02, but T-01 itself is checked off.
    # Only unchecked lines enter the candidate set, so no false match.
    text = ("- [x] (T-01) **first task**\n"
            "- [ ] (T-02) **second task** — blocked on T-01\n")
    with pytest.raises(LocatorError):
        locate(CHECK_ROLE, text, task_id="T-01")
