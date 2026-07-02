"""LTG Phase 4 — graph assembly.

Loads graph-build configuration from the retrieval config.yaml `graph:` section.
"""

from pathlib import Path
import yaml
import numpy as np
from typing import NamedTuple

REQUIRED_KEYS = ("tau_floor", "top_k", "resolutions", "seed")
RESOLUTIONS_KEYS = ("coarse", "fine")

def load_graph_config(path: Path | str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist")
    
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    
    if "graph" not in raw:
        raise KeyError("Missing 'graph' section in config file")
    
    graph_config = raw["graph"]
    
    missing_keys = [key for key in REQUIRED_KEYS if key not in graph_config]
    if missing_keys:
        raise KeyError(f"Missing required key(s) in 'graph' section: {', '.join(missing_keys)}")
    
    resolutions = graph_config.get("resolutions", {})
    missing_resolutions_keys = [key for key in RESOLUTIONS_KEYS if key not in resolutions]
    if missing_resolutions_keys:
        raise KeyError(f"Missing required resolution key(s) in 'graph' section: {', '.join(missing_resolutions_keys)}")
    
    return graph_config

class Edge(NamedTuple):
    src_id: str
    dst_id: str
    edge_kind: str
    weight: float
    directed: bool

def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / norms

def _compute_cosine_matrix(normalized_vectors: np.ndarray) -> np.ndarray:
    return normalized_vectors @ normalized_vectors.T

def _top_k_neighbor_sets(cosine_matrix: np.ndarray, top_k: int) -> list[set[int]]:
    """Per-node index sets: sets[i] = the top_k most-similar neighbor indices of i (self excluded)."""
    n = cosine_matrix.shape[0]
    k = min(top_k, n - 1)
    if k <= 0:
        return [set() for _ in range(n)]
    
    masked = cosine_matrix.copy()
    np.fill_diagonal(masked, -np.inf)
    
    neighbor_sets = []
    for i in range(n):
        top_indices = np.argpartition(-masked[i], kth=k-1)[:k]
        neighbor_sets.append(set(top_indices))
    
    return neighbor_sets

def similarity_edges(ids: list[str], vectors: np.ndarray, tau_floor: float, top_k: int) -> list[Edge]:
    normalized_vectors = _normalize_vectors(vectors)
    cosine_matrix = _compute_cosine_matrix(normalized_vectors)
    neighbor_sets = _top_k_neighbor_sets(cosine_matrix, top_k)
    
    edges = []
    n = len(ids)
    for i in range(n):
        for j in range(i + 1, n):
            if cosine_matrix[i, j] >= tau_floor and (j in neighbor_sets[i] or i in neighbor_sets[j]):
                src_id, dst_id = sorted((ids[i], ids[j]))
                edges.append(Edge(src_id=src_id, dst_id=dst_id, edge_kind="similarity", weight=float(cosine_matrix[i, j]), directed=False))
    
    return sorted(edges, key=lambda e: (e.src_id, e.dst_id))

def _topk_membership_mask(sim: np.ndarray, k: int) -> np.ndarray:
    """Boolean n×n mask: mask[i, j] = True iff j is among i's top-k most-similar neighbors (self excluded)."""
    masked = sim.copy()
    np.fill_diagonal(masked, -np.inf)
    kk = min(k, sim.shape[0] - 1)
    if kk <= 0:
        return np.zeros_like(sim, dtype=bool)

    idx = np.argpartition(-masked, kth=kk - 1, axis=1)[:, :kk]
    mask = np.zeros_like(sim, dtype=bool)
    mask[np.arange(mask.shape[0])[:, None], idx] = True
    return mask

def degree_probe_grid(ids: list[str], vectors: np.ndarray, groups: list[str], taus: list[float], ks: list[int]) -> list[dict]:
    """Stats for every (tau, k) combo about the graph similarity_edges() would build."""
    normalized = _normalize_vectors(vectors)
    sim = _compute_cosine_matrix(normalized)
    archive = np.array([g == "archive" for g in groups])
    archive_pair = np.outer(archive, archive)

    results = []
    for k in ks:                      # k outer
        union_mask = _topk_membership_mask(sim, k)
        union_mask |= union_mask.T
        for tau in taus:              # tau inner
            keep = (sim >= tau) & union_mask
            np.fill_diagonal(keep, False)
            degrees = keep.sum(axis=1)
            n_edges = int(degrees.sum() // 2)
            archive_edges = int((keep & archive_pair).sum() // 2)

            result = {
                "tau": tau,
                "k": k,
                "n_edges": n_edges,
                "isolated": int(np.sum(degrees == 0)),
                "deg_p50": float(np.percentile(degrees, 50)),
                "deg_p90": float(np.percentile(degrees, 90)),
                "deg_p99": float(np.percentile(degrees, 99)),
                "deg_max": int(np.max(degrees)),
                "archive_share": round(archive_edges / n_edges, 4) if n_edges > 0 else 0.0
            }

            results.append(result)

    return results

import argparse
from collections import Counter
import lancedb

def load_nodes(index_path: Path, table_name: str = "topics") -> tuple[list[str], np.ndarray, list[str]]:
    db = lancedb.connect(str(index_path))
    arrow = db.open_table(table_name).to_arrow()

    ids = arrow.column("id").to_pylist()
    groups = arrow.column("source_group").to_pylist()
    vectors = np.array(arrow.column("vector").to_pylist(), dtype=np.float32)

    return ids, vectors, groups

def _print_probe_report(ids: list[str], groups: list[str], results: list[dict]) -> None:
    print(f"nodes: {len(ids)}")
    group_counts = Counter(groups)
    print("groups:", dict(sorted(group_counts.items(), key=lambda item: item[1], reverse=True)))

    header = "| tau | k | edges | isolated | p50 | p90 | p99 | max | archive_share |"
    separator = "-" * len(header)
    print(header)
    print(separator)

    for result in results:
        row = (
            f"| {result['tau']:.2f} "
            f"| {result['k']} "
            f"| {result['n_edges']:d} "
            f"| {result['isolated']:d} "
            f"| {result['deg_p50']:.1f} "
            f"| {result['deg_p90']:.1f} "
            f"| {result['deg_p99']:.1f} "
            f"| {result['deg_max']:d} "
            f"| {result['archive_share']:.4f} |"
        )
        print(row)

def main() -> None:
    parser = argparse.ArgumentParser(description="Graph assembly tool.")
    parser.add_argument("--degree-probe", action="store_true", help="Run degree probe analysis")
    parser.add_argument("--index", type=Path, default=Path(__file__).parent / "index", help="Path to the index database")
    parser.add_argument("--table", default="topics", help="Table name in the index database")
    parser.add_argument("--taus", default="0.65,0.70,0.75,0.80", help="Comma-separated list of tau values")
    parser.add_argument("--ks", default="5,10,15", help="Comma-separated list of k values")

    args = parser.parse_args()

    if not args.degree_probe:
        parser.error("only --degree-probe mode is implemented")

    taus = [float(tau) for tau in args.taus.split(",")]
    ks = [int(k) for k in args.ks.split(",")]

    ids, vectors, groups = load_nodes(args.index, args.table)
    results = degree_probe_grid(ids, vectors, groups, taus, ks)
    _print_probe_report(ids, groups, results)

if __name__ == "__main__":
    main()

import json
import re
from anchors import Anchor, _read_block_lines

def same_as_edges(rows: list[dict]) -> list[Edge]:
    edges = []
    for row in rows:
        alias_of = row.get("alias_of")
        if not alias_of:
            continue

        keys = json.loads(alias_of)
        for key in keys:
            src_id, dst_id = sorted((row["id"], key))
            edge = Edge(src_id=src_id, dst_id=dst_id, edge_kind="same_as", weight=1.0, directed=False)
            edges.append(edge)

    return sorted(edges)

def reference_edges(anchors: list[Anchor], repo_root: Path) -> list[Edge]:
    known_keys = {a.bare_key for a in anchors}
    edges = set()

    def _block_mentions(anchor: Anchor, repo_root: Path, known: set[str]) -> None:
        body_lines = _read_block_lines(repo_root / anchor.file_path, anchor.start_line, anchor.bare_key)
        body = "\n".join(body_lines)
        mentions = re.findall(r"(?<!/)ref:([a-z0-9-]+)", body)

        for mention in mentions:
            if mention == anchor.bare_key or mention not in known:
                continue
            edge = Edge(src_id=anchor.key, dst_id=f"ref:{mention}", edge_kind="references", weight=1.0, directed=True)
            edges.add(edge)

    for anchor in anchors:
        _block_mentions(anchor, repo_root, known_keys)

    return sorted(edges)
