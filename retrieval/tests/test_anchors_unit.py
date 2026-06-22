"""Unit tests for SA-1 slice: ingest_anchors, parse_first_prose_line, describe_*.

Heading direction (contract ambiguity resolved):
  heading = first ``#``-line WITHIN the block (at/after the opening marker),
  not scanning upward. Every real block in the repo opens with its own heading
  immediately below the marker. Scanning up would grab the previous block's heading.
  This is documented in SA-1 implementation notes and in item 5 of the final report.

Fixture strategy:
  - parse_first_prose_line: inline string literals — pure function, no I/O.
  - describe_*: Anchor dataclass with known fields — no I/O.
  - ingest_anchors: tmp git repo (git init + git add) for real tracked-only filter.
"""

import subprocess
import textwrap
from pathlib import Path

import pytest

from retrieval.anchors import (
    Anchor,
    DEFAULT_METHOD,
    METHOD_KEY_ONLY,
    METHOD_MECHANICAL,
    METHOD_MECHANICAL_KEY,
    describe,
    describe_key_only,
    describe_mechanical,
    describe_mechanical_key,
    ingest_anchors,
    parse_first_prose_line,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_anchor(
    bare_key: str = "concept-latent-topic-graph",
    heading: str = "Latent Topic Graph",
    first_prose: str = "The core concept behind LTG retrieval.",
    file_path: str = "docs/foo.md",
    start_line: int = 1,
) -> Anchor:
    return Anchor(
        key=f"ref:{bare_key}",
        bare_key=bare_key,
        file_path=file_path,
        start_line=start_line,
        heading=heading,
        first_prose=first_prose,
    )


# ---------------------------------------------------------------------------
# parse_first_prose_line — skip rules
# ---------------------------------------------------------------------------


def test_parse_returns_first_real_prose_line():
    body = "Some prose here.\nAnother line."
    assert parse_first_prose_line(body) == "Some prose here."


def test_parse_skips_blank_lines_before_prose():
    body = "\n\nActual prose."
    assert parse_first_prose_line(body) == "Actual prose."


def test_parse_skips_italic_only_metadata_line():
    body = "*Status: frozen*\nReal prose."
    assert parse_first_prose_line(body) == "Real prose."


def test_parse_does_not_skip_bold_line():
    """Bold (``**...**``) is NOT skipped — only italic-only ``*...*`` is."""
    body = "**Full discussion:** see design doc.\nSecond line."
    assert parse_first_prose_line(body) == "**Full discussion:** see design doc."


def test_parse_does_not_skip_inline_italic():
    """A line with inline italic (not the whole line) is NOT skipped."""
    body = "Foo *bar* baz\nOther."
    assert parse_first_prose_line(body) == "Foo *bar* baz"


def test_parse_skips_subheadings():
    body = "## Sub-heading\nProse after heading."
    assert parse_first_prose_line(body) == "Prose after heading."


def test_parse_skips_top_level_heading():
    body = "# Top Heading\nProse."
    assert parse_first_prose_line(body) == "Prose."


def test_parse_skips_horizontal_rule():
    body = "---\nProse after rule."
    assert parse_first_prose_line(body) == "Prose after rule."


def test_parse_skips_html_comment_markers():
    """HTML comment lines (<!-- ... -->) are skipped."""
    body = "<!-- /ref:foo -->\nProse."
    assert parse_first_prose_line(body) == "Prose."


def test_parse_skips_multiple_skip_types_in_sequence():
    body = "\n*meta*\n---\n## heading\nReal prose here."
    assert parse_first_prose_line(body) == "Real prose here."


def test_parse_returns_empty_string_when_no_prose():
    body = "\n*meta*\n---\n## heading\n"
    assert parse_first_prose_line(body) == ""


def test_parse_table_row_counts_as_prose():
    """Tables are not in the skip list — a | row | counts as prose (spec literal)."""
    body = "| Field | Value |\nOther."
    assert parse_first_prose_line(body) == "| Field | Value |"


def test_parse_empty_body_returns_empty_string():
    assert parse_first_prose_line("") == ""


# ---------------------------------------------------------------------------
# describe_mechanical_key
# ---------------------------------------------------------------------------


def test_describe_mechanical_key_format_uses_em_dash():
    a = make_anchor(
        bare_key="concept-ltg",
        heading="Latent Topic Graph",
        first_prose="Core concept.",
    )
    result = describe_mechanical_key(a)
    # Must use em-dash U+2014 exactly
    assert result == "concept-ltg: Latent Topic Graph — Core concept."


def test_describe_mechanical_key_bare_key_is_hyphenated():
    """bare_key must never be space-normalised — D3 requirement."""
    a = make_anchor(bare_key="my-hyphenated-key", heading="H", first_prose="P")
    assert "my-hyphenated-key:" in describe_mechanical_key(a)


def test_describe_mechanical_key_no_ref_prefix_in_output():
    a = make_anchor(bare_key="git-safety", heading="Git Safety", first_prose="Foo.")
    result = describe_mechanical_key(a)
    assert not result.startswith("ref:")


# ---------------------------------------------------------------------------
# describe_key_only
# ---------------------------------------------------------------------------


def test_describe_key_only_returns_bare_key_alone():
    a = make_anchor(bare_key="git-safety", heading="Git Safety", first_prose="Foo.")
    assert describe_key_only(a) == "git-safety"


def test_describe_key_only_no_heading_or_prose_included():
    a = make_anchor(bare_key="foo", heading="Some Heading", first_prose="Some prose.")
    result = describe_key_only(a)
    assert "Some Heading" not in result
    assert "Some prose" not in result


# ---------------------------------------------------------------------------
# describe_mechanical
# ---------------------------------------------------------------------------


def test_describe_mechanical_includes_heading_and_prose():
    a = make_anchor(bare_key="irrelevant", heading="The Heading", first_prose="The prose.")
    result = describe_mechanical(a)
    assert "The Heading" in result
    assert "The prose." in result


def test_describe_mechanical_excludes_key():
    a = make_anchor(bare_key="my-key", heading="H", first_prose="P")
    result = describe_mechanical(a)
    assert "my-key" not in result
    assert "ref:" not in result


def test_describe_mechanical_uses_em_dash_separator():
    a = make_anchor(bare_key="k", heading="H", first_prose="P")
    result = describe_mechanical(a)
    assert "—" in result


# ---------------------------------------------------------------------------
# describe — dispatch
# ---------------------------------------------------------------------------


def test_describe_default_method_is_mechanical_key():
    a = make_anchor(bare_key="k", heading="H", first_prose="P")
    assert describe(a) == describe_mechanical_key(a)


def test_describe_with_method_mechanical_key():
    a = make_anchor(bare_key="k", heading="H", first_prose="P")
    assert describe(a, METHOD_MECHANICAL_KEY) == describe_mechanical_key(a)


def test_describe_with_method_key_only():
    a = make_anchor(bare_key="k", heading="H", first_prose="P")
    assert describe(a, METHOD_KEY_ONLY) == describe_key_only(a)


def test_describe_with_method_mechanical():
    a = make_anchor(bare_key="k", heading="H", first_prose="P")
    assert describe(a, METHOD_MECHANICAL) == describe_mechanical(a)


def test_describe_raises_on_unknown_method():
    a = make_anchor()
    with pytest.raises((ValueError, KeyError)):
        describe(a, "nonexistent_method")


# ---------------------------------------------------------------------------
# ingest_anchors — tmp git repo
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_git_repo(tmp_path):
    """A minimal git repo with tracked + untracked .md files."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    return tmp_path


def write_and_track(repo: Path, rel_path: str, content: str) -> Path:
    """Write a file and git add it."""
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", str(p)], cwd=repo, check=True, capture_output=True)
    return p


def test_ingest_finds_opening_marker_not_closing(tmp_git_repo):
    """``<!-- ref:KEY -->`` is ingested; ``<!-- /ref:KEY -->`` is not."""
    content = textwrap.dedent("""\
        <!-- ref:my-key -->
        # My Heading
        Some prose.
        <!-- /ref:my-key -->
    """)
    write_and_track(tmp_git_repo, "a.md", content)
    anchors = ingest_anchors(tmp_git_repo)
    keys = [a.key for a in anchors]
    assert "ref:my-key" in keys
    assert len([a for a in anchors if a.key == "ref:my-key"]) == 1


def test_ingest_dedup_first_occurrence_wins(tmp_git_repo):
    """Duplicate key across files: lexicographically-first file, lowest line wins."""
    content_a = textwrap.dedent("""\
        <!-- ref:dup-key -->
        # From A
        Prose from a.md.
        <!-- /ref:dup-key -->
    """)
    content_z = textwrap.dedent("""\
        <!-- ref:dup-key -->
        # From Z
        Prose from z.md.
        <!-- /ref:dup-key -->
    """)
    write_and_track(tmp_git_repo, "a.md", content_a)
    write_and_track(tmp_git_repo, "z.md", content_z)
    anchors = ingest_anchors(tmp_git_repo)
    dup = [a for a in anchors if a.key == "ref:dup-key"]
    assert len(dup) == 1
    assert dup[0].file_path == "a.md"


def test_ingest_untracked_file_not_ingested(tmp_git_repo):
    """An untracked .md file must NOT yield anchors (D2 safety: git grep tracked-only)."""
    content = textwrap.dedent("""\
        <!-- ref:untracked-key -->
        # Heading
        Prose.
        <!-- /untracked-key -->
    """)
    p = tmp_git_repo / "untracked.md"
    p.write_text(content, encoding="utf-8")
    # do NOT git add — file stays untracked
    anchors = ingest_anchors(tmp_git_repo)
    assert all(a.key != "ref:untracked-key" for a in anchors)


def test_ingest_populates_anchor_fields(tmp_git_repo):
    """Anchor fields are populated correctly: key, bare_key, file_path, start_line, heading, first_prose."""
    content = textwrap.dedent("""\
        Line 1
        <!-- ref:test-anchor -->
        # Test Section
        First real prose line.
        <!-- /ref:test-anchor -->
    """)
    write_and_track(tmp_git_repo, "docs/test.md", content)
    anchors = ingest_anchors(tmp_git_repo)
    a = next(x for x in anchors if x.key == "ref:test-anchor")
    assert a.bare_key == "test-anchor"
    assert a.file_path == "docs/test.md"
    assert a.start_line == 2  # 1-based; "<!-- ref:test-anchor -->" is on line 2
    assert a.heading == "Test Section"
    assert a.first_prose == "First real prose line."


def test_ingest_heading_is_within_block_not_above(tmp_git_repo):
    """Heading must be the first #-line INSIDE the block, not the previous block's heading."""
    content = textwrap.dedent("""\
        <!-- ref:first-block -->
        # First Block Heading
        Some prose.
        <!-- /ref:first-block -->

        <!-- ref:second-block -->
        # Second Block Heading
        Different prose.
        <!-- /ref:second-block -->
    """)
    write_and_track(tmp_git_repo, "multi.md", content)
    anchors = ingest_anchors(tmp_git_repo)
    second = next(a for a in anchors if a.key == "ref:second-block")
    assert second.heading == "Second Block Heading"


def test_ingest_heading_empty_when_no_heading_in_block(tmp_git_repo):
    """heading is "" when no #-line appears within the block."""
    content = textwrap.dedent("""\
        <!-- ref:no-heading-key -->
        Just prose, no heading.
        <!-- /ref:no-heading-key -->
    """)
    write_and_track(tmp_git_repo, "b.md", content)
    anchors = ingest_anchors(tmp_git_repo)
    a = next(x for x in anchors if x.key == "ref:no-heading-key")
    assert a.heading == ""


def test_ingest_multiple_anchors_in_one_file(tmp_git_repo):
    """Multiple distinct keys in one file each produce an Anchor."""
    content = textwrap.dedent("""\
        <!-- ref:key-alpha -->
        # Alpha
        Prose alpha.
        <!-- /ref:key-alpha -->

        <!-- ref:key-beta -->
        # Beta
        Prose beta.
        <!-- /ref:key-beta -->
    """)
    write_and_track(tmp_git_repo, "multi2.md", content)
    anchors = ingest_anchors(tmp_git_repo)
    keys = {a.key for a in anchors}
    assert "ref:key-alpha" in keys
    assert "ref:key-beta" in keys
