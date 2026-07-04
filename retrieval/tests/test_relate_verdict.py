"""
Tests for retrieval/relate.py — T3 nearest_miss + verdict banding + orchestrator.

Banding cascade (P5-D4, derived from recorded thresholds):
  1. cross-file same_as edge        -> strong
  2. max similarity-edge weight>=0.85 -> strong  (merge_cosine, anchors.COSINE_THRESHOLD)
  3. any cross-file similarity edge  -> moderate (>= tau_floor by construction)
  4. else compute nearest_miss (matmul, sub-tau only, P5-D3):
        nearest_miss cosine >= 0.55  -> weak
        else                         -> unrelated

Exact-cosine unit-vector fixtures: base=[1,0], vec(t)=[t, sqrt(1-t^2)] -> cos=t.
"""

import math

import pytest

from relate import (
    Node,
    nearest_miss,
    classify_verdict,
    build_relation,
    StaleCommunitiesError,
    UnknownFileError,
)

THRESHOLDS = {
    "tau_floor": 0.70,
    "merge_cosine": 0.85,
    "weak_floor": 0.55,
    "bands": {
        "strong": "same_as edge OR max similarity cosine >= merge_cosine",
        "moderate": "any cross-file similarity edge (cosine >= tau_floor)",
        "weak": "nearest_miss cosine >= weak_floor",
        "unrelated": "nearest_miss cosine < weak_floor",
    },
}

BASE = [1.0, 0.0]


def vec(t):
    """Unit vector whose cosine with BASE=[1,0] is exactly t."""
    return [t, math.sqrt(1.0 - t * t)]


def _node(id, file_path, vector, coarse=1, fine=1, kind="extracted", group="docs-research"):
    return Node(
        id=id,
        file_path=file_path,
        node_kind=kind,
        source_group=group,
        community_coarse=coarse,
        community_fine=fine,
        vector=vector,
    )


def _cross(kind, weight):
    return {"node_a": "a1", "node_b": "b1", "edge_kind": kind, "weight": weight}


# --- nearest_miss (matmul) ----------------------------------------------------

def test_nearest_miss_returns_best_cross_pair():
    # single node in A avoids intra-side ambiguity: argmax is over B.
    nodes_a = [_node("a1", "docs/a.md", BASE)]
    nodes_b = [_node("b1", "docs/b.md", vec(0.6)), _node("b2", "docs/b.md", vec(0.9))]
    nm = nearest_miss(nodes_a, nodes_b)
    # best pair is a1 (BASE) vs b2 (cos 0.9)
    assert nm["node_a"] == "a1"
    assert nm["node_b"] == "b2"
    assert nm["cosine"] == pytest.approx(0.9, abs=1e-6)


# --- verdict banding cascade --------------------------------------------------

def test_strong_via_same_as_edge_skips_matmul():
    verdict, nm = classify_verdict([_cross("same_as", 1.0)], [], [], THRESHOLDS)
    assert verdict == "strong"
    assert nm is None


def test_strong_via_similarity_at_merge_cosine():
    verdict, nm = classify_verdict([_cross("similarity", 0.85)], [], [], THRESHOLDS)
    assert verdict == "strong"
    assert nm is None


def test_just_below_merge_cosine_is_moderate():
    verdict, nm = classify_verdict([_cross("similarity", 0.8499)], [], [], THRESHOLDS)
    assert verdict == "moderate"
    assert nm is None


def test_similarity_edge_at_tau_floor_is_moderate():
    verdict, nm = classify_verdict([_cross("similarity", 0.70)], [], [], THRESHOLDS)
    assert verdict == "moderate"
    assert nm is None


def test_references_only_does_not_band_and_falls_through_to_matmul():
    # a lone references edge is reported but never banded; with no similarity/same_as
    # the cascade must fall through to the nearest-miss branch.
    nodes_a = [_node("a1", "docs/a.md", BASE)]
    nodes_b = [_node("b1", "docs/b.md", vec(0.40))]
    verdict, nm = classify_verdict([_cross("references", 1.0)], nodes_a, nodes_b, THRESHOLDS)
    assert verdict == "unrelated"
    assert nm["cosine"] == pytest.approx(0.40, abs=1e-6)


def test_weak_at_weak_floor():
    nodes_a = [_node("a1", "docs/a.md", BASE)]
    nodes_b = [_node("b1", "docs/b.md", vec(0.55))]
    verdict, nm = classify_verdict([], nodes_a, nodes_b, THRESHOLDS)
    assert verdict == "weak"
    assert nm["cosine"] == pytest.approx(0.55, abs=1e-6)


def test_weak_can_carry_above_tau_nearest_miss():
    # DOCUMENTING (not a bug): the cascade reaches the matmul branch only when NO
    # cross-file similarity edge exists. A pair can clear tau (>=0.70) yet fail the
    # union-top-K cut over all nodes, so it has no stored edge. nearest_miss is the
    # best cross pair (not the best strictly-sub-tau pair), so a "weak" verdict can
    # carry an above-tau nearest_miss. P5-D4 band tuning (T6) decides whether the
    # weak band should additionally gate on < tau_floor. Pinned here so T6 does not
    # misread the behavior as a regression.
    nodes_a = [_node("a1", "docs/a.md", BASE)]
    nodes_b = [_node("b1", "docs/b.md", vec(0.72))]
    verdict, nm = classify_verdict([], nodes_a, nodes_b, THRESHOLDS)
    assert verdict == "weak"
    assert nm["cosine"] == pytest.approx(0.72, abs=1e-6)
    assert nm["cosine"] > THRESHOLDS["tau_floor"]


def test_unrelated_just_below_weak_floor():
    nodes_a = [_node("a1", "docs/a.md", BASE)]
    nodes_b = [_node("b1", "docs/b.md", vec(0.5499))]
    verdict, nm = classify_verdict([], nodes_a, nodes_b, THRESHOLDS)
    assert verdict == "unrelated"
    assert nm is not None


# --- build_relation orchestrator (structured dict, no summary) ----------------

def _fresh_nodes():
    return [
        _node("a1", "docs/a.md", BASE, coarse=1, fine=10, group="docs-research"),
        _node("b1", "docs/b.md", vec(0.95), coarse=1, fine=10, group="docs-ideas"),
    ]


def test_build_relation_positive_case_strong():
    nodes = _fresh_nodes()
    edges = [{"src_id": "a1", "dst_id": "b1", "edge_kind": "similarity", "weight": 0.95, "directed": False}]
    result = build_relation("docs/a.md", "docs/b.md", nodes, edges, THRESHOLDS)

    assert result["inputs"] == {"file_a": "docs/a.md", "file_b": "docs/b.md", "nodes_a": 1, "nodes_b": 1}
    assert result["verdict"] == "strong"
    assert result["edge_stats"]["similarity"] == 1
    assert result["nearest_miss"] is None
    assert result["thresholds"]["tau_floor"] == pytest.approx(0.70)
    assert len(result["top_edges"]) == 1
    # community overlap present at both resolutions
    assert result["community_overlap"]["coarse"]["shared"] == [1]
    # summary is a T4 concern — the seam leaves it out of the structured dict
    assert "summary" not in result


def test_build_relation_negative_case_first_class_shape():
    nodes = [
        _node("a1", "docs/a.md", BASE, coarse=1, fine=10),
        _node("b1", "docs/b.md", vec(0.40), coarse=5, fine=50),
    ]
    result = build_relation("docs/a.md", "docs/b.md", nodes, [], THRESHOLDS)
    assert result["verdict"] == "unrelated"
    # negative case is a first-class shape: zeros, disjoint communities, populated nearest_miss
    assert result["edge_stats"]["similarity"] == 0
    assert result["edge_stats"]["max_weight"] == 0.0
    assert result["community_overlap"]["coarse"]["jaccard"] == 0.0
    assert result["nearest_miss"]["cosine"] == pytest.approx(0.40, abs=1e-6)
    assert result["top_edges"] == []


def test_build_relation_aborts_on_stale_communities():
    nodes = [
        _node("a1", "docs/a.md", BASE, coarse=None, fine=None),
        _node("b1", "docs/b.md", vec(0.4)),
    ]
    with pytest.raises(StaleCommunitiesError):
        build_relation("docs/a.md", "docs/b.md", nodes, [], THRESHOLDS)


def test_build_relation_unknown_file_raises():
    nodes = _fresh_nodes()
    with pytest.raises(UnknownFileError):
        build_relation("docs/missing.md", "docs/b.md", nodes, [], THRESHOLDS)
