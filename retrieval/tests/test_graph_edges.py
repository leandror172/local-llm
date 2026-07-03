# /mnt/i/workspaces/llm/retrieval/tests/test_graph_edges.py

import pytest
from pathlib import Path
from typing import Any

from graph import Edge, same_as_edges, reference_edges
from anchors import Anchor


def make_row(id: str, alias_of: Any = None) -> dict:
    row = {"id": id}
    if alias_of is not None:
        row["alias_of"] = alias_of
    return row


@pytest.fixture
def ref_doc(tmp_path) -> tuple[Path, list[Anchor]]:
    content = """\
<!-- ref:a -->
# Section A
See [ref:b] for storage. Also ref:b again, plus self ref:a and [ref:unknown].
A stray closing marker in prose: <!-- /ref:b -->
<!-- /ref:a -->
<!-- ref:b -->
# Section B
No mentions here.
<!-- /ref:b -->
"""
    doc_path = tmp_path / "doc.md"
    doc_path.write_text(content)

    anchors = [
        Anchor(key="ref:a", bare_key="a", file_path="doc.md", start_line=1, heading="Section A", first_prose=""),
        Anchor(key="ref:b", bare_key="b", file_path="doc.md", start_line=6, heading="Section B", first_prose=""),
    ]

    return tmp_path, anchors


def test_same_as_projects_each_alias_pair():
    rows = [make_row("topic-1", '["ref:a", "ref:b"]')]
    edges = same_as_edges(rows)
    assert len(edges) == 2
    edge_pairs = {(edge.src_id, edge.dst_id) for edge in edges}
    assert edge_pairs == {("ref:a", "topic-1"), ("ref:b", "topic-1")}
    for edge in edges:
        assert edge.edge_kind == "same_as"
        assert edge.weight == 1.0
        assert not edge.directed


def test_same_as_skips_rows_without_alias():
    rows = [
        make_row("topic-1"),
        make_row("topic-2", None),
        make_row("topic-3", '[]'),
    ]
    edges = same_as_edges(rows)
    assert edges == []


def test_same_as_canonical_ordering_and_sorted():
    rows = [
        make_row("topic-3", '["ref:b"]'),
        make_row("topic-1", '["ref:a", "ref:c"]'),
        make_row("topic-2", '["ref:a"]'),
    ]
    edges = same_as_edges(rows)
    assert len(edges) == 4
    for i in range(len(edges) - 1):
        assert edges[i].src_id <= edges[i + 1].src_id
        if edges[i].src_id == edges[i + 1].src_id:
            assert edges[i].dst_id < edges[i + 1].dst_id


def test_reference_edges_basic(ref_doc):
    repo_root, anchors = ref_doc
    edges = reference_edges(anchors, repo_root)
    assert len(edges) == 1
    edge = edges[0]
    assert edge.src_id == "ref:a"
    assert edge.dst_id == "ref:b"
    assert edge.edge_kind == "references"
    assert edge.weight == 1.0
    assert edge.directed


def test_reference_edges_no_mentions_no_edges(ref_doc):
    repo_root, anchors = ref_doc
    # Only include the "b" anchor with no mentions
    edges = reference_edges([anchors[1]], repo_root)
    assert edges == []


def test_reference_edges_directed_not_reordered(ref_doc):
    repo_root, anchors = ref_doc
    edges = reference_edges(anchors, repo_root)
    assert len(edges) == 1
    edge = edges[0]
    assert edge.src_id == "ref:a"
    assert edge.dst_id == "ref:b"
    assert edge.directed
