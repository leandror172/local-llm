"""Contract tests for F4 Verifier (session-handoff pipeline, Scope A).

F4 is the trust boundary. Given the original text, the modified text, and the
list of edits that were *intended* (each = a Region from F1 + the authored
content), it independently re-derives what the modified text must be and asserts
byte-exact equality. This proves two things at once:
  - every byte OUTSIDE the edited regions is identical to the original, and
  - each edited region holds exactly the intended content.
It also asserts the ref-marker multiset is preserved, and refuses to verify
overlapping edit regions. Any violation raises VerifyError.

F4 does NOT call apply() — it re-derives segments itself, so an orchestration
bug (a skipped edit, a corrupted neighbouring byte) is caught.

API under test:
    from verifier import verify, VerifyError
    from locator import Region, locate
    from applier import apply
    verify(original: str, modified: str, edits: list[tuple[Region, str]]) -> None
        # returns None on success, raises VerifyError on any violation

Per-mode segment F4 expects in each region's span after edit:
    replace / nomodel : content
    prepend           : content + region.interior
    append            : region.interior + content
    checkoff          : region.interior with the first "[ ]" flipped to "[x]"
"""

import pytest

from verifier import verify, VerifyError
from locator import Region, locate
from applier import apply


# --- role fixtures (mirror registry.yaml shapes) ---------------------------- #

ROLE_REPLACE = {"locator": {"type": "ref_block", "key": "current-status"},
                "write_mode": "replace"}
ROLE_STRUCT_PREPEND = {"locator": {"type": "structural", "pattern": "^---$",
                                   "occurrence": 1, "position": "after"},
                       "write_mode": "prepend"}
ROLE_CHECK = {"locator": {"type": "checklist", "scope": "file"},
              "write_mode": "checkoff"}
ROLE_FIELD = {"locator": {"type": "field", "label": "Current Session"},
              "write_mode": "nomodel"}


def _ref_doc(key, interior):
    return f"PRE\n<!-- ref:{key} -->\n{interior}<!-- /ref:{key} -->\nPOST\n"


def _apply_all(text, edits):
    """Build a 'good' modified text by applying edits right-to-left."""
    for region, content in sorted(edits, key=lambda e: e[0].start, reverse=True):
        text = apply(text, region, content)
    return text


# --- passing cases ---------------------------------------------------------- #

def test_verify_passes_for_single_replace():
    original = _ref_doc("current-status", "OLD\n")
    region = locate(ROLE_REPLACE, original)
    edits = [(region, "NEW\n")]
    modified = _apply_all(original, edits)
    verify(original, modified, edits)  # no raise


def test_verify_passes_for_multiple_replaces_in_one_text():
    original = (_ref_doc("current-status", "A\n")
                + "<!-- ref:active-decisions -->\nB\n<!-- /ref:active-decisions -->\n")
    r1 = locate(ROLE_REPLACE, original)
    r2 = locate({"locator": {"type": "ref_block", "key": "active-decisions"},
                 "write_mode": "replace"}, original)
    edits = [(r1, "AA\n"), (r2, "BB\n")]
    modified = _apply_all(original, edits)
    verify(original, modified, edits)  # offsets shift; verify still passes


def test_verify_passes_for_structural_prepend_insertion():
    original = "# Header\n\n---\n## Session 82\n"
    region = locate(ROLE_STRUCT_PREPEND, original)
    edits = [(region, "## Session 83\n")]
    modified = _apply_all(original, edits)
    verify(original, modified, edits)


def test_verify_passes_for_checkoff():
    original = "- [ ] (T-04) a\n- [ ] (T-05) b\n"
    region = locate(ROLE_CHECK, original, task_id="T-05")
    edits = [(region, "")]
    modified = _apply_all(original, edits)
    verify(original, modified, edits)


def test_verify_passes_for_field_value_bump():
    # nomodel field is treated as a value replace for verification purposes
    original = "**Current Session:** old value\n"
    region = locate(ROLE_FIELD, original)
    new_value = "2026-06-04 — Session 83"
    modified = original[:region.start] + new_value + original[region.end:]
    verify(original, modified, [(region, new_value)])


# --- failing cases (must raise VerifyError) --------------------------------- #

def test_verify_raises_when_bytes_outside_regions_change():
    original = _ref_doc("current-status", "OLD\n")
    region = locate(ROLE_REPLACE, original)
    edits = [(region, "NEW\n")]
    modified = _apply_all(original, edits).replace("POST", "PWND")  # outside tamper
    with pytest.raises(VerifyError):
        verify(original, modified, edits)


def test_verify_raises_when_a_ref_marker_is_dropped():
    original = _ref_doc("current-status", "OLD\n")
    region = locate(ROLE_REPLACE, original)
    edits = [(region, "NEW\n")]
    modified = _apply_all(original, edits).replace("<!-- /ref:current-status -->", "")
    with pytest.raises(VerifyError):
        verify(original, modified, edits)


def test_verify_raises_on_overlapping_regions():
    original = "0123456789abcdef"
    r1 = Region(kind="ref_block", mode="replace", start=0, end=10, interior=original[0:10])
    r2 = Region(kind="ref_block", mode="replace", start=5, end=15, interior=original[5:15])
    with pytest.raises(VerifyError):
        verify(original, original, [(r1, "x"), (r2, "y")])


# --- T-57 regression: tasks-append + tasks-checkoff in same ref block -------- #

def test_append_and_checkoff_in_same_block_do_not_overlap():
    """Regression for T-57: append (inserts at block end) and checkoff (flips 3 bytes)
    must not raise a false VerifyError even when their raw region spans overlap."""
    original = (
        "<!-- ref:deferred-infra -->\n"
        "- [ ] (T-10) existing task\n"
        "<!-- /ref:deferred-infra -->"
    )
    open_marker = "<!-- ref:deferred-infra -->\n"
    close_marker = "<!-- /ref:deferred-infra -->"
    block_start = len(open_marker)
    block_end = original.index(close_marker)
    line_start = original.index("- [ ] (T-10) existing task\n", block_start)
    line_end = line_start + len("- [ ] (T-10) existing task\n")

    append_region = Region(kind="ref_block", mode="append",
                           start=block_start, end=block_end,
                           interior=original[block_start:block_end])
    checkoff_region = Region(kind="checklist", mode="checkoff",
                             start=line_start, end=line_end,
                             interior=original[line_start:line_end])
    edits = [(append_region, "- [ ] (T-11) new task\n"), (checkoff_region, "")]
    modified = _apply_all(original, edits)
    verify(original, modified, edits)  # must not raise
