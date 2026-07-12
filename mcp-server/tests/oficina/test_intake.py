"""Tests for oficina.intake — every deterministic rejection rule, both profiles.

Synchronous tests (plain ``def``), not async.
"""

import pytest

from ollama_mcp.oficina.intake import (
    RULE_ANSWER_WITH_TARGET,
    RULE_CONTEXT_FILE_MISSING,
    RULE_FILE_WITHOUT_TARGET,
    RULE_OBJECTIVE_MISSING,
    RULE_UNKNOWN_KEY,
    RULE_UNKNOWN_KIND,
    RULE_WORKSPACE_UNSUPPORTED,
    check_intake,
)


def _file_spec(tmp_path):
    """A minimal valid kind:file spec targeting a path under tmp_path."""
    return {
        "deliverable": {"kind": "file", "target": str(tmp_path / "out.py")},
        "objective": "write a function",
    }


def _answer_spec():
    """A minimal valid kind:answer spec."""
    return {
        "deliverable": {"kind": "answer"},
        "objective": "answer the question",
    }


# --- Accepted specs pass through unchanged ----------------------------------


def test_valid_file_spec_accepted(tmp_path):
    """A well-formed kind:file spec is accepted."""
    result = check_intake(_file_spec(tmp_path))
    assert result.accepted is True


def test_valid_answer_spec_accepted():
    """A well-formed kind:answer spec is accepted."""
    result = check_intake(_answer_spec())
    assert result.accepted is True


def test_accepted_spec_passes_through_unchanged(tmp_path):
    """The accepted result's spec is the exact same object/content as the input."""
    spec = _file_spec(tmp_path)
    result = check_intake(spec)
    assert result.accepted and result.spec == spec


def test_accepted_result_has_no_rejection():
    """An accepted result carries no rejection."""
    result = check_intake(_answer_spec())
    assert result.rejection is None


# --- Objective rule ---------------------------------------------------------


def test_missing_objective_rejected():
    """A spec with no objective is rejected with the objective rule."""
    spec = _answer_spec()
    del spec["objective"]
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_OBJECTIVE_MISSING


def test_empty_objective_rejected():
    """An empty-string objective is rejected with the objective rule."""
    spec = _answer_spec()
    spec["objective"] = ""
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_OBJECTIVE_MISSING


# --- kind / target cross-rules (per profile) --------------------------------


def test_unknown_kind_rejected():
    """A deliverable.kind outside {file, answer} is rejected."""
    spec = {"deliverable": {"kind": "banana"}, "objective": "x"}
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_UNKNOWN_KIND


def test_missing_kind_rejected():
    """A deliverable with no kind is rejected as unknown_kind."""
    spec = {"deliverable": {}, "objective": "x"}
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_UNKNOWN_KIND


def test_file_without_target_rejected():
    """kind:file with no target is rejected with the file_without_target rule."""
    spec = {"deliverable": {"kind": "file"}, "objective": "x"}
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_FILE_WITHOUT_TARGET


def test_answer_with_target_rejected(tmp_path):
    """kind:answer that carries a target is rejected with the answer_with_target rule."""
    spec = {"deliverable": {"kind": "answer", "target": str(tmp_path / "x")}, "objective": "x"}
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_ANSWER_WITH_TARGET


# --- Unknown-key fail-loud --------------------------------------------------


def test_unknown_top_level_key_rejected(tmp_path):
    """A typo'd top-level key (e.g. 'contxt') fails loud, not silently ignored."""
    spec = _file_spec(tmp_path)
    spec["contxt"] = {}
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_UNKNOWN_KEY


def test_unknown_deliverable_key_rejected(tmp_path):
    """An unknown key inside deliverable fails loud."""
    spec = _file_spec(tmp_path)
    spec["deliverable"]["bogus"] = 1
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_UNKNOWN_KEY


# --- Workspace rule ---------------------------------------------------------


def test_unsupported_workspace_rejected():
    """workspace other than in_place is rejected in P1."""
    spec = _answer_spec()
    spec["workspace"] = "worktree"
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_WORKSPACE_UNSUPPORTED


def test_in_place_workspace_accepted():
    """An explicit workspace: in_place is accepted."""
    spec = _answer_spec()
    spec["workspace"] = "in_place"
    result = check_intake(spec)
    assert result.accepted is True


# --- Context-file existence -------------------------------------------------


def test_nonexistent_context_file_rejected():
    """A context.files entry pointing at a missing path is rejected."""
    spec = _answer_spec()
    spec["context"] = {"files": ["/definitely/not/here/nope.txt"]}
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == RULE_CONTEXT_FILE_MISSING


def test_existing_context_file_accepted(tmp_path):
    """A context.files entry that exists on disk is accepted."""
    f = tmp_path / "ctx.txt"
    f.write_text("hi")
    spec = _answer_spec()
    spec["context"] = {"files": [str(f)]}
    result = check_intake(spec)
    assert result.accepted is True


# --- Rejection payload shape (where/whose/what triad) -----------------------


def test_rejection_payload_carries_triad():
    """Every rejection's payload names stage=intake, fault=payload, and the rule."""
    spec = _answer_spec()
    del spec["objective"]
    result = check_intake(spec)
    assert not result.accepted
    payload = result.rejection.payload
    assert payload["stage"] == "intake"
    assert payload["fault"] == "payload"
    assert payload["rule"] == result.rejection.rule
