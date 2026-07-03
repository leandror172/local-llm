# /mnt/i/workspaces/llm/retrieval/tests/test_graph_store.py

import pytest
from pathlib import Path
import pyarrow as pa
import lancedb
from typing import List

from graph import Edge, EDGES_SCHEMA, build_all_edges, edges_to_arrow_table, write_edges_table


def sample_edges() -> List[Edge]:
    return [
        Edge(src_id="node1", dst_id="node2", edge_kind="similarity", weight=0.87, directed=False),
        Edge(src_id="node3", dst_id="node4", edge_kind="same_as", weight=1.0, directed=False),
        Edge(src_id="node5", dst_id="node6", edge_kind="references", weight=1.0, directed=True),
    ]


def test_edges_schema_field_names_and_types():
    assert [f.name for f in EDGES_SCHEMA] == ["src_id", "dst_id", "edge_kind", "weight", "directed", "created_at", "run_id"]
    assert EDGES_SCHEMA.field("weight").type == pa.float32()
    assert EDGES_SCHEMA.field("directed").type == pa.bool_()


def test_edges_to_arrow_table_roundtrip():
    edges = sample_edges()
    run_id = "run-1"
    created_at = "2026-07-02T00:00:00+00:00"
    table = edges_to_arrow_table(edges, run_id=run_id, created_at=created_at)

    assert table.num_rows == 3
    assert table.schema == EDGES_SCHEMA

    src_ids = table.column("src_id").to_pylist()
    assert src_ids == [edge.src_id for edge in edges]

    run_ids = table.column("run_id").to_pylist()
    assert all(r == run_id for r in run_ids)

    created_ats = table.column("created_at").to_pylist()
    assert all(c == created_at for c in created_ats)

    weights = table.column("weight").to_pylist()
    assert weights[0] == pytest.approx(0.87)


def test_write_edges_table_roundtrip(tmp_path):
    edges = sample_edges()
    run_id = "run-1"
    created_at = "2026-07-02T00:00:00+00:00"
    table = edges_to_arrow_table(edges, run_id=run_id, created_at=created_at)
    index_path = tmp_path / "index"

    write_edges_table(index_path, table)

    db = lancedb.connect(str(index_path))
    reopened_table = db.open_table("edges").to_arrow()

    assert reopened_table.num_rows == 3
    src_ids = reopened_table.column("src_id").to_pylist()
    assert src_ids == [edge.src_id for edge in edges]


def test_build_all_edges_reads_from_named_table(tmp_path):
    """build_all_edges must honor a non-default table name end-to-end
    (load_nodes + load_alias_rows), not hard-code 'topics'."""
    index_path = tmp_path / "index"
    db = lancedb.connect(str(index_path))

    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("source_group", pa.string()),
        pa.field("vector", pa.list_(pa.float32())),
        pa.field("alias_of", pa.string()),
    ])
    table = pa.table({
        "id": ["node1", "node2"],
        "source_group": ["archive", "archive"],
        "vector": [[1.0, 0.0], [0.9, 0.1]],
        "alias_of": [None, None],
    }, schema=schema)
    db.create_table("custom_nodes", data=table, mode="overwrite")

    config = {"tau_floor": 0.0, "top_k": 5}
    repo_root = tmp_path  # not a git repo => ingest_anchors returns [] harmlessly

    by_kind = build_all_edges(index_path, repo_root, config, table_name="custom_nodes")

    assert len(by_kind["similarity"]) == 1
    edge = by_kind["similarity"][0]
    assert {edge.src_id, edge.dst_id} == {"node1", "node2"}


def test_write_edges_table_overwrites(tmp_path):
    edges1 = sample_edges()
    run_id = "run-1"
    created_at = "2026-07-02T00:00:00+00:00"
    table1 = edges_to_arrow_table(edges1, run_id=run_id, created_at=created_at)
    index_path = tmp_path / "index"

    write_edges_table(index_path, table1)

    edges2 = [edges1[0]]
    table2 = edges_to_arrow_table(edges2, run_id=run_id, created_at=created_at)
    write_edges_table(index_path, table2)

    db = lancedb.connect(str(index_path))
    reopened_table = db.open_table("edges").to_arrow()

    assert reopened_table.num_rows == 1
