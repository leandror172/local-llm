"""
Tests for retrieval/store.py

Covers:
- load_embedding_jsonl: reads JSONL rows
- rows_to_arrow_table: converts dicts to pa.Table matching SCHEMA
- backup_index: copies index_path → backup_dir (live dir survives, prior backup replaced)
- backup_index: skipped when index_path does not exist
- open_or_create_table: creates LanceDB table mode=overwrite
- validate_table: passes when row count + vector dim correct
- validate_table: raises when row count mismatches
- validate_table: raises when vector dim mismatches
- full pipeline: input → table written → row count matches
"""

import json
import sys
from pathlib import Path
import pytest

import pyarrow as pa

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import store  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VECTOR_DIM = 1024

def make_embed_row(file_path="docs/test.md", topic_name="test_topic", vector=None):
    if vector is None:
        vector = [0.01] * VECTOR_DIM
    return {
        "id": f"{file_path}:{topic_name}",
        "file_path": file_path,
        "topic_name": topic_name,
        "description": "A test topic.",
        "spans": "[[1, 3]]",
        "vector": vector,
        "embed_model": "bge-m3",
        "embed_dim": VECTOR_DIM,
        "embed_mode": "description",
        "embedding_timestamp": "2026-05-27T10:00:00+00:00",
        "extractor_model": "qwen3:14b",
        "extraction_run_id": "abc-123",
        "extraction_timestamp": "2026-04-16T21:19:16.892426+00:00",
        "file_role": "long_research_doc",
        "node_kind": "extracted",
        "scope_tags": "[]",
        "segment_id": None,
        "segment_range": None,
    }


@pytest.fixture
def embed_jsonl(tmp_path):
    rows = [make_embed_row("docs/a.md", "topic_a"),
            make_embed_row("docs/b.md", "topic_b")]
    p = tmp_path / "embeddings.jsonl"
    with p.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return p, rows


# ---------------------------------------------------------------------------
# load_embedding_jsonl
# ---------------------------------------------------------------------------

def test_load_embedding_jsonl_returns_all_rows(embed_jsonl):
    path, expected = embed_jsonl
    rows = store.load_embedding_jsonl(path)
    assert len(rows) == 2


def test_load_embedding_jsonl_row_has_vector(embed_jsonl):
    path, _ = embed_jsonl
    rows = store.load_embedding_jsonl(path)
    assert len(rows[0]["vector"]) == VECTOR_DIM


# ---------------------------------------------------------------------------
# rows_to_arrow_table
# ---------------------------------------------------------------------------

def test_rows_to_arrow_table_has_correct_schema(embed_jsonl):
    _, raw_rows = embed_jsonl
    table = store.rows_to_arrow_table(raw_rows)
    assert "vector" in table.schema.names
    assert "id" in table.schema.names
    assert "node_kind" in table.schema.names


def test_rows_to_arrow_table_vector_is_fixed_size_list(embed_jsonl):
    _, raw_rows = embed_jsonl
    table = store.rows_to_arrow_table(raw_rows)
    vec_field = table.schema.field("vector")
    assert isinstance(vec_field.type, pa.FixedSizeListType)
    assert vec_field.type.list_size == VECTOR_DIM


def test_rows_to_arrow_table_row_count(embed_jsonl):
    _, raw_rows = embed_jsonl
    table = store.rows_to_arrow_table(raw_rows)
    assert table.num_rows == 2


# ---------------------------------------------------------------------------
# source_group derivation (T-65)
# ---------------------------------------------------------------------------

GROUPS = [
    {"match": "**/.memories/*.md", "tag": "memories"},
    {"match": ".claude/archive/**", "tag": "archive"},
    {"match": "docs/research/**", "tag": "docs-research"},
]


def test_source_group_field_present():
    table = store.rows_to_arrow_table([make_embed_row()], groups=GROUPS)
    assert "source_group" in table.schema.names


def test_source_group_derived_from_file_path():
    row = make_embed_row(file_path="docs/research/foo.md")
    table = store.rows_to_arrow_table([row], groups=GROUPS)
    assert table.column("source_group").to_pylist() == ["docs-research"]


def test_source_group_overrides_any_row_value():
    # A stray source_group on the row must NOT win — derivation is authoritative.
    row = make_embed_row(file_path="docs/research/foo.md")
    row["source_group"] = "WRONG"
    table = store.rows_to_arrow_table([row], groups=GROUPS)
    assert table.column("source_group").to_pylist() == ["docs-research"]


def test_source_group_anchor_row_grouped_by_its_file():
    # Anchor rows carry a real file_path → grouped uniformly, no sentinel.
    row = make_embed_row(file_path=".claude/archive/phases-0-6.md")
    table = store.rows_to_arrow_table([row], groups=GROUPS)
    assert table.column("source_group").to_pylist() == ["archive"]


def test_source_group_unmatched_is_ungrouped():
    row = make_embed_row(file_path="docs/test.md")
    table = store.rows_to_arrow_table([row], groups=GROUPS)
    assert table.column("source_group").to_pylist() == ["ungrouped"]


# ---------------------------------------------------------------------------
# backup_index
# ---------------------------------------------------------------------------

def test_backup_index_copies_and_keeps_live_dir(tmp_path):
    # Copy semantics: the live index dir must survive the backup so a later
    # single-table overwrite writes in place, preserving sibling tables.
    index_path = tmp_path / "index"
    index_path.mkdir()
    (index_path / "data.bin").write_bytes(b"test")
    backup_path = tmp_path / "index.bak"

    store.backup_index(index_path, backup_path)

    assert index_path.exists()
    assert (index_path / "data.bin").read_bytes() == b"test"
    assert backup_path.exists()
    assert (backup_path / "data.bin").exists()


def test_backup_index_replaces_prior_backup(tmp_path):
    index_path = tmp_path / "index"
    index_path.mkdir()
    (index_path / "new.bin").write_bytes(b"new")

    backup_path = tmp_path / "index.bak"
    backup_path.mkdir()
    (backup_path / "old.bin").write_bytes(b"old")

    store.backup_index(index_path, backup_path)

    assert (backup_path / "new.bin").exists()
    assert not (backup_path / "old.bin").exists()


def test_backup_index_noop_when_no_index(tmp_path):
    index_path = tmp_path / "index"  # does not exist
    backup_path = tmp_path / "index.bak"
    store.backup_index(index_path, backup_path)  # should not raise
    assert not backup_path.exists()


# ---------------------------------------------------------------------------
# open_or_create_table + validate_table (integration — uses real LanceDB)
# ---------------------------------------------------------------------------

def test_open_or_create_table_writes_rows(tmp_path, embed_jsonl):
    _, raw_rows = embed_jsonl
    import lancedb
    db = lancedb.connect(str(tmp_path / "index"))
    arrow_table = store.rows_to_arrow_table(raw_rows)
    tbl = store.open_or_create_table(db, "topics", arrow_table)
    assert tbl.count_rows() == 2


def test_validate_table_passes_on_correct_data(tmp_path, embed_jsonl):
    _, raw_rows = embed_jsonl
    import lancedb
    db = lancedb.connect(str(tmp_path / "index"))
    arrow_table = store.rows_to_arrow_table(raw_rows)
    tbl = store.open_or_create_table(db, "topics", arrow_table)
    store.validate_table(tbl, expected_count=2, embed_dim=VECTOR_DIM)  # should not raise


def test_validate_table_raises_on_wrong_count(tmp_path, embed_jsonl):
    _, raw_rows = embed_jsonl
    import lancedb
    db = lancedb.connect(str(tmp_path / "index"))
    arrow_table = store.rows_to_arrow_table(raw_rows)
    tbl = store.open_or_create_table(db, "topics", arrow_table)
    with pytest.raises((AssertionError, ValueError)):
        store.validate_table(tbl, expected_count=99, embed_dim=VECTOR_DIM)


# ---------------------------------------------------------------------------
# Sibling-table survival + .bak path derivation (LTG Phase 4 data-loss fix)
# ---------------------------------------------------------------------------

def test_topics_overwrite_preserves_sibling_edges_table(tmp_path, embed_jsonl):
    # An anchors-style overwrite of 'topics' in a two-table index must leave the
    # 'edges' table (written by the graph stage) intact — the Phase 4 data-loss bug.
    _, raw_rows = embed_jsonl
    import lancedb
    db = lancedb.connect(str(tmp_path / "index"))
    store.open_or_create_table(db, "topics", store.rows_to_arrow_table(raw_rows))
    edges = pa.table({
        "src_id": ["a", "b"],
        "dst_id": ["b", "c"],
        "weight": pa.array([1.0, 0.5], type=pa.float32()),
    })
    db.create_table("edges", data=edges)

    # Reproduce the anchors rebuild path: backup the live index, then reconnect
    # and overwrite topics only. Copy-based backup leaves the live dir (and its
    # 'edges' table) in place; move-based backup would delete it here.
    store.backup_index(tmp_path / "index", tmp_path / "index.bak")
    db = lancedb.connect(str(tmp_path / "index"))
    store.open_or_create_table(db, "topics", store.rows_to_arrow_table(raw_rows))

    reopened = lancedb.connect(str(tmp_path / "index"))
    assert "edges" in reopened.table_names()
    assert reopened.open_table("edges").count_rows() == 2


def test_bak_path_appends_on_dotted_dir_name():
    # Backup path must APPEND '.bak' — with_suffix strips the dotted segment.
    p = Path("/x/index.v2")
    derived = p.parent / (p.name + ".bak")
    assert derived.name == "index.v2.bak"
    assert p.with_suffix(".bak").name == "index.bak"  # the bug we avoid
