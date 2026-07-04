"""
Tests for retrieval/relate.py — T2 aggregation (synthetic fixtures, no live index).

Covers:
- cross_file_edges: collect edges spanning the two node sets, both orientations,
  node_a always normalized to the file_a side.
- edge_stats: per-kind counts + max/mean weight; negative case is all-zero.
- top_edges: top-N cross-file edges by weight.
- community_overlap: shared community ids + Jaccard at coarse and fine.
- shared_anchors: anchor nodes with edges into BOTH files' node sets.
- provenance: source_group counts per side (reported, never weighted).
"""

import pytest

from relate import (
    Node,
    cross_file_edges,
    edge_stats,
    top_edges,
    community_overlap,
    shared_anchors,
    provenance,
)


def _node(id, file_path, coarse=1, fine=1, kind="extracted", group="docs-research", vector=(1.0, 0.0)):
    return Node(
        id=id,
        file_path=file_path,
        node_kind=kind,
        source_group=group,
        community_coarse=coarse,
        community_fine=fine,
        vector=list(vector),
    )


def _edge(src, dst, kind="similarity", weight=0.8, directed=False):
    return {"src_id": src, "dst_id": dst, "edge_kind": kind, "weight": weight, "directed": directed}


A_IDS = {"a1", "a2"}
B_IDS = {"b1", "b2"}


# --- cross_file_edges ---------------------------------------------------------

def test_cross_file_edges_collects_spanning_edges():
    edges = [
        _edge("a1", "b1"),          # cross
        _edge("a1", "a2"),          # within A — excluded
        _edge("b1", "b2"),          # within B — excluded
    ]
    cross = cross_file_edges(edges, A_IDS, B_IDS)
    assert len(cross) == 1
    assert cross[0]["node_a"] == "a1"
    assert cross[0]["node_b"] == "b1"


def test_cross_file_edges_normalizes_reversed_orientation():
    # undirected edges are stored canonical src_id < dst_id, so the A-side node
    # may sit in dst; node_a must still resolve to the file_a side.
    edges = [_edge("b1", "a2")]
    cross = cross_file_edges(edges, A_IDS, B_IDS)
    assert cross[0]["node_a"] == "a2"
    assert cross[0]["node_b"] == "b1"


def test_cross_file_edges_ignores_unrelated_endpoints():
    edges = [_edge("a1", "zzz"), _edge("qqq", "b2")]
    assert cross_file_edges(edges, A_IDS, B_IDS) == []


# --- edge_stats ---------------------------------------------------------------

def test_edge_stats_counts_by_kind_and_weights():
    cross = [
        {"node_a": "a1", "node_b": "b1", "edge_kind": "similarity", "weight": 0.9},
        {"node_a": "a2", "node_b": "b2", "edge_kind": "similarity", "weight": 0.7},
        {"node_a": "a1", "node_b": "b2", "edge_kind": "same_as", "weight": 1.0},
        {"node_a": "a2", "node_b": "b1", "edge_kind": "references", "weight": 1.0},
    ]
    stats = edge_stats(cross)
    assert stats["similarity"] == 2
    assert stats["same_as"] == 1
    assert stats["references"] == 1
    assert stats["max_weight"] == pytest.approx(1.0)
    assert stats["mean_weight"] == pytest.approx((0.9 + 0.7 + 1.0 + 1.0) / 4)


def test_edge_stats_negative_case_all_zero():
    stats = edge_stats([])
    assert stats["similarity"] == 0
    assert stats["same_as"] == 0
    assert stats["references"] == 0
    assert stats["max_weight"] == 0.0
    assert stats["mean_weight"] == 0.0


# --- top_edges ----------------------------------------------------------------

def test_top_edges_sorted_desc_and_limited():
    cross = [
        {"node_a": f"a{i}", "node_b": f"b{i}", "edge_kind": "similarity", "weight": w}
        for i, w in enumerate([0.1, 0.9, 0.5, 0.7, 0.3])
    ]
    top = top_edges(cross, n=3)
    assert [e["weight"] for e in top] == [0.9, 0.7, 0.5]


def test_top_edges_empty_is_empty():
    assert top_edges([], n=10) == []


# --- community_overlap --------------------------------------------------------

def test_community_overlap_shared_and_jaccard():
    nodes_a = [_node("a1", "docs/a.md", coarse=1, fine=10), _node("a2", "docs/a.md", coarse=2, fine=11)]
    nodes_b = [_node("b1", "docs/b.md", coarse=2, fine=20), _node("b2", "docs/b.md", coarse=3, fine=11)]
    overlap = community_overlap(nodes_a, nodes_b)
    # coarse: A={1,2} B={2,3} -> shared {2}, union {1,2,3} -> 1/3
    assert overlap["coarse"]["shared"] == [2]
    assert overlap["coarse"]["jaccard"] == pytest.approx(1 / 3)
    # fine: A={10,11} B={20,11} -> shared {11}, union {10,11,20} -> 1/3
    assert overlap["fine"]["shared"] == [11]
    assert overlap["fine"]["jaccard"] == pytest.approx(1 / 3)


def test_community_overlap_disjoint_is_zero():
    nodes_a = [_node("a1", "docs/a.md", coarse=1, fine=10)]
    nodes_b = [_node("b1", "docs/b.md", coarse=9, fine=99)]
    overlap = community_overlap(nodes_a, nodes_b)
    assert overlap["coarse"]["shared"] == []
    assert overlap["coarse"]["jaccard"] == 0.0
    assert overlap["fine"]["shared"] == []
    assert overlap["fine"]["jaccard"] == 0.0


# --- shared_anchors -----------------------------------------------------------

def test_shared_anchors_bridging_both_files():
    nodes = [
        _node("a1", "docs/a.md"),
        _node("b1", "docs/b.md"),
        _node("ref:concept-x", "docs/x.md", kind="anchor", group="ungrouped"),
    ]
    edges = [
        _edge("ref:concept-x", "a1", kind="references", weight=1.0, directed=True),
        _edge("ref:concept-x", "b1", kind="references", weight=1.0, directed=True),
    ]
    result = shared_anchors(nodes, edges, {"a1"}, {"b1"})
    assert len(result) == 1
    assert result[0]["anchor_key"] == "ref:concept-x"
    assert result[0]["linked_from_a"] == ["a1"]
    assert result[0]["linked_from_b"] == ["b1"]


def test_shared_anchors_excludes_one_sided_anchor():
    nodes = [
        _node("a1", "docs/a.md"),
        _node("ref:concept-y", "docs/y.md", kind="anchor"),
    ]
    edges = [_edge("ref:concept-y", "a1", kind="references", directed=True)]
    # anchor links only into file A -> not shared
    assert shared_anchors(nodes, edges, {"a1"}, {"b1"}) == []


# --- provenance ---------------------------------------------------------------

def test_provenance_counts_per_side():
    nodes_a = [
        _node("a1", "docs/a.md", group="docs-research"),
        _node("a2", "docs/a.md", group="docs-research"),
        _node("a3", "docs/a.md", group="memories"),
    ]
    nodes_b = [_node("b1", "docs/b.md", group="archive")]
    prov = provenance(nodes_a, nodes_b)
    assert prov["a"] == {"docs-research": 2, "memories": 1}
    assert prov["b"] == {"archive": 1}
