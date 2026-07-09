"""Tests for the resume step interpreter (R-D1, R-D2, R-D3).

`present()` carries all the shared presentation rules, so most step behavior is tested
through it. The key distinction the options encode: **empty is not absent.** A step that
yields no lines still prints its title and fallback — it ran and found nothing — unless
`omit_if_empty` says the section should disappear entirely.
"""

import pytest

from sessiontracking.resume.config import (
    ResumeConfigError,
    Step,
    load_resume_config,
)
from sessiontracking.resume.steps import (
    Context,
    StepError,
    _extract_next_section,
    present,
    render,
)


# ── present(): the shared presentation rules ─────────────────────────────────


def test_filters_drop_matching_lines():
    step = Step(kind="region", filters=("^<!-- ", "^$"))
    raw = "<!-- ref:x -->\nkeep me\n\nalso me\n"
    assert present(step, raw) == ["keep me", "also me"]


def test_head_truncates_after_filtering():
    """Order matters: filter first, then head. Otherwise a filtered line eats a slot."""
    step = Step(kind="region", filters=("^<!-- ",), head=2)
    raw = "<!-- drop -->\na\nb\nc\n"
    assert present(step, raw) == ["a", "b"]


def test_title_precedes_body_when_non_empty():
    step = Step(kind="region", title="── T ──")
    assert present(step, "a\n") == ["── T ──", "a"]


def test_empty_prints_title_and_fallback():
    """The step ran and found nothing — say so, under its own heading."""
    step = Step(kind="region", title="── T ──", fallback="(none)")
    assert present(step, "") == ["── T ──", "(none)"]


def test_title_on_empty_false_suppresses_the_title():
    step = Step(kind="region", title="  User preferences:",
                title_on_empty=False, fallback="  (no prefs)")
    assert present(step, "") == ["  (no prefs)"]


def test_omit_if_empty_removes_the_whole_section():
    step = Step(kind="git_status", title="── Uncommitted ──",
                omit_if_empty=True, trailing_blank=True)
    assert present(step, "") == []


def test_omitted_step_gets_no_trailing_blank():
    """Regression: an omitted section must not leave a stray blank line behind."""
    step = Step(kind="git_status", omit_if_empty=True, trailing_blank=True)
    assert present(step, "\n") == []


def test_empty_with_trailing_blank_still_emits_the_blank():
    """Empty is not absent: the step ran, so its spacing survives."""
    step = Step(kind="region", trailing_blank=True)
    assert present(step, "") == [""]


def test_empty_string_fallback_is_not_treated_as_absent():
    """`fallback: ""` is a value. Truthiness would silently drop it."""
    step = Step(kind="region", fallback="")
    assert present(step, "") == [""]


def test_all_lines_filtered_behaves_like_empty():
    step = Step(kind="region", filters=("^x",), fallback="(none)")
    assert present(step, "xa\nxb\n") == ["(none)"]


def test_trailing_newline_does_not_create_a_blank_line():
    step = Step(kind="region")
    assert present(step, "a\n") == ["a"]


# ── log_next: the overlay owns session-log.md's structure ────────────────────


def test_extract_next_takes_the_newest_entry_only():
    """The heading is part of the output — it says WHICH session's Next you are reading."""
    text = (
        "# Log\n\n---\n"
        "## 2026-07-09 - Session 2: newer\n"
        "### Context\nskipped\n"
        "### Next\n- do the new thing\n\n---\n"
        "## 2026-07-01 - Session 1: older\n"
        "### Next\n- do the old thing\n"
    )
    assert _extract_next_section(text) == (
        "## 2026-07-09 - Session 2: newer\n### Next\n- do the new thing\n"
    )


def test_extract_next_returns_only_the_heading_when_next_is_absent():
    text = "## 2026-07-09 - Session 2: x\n### Context\nnope\n"
    assert _extract_next_section(text) == "## 2026-07-09 - Session 2: x"


def test_extract_next_returns_empty_when_there_is_no_entry():
    assert _extract_next_section("# Log\n\n---\n") == ""


def test_text_step_trailing_blank_survives_the_rstrip():
    """Spacing must come from `trailing_blank:`, not a bare "" in `lines:` — present()
    sheds trailing newlines, so a blank data line would be silently eaten."""
    swallowed = Step(kind="text", lines=("a", ""))
    assert present(swallowed, "a\n") == ["a"]  # the "" is gone, by design
    explicit = Step(kind="text", lines=("a",), trailing_blank=True)
    assert present(explicit, "a") == ["a", ""]


# ── region: role resolution goes through the register ────────────────────────


def _ctx(tmp_path, register):
    return Context(tmp_path, register, date="2026-07-09")


REGION_ROLE = {
    "file": "notes.md",
    "locator": {"type": "ref_block", "key": "k"},
    "write_mode": "nomodel",
}


def test_region_resolves_through_the_register(tmp_path):
    (tmp_path / "notes.md").write_text("pre\n<!-- ref:k -->\nbody\n<!-- /ref:k -->\npost\n")
    step = Step(kind="region", role="r")
    assert render(step, _ctx(tmp_path, {"r": REGION_ROLE})) == ["body"]


def test_region_names_a_missing_role_with_a_repair_hint(tmp_path):
    step = Step(kind="region", role="ghost")
    with pytest.raises(StepError) as exc:
        render(step, _ctx(tmp_path, {}))
    assert "ghost" in str(exc.value)
    assert "registry.yaml" in str(exc.value)


def test_region_reports_a_missing_target_file(tmp_path):
    step = Step(kind="region", role="r")
    with pytest.raises(StepError) as exc:
        render(step, _ctx(tmp_path, {"r": REGION_ROLE}))
    assert "missing file" in str(exc.value)


# ── text + run ───────────────────────────────────────────────────────────────


def test_text_substitutes_the_date(tmp_path):
    step = Step(kind="text", lines=("  PROJECT RESUME — {date}",))
    assert render(step, _ctx(tmp_path, {})) == ["  PROJECT RESUME — 2026-07-09"]


def test_run_captures_stdout(tmp_path):
    step = Step(kind="run", command="echo hello")
    assert render(step, _ctx(tmp_path, {})) == ["hello"]


def test_run_failure_yields_nothing_not_a_crash(tmp_path):
    step = Step(kind="run", command="exit 7", fallback="(step failed)")
    assert render(step, _ctx(tmp_path, {})) == ["(step failed)"]


# ── config validation ────────────────────────────────────────────────────────


def _write_cfg(tmp_path, text):
    p = tmp_path / "resume.yaml"
    p.write_text(text)
    return p


def test_unknown_step_kind_points_at_the_escape_hatch(tmp_path):
    p = _write_cfg(tmp_path, "steps:\n  - kind: sacrifice_goat\n")
    with pytest.raises(ResumeConfigError) as exc:
        load_resume_config(p)
    assert "sacrifice_goat" in str(exc.value)
    assert "kind: run" in str(exc.value)


def test_region_without_role_or_ref_key_is_refused(tmp_path):
    p = _write_cfg(tmp_path, "steps:\n  - kind: region\n    title: x\n")
    with pytest.raises(ResumeConfigError) as exc:
        load_resume_config(p)
    assert "role:" in str(exc.value)


def test_run_without_command_is_refused(tmp_path):
    p = _write_cfg(tmp_path, "steps:\n  - kind: run\n")
    with pytest.raises(ResumeConfigError):
        load_resume_config(p)


def test_unsupported_schema_is_refused(tmp_path):
    p = _write_cfg(tmp_path, "version: 99\nsteps: []\n")
    with pytest.raises(ResumeConfigError) as exc:
        load_resume_config(p)
    assert "99" in str(exc.value)


def test_absent_version_is_schema_1(tmp_path):
    p = _write_cfg(tmp_path, "steps:\n  - kind: text\n    lines: [hi]\n")
    assert len(load_resume_config(p).steps) == 1


def test_shipped_default_config_parses():
    """The resume.yaml this overlay ships must load under the current schema."""
    from pathlib import Path
    default = Path(__file__).resolve().parents[1] / "files" / "resume.yaml"
    cfg = load_resume_config(default)
    assert [s.kind for s in cfg.steps][:2] == ["text", "region"]
    roles = {s.role for s in cfg.steps if s.kind == "region"}
    assert roles == {"current-status", "reading-guide", "quick-pointers",
                     "active-decisions", "user-prefs"}
