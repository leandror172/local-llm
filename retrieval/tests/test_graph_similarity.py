"""
Tests for retrieval/graph.py

Covers:
- Edge: a NamedTuple with fields: src_id (str), dst_id (str), edge_kind (str), weight (float), directed (bool).
- similarity_edges(ids: list[str], vectors, tau_floor: float, top_k: int) -> list[Edge]
"""

import warnings

import pytest
import numpy as np
import math
from graph import Edge, similarity_edges

def make_vectors(angles_deg):
    angles_rad = [math.radians(a) for a in angles_deg]
    return np.array([[math.cos(a), math.sin(a)] for a in angles_rad])

def test_floor_excludes_low_similarity_pairs():
    ids = ["a", "b", "c"]
    vectors = make_vectors([0, 10, 20])
    tau_floor = 0.95
    top_k = 10
    edges = similarity_edges(ids, vectors, tau_floor, top_k)
    expected_edges = [Edge(src_id="a", dst_id="b", edge_kind="similarity", weight=pytest.approx(0.984807753012208), directed=False),
                      Edge(src_id="b", dst_id="c", edge_kind="similarity", weight=pytest.approx(0.984807753012208), directed=False)]
    assert edges == expected_edges

def test_union_top_k_keeps_edge_if_in_either_endpoints_top_k():
    ids = ["a", "b", "c"]
    vectors = make_vectors([0, 10, 18])
    tau_floor = 0.0
    top_k = 1
    edges = similarity_edges(ids, vectors, tau_floor, top_k)
    expected_edges = [Edge(src_id="a", dst_id="b", edge_kind="similarity", weight=pytest.approx(math.cos(math.radians(10))), directed=False),
                      Edge(src_id="b", dst_id="c", edge_kind="similarity", weight=pytest.approx(math.cos(math.radians(8))), directed=False)]
    assert edges == expected_edges

def test_no_self_edges():
    ids = ["a", "b", "c"]
    vectors = make_vectors([0, 10, 20])
    tau_floor = 0.0
    top_k = 10
    edges = similarity_edges(ids, vectors, tau_floor, top_k)
    for edge in edges:
        assert edge.src_id != edge.dst_id

def test_canonical_ordering_and_sorted_output():
    ids = ["c", "a", "b"]
    vectors = make_vectors([0, 5, 10])
    tau_floor = 0.0
    top_k = 10
    edges = similarity_edges(ids, vectors, tau_floor, top_k)
    sorted_edges = sorted(edges, key=lambda e: (e.src_id, e.dst_id))
    assert edges == sorted_edges
    for edge in edges:
        assert edge.src_id < edge.dst_id

def test_edge_fields_and_weight_value():
    ids = ["x", "y"]
    vectors = make_vectors([0, 60])
    tau_floor = 0.0
    top_k = 5
    edges = similarity_edges(ids, vectors, tau_floor, top_k)
    expected_edge = Edge(src_id="x", dst_id="y", edge_kind="similarity", weight=pytest.approx(0.5), directed=False)
    assert edges == [expected_edge]

def test_zero_vector_row_is_isolated_without_nan_or_warning():
    ids = ["a", "b", "zero"]
    vectors = np.array([
        [math.cos(math.radians(0)), math.sin(math.radians(0))],
        [math.cos(math.radians(10)), math.sin(math.radians(10))],
        [0.0, 0.0],
    ])
    tau_floor = 0.5  # zero vector's cosine similarity to anything is 0.0, below floor
    top_k = 10

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        edges = similarity_edges(ids, vectors, tau_floor, top_k)

    for edge in edges:
        assert not math.isnan(edge.weight)
        assert edge.src_id != "zero"
        assert edge.dst_id != "zero"

def test_non_normalized_input_is_normalized():
    ids = ["x", "y"]
    vectors = make_vectors([0, 60])
    vectors[0] *= 3.0
    vectors[1] *= 0.5
    tau_floor = 0.0
    top_k = 5
    edges = similarity_edges(ids, vectors, tau_floor, top_k)
    expected_edge = Edge(src_id="x", dst_id="y", edge_kind="similarity", weight=pytest.approx(0.5), directed=False)
    assert edges == [expected_edge]
