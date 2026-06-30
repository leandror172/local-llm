"""Tests for retrieval/corpus_groups.py — shared corpus group matcher (T-65)."""
import sys
from pathlib import Path

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import corpus_groups as cg  # noqa: E402

GROUPS = [
    {"match": "**/.memories/*.md", "tag": "memories"},
    {"match": ".claude/archive/**", "tag": "archive"},
    {"match": "docs/research/**", "tag": "docs-research"},
    {"match": ".claude/**", "tag": "claude-meta"},
]


# --- glob_to_regex: ** semantics ------------------------------------------- #
def test_double_star_slash_matches_zero_leading_dirs():
    assert cg.glob_to_regex("**/.memories/*.md").match(".memories/QUICK.md")


def test_double_star_slash_matches_nested():
    assert cg.glob_to_regex("**/.memories/*.md").match("retrieval/.memories/QUICK.md")


def test_single_star_does_not_cross_slash():
    assert cg.glob_to_regex("docs/*.md").match("docs/x.md")
    assert not cg.glob_to_regex("docs/*.md").match("docs/sub/x.md")


def test_recursive_glob_matches_any_depth():
    assert cg.glob_to_regex(".claude/archive/**").match(".claude/archive/a/b/c.md")


# --- assign_group: first-match-wins ---------------------------------------- #
def test_first_match_wins_archive_before_catchall():
    # archive rule precedes the .claude/** catch-all
    assert cg.assign_group(".claude/archive/x.md", GROUPS) == "archive"


def test_memories_glob_beats_claude_catchall():
    assert cg.assign_group(".claude/.memories/QUICK.md", GROUPS) == "memories"


def test_unmatched_path_is_ungrouped():
    assert cg.assign_group("README.md", GROUPS) == cg.UNGROUPED


def test_load_group_rules_reads_corpus_yaml():
    rules = cg.load_group_rules()
    tags = {r["tag"] for r in rules}
    assert {"memories", "archive", "docs-research", "docs-ideas", "claude-meta"} <= tags
