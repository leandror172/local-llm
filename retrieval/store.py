"""
Module for storing embedding data in a LanceDB table.

Functions:
- load_embedding_jsonl: reads JSONL rows from a file.
- rows_to_arrow_table: converts dicts to pa.Table matching SCHEMA.
- backup_index: moves index_path → backup_dir (replacing prior backup).
- open_or_create_table: creates or opens a LanceDB table.
- validate_table: validates the table's row count and vector dimension.
- main: CLI entry point for storing embeddings in LanceDB.

Usage:
    python store.py --input retrieval/embeddings.jsonl \\
                   --index retrieval/index \\
                   --table topics \\
                   --backup-dir retrieval/index.bak \\
                   --no-backup \\
                   --log-dir retrieval/runs/
"""

#!/usr/bin/env python3
"""
Phase 2 store script — reads embedding JSONL, creates/overwrites LanceDB table.

Usage:
    retrieval/run-store.sh --input retrieval/embeddings.jsonl --index retrieval/index
"""

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pyarrow as pa
import lancedb

REPO_ROOT = Path(__file__).parent.parent
SCHEMA = pa.schema([
    pa.field("id",                   pa.string()),
    pa.field("file_path",            pa.string()),
    pa.field("topic_name",           pa.string()),
    pa.field("description",          pa.string()),
    pa.field("spans",                pa.string()),
    pa.field("vector",               pa.list_(pa.float32(), 1024)),
    pa.field("embed_model",          pa.string()),
    pa.field("embed_dim",            pa.int32()),
    pa.field("embed_mode",           pa.string()),
    pa.field("embedding_timestamp",  pa.string()),
    pa.field("extractor_model",      pa.string()),
    pa.field("extraction_run_id",    pa.string()),
    pa.field("extraction_timestamp", pa.string()),
    pa.field("file_role",            pa.string()),
    pa.field("node_kind",            pa.string()),
    pa.field("scope_tags",           pa.string()),
    pa.field("segment_id",           pa.string(), nullable=True),
    pa.field("segment_range",        pa.string(), nullable=True),
])

RUNS_DIR = Path(__file__).parent / "runs"


def load_embedding_jsonl(path: Path) -> List[Dict]:
    """Reads a JSONL file and returns a list of dicts."""
    rows = []
    with path.open("r") as f:
        for line in f:
            row = json.loads(line)
            rows.append(row)
    return rows

def rows_to_arrow_table(rows: List[Dict]) -> pa.Table:
    """Converts embedding dicts to a PyArrow Table matching SCHEMA."""
    vectors = pa.array(
        [pa.array(r["vector"], type=pa.float32()) for r in rows],
        type=pa.list_(pa.float32(), 1024),
    )
    scalar_fields = [f.name for f in SCHEMA if f.name != "vector"]
    col_data = {name: [r.get(name) for r in rows] for name in scalar_fields}
    col_data["vector"] = vectors
    return pa.table(col_data, schema=SCHEMA)

def backup_index(index_path: Path, backup_path: Path) -> None:
    """Backups the index directory."""
    if index_path.exists():
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.move(str(index_path), str(backup_path))

def open_or_create_table(db, table_name: str, arrow_table: pa.Table):
    """Opens or creates a LanceDB table."""
    return db.create_table(table_name, data=arrow_table, mode="overwrite")

def validate_table(table, expected_count: int, embed_dim: int) -> None:
    """Validates the table's row count and vector dimension."""
    assert table.count_rows() == expected_count, f"Row count mismatch: {table.count_rows()} != {expected_count}"
    first_vector = table.to_arrow().column("vector").to_pylist()[0]
    assert len(first_vector) == embed_dim, f"Vector dimension mismatch: {len(first_vector)} != {embed_dim}"

def write_run_log(log_dir: Path, input_path: Path, table_path: Path):
    """Writes a run log to the specified directory."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"store-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.jsonl"
    
    with log_file.open("w") as f:
        for row in load_embedding_jsonl(input_path):
            file_path = row["file_path"]
            node_kind = row["node_kind"]
            f.write(json.dumps({"file_path": file_path, "node_kind": node_kind}) + "\n")
        
        summary_row = {
            "event": "summary",
            "n_rows": table_path.stat().st_size,
            "table_path": str(table_path),
            "table_bytes": os.path.getsize(str(table_path))
        }
        f.write(json.dumps(summary_row) + "\n")

def main():
    """CLI entry point for storing embeddings in LanceDB."""
    parser = argparse.ArgumentParser(description="Store embeddings in LanceDB.")
    parser.add_argument("--input", type=Path, required=True, help="Path to embedding JSONL")
    parser.add_argument("--index", type=Path, required=True, help="Path for LanceDB directory")
    parser.add_argument("--table", default="topics", help="Table name (default: topics)")
    parser.add_argument("--backup-dir", type=Path, default=None, help="Backup directory (default: {index}.bak)")
    parser.add_argument("--no-backup", action="store_true", help="Do not perform backup")
    parser.add_argument("--log-dir", type=Path, default=RUNS_DIR)
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file {args.input} does not exist.")
        return
    
    if not args.no_backup:
        backup_dir = args.backup_dir or args.index.with_suffix(".bak")
        backup_index(args.index, backup_dir)
    
    db = lancedb.connect(str(args.index))
    rows = load_embedding_jsonl(args.input)
    arrow_table = rows_to_arrow_table(rows)
    table = open_or_create_table(db, args.table, arrow_table)
    validate_table(table, expected_count=len(rows), embed_dim=1024)
    
    write_run_log(args.log_dir, args.input, args.index)
    logger.info(f"{len(rows)} rows written to {args.index}.")

if __name__ == "__main__":
    main()
