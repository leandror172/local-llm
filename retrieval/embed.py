#!/usr/bin/env python3
"""
Phase 2 embedding script for the Latent Topic Graph pipeline.

Reads Phase 1 extraction JSONL, filters to winning extractor per file,
embeds topic descriptions (batched) via bge-m3, writes embedding JSONL.

Usage:
    retrieval/run-embed.sh --input retrieval/runs/20260416-181839.jsonl \\
                           --output retrieval/embeddings.jsonl
"""

# Sequential constraint: do not run alongside qwen3:14b or qwen2.5-coder:14b inference.
# bge-m3 (~700MB VRAM) + qwen3:14b (~9GB VRAM) co-fit, but a concurrent extraction +
# embedding pass on the 12GB GPU has been observed to thrash. See ref:ltg-vram-probe.
# In Phase 2's pipeline, embed.py runs after extraction is complete, so this is policy
# (don't manually launch extraction in another shell while embed.py runs), not a lock.

import argparse
import json
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from model_client import ModelClient, load_config

REPO_ROOT = Path(__file__).parent.parent
CONFIG_PATH = Path(__file__).parent / "config.yaml"
RUNS_DIR = Path(__file__).parent / "runs"

CODE_EXTENSIONS = {".py", ".go", ".ts", ".java"}
CODE_EXTRACTOR = "qwen2.5-coder:14b"
PROSE_EXTRACTOR = "qwen3:14b"

def winning_extractor(filepath: str) -> str:
    """Return the winning extractor model name for a given file path."""
    ext = Path(filepath).suffix.lower()
    return CODE_EXTRACTOR if ext in CODE_EXTENSIONS else PROSE_EXTRACTOR

def select_winning_row(rows: List[Dict], file_path: str) -> Optional[Dict]:
    """Select the winning row based on file path, model, and status."""
    expected_model = winning_extractor(file_path)
    for row in rows:
        if (row["file"] == file_path and
            row["model"] == expected_model and
            row["status"] == "ok"):
            return row
    return None

def slugify_snake(name: str) -> str:
    """Convert a name to snake_case with collision suffix handling."""
    # Lowercase, replace non-alphanumeric with underscores, collapse repeats, strip edges
    name = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def unique_slugs(names: List[str]) -> List[str]:
    """Return slugified names with -2/-3/... suffixes on collisions."""
    counts: Dict[str, int] = {}
    result = []
    for name in names:
        base = slugify_snake(name)
        if base not in counts:
            counts[base] = 1
            result.append(base)
        else:
            counts[base] += 1
            result.append(f"{base}-{counts[base]}")
    return result

def build_embed_text(topic: Dict, mode: str, file_path: Optional[str], repo_root) -> str:
    """Construct the embed text based on the specified mode."""
    description = topic.get("description", "")
    if mode == "description":
        return description
    elif mode == "description_plus_spans" and file_path:
        spans = topic.get("spans", [])
        try:
            with (repo_root / file_path).open('r') as f:
                lines = f.readlines()
            span_texts = [''.join(lines[start - 1:end]) for start, end in spans]
            return description + "\n\n" + '\n'.join(span_texts)
        except Exception:
            pass
    return description

def filter_valid_topics(topics: List[Dict]) -> List[Dict]:
    """Filter topics to include only those with non-empty descriptions."""
    return [topic for topic in topics if topic.get("description", "").strip()]

def build_output_row(row, topic, slug, vector, embed_model, embed_dim, embed_mode) -> Dict:
    """Build the output row dictionary with all required fields."""
    return {
        "id": f"{row['file']}:{slug}",
        "file_path": row["file"],
        "topic_name": topic["name"],
        "description": topic["description"],
        "spans": json.dumps(topic.get("spans", [])),
        "vector": vector,
        "embed_model": embed_model,
        "embed_dim": embed_dim,
        "embed_mode": embed_mode,
        "embedding_timestamp": datetime.now(timezone.utc).isoformat(),
        "extractor_model": row["model"],
        "extraction_run_id": row["run_id"],
        "extraction_timestamp": row["timestamp"],
        "file_role": row["file_role"],
        "node_kind": "extracted",
        "scope_tags": "[]",
        "segment_id": None,
        "segment_range": None,
    }


# ---------------------------------------------------------------------------
# Batch embed
# ---------------------------------------------------------------------------

def embed_batch(texts: List[str], model: str, url: str) -> List[List[float]]:
    response = httpx.post(
        f"{url}/api/embed",
        json={"model": model, "input": texts},
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()["embeddings"]


def embed_batch_with_retry(texts: List[str], model: str, url: str) -> List[List[float]]:
    try:
        return embed_batch(texts, model, url)
    except Exception:
        time.sleep(2.0)
        return embed_batch(texts, model, url)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def group_rows_by_file(rows: List[dict]) -> Dict[str, List[dict]]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["file"]].append(row)
    return grouped


def collect_embed_tuples(rows_by_file: Dict[str, List[dict]], embed_mode: str, repo_root: Path):
    for file_path, rows in rows_by_file.items():
        winning_row = select_winning_row(rows, file_path)
        if not winning_row:
            print(f"  WARNING: no winning row for {file_path}, skipping", file=sys.stderr)
            continue
        topics = filter_valid_topics(winning_row.get("parsed_topics") or [])
        if not topics:
            print(f"  WARNING: no valid topics for {file_path}, skipping", file=sys.stderr)
            continue
        slugs = unique_slugs([t["name"] for t in topics])
        for topic, slug in zip(topics, slugs):
            text = build_embed_text(topic, embed_mode, file_path, repo_root)
            yield (file_path, topic, slug, text, winning_row)


def validate_vectors(vectors: List[List[float]], embed_dim: int, batch_texts: List[str]) -> None:
    for i, vec in enumerate(vectors):
        if len(vec) != embed_dim:
            print(f"ERROR: vector {i} has dim {len(vec)}, expected {embed_dim}. "
                  f"Wrong model? Aborting.", file=sys.stderr)
            sys.exit(1)


def process_batches(all_tuples: List[tuple], batch_size: int, embed_model: str,
                    ollama_url: str, embed_dim: int, max_failures: int):
    failures = 0
    for i in range(0, len(all_tuples), batch_size):
        batch = all_tuples[i: i + batch_size]
        texts = [t[3] for t in batch]
        try:
            vectors = embed_batch_with_retry(texts, embed_model, ollama_url)
            validate_vectors(vectors, embed_dim, texts)
            for (file_path, topic, slug, _, row), vector in zip(batch, vectors):
                yield (file_path, topic, slug, vector, row)
        except Exception as exc:
            failures += 1
            print(f"  WARNING: batch embed failed ({exc}); failures={failures}", file=sys.stderr)
            if failures > max_failures:
                print("ERROR: max_failures exceeded. Aborting.", file=sys.stderr)
                sys.exit(1)


def write_output_jsonl(results: List[tuple], output_path: Path,
                       embed_model: str, embed_dim: int, embed_mode: str) -> List[dict]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with output_path.open("w", encoding="utf-8") as f:
        for file_path, topic, slug, vector, row in results:
            out = build_output_row(row, topic, slug, vector, embed_model, embed_dim, embed_mode)
            f.write(json.dumps(out) + "\n")
            rows.append(out)
    return rows


def write_run_log(log_dir: Path, output_rows: List[dict], elapsed_s: float) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    tag = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"embed-{tag}.jsonl"
    by_file: Dict[str, List[dict]] = defaultdict(list)
    for row in output_rows:
        by_file[row["file_path"]].append(row)
    with log_path.open("w", encoding="utf-8") as f:
        for fp, rows in by_file.items():
            f.write(json.dumps({"file": fp, "topics_emitted": len(rows)}) + "\n")
        f.write(json.dumps({
            "event": "summary",
            "n_files": len(by_file),
            "n_topics": len(output_rows),
            "total_latency_s": round(elapsed_s, 2),
        }) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = load_config(CONFIG_PATH)
    cfg_model    = cfg.get("embedding", {}).get("model", "bge-m3")
    cfg_dim      = cfg.get("embedding", {}).get("embed_dim", 1024)

    parser = argparse.ArgumentParser(description="LTG Phase 2 embed — topic embedding")
    parser.add_argument("--input",         required=True,  type=Path)
    parser.add_argument("--output",        required=True,  type=Path)
    parser.add_argument("--embed-model",   default=cfg_model)
    parser.add_argument("--embed-mode",    default="description",
                        choices=["description", "description_plus_spans"])
    parser.add_argument("--batch-size",    default=32,  type=int)
    parser.add_argument("--ollama-url",    default="http://localhost:11434")
    parser.add_argument("--log-dir",       default=RUNS_DIR, type=Path)
    parser.add_argument("--max-failures",  default=5,   type=int)
    args = parser.parse_args()

    # Preflight ping
    try:
        httpx.get(f"{args.ollama_url}/api/tags", timeout=5.0).raise_for_status()
    except httpx.ConnectError:
        print(f"ERROR: Ollama not reachable at {args.ollama_url}. "
              "Is it running? Try: ollama serve", file=sys.stderr)
        sys.exit(3)

    t0 = time.monotonic()
    rows = load_jsonl(args.input)
    grouped = group_rows_by_file(rows)
    all_tuples = list(collect_embed_tuples(grouped, args.embed_mode, REPO_ROOT))
    results = list(process_batches(
        all_tuples, args.batch_size, args.embed_model,
        args.ollama_url, cfg_dim, args.max_failures,
    ))
    output_rows = write_output_jsonl(results, args.output, args.embed_model, cfg_dim, args.embed_mode)
    elapsed = time.monotonic() - t0
    write_run_log(args.log_dir, output_rows, elapsed)
    print(f"{len(grouped)} files, {len(output_rows)} topics emitted, "
          f"{len(all_tuples) - len(output_rows)} failed — {elapsed:.1f}s → {args.output}")


if __name__ == "__main__":
    main()
