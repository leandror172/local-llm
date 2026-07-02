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
