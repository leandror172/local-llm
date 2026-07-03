# /mnt/i/workspaces/llm/retrieval/tests/test_communities.py

import pytest
from pathlib import Path
import pyarrow as pa
import lancedb
import networkx as nx
from typing import List, Dict, Tuple

from communities import build_graph, leiden_assignments, write_communities
from store import build_schema


RESOLUTIONS = {"coarse": 0.5, "fine": 1.5}


def _make_topics_table(index_path: Path) -> None:
    table = pa.table({
        "id": ["a", "b", "x"],
        "payload": ["p1", "p2", "p3"],
        "community_coarse": pa.array([None, None, None], type=pa.int32()),
        "community_fine": pa.array([None, None, None], type=pa.int32())
    })
    db = lancedb.connect(str(index_path))
    db.create_table("topics", data=table)


def two_cluster_edges() -> List[Dict[str, str]]:
    return [
        {"src_id": "a", "dst_id": "b", "weight": 1.0},
        {"src_id": "b", "dst_id": "c", "weight": 1.0},
        {"src_id": "c", "dst_id": "a", "weight": 1.0},
        {"src_id": "d", "dst_id": "e", "weight": 1.0},
        {"src_id": "e", "dst_id": "f", "weight": 1.0},
        {"src_id": "f", "dst_id": "d", "weight": 1.0},
        {"src_id": "c", "dst_id": "d", "weight": 0.1},  # weak bridge
    ]


def test_schema_has_nullable_community_columns():
    schema = build_schema(8)
    assert "community_coarse" in schema.names
    assert "community_fine" in schema.names
    assert schema.field("community_coarse").type == pa.int32() and schema.field("community_coarse").nullable is True
    assert schema.field("community_fine").type == pa.int32() and schema.field("community_fine").nullable is True


def test_build_graph_nodes_edges_and_max_weight():
    ids = ["a", "b", "c", "d", "e", "f", "g"]
    edge_rows = [
        {"src_id": "a", "dst_id": "b", "weight": 1.0},
        {"src_id": "b", "dst_id": "c", "weight": 1.0},
        {"src_id": "c", "dst_id": "a", "weight": 1.0},
        {"src_id": "a", "dst_id": "b", "weight": 0.5},  # duplicate with lower weight
    ]
    graph = build_graph(ids, edge_rows)

    assert len(graph.nodes) == 7
    assert len(graph.edges) == 3  # only unique edges with max weights

    for u, v in [("a", "b"), ("b", "c"), ("c", "a")]:
        assert graph[u][v]["weight"] == 1.0


def test_two_clusters_detected_at_coarse():
    ids = ["a", "b", "c", "d", "e", "f"]
    edge_rows = two_cluster_edges()
    graph = build_graph(ids, edge_rows)
    assignments = leiden_assignments(graph, RESOLUTIONS, seed=42)

    assert assignments["a"][0] == assignments["b"][0] == assignments["c"][0]
    assert assignments["d"][0] == assignments["e"][0] == assignments["f"][0]
    assert assignments["a"][0] != assignments["d"][0]


def test_isolated_node_gets_singleton_assignment():
    ids = ["a", "b", "c", "d", "e", "f", "g"]
    edge_rows = two_cluster_edges()
    graph = build_graph(ids, edge_rows)
    assignments = leiden_assignments(graph, RESOLUTIONS, seed=42)

    assert assignments["g"][0] != assignments["a"][0]
    assert assignments["g"][0] != assignments["d"][0]


def test_deterministic_with_seed():
    ids = ["a", "b", "c", "d", "e", "f"]
    edge_rows = two_cluster_edges()
    graph1 = build_graph(ids, edge_rows)
    assignments1 = leiden_assignments(graph1, RESOLUTIONS, seed=42)

    graph2 = build_graph(ids, edge_rows)
    assignments2 = leiden_assignments(graph2, RESOLUTIONS, seed=42)

    assert assignments1 == assignments2


def test_write_communities_roundtrip(tmp_path: Path):
    index_path = tmp_path / "index"
    _make_topics_table(index_path)

    assignments = {"a": (0, 1), "b": (0, 2)}
    write_communities(index_path, assignments, backup=False)

    db = lancedb.connect(str(index_path))
    reopened_table = db.open_table("topics").to_arrow()

    assert reopened_table.column("community_coarse").to_pylist() == [0, 0, None]
    assert reopened_table.column("community_fine").to_pylist() == [1, 2, None]
    assert reopened_table.column("payload").to_pylist() == ["p1", "p2", "p3"]


def test_write_communities_backup_creates_bak(tmp_path: Path):
    index_path = tmp_path / "index"
    _make_topics_table(index_path)

    assignments = {"a": (0, 1), "b": (0, 2)}
    write_communities(index_path, assignments, backup=True)

    # T-71: ad-hoc communities runs use a stage-suffixed slot, not the shared .bak
    assert (index_path.parent / (index_path.name + ".bak-communities")).exists()
