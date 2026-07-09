# test_p2_renderer.py
#
# P2 — tests for the structured log-entry renderer in mechanics.py.
# These tests define the contract that the Ollama renderer must satisfy.
# They test both the LogEntry dataclass and the render_log_entry() function.
#
# Flat imports — run from inside the handoff dir.

import pytest
from sessiontracking.handoff.mechanics import render_log_entry, LogEntry


# ---- LogEntry dataclass -------------------------------------------------

def test_log_entry_requires_what_was_done():
    """what_was_done is REQUIRED — empty list must fail."""
    with pytest.raises((ValueError, TypeError)):
        LogEntry(what_was_done=[], next=["something"])


def test_log_entry_requires_next():
    """next is REQUIRED — empty list must fail."""
    with pytest.raises((ValueError, TypeError)):
        LogEntry(what_was_done=["did a thing"], next=[])


def test_log_entry_minimal_valid():
    """Only required fields — optional fields default to empty/None."""
    le = LogEntry(what_was_done=["did something"], next=["do next thing"])
    assert le.what_was_done == ["did something"]
    assert le.next == ["do next thing"]
    assert not le.context
    assert not le.decisions
    assert not le.gotchas


def test_log_entry_full():
    """All fields set."""
    le = LogEntry(
        context="resumed from B3",
        what_was_done=["fixed the bug", "wrote tests"],
        decisions=["use X over Y because Z"],
        next=["run benchmarks"],
        gotchas=["F4 can't see newline gaps"],
    )
    assert le.context == "resumed from B3"
    assert len(le.what_was_done) == 2
    assert len(le.decisions) == 1
    assert len(le.gotchas) == 1


# ---- render_log_entry: heading -------------------------------------------

def test_render_heading_uses_hyphen():
    """Heading: '## <date> - Session <N>: <title>' with a hyphen, not em-dash."""
    out = render_log_entry(
        LogEntry(what_was_done=["x"], next=["y"]),
        date="2026-06-15",
        session_number=91,
        session_title="P2 renderer",
    )
    assert "## 2026-06-15 - Session 91: P2 renderer\n" in out


def test_render_heading_is_first_line():
    """The heading must be the very first line of the rendered block."""
    out = render_log_entry(
        LogEntry(what_was_done=["x"], next=["y"]),
        date="2026-06-15",
        session_number=91,
        session_title="P2 renderer",
    )
    assert out.startswith("## 2026-06-15 - Session 91: P2 renderer\n")


# ---- render_log_entry: sections ------------------------------------------

def test_render_required_sections_present():
    """### What Was Done and ### Next appear in the rendered output."""
    out = render_log_entry(
        LogEntry(what_was_done=["item A", "item B"], next=["step X"]),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    assert "### What Was Done\n" in out
    assert "### Next\n" in out


def test_render_bullets_for_list_fields():
    """List fields render as '- item' bullets."""
    out = render_log_entry(
        LogEntry(what_was_done=["did A", "did B"], next=["do C"]),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    assert "- did A\n" in out
    assert "- did B\n" in out
    assert "- do C\n" in out


def test_render_context_as_paragraph():
    """context renders as a plain paragraph, NOT as a bullet."""
    out = render_log_entry(
        LogEntry(context="entry point was X", what_was_done=["y"], next=["z"]),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    assert "### Context\n" in out
    assert "entry point was X" in out
    # context is NOT a bullet
    assert "- entry point was X" not in out


def test_render_optional_sections_present_when_set():
    """All optional sections appear when provided."""
    out = render_log_entry(
        LogEntry(
            context="ctx",
            what_was_done=["w"],
            decisions=["d"],
            next=["n"],
            gotchas=["g"],
        ),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    assert "### Context\n" in out
    assert "### Decisions Made\n" in out
    assert "### Gotchas\n" in out


def test_render_optional_sections_omitted_when_empty():
    """Empty optional sections produce NO header in the output."""
    out = render_log_entry(
        LogEntry(what_was_done=["w"], next=["n"]),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    assert "### Context" not in out
    assert "### Decisions Made" not in out
    assert "### Gotchas" not in out


def test_render_section_order():
    """Sections appear in the canonical order: heading, Context, What Was Done,
    Decisions Made, Next, Gotchas."""
    out = render_log_entry(
        LogEntry(
            context="c",
            what_was_done=["w"],
            decisions=["d"],
            next=["n"],
            gotchas=["g"],
        ),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    positions = {
        "heading": out.index("## 2026-06-15"),
        "context": out.index("### Context"),
        "done": out.index("### What Was Done"),
        "decisions": out.index("### Decisions Made"),
        "next": out.index("### Next"),
        "gotchas": out.index("### Gotchas"),
    }
    assert positions["heading"] < positions["context"]
    assert positions["context"] < positions["done"]
    assert positions["done"] < positions["decisions"]
    assert positions["decisions"] < positions["next"]
    assert positions["next"] < positions["gotchas"]


# ---- newline-termination contract (the session-86 dog-food bug) ----------

def test_rendered_block_ends_with_exactly_one_newline():
    """Rendered block must end with exactly one trailing newline.

    The block is prepended; without a trailing newline it would glue onto the
    next line (e.g. the `---` separator), which F4 cannot detect.
    """
    out = render_log_entry(
        LogEntry(what_was_done=["w"], next=["n"]),
        date="2026-06-15",
        session_number=91,
        session_title="T",
    )
    assert out.endswith("\n"), "rendered block must end with a newline"
    assert not out.endswith("\n\n"), "rendered block must not end with a double newline"


def test_rendered_block_does_not_glue_onto_following_line():
    """Prepending rendered block in front of an existing heading line must not
    corrupt the heading. The existing heading must still be at a line start.

    This is the F4-invisible failure: F4 cannot see the missing-newline gap,
    so we test the no-glue property explicitly here.
    """
    from sessiontracking.handoff.mechanics import _extract_heading_numbers

    existing_log = (
        "# Session Log\n"
        "\n"
        "---\n"
        "\n"
        "## 2026-06-12 - Session 89: old entry\n"
        "### Next\n"
        "- do something\n"
    )
    rendered = render_log_entry(
        LogEntry(what_was_done=["new thing"], next=["next thing"]),
        date="2026-06-15",
        session_number=90,
        session_title="new entry",
    )
    # Simulate the prepend applier: insert rendered block at the start of the interior
    # (which starts after the `---` line — immediately after position of `\n---\n`)
    insert_pos = existing_log.index("---\n") + len("---\n")
    combined = existing_log[:insert_pos] + rendered + existing_log[insert_pos:]

    # Both session headings must be parseable
    numbers = _extract_heading_numbers(combined)
    assert 89 in numbers, "old heading must still be intact"
    assert 90 in numbers, "new heading must be present"

    # The old heading must still start at a line start
    idx = combined.index("## 2026-06-12 - Session 89:")
    assert combined[idx - 1] == "\n", "old heading must be preceded by a newline"
