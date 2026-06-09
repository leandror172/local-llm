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


PAYLOAD = (
    "---\n"
    "session_title: B4 test\n"
    "current_layer: Tooling — pipeline (B4 in progress)\n"
    "checkoffs: [T-05, T-06]\n"
    "---\n"
    "## role: log-entry\n"
    "\n"
    "## 2026-06-06 - Session 86: B4 test\n"
    "### Context\n"
    "resumed; body has --- separators\n"
    "\n"
    "---\n"
    "\n"
    "### Next\n"
    "do B4.2\n"
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
    p = parse(PAYLOAD)
    assert set(p.blocks.keys()) == {"log-entry", "current-status"}
    assert "new status interior" in p.blocks["current-status"]


def test_parse_log_entry_keeps_internal_separators():
    """The body's own --- and ## headings must NOT be treated as fences/role headers."""
    le = parse(PAYLOAD).blocks["log-entry"]
    assert "## 2026-06-06 - Session 86: B4 test" in le
    assert "---" in le
    assert "do B4.2" in le
    assert "new status interior" not in le  # did not bleed into the next section


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
