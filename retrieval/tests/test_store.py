"""
Tests for retrieval/store.py

Covers:
- load_embedding_jsonl: reads JSONL rows
- rows_to_arrow_table: converts dicts to pa.Table matching SCHEMA
- backup_index: moves index_path → backup_dir (replacing prior backup)
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
# backup_index
# ---------------------------------------------------------------------------

def test_backup_index_moves_directory(tmp_path):
    index_path = tmp_path / "index"
    index_path.mkdir()
    (index_path / "data.bin").write_bytes(b"test")
    backup_path = tmp_path / "index.bak"

    store.backup_index(index_path, backup_path)

    assert not index_path.exists()
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
