# retrieval/inspect.py

import argparse
import json
import sys
import math
import time
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import lancedb
import httpx
from model_client import ModelClient, load_config

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_INDEX = str(REPO_ROOT / "retrieval" / "index")
DEFAULT_TABLE = "topics"
DEFAULT_CONFIG = str(REPO_ROOT / "retrieval" / "config.yaml")
DEFAULT_K = 5
DEFAULT_TOP_PAIRS = 10


def open_table(index_path: str, table_name: str) -> lancedb.table.Table:
    """Open a LanceDB table at the specified index path and table name."""
    db = lancedb.connect(index_path)
    return db.open_table(table_name)


def list_mode(table: lancedb.table.Table):
    """Print topic names and file paths for every row in the table."""
    arrow_table = table.to_arrow()
    file_paths = arrow_table.column("file_path").to_pylist()
    topic_names = arrow_table.column("topic_name").to_pylist()

    for fp, tn in zip(file_paths, topic_names):
        print(f"{fp}  {tn}")


def stats_mode(table: lancedb.table.Table):
    """Print statistics about the table's contents."""
    row_count = table.count_rows()
    arrow_table = table.to_arrow()
    
    file_paths = arrow_table.column("file_path").to_pylist()
    embed_models = arrow_table.column("embed_model").to_pylist()
    extractor_models = arrow_table.column("extractor_model").to_pylist()

    print(f"Rows: {row_count}")
    print(f"Files: {len(set(file_paths))}")
    
    # Embed model breakdown
    embed_counter = Counter(embed_models)
    sorted_embeds = sorted(embed_counter.items(), key=lambda x: (-x[1], x[0]))
    print("embed_model breakdown:", ", ".join(f"{model} ({count})" for model, count in sorted_embeds))
    
    # Extractor model breakdown
    extractor_counter = Counter(extractor_models)
    sorted_extractors = sorted(extractor_counter.items(), key=lambda x: (-x[1], x[0]))
    print("extractor_model breakdown:", ", ".join(f"{model} ({count})" for model, count in sorted_extractors))


def query_mode(table: lancedb.table.Table, query: str, k: int = DEFAULT_K, output_md: Path | None = None):
    """Embed the query and search the table for similar vectors."""
    config = load_config(DEFAULT_CONFIG)
    client = ModelClient(config)
    
    # Embed the query
    embeddings = client.embed_texts([query], role="embedding")
    vector = embeddings[0]
    
    # Search the table
    results = table.search(vector).limit(k).to_list()
    
    # Print results
    for i, result in enumerate(results):
        score = result["_distance"]
        print(f"#{i+1}  score={score:.4f}  {result['file_path']}")
        print(f"    {result['topic_name']}")
        print(f"    {result['description'][:120]}\n")
    
    # Write to markdown if requested
    if output_md:
        with open_md_file(output_md, "a") as f:
            f.write(f"### Query: '{query}'\n\n")
            for i, result in enumerate(results):
                score = result["_distance"]
                f.write(f"{i+1}. **{result['topic_name']}** ({result['file_path']}) - Score: {score:.4f}\n")
                f.write(f"    {result['description'][:120]}\n\n")


def relate_mode(table: lancedb.table.Table, file_a: str, file_b: str, top_pairs: int = DEFAULT_TOP_PAIRS):
    """Find related topics between two files and compute divergences."""
    arrow_table = table.to_arrow()
    
    # Extract all rows
    file_paths = arrow_table.column("file_path").to_pylist()
    topic_names = arrow_table.column("topic_name").to_pylist()
    descriptions = arrow_table.column("description").to_pylist()
    vectors = arrow_table.column("vector").to_pylist()
    
    # Filter and separate by file
    rows_a = []
    rows_b = []
    
    for fp, tn, desc, vec in zip(file_paths, topic_names, descriptions, vectors):
        if fp == file_a:
            rows_a.append({"topic": tn, "description": desc, "vector": vec})
        elif fp == file_b:
            rows_b.append({"topic": tn, "description": desc, "vector": vec})
    
    # Compute all pairs
    pairs = []
    for a in rows_a:
        for b in rows_b:
            cosine = sum(x * y for x, y in zip(a["vector"], b["vector"]))
            pairs.append((cosine, a["topic"], b["topic"]))
    
    # Sort and print top-N pairs
    pairs.sort(reverse=True)
    print(f"Top {top_pairs} related pairs:")
    for cosine, topic_a, topic_b in pairs[:top_pairs]:
        print(f"{cosine:.4f}  {topic_a}  <->  {topic_b}")
    
    # Compute divergences
    best_matches = defaultdict(float)
    for a in rows_a:
        max_cosine = max(sum(x * y for x, y in zip(a["vector"], rb["vector"])) for rb in rows_b)
        if max_cosine < 0.5:
            best_matches[a["topic"]] = max_cosine

    for b in rows_b:
        max_cosine = max(sum(x * y for x, y in zip(ra["vector"], b["vector"])) for ra in rows_a)
        if max_cosine < 0.5:
            best_matches[b["topic"]] = max_cosine
    
    print("\nDivergences:")
    for topic, score in best_matches.items():
        print(f"- {topic}: {score:.4f}")
    
    # Compute overall similarity
    mean_similarity = sum(cosine for cosine, _, _ in pairs[:top_pairs]) / len(pairs[:top_pairs])
    print(f"\nOverall similarity: {mean_similarity:.4f}")


def acceptance_mode(table: lancedb.table.Table, output_md: Path | None = None):
    """Run predefined queries and relate mode test."""
    queries = [
        "what's special about Repowise's git co-change analysis",
        "how do we handle memory across sessions",
        "which models are good at topic extraction",
        "how does Repowise analyze code repositories",
        "expense report classification accuracy",
        "Kubernetes deployment YAML"
    ]
    
    results = []
    
    for i, query in enumerate(queries):
        print(f"\nRunning query {i+1}: '{query}'")
        config = load_config(DEFAULT_CONFIG)
        client = ModelClient(config)
        
        # Embed the query
        embeddings = client.embed_texts([query], role="embedding")
        vector = embeddings[0]
        
        # Search the table
        results_list = table.search(vector).limit(5).to_list()
        
        # Record results
        result_entry = {
            "query": query,
            "top_1_file": results_list[0]["file_path"] if results_list else None,
            "top_1_score": results_list[0]["_distance"] if results_list else None,
            "top_5_results": results_list[:5]
        }
        results.append(result_entry)
    
    # Run relate mode test
    print("\nRunning relate mode test:")
    relate_mode(table, "docs/research/smart-rag-repowise.md", "docs/research/smart-rag-claude-mem.md", top_pairs=10)
    
    # Write results to markdown if requested
    if output_md:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        md_path = Path(output_md) / f"probes_{timestamp}.md"
        
        with open_md_file(md_path, "w") as f:
            f.write("# Acceptance Test Results\n\n")
            
            for i, result in enumerate(results):
                f.write(f"## Query {i+1}: '{result['query']}'\n\n")
                if result["top_1_file"]:
                    f.write(f"- Top 1 file: {result['top_1_file']}\n")
                    f.write(f"- Top 1 score: {result['top_1_score']:.4f}\n\n")
                
                f.write("Top 5 results:\n")
                for j, res in enumerate(result["top_5_results"]):
                    f.write(f"{j+1}. **{res['topic_name']}** ({res['file_path']}) - Score: {res['_distance']:.4f}\n")
                    f.write(f"    {res['description'][:120]}\n\n")


def open_md_file(path: Path, mode: str):
    """Open a markdown file for writing with proper encoding and directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open(mode, encoding="utf-8")


def main():
    """Parse command line arguments and dispatch to the appropriate mode function."""
    parser = argparse.ArgumentParser(description="Query a LanceDB vector index")
    
    # Shared options
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--table", default=DEFAULT_TABLE)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--output-md", type=Path, help="Output markdown file path")
    
    # Mode flags (mutually exclusive group)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--list", action="store_true", help="List all topics and their file paths")
    mode_group.add_argument("--stats", action="store_true", help="Print statistics about the table")
    mode_group.add_argument("--query", type=str, help="Query the index with a text string")
    mode_group.add_argument("--relate", action="store_true", help="Find related topics between two files")
    mode_group.add_argument("--acceptance", action="store_true", help="Run predefined acceptance tests")
    
    # Query-specific options
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    
    # Relate-specific options
    parser.add_argument("--file-a", type=str, help="First file to compare")
    parser.add_argument("--file-b", type=str, help="Second file to compare")
    parser.add_argument("--top-pairs", type=int, default=DEFAULT_TOP_PAIRS)
    
    args = parser.parse_args()
    
    try:
        table = open_table(args.index, args.table)
        
        if args.list:
            list_mode(table)
        elif args.stats:
            stats_mode(table)
        elif args.query is not None:
            query_mode(table, args.query, k=args.k, output_md=args.output_md)
        elif args.relate:
            relate_mode(table, args.file_a, args.file_b, top_pairs=args.top_pairs)
        elif args.acceptance:
            acceptance_mode(table, output_md=args.output_md)
            
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
