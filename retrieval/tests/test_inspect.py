"""
Tests for retrieval/inspect.py

Covers:
- --list mode: prints topic_name and file_path for every row
- --stats mode: row count, unique file count, embed_model breakdown, extractor_model breakdown
- --query mode: embeds query via ModelClient, calls ANN search, prints ranked results with truncated description
- --relate mode: cross-file cosine pairs, top-N sorted, divergences for best-match < 0.5
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

RETRIEVAL_DIR = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("retrieval_inspect", RETRIEVAL_DIR / "inspect.py")
retrieval_inspect = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(retrieval_inspect)
sys.modules["retrieval_inspect"] = retrieval_inspect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_row(file_path, topic_name, description="A desc.", vector=None,
             embed_model="bge-m3", extractor_model="qwen3:14b"):
    return {
        "id": f"{file_path}:{topic_name}",
        "file_path": file_path,
        "topic_name": topic_name,
        "description": description,
        "spans": "[]",
        "vector": vector if vector is not None else [1.0] + [0.0] * 1023,
        "embed_model": embed_model,
        "embed_dim": 1024,
        "embed_mode": "description",
        "embedding_timestamp": "2026-01-01T00:00:00+00:00",
        "extractor_model": extractor_model,
        "extraction_run_id": "run-001",
        "extraction_timestamp": "2026-01-01T00:00:00+00:00",
        "file_role": "long_research_doc",
        "node_kind": "extracted",
        "scope_tags": "[]",
        "segment_id": None,
        "segment_range": None,
    }


def make_mock_table(rows):
    mock = MagicMock()
    mock.count_rows.return_value = len(rows)
    mock.to_arrow.return_value.column.side_effect = lambda f: _column_list(rows, f)
    mock.search.return_value.limit.return_value.to_list.return_value = [
        {**r, "_distance": 0.1} for r in rows
    ]
    return mock


def _column_list(rows, field):
    col = MagicMock()
    col.to_pylist.return_value = [r[field] for r in rows]
    return col


def run_cli(argv_list, mock_table, capsys):
    original = sys.argv
    sys.argv = ["inspect"] + argv_list
    mock_db = MagicMock()
    mock_db.open_table.return_value = mock_table
    with patch("lancedb.connect", return_value=mock_db):
        retrieval_inspect.main()
    sys.argv = original
    return capsys.readouterr().out


# ---------------------------------------------------------------------------
# --list mode

def test_list_prints_topic_names(capsys):
    rows = [make_row("file1.txt", "topic1"), make_row("file2.txt", "topic2")]
    mock_table = make_mock_table(rows)
    out = run_cli(["--list"], mock_table, capsys)
    assert "topic1" in out
    assert "topic2" in out


def test_list_prints_file_paths(capsys):
    rows = [make_row("file1.txt", "topic1"), make_row("file2.txt", "topic2")]
    mock_table = make_mock_table(rows)
    out = run_cli(["--list"], mock_table, capsys)
    assert "file1.txt" in out
    assert "file2.txt" in out


def test_list_empty_table_produces_no_topic_output(capsys):
    mock_table = make_mock_table([])
    out = run_cli(["--list"], mock_table, capsys)
    assert out.strip() == ""


# --stats mode

def test_stats_total_row_count(capsys):
    rows = [make_row("file1.txt", "topic1"), make_row("file2.txt", "topic2")]
    mock_table = make_mock_table(rows)
    out = run_cli(["--stats"], mock_table, capsys)
    assert "2" in out


def test_stats_embed_model_breakdown(capsys):
    rows = [
        make_row("f1.txt", "t1", embed_model="bge-m3"),
        make_row("f2.txt", "t2", embed_model="bge-m3"),
        make_row("f3.txt", "t3", embed_model="bge-m3"),
    ]
    mock_table = make_mock_table(rows)
    out = run_cli(["--stats"], mock_table, capsys)
    assert "bge-m3 (3)" in out


def test_stats_extractor_model_breakdown(capsys):
    rows = [
        make_row("f1.txt", "t1", extractor_model="qwen3:14b"),
        make_row("f2.txt", "t2", extractor_model="qwen3:14b"),
    ]
    mock_table = make_mock_table(rows)
    out = run_cli(["--stats"], mock_table, capsys)
    assert "qwen3:14b (2)" in out


def test_stats_unique_file_count(capsys):
    rows = [make_row("file1.txt", "topic1"), make_row("file1.txt", "topic2")]
    mock_table = make_mock_table(rows)
    out = run_cli(["--stats"], mock_table, capsys)
    assert "1" in out


# --query mode

def test_query_calls_embed_texts_with_query(capsys):
    rows = [make_row("file1.txt", "topic1")]
    mock_table = make_mock_table(rows)
    with patch("retrieval_inspect.ModelClient") as mock_client:
        mock_client.return_value.embed_texts.return_value = [[0.1] * 1024]
        run_cli(["--query", "test query"], mock_table, capsys)
        mock_client.return_value.embed_texts.assert_called_once_with(
            ["test query"], role="embedding"
        )


def test_query_calls_search_with_embedded_vector(capsys):
    rows = [make_row("file1.txt", "topic1")]
    mock_table = make_mock_table(rows)
    with patch("retrieval_inspect.ModelClient") as mock_client:
        mock_client.return_value.embed_texts.return_value = [[0.1] * 1024]
        run_cli(["--query", "test query"], mock_table, capsys)
        mock_table.search.assert_called_once_with([0.1] * 1024)


def test_query_prints_topic_name_and_file_path(capsys):
    rows = [make_row("file1.txt", "topic1")]
    mock_table = make_mock_table(rows)
    with patch("retrieval_inspect.ModelClient") as mock_client:
        mock_client.return_value.embed_texts.return_value = [[0.1] * 1024]
        out = run_cli(["--query", "test query"], mock_table, capsys)
    assert "topic1" in out
    assert "file1.txt" in out


def test_query_truncates_description_at_120_chars(capsys):
    long_desc = "x" * 200
    rows = [make_row("file1.txt", "topic1", description=long_desc)]
    mock_table = make_mock_table(rows)
    with patch("retrieval_inspect.ModelClient") as mock_client:
        mock_client.return_value.embed_texts.return_value = [[0.1] * 1024]
        out = run_cli(["--query", "test query"], mock_table, capsys)
    assert "x" * 200 not in out
    assert "x" * 120 in out


# --relate mode

def test_relate_prints_top_pairs(capsys):
    rows_a = [make_row("file-a.txt", "topicA"), make_row("file-a.txt", "topicB")]
    rows_b = [make_row("file-b.txt", "topicX")]
    mock_table = make_mock_table(rows_a + rows_b)
    out = run_cli(["--relate", "--file-a", "file-a.txt", "--file-b", "file-b.txt"], mock_table, capsys)
    assert "topicA" in out or "topicB" in out
    assert "topicX" in out


def test_relate_ignores_rows_from_other_files(capsys):
    rows = [
        make_row("file-a.txt", "topicA"),
        make_row("file-b.txt", "topicX"),
        make_row("file-c.txt", "topicY"),
    ]
    mock_table = make_mock_table(rows)
    out = run_cli(["--relate", "--file-a", "file-a.txt", "--file-b", "file-b.txt"], mock_table, capsys)
    assert "topicY" not in out


def test_relate_prints_divergences(capsys):
    vec_orthogonal = [0.0] * 512 + [1.0] + [0.0] * 511
    vec_normal = [1.0] + [0.0] * 1023
    rows = [
        make_row("file-a.txt", "topicA", vector=vec_orthogonal),
        make_row("file-b.txt", "topicX", vector=vec_normal),
        make_row("file-b.txt", "topicY", vector=vec_normal),
    ]
    mock_table = make_mock_table(rows)
    out = run_cli(["--relate", "--file-a", "file-a.txt", "--file-b", "file-b.txt"], mock_table, capsys)
    assert "topicA" in out
    assert "diverge" in out.lower()
# ---------------------------------------------------------------------------
