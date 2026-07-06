# test_payload.py
#
# Contract tests for B4.1 — the F7 payload schema + parser + validator.
# The format is YAML-ish frontmatter (scalars + checkoffs) followed by
# `## role: <name>` markdown sections. The parser MUST be robust to the body
# legitimately containing `---` separators and `## ` headings.
#
# Flat imports — run from inside the handoff dir or pass absolute file paths.

import pytest

from payload import parse, validate, PayloadError, HandoffPayload
from mechanics import LogEntry


PAYLOAD = (
    "---\n"
    "session_title: B4 test\n"
    "current_layer: Tooling — pipeline (B4 in progress)\n"
    "checkoffs: [T-05, T-06]\n"
    "---\n"
    "## role: log-entry\n"
    "\n"
    "### context\n"
    "resumed; started from the P2 branch\n"
    "\n"
    "### what_was_done\n"
    "- implemented slot parser\n"
    "- added renderer tests\n"
    "\n"
    "### next\n"
    "- do B4.2\n"
    "\n"
    "## role: current-status\n"
    "\n"
    "new status interior\n"
)

REGISTER = {
    "log-entry": {"write_mode": "prepend"},
    "current-status": {"write_mode": "replace"},
    "header-current-session": {"write_mode": "nomodel"},
    "tasks-checkoff": {"write_mode": "checkoff"},
}


# ---- parse: scalars + checkoffs ---------------------------------------------

def test_parse_extracts_scalars():
    p = parse(PAYLOAD)
    assert p.session_title == "B4 test"
    assert p.current_layer == "Tooling — pipeline (B4 in progress)"


def test_parse_extracts_checkoffs_list():
    assert parse(PAYLOAD).checkoffs == ["T-05", "T-06"]


def test_parse_checkoffs_default_empty_when_absent():
    text = "---\nsession_title: t\ncurrent_layer: l\n---\n## role: current-status\nx\n"
    assert parse(text).checkoffs == []


# ---- parse: role sections ---------------------------------------------------

def test_parse_splits_role_sections():
    """log-entry is parsed into log_entry (structured), not into blocks."""
    p = parse(PAYLOAD)
    # log-entry is NOT in blocks — it's in log_entry
    assert "log-entry" not in p.blocks
    assert "current-status" in p.blocks
    assert "new status interior" in p.blocks["current-status"]


def test_parse_log_entry_structured_slots():
    """log-entry body is parsed into a LogEntry with the correct slot values."""
    p = parse(PAYLOAD)
    le = p.log_entry
    assert le is not None
    assert isinstance(le, LogEntry)
    assert le.context == "resumed; started from the P2 branch"
    assert "implemented slot parser" in le.what_was_done
    assert "do B4.2" in le.next


def test_parse_log_entry_body_does_not_bleed_into_next_role():
    """log-entry content must not bleed into the next role section."""
    p = parse(PAYLOAD)
    assert p.log_entry is not None
    assert "new status interior" not in str(p.log_entry)


def test_parse_replace_role_keeps_internal_separators():
    """The body's own --- and ## headings in replace-mode roles must NOT be treated as fences/role headers."""
    text = (
        "---\nsession_title: t\ncurrent_layer: l\n---\n"
        "## role: current-status\n"
        "## Internal heading\n"
        "---\n"
        "content after sep\n"
    )
    p = parse(text)
    assert "## Internal heading" in p.blocks["current-status"]
    assert "---" in p.blocks["current-status"]
    assert "content after sep" in p.blocks["current-status"]


def test_parse_raw_is_verbatim():
    assert parse(PAYLOAD).raw == PAYLOAD


# ---- parse: structural errors -----------------------------------------------

def test_parse_missing_frontmatter_raises():
    with pytest.raises(PayloadError):
        parse("## role: log-entry\nx\n")


def test_parse_duplicate_role_raises():
    text = (
        "---\nsession_title: t\ncurrent_layer: l\n---\n"
        "## role: current-status\na\n"
        "## role: current-status\nb\n"
    )
    with pytest.raises(PayloadError):
        parse(text)


# ---- validate ---------------------------------------------------------------

def test_validate_accepts_valid_payload():
    assert validate(parse(PAYLOAD), REGISTER) == []


def test_validate_flags_unknown_role():
    p = parse("---\nsession_title: t\ncurrent_layer: l\n---\n## role: bogus-role\nx\n")
    errors = validate(p, REGISTER)
    assert any("bogus-role" in e for e in errors)


def test_validate_flags_missing_scalar():
    p = parse("---\nsession_title: t\ncurrent_layer:\n---\n## role: current-status\nx\n")
    errors = validate(p, REGISTER)
    assert any("current_layer" in e for e in errors)


def test_validate_flags_malformed_checkoff_id():
    text = (
        "---\nsession_title: t\ncurrent_layer: l\ncheckoffs: [T-05, #bogus]\n---\n"
        "## role: current-status\nx\n"
    )
    errors = validate(parse(text), REGISTER)
    assert any("#bogus" in e for e in errors)


def _checkoff_text(ids: str) -> str:
    return (
        f"---\nsession_title: t\ncurrent_layer: l\ncheckoffs: [{ids}]\n---\n"
        "## role: current-status\nx\n"
    )


def test_validate_accepts_dot_numeric_id():
    assert not any("malformed" in e for e in validate(parse(_checkoff_text("5.R1")), REGISTER))


def test_validate_accepts_prefix_dash_id():
    assert not any("malformed" in e for e in validate(parse(_checkoff_text("RUI-4")), REGISTER))


def test_validate_accepts_bare_numeric_id():
    assert not any("malformed" in e for e in validate(parse(_checkoff_text("1.0")), REGISTER))


def test_validate_accepts_no_dash_id():
    assert not any("malformed" in e for e in validate(parse(_checkoff_text("T1")), REGISTER))


def test_validate_rejects_hash_id():
    errors = validate(parse(_checkoff_text("#035")), REGISTER)
    assert any("#035" in e for e in errors)


def test_validate_rejects_id_with_space():
    errors = validate(parse(_checkoff_text("LLM repo")), REGISTER)
    assert any("malformed" in e for e in errors)


def test_validate_rejects_nomodel_block_role():
    """Header fields come from scalars; a nomodel block role is a category error."""
    p = parse("---\nsession_title: t\ncurrent_layer: l\n---\n## role: header-current-session\nx\n")
    errors = validate(p, REGISTER)
    assert errors  # must complain (nomodel role cannot be written from the payload)


# ---- P2 — log-entry structured slots ----------------------------------------

def _log_entry_payload(slots_body: str) -> str:
    return (
        "---\nsession_title: t\ncurrent_layer: l\n---\n"
        "## role: log-entry\n"
        + slots_body
    )


def test_parse_log_entry_minimal_slots():
    """Minimal log-entry with only required slots parses into a LogEntry."""
    text = _log_entry_payload(
        "\n### what_was_done\n- did A\n\n### next\n- do B\n"
    )
    p = parse(text)
    assert p.log_entry is not None
    assert p.log_entry.what_was_done == ["did A"]
    assert p.log_entry.next == ["do B"]
    assert not p.log_entry.context
    assert not p.log_entry.decisions
    assert not p.log_entry.gotchas


def test_parse_log_entry_all_slots():
    """All optional slots parsed correctly."""
    text = _log_entry_payload(
        "\n### context\nentered from B3\n\n"
        "### what_was_done\n- thing 1\n- thing 2\n\n"
        "### decisions\n- picked X over Y\n\n"
        "### next\n- run benchmarks\n\n"
        "### gotchas\n- F4 blind spot\n"
    )
    p = parse(text)
    le = p.log_entry
    assert le.context == "entered from B3"
    assert le.what_was_done == ["thing 1", "thing 2"]
    assert le.decisions == ["picked X over Y"]
    assert le.next == ["run benchmarks"]
    assert le.gotchas == ["F4 blind spot"]


def test_parse_log_entry_missing_what_was_done_raises():
    """Missing what_was_done slot raises PayloadError with specific message."""
    text = _log_entry_payload("\n### next\n- do something\n")
    with pytest.raises(PayloadError) as exc_info:
        parse(text)
    assert "what_was_done" in str(exc_info.value)


def test_parse_log_entry_missing_next_raises():
    """Missing next slot raises PayloadError with specific message."""
    text = _log_entry_payload("\n### what_was_done\n- did something\n")
    with pytest.raises(PayloadError) as exc_info:
        parse(text)
    assert "next" in str(exc_info.value)


def test_parse_log_entry_empty_what_was_done_raises():
    """Empty what_was_done slot (header present but no items) raises PayloadError."""
    text = _log_entry_payload("\n### what_was_done\n\n### next\n- do B\n")
    with pytest.raises(PayloadError) as exc_info:
        parse(text)
    assert "what_was_done" in str(exc_info.value)


def test_parse_log_entry_rejects_old_form_heading():
    """Old form with '## <date> - Session N:' heading inside log-entry is rejected."""
    text = _log_entry_payload(
        "\n## 2026-06-06 - Session 86: B4 test\n### Context\nbody\n"
    )
    with pytest.raises(PayloadError) as exc_info:
        parse(text)
    assert "pipeline now renders" in str(exc_info.value)


def test_parse_log_entry_rejects_title_case_headers():
    """Old form with Title-Case section headers inside log-entry is rejected."""
    text = _log_entry_payload(
        "\n### What Was Done\n- did something\n\n### Next\n- do B\n"
    )
    with pytest.raises(PayloadError) as exc_info:
        parse(text)
    assert "snake_case" in str(exc_info.value)


def test_parse_log_entry_unknown_slot_raises():
    """Unknown slot key in log-entry raises PayloadError."""
    text = _log_entry_payload(
        "\n### what_was_done\n- A\n\n### unknown_slot\n- B\n\n### next\n- C\n"
    )
    with pytest.raises(PayloadError) as exc_info:
        parse(text)
    assert "unknown_slot" in str(exc_info.value)


# ---- T-78 — wrapped bullet continuation lines --------------------------------

def test_parse_log_entry_wrapped_bullet_joins_to_single_item():
    """A '- ' bullet followed by indented continuation lines is one item, space-joined."""
    text = _log_entry_payload(
        "\n### what_was_done\n"
        "- implemented a fairly long change that\n"
        "  wraps onto a second line\n"
        "  and even a third line\n"
        "\n### next\n- do B\n"
    )
    p = parse(text)
    assert p.log_entry.what_was_done == [
        "implemented a fairly long change that wraps onto a second line and even a third line"
    ]


def test_parse_log_entry_wrapped_bullet_then_single_line_bullet():
    """A wrapped bullet followed by a separate single-line bullet parses to exactly 2 items."""
    text = _log_entry_payload(
        "\n### what_was_done\n"
        "- first item that wraps\n"
        "  onto a continuation line\n"
        "- second item, single line\n"
        "\n### next\n- do B\n"
    )
    p = parse(text)
    assert p.log_entry.what_was_done == [
        "first item that wraps onto a continuation line",
        "second item, single line",
    ]


def test_parse_log_entry_prefixless_multiline_block_joins_to_single_item():
    """A multi-line block with no '- ' prefix at all collapses to one joined item."""
    text = _log_entry_payload(
        "\n### what_was_done\n- placeholder\n"
        "\n### next\n"
        "no dash here\n"
        "just a continuation\n"
        "of plain text\n"
    )
    p = parse(text)
    assert p.log_entry.next == ["no dash here just a continuation of plain text"]


def test_parse_log_entry_two_single_line_bullets_stay_separate():
    """Regression: two separate single-line '- ' bullets still parse to 2 distinct items."""
    text = _log_entry_payload(
        "\n### what_was_done\n- did A\n- did B\n\n### next\n- do B\n"
    )
    p = parse(text)
    assert p.log_entry.what_was_done == ["did A", "did B"]


def test_validate_rejects_log_entry_in_amend_mode():
    """log-entry is not allowed in amend mode (would duplicate session heading)."""
    text = _log_entry_payload("\n### what_was_done\n- A\n\n### next\n- B\n")
    p = parse(text)
    errors = validate(p, REGISTER, amend=True)
    assert any("log-entry" in e for e in errors)
    assert any("amend" in e for e in errors)
