"""
Tests for retrieval/relate.py — T1 loaders + selectors.

Covers:
- Node: NamedTuple carried through relate().
- load_node_table / load_edges: thin LanceDB reads (minimal round-trip).
- load_manifest_paths / load_thresholds: yaml + config reads.
- nodes_for_file: file->node-set selection; unknown path -> UnknownFileError with nearest matches.
- assert_communities_fresh: P5-D7 staleness guard (null community col -> StaleCommunitiesError).
"""

import numpy as np
import pyarrow as pa
import lancedb
import pytest

from relate import (
    Node,
    UnknownFileError,
    StaleCommunitiesError,
    load_node_table,
    load_edges,
    load_manifest_paths,
    load_thresholds,
    nodes_for_file,
    assert_communities_fresh,
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


# --- nodes_for_file selection -------------------------------------------------

def test_nodes_for_file_selects_only_that_files_nodes():
    nodes = [
        _node("f1:a", "docs/a.md"),
        _node("f1:b", "docs/a.md"),
        _node("f2:a", "docs/b.md"),
    ]
    selected = nodes_for_file(nodes, "docs/a.md")
    assert {n.id for n in selected} == {"f1:a", "f1:b"}


def test_unknown_path_raises_with_nearest_matches():
    nodes = [_node("f1:a", "docs/research/smart-rag-dify.md")]
    manifest_paths = [
        "docs/research/smart-rag-dify.md",
        "docs/research/smart-rag-repowise.md",
    ]
    with pytest.raises(UnknownFileError) as exc:
        nodes_for_file(nodes, "docs/research/smart-rag-dfy.md", manifest_paths=manifest_paths)
    # the misspelling should surface the closest manifest path as a suggestion
    assert "smart-rag-dify.md" in str(exc.value)


def test_unknown_path_error_message_names_the_bad_path():
    nodes = [_node("f1:a", "docs/a.md")]
    with pytest.raises(UnknownFileError) as exc:
        nodes_for_file(nodes, "docs/nope.md")
    assert "docs/nope.md" in str(exc.value)


# --- staleness guard (P5-D7) --------------------------------------------------

def test_fresh_communities_pass():
    nodes = [_node("f1:a", "docs/a.md", coarse=3, fine=7)]
    assert_communities_fresh(nodes)  # no raise


def test_null_coarse_community_aborts():
    nodes = [_node("f1:a", "docs/a.md", coarse=None, fine=7)]
    with pytest.raises(StaleCommunitiesError):
        assert_communities_fresh(nodes)


def test_null_fine_community_aborts():
    nodes = [_node("f1:a", "docs/a.md", coarse=3, fine=None)]
    with pytest.raises(StaleCommunitiesError):
        assert_communities_fresh(nodes)


def test_staleness_message_names_the_remedy_scripts():
    nodes = [_node("f1:a", "docs/a.md", coarse=None, fine=None)]
    with pytest.raises(StaleCommunitiesError) as exc:
        assert_communities_fresh(nodes)
    msg = str(exc.value)
    assert "run-graph.sh" in msg
    assert "run-communities.sh" in msg
    assert "run-rebuild-all.sh" in msg


# --- LanceDB round-trip loaders (minimal tables, no live index) ---------------

def _write_minimal_nodes_table(index_path):
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("file_path", pa.string()),
        pa.field("node_kind", pa.string()),
        pa.field("source_group", pa.string()),
        pa.field("community_coarse", pa.int32(), nullable=True),
        pa.field("community_fine", pa.int32(), nullable=True),
        pa.field("vector", pa.list_(pa.float32(), 2)),
    ])
    table = pa.table({
        "id": ["f1:a", "ref:concept-x"],
        "file_path": ["docs/a.md", "docs/a.md"],
        "node_kind": ["extracted", "anchor"],
        "source_group": ["docs-research", "ungrouped"],
        "community_coarse": [1, 1],
        "community_fine": [2, 2],
        "vector": pa.array([[1.0, 0.0], [0.0, 1.0]], type=pa.list_(pa.float32(), 2)),
    }, schema=schema)
    db = lancedb.connect(str(index_path))
    db.create_table("topics", data=table, mode="overwrite")


def test_load_node_table_round_trip(tmp_path):
    index_path = tmp_path / "index"
    _write_minimal_nodes_table(index_path)
    nodes = load_node_table(index_path)
    by_id = {n.id: n for n in nodes}
    assert set(by_id) == {"f1:a", "ref:concept-x"}
    assert by_id["ref:concept-x"].node_kind == "anchor"
    assert by_id["f1:a"].community_coarse == 1
    assert list(by_id["f1:a"].vector) == pytest.approx([1.0, 0.0])


def test_load_edges_round_trip(tmp_path):
    index_path = tmp_path / "index"
    schema = pa.schema([
        pa.field("src_id", pa.string()),
        pa.field("dst_id", pa.string()),
        pa.field("edge_kind", pa.string()),
        pa.field("weight", pa.float32()),
        pa.field("directed", pa.bool_()),
    ])
    table = pa.table({
        "src_id": ["f1:a"],
        "dst_id": ["f2:b"],
        "edge_kind": ["similarity"],
        "weight": [0.8],
        "directed": [False],
    }, schema=schema)
    db = lancedb.connect(str(index_path))
    db.create_table("edges", data=table, mode="overwrite")

    edges = load_edges(index_path)
    assert len(edges) == 1
    assert edges[0]["src_id"] == "f1:a"
    assert edges[0]["dst_id"] == "f2:b"
    assert edges[0]["edge_kind"] == "similarity"
    assert edges[0]["weight"] == pytest.approx(0.8)


# --- config / manifest loaders ------------------------------------------------

def test_load_thresholds_reads_config_and_constants(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "graph:\n"
        "  tau_floor: 0.70\n"
        "  top_k: 10\n"
        "  resolutions:\n"
        "    coarse: 0.5\n"
        "    fine: 1.5\n"
        "  seed: 42\n"
    )
    thresholds = load_thresholds(config)
    assert thresholds["tau_floor"] == pytest.approx(0.70)
    assert thresholds["merge_cosine"] == pytest.approx(0.85)  # anchors.COSINE_THRESHOLD
    assert thresholds["weak_floor"] == pytest.approx(0.55)
    assert "bands" in thresholds


def test_load_manifest_paths(tmp_path):
    manifest = tmp_path / "corpus-manifest.yaml"
    manifest.write_text(
        "meta:\n  file_count: 2\n"
        "files:\n"
        "- path: docs/a.md\n  group: docs-research\n"
        "- path: docs/b.md\n  group: docs-ideas\n"
    )
    paths = load_manifest_paths(manifest)
    assert paths == ["docs/a.md", "docs/b.md"]
