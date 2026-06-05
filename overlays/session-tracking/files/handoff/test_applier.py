"""Contract tests for F3 Applier (session-handoff pipeline, Scope A).

The Applier takes the file text, a Region (from F1 Locator), and an authored
`content` block, and returns the NEW file text with the content spliced in
according to the region's write mode. It must never alter bytes outside the
region it edits — that invariant is what F4 Verifier later proves by hashing.

API under test:
    from applier import apply, ApplierError
    from locator import Region, locate
    apply(text: str, region: Region, content: str = "") -> str

Write modes:
    replace  — swap the region interior with `content`
    prepend  — insert `content` at region.start (before existing interior / at anchor)
    append   — insert `content` at region.end   (after existing interior / at anchor)
    checkoff — flip the matched task line's first "[ ]" to "[x]" (`content` ignored)
    nomodel  — never applied from the payload -> raise ApplierError

Each test obtains its Region via locate(role, text[, task_id]) — the same path
the orchestrator uses — then applies and asserts on the resulting string.
"""

import pytest

from applier import apply, ApplierError
from locator import locate


# --- fixtures: role dicts (mirror registry.yaml shapes) --------------------- #

ROLE_REPLACE = {"locator": {"type": "ref_block", "key": "current-status"},
                "write_mode": "replace"}
ROLE_PREPEND_SPAN = {"locator": {"type": "ref_block", "key": "current-status"},
                     "write_mode": "prepend"}
ROLE_APPEND = {"locator": {"type": "ref_block", "key": "deferred-infra"},
               "write_mode": "append"}
ROLE_STRUCT_PREPEND = {"locator": {"type": "structural", "pattern": "^---$",
                                   "occurrence": 1, "position": "after"},
                       "write_mode": "prepend"}
ROLE_CHECK = {"locator": {"type": "checklist", "scope": "file"},
              "write_mode": "checkoff"}
ROLE_NOMODEL = {"locator": {"type": "field", "label": "Current Session"},
                "write_mode": "nomodel"}


def _ref_doc(key, interior):
    return f"PRE\n<!-- ref:{key} -->\n{interior}<!-- /ref:{key} -->\nPOST\n"


# --- replace ---------------------------------------------------------------- #

def test_replace_swaps_interior_with_content():
    """replace mode replaces the marker interior with the authored content."""
    text = _ref_doc("current-status", "OLD\n")
    region = locate(ROLE_REPLACE, text)
    result = apply(text, region, content="NEW\n")
    assert result == ("PRE\n<!-- ref:current-status -->\n"
                      "NEW\n"
                      "<!-- /ref:current-status -->\nPOST\n")
    assert "OLD" not in result


def test_replace_leaves_bytes_outside_the_region_untouched():
    """Everything before the open marker and after the close marker is byte-identical."""
    text = _ref_doc("current-status", "OLD\n")
    region = locate(ROLE_REPLACE, text)
    result = apply(text, region, content="anything at all\n")
    assert result.startswith("PRE\n<!-- ref:current-status -->\n")
    assert result.endswith("<!-- /ref:current-status -->\nPOST\n")


# --- prepend ---------------------------------------------------------------- #

def test_prepend_on_span_inserts_before_existing_interior():
    """prepend keeps the existing interior and puts content ahead of it (newest-first)."""
    text = _ref_doc("current-status", "EXISTING\n")
    region = locate(ROLE_PREPEND_SPAN, text)
    result = apply(text, region, content="NEW\n")
    assert result == ("PRE\n<!-- ref:current-status -->\n"
                      "NEW\nEXISTING\n"
                      "<!-- /ref:current-status -->\nPOST\n")
    assert result.index("NEW") < result.index("EXISTING")


def test_prepend_on_structural_anchor_inserts_at_the_anchor():
    """For a zero-width structural anchor, content lands exactly at the insertion point."""
    text = "# Header\n\n---\n## Session 82\n"
    region = locate(ROLE_STRUCT_PREPEND, text)
    result = apply(text, region, content="## Session 83\n")
    assert result == "# Header\n\n---\n## Session 83\n## Session 82\n"


# --- append ----------------------------------------------------------------- #

def test_append_on_span_inserts_after_existing_interior():
    """append keeps the existing interior and puts content after it."""
    text = _ref_doc("deferred-infra", "OLD\n")
    region = locate(ROLE_APPEND, text)
    result = apply(text, region, content="NEW\n")
    assert result == ("PRE\n<!-- ref:deferred-infra -->\n"
                      "OLD\nNEW\n"
                      "<!-- /ref:deferred-infra -->\nPOST\n")
    assert result.index("OLD") < result.index("NEW")


# --- checkoff --------------------------------------------------------------- #

def test_checkoff_flips_matched_task_to_checked():
    """checkoff turns the matched '- [ ] (T-NN)' line into '- [x] (T-NN)'."""
    text = ("- [ ] (T-04) **B2.3** — gate\n"
            "- [ ] (T-05) **B3.1** — bumps\n")
    region = locate(ROLE_CHECK, text, task_id="T-05")
    result = apply(text, region)
    assert "- [x] (T-05) **B3.1** — bumps\n" in result


def test_checkoff_changes_only_the_matched_line():
    """Other task lines (including other ids) are unchanged."""
    text = ("- [ ] (T-04) **B2.3** — gate\n"
            "- [ ] (T-05) **B3.1** — bumps\n")
    region = locate(ROLE_CHECK, text, task_id="T-05")
    result = apply(text, region)
    assert result == ("- [ ] (T-04) **B2.3** — gate\n"
                      "- [x] (T-05) **B3.1** — bumps\n")


# --- guards ----------------------------------------------------------------- #

def test_nomodel_mode_is_rejected():
    """Applying a nomodel region from the payload raises ApplierError."""
    text = "**Current Session:** foo\n"
    region = locate(ROLE_NOMODEL, text)
    with pytest.raises(ApplierError):
        apply(text, region, content="x")
