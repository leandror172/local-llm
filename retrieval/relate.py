"""LTG Phase 5 — relate(a, b): structured pairwise relation between two corpus files.

Read-only over the LanceDB `topics` (nodes) and `edges` tables. Given two
corpus-relative file paths, it aggregates the direct cross-file edge evidence,
community overlap, shared anchors, and provenance into a single auditable
structured dict, and assigns a verdict band derived from recorded thresholds.

Scope note: T1–T3 build the structured result WITHOUT `summary` (the `build_relation`
seam). Prose synthesis (`summary`, P5-D5), the CLI, and the `__main__` guard are T4/T5.
The summary is attached in the `relate()` wrapper — never inside `build_relation`, which
stays pure/summary-free. The only model call in this module is the prose synthesis.

Decisions: ref:ltg-phase5-plan (P5-D1..D7). Read-only boundary: P4-D6.
"""

import argparse
import difflib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import NamedTuple

import lancedb
import numpy as np
import yaml

from anchors import COSINE_THRESHOLD
from graph import _normalize_vectors, load_graph_config
from model_client import ModelClient, load_config

# Provisional weak/unrelated cosine floor (P5-D4). Recorded here, not scattered
# as a magic literal; tuned + frozen at T6 acceptance against real pairs.
WEAK_COSINE_FLOOR = 0.55

ANCHOR_NODE_KIND = "anchor"

DEFAULT_INDEX = Path(__file__).parent / "index"
DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"
DEFAULT_MANIFEST = Path(__file__).parent / "corpus-manifest.yaml"
SUMMARY_PROMPT_PATH = Path(__file__).parent / "prompts" / "relate_summary.txt"

_STALE_REMEDY = (
    "Community assignments are stale (null community_coarse/community_fine on "
    "{n} contributing node(s)). Communities are derived data, nulled by the last "
    "topics/anchors rebuild (P4-D5). Regenerate before relating: run "
    "`retrieval/run-graph.sh` then `retrieval/run-communities.sh`, or "
    "`retrieval/run-rebuild-all.sh --embeddings retrieval/embeddings.jsonl`."
)


class Node(NamedTuple):
    id: str
    file_path: str
    node_kind: str
    source_group: str
    community_coarse: int | None
    community_fine: int | None
    vector: list[float]


class UnknownFileError(ValueError):
    """Raised when a requested file path is not present in the index."""


class StaleCommunitiesError(RuntimeError):
    """Raised when any contributing node has a null community column (P5-D7)."""


# --- Loaders (thin: LanceDB / yaml / config) ---------------------------------

def load_node_table(index_path: Path | str, table_name: str = "topics") -> list[Node]:
    """Read the nodes table into Node records (read-only)."""
    db = lancedb.connect(str(index_path))
    arrow = db.open_table(table_name).to_arrow()
    columns = {
        name: arrow.column(name).to_pylist()
        for name in ("id", "file_path", "node_kind", "source_group",
                     "community_coarse", "community_fine", "vector")
    }
    return [
        Node(
            id=columns["id"][i],
            file_path=columns["file_path"][i],
            node_kind=columns["node_kind"][i],
            source_group=columns["source_group"][i],
            community_coarse=columns["community_coarse"][i],
            community_fine=columns["community_fine"][i],
            vector=columns["vector"][i],
        )
        for i in range(arrow.num_rows)
    ]


def load_edges(index_path: Path | str, table_name: str = "edges") -> list[dict]:
    """Read the edges table into plain dicts (read-only)."""
    db = lancedb.connect(str(index_path))
    arrow = db.open_table(table_name).to_arrow()
    fields = ("src_id", "dst_id", "edge_kind", "weight", "directed")
    columns = {name: arrow.column(name).to_pylist() for name in fields}
    return [{name: columns[name][i] for name in fields} for i in range(arrow.num_rows)]


def load_manifest_paths(manifest_path: Path | str = DEFAULT_MANIFEST) -> list[str]:
    """Corpus-relative file paths from the frozen manifest (for path suggestions)."""
    with Path(manifest_path).open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}
    return [entry["path"] for entry in manifest.get("files", [])]


def load_thresholds(config_path: Path | str = DEFAULT_CONFIG) -> dict:
    """Recorded verdict thresholds — tau_floor from config, merge_cosine from the
    frozen anchor constant, weak_floor from this module. Emitted in the result so
    verdicts are auditable."""
    graph_config = load_graph_config(config_path)
    return {
        "tau_floor": float(graph_config["tau_floor"]),
        "merge_cosine": float(COSINE_THRESHOLD),
        "weak_floor": float(WEAK_COSINE_FLOOR),
        "bands": {
            "strong": "same_as edge OR max similarity cosine >= merge_cosine",
            "moderate": "any cross-file similarity edge (cosine >= tau_floor)",
            "weak": "nearest_miss cosine >= weak_floor",
            "unrelated": "nearest_miss cosine < weak_floor",
        },
    }


# --- Selectors + guards (T1) --------------------------------------------------

def nodes_for_file(nodes: list[Node], path: str, manifest_paths: list[str] | None = None) -> list[Node]:
    """Select a file's node set. Unknown path (not indexed) -> UnknownFileError
    naming the path and the nearest manifest matches (P5-D1)."""
    selected = [n for n in nodes if n.file_path == path]
    if selected:
        return selected
    suggestion_pool = manifest_paths if manifest_paths is not None else [n.file_path for n in nodes]
    suggestions = difflib.get_close_matches(path, suggestion_pool, n=5)
    raise UnknownFileError(
        f"'{path}' is not present in the index. Nearest known files: {suggestions}"
    )


def assert_communities_fresh(nodes: list[Node]) -> None:
    """Abort if any contributing node has a null community column (P5-D7)."""
    stale = [n for n in nodes if n.community_coarse is None or n.community_fine is None]
    if stale:
        raise StaleCommunitiesError(_STALE_REMEDY.format(n=len(stale)))


# --- Aggregation (T2) — self-contained pure helpers ---------------------------

def cross_file_edges(edges: list[dict], a_ids: set[str], b_ids: set[str]) -> list[dict]:
    """Collect edges spanning the two node sets, normalizing node_a to the file_a
    side. Undirected kinds are stored once (canonical src_id < dst_id), so the
    A-side node may sit in either endpoint — both orientations are matched."""
    cross = []
    for edge in edges:
        src, dst = edge["src_id"], edge["dst_id"]
        if src in a_ids and dst in b_ids:
            node_a, node_b = src, dst
        elif src in b_ids and dst in a_ids:
            node_a, node_b = dst, src
        else:
            continue
        cross.append({
            "node_a": node_a,
            "node_b": node_b,
            "edge_kind": edge["edge_kind"],
            "weight": edge["weight"],
        })
    return cross


def edge_stats(cross_edges: list[dict]) -> dict:
    """Per-kind counts plus max/mean weight. Empty input -> all-zero (negative case)."""
    counts = Counter(edge["edge_kind"] for edge in cross_edges)
    weights = [edge["weight"] for edge in cross_edges]
    return {
        "similarity": counts.get("similarity", 0),
        "same_as": counts.get("same_as", 0),
        "references": counts.get("references", 0),
        "max_weight": max(weights) if weights else 0.0,
        "mean_weight": (sum(weights) / len(weights)) if weights else 0.0,
    }


def top_edges(cross_edges: list[dict], n: int = 10) -> list[dict]:
    """Top-N cross-file edges by descending weight."""
    return sorted(cross_edges, key=lambda edge: edge["weight"], reverse=True)[:n]


def _communities(nodes: list[Node], attr: str) -> set[int]:
    return {getattr(n, attr) for n in nodes if getattr(n, attr) is not None}


def _overlap_at(nodes_a: list[Node], nodes_b: list[Node], attr: str) -> dict:
    coms_a = _communities(nodes_a, attr)
    coms_b = _communities(nodes_b, attr)
    shared = coms_a & coms_b
    union = coms_a | coms_b
    return {
        "shared": sorted(shared),
        "jaccard": (len(shared) / len(union)) if union else 0.0,
    }


def community_overlap(nodes_a: list[Node], nodes_b: list[Node]) -> dict:
    """Shared community ids + Jaccard at coarse and fine resolutions."""
    return {
        "coarse": _overlap_at(nodes_a, nodes_b, "community_coarse"),
        "fine": _overlap_at(nodes_a, nodes_b, "community_fine"),
    }


def shared_anchors(nodes: list[Node], edges: list[dict], a_ids: set[str], b_ids: set[str]) -> list[dict]:
    """Anchor nodes with edges into BOTH files' node sets. Edge direction is
    ignored for neighbor discovery; self-links are excluded."""
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge["src_id"], set()).add(edge["dst_id"])
        adjacency.setdefault(edge["dst_id"], set()).add(edge["src_id"])

    result = []
    for node in nodes:
        if node.node_kind != ANCHOR_NODE_KIND:
            continue
        neighbors = adjacency.get(node.id, set()) - {node.id}
        linked_from_a = sorted(neighbors & a_ids)
        linked_from_b = sorted(neighbors & b_ids)
        if linked_from_a and linked_from_b:
            result.append({
                "anchor_key": node.id,
                "linked_from_a": linked_from_a,
                "linked_from_b": linked_from_b,
            })
    return result


def provenance(nodes_a: list[Node], nodes_b: list[Node]) -> dict:
    """source_group counts per side — reported, never weighted (P5-D6)."""
    return {
        "a": dict(Counter(n.source_group for n in nodes_a)),
        "b": dict(Counter(n.source_group for n in nodes_b)),
    }


# --- nearest_miss + verdict banding (T3) --------------------------------------

def nearest_miss(nodes_a: list[Node], nodes_b: list[Node]) -> dict:
    """Best (highest-cosine) cross-file node pair via exact matmul on stored
    unit-normalized vectors (P5-D3). NEVER LanceDB ANN search (returns L2)."""
    vectors_a = _normalize_vectors(np.array([n.vector for n in nodes_a], dtype=np.float32))
    vectors_b = _normalize_vectors(np.array([n.vector for n in nodes_b], dtype=np.float32))
    similarity = vectors_a @ vectors_b.T
    i, j = np.unravel_index(int(np.argmax(similarity)), similarity.shape)
    return {
        "node_a": nodes_a[i].id,
        "node_b": nodes_b[j].id,
        "cosine": float(similarity[i, j]),
    }


def _max_similarity_weight(cross_edges: list[dict]) -> float | None:
    weights = [edge["weight"] for edge in cross_edges if edge["edge_kind"] == "similarity"]
    return max(weights) if weights else None


def _has_same_as(cross_edges: list[dict]) -> bool:
    return any(edge["edge_kind"] == "same_as" for edge in cross_edges)


def classify_verdict(
    cross_edges: list[dict],
    nodes_a: list[Node],
    nodes_b: list[Node],
    thresholds: dict,
) -> tuple[str, dict | None]:
    """Verdict-band cascade (P5-D4). strong/moderate rest on edge evidence; the
    nearest-miss matmul runs ONLY in the no-edge branch (P5-D3). Only similarity
    edges carry cosine weights — same_as is a boolean trigger, references never bands.
    Returns (verdict, nearest_miss_or_None)."""
    if _has_same_as(cross_edges):
        return "strong", None

    max_similarity = _max_similarity_weight(cross_edges)
    if max_similarity is not None:
        if max_similarity >= thresholds["merge_cosine"]:
            return "strong", None
        return "moderate", None

    miss = nearest_miss(nodes_a, nodes_b)
    if miss["cosine"] >= thresholds["weak_floor"]:
        return "weak", miss
    return "unrelated", miss


# --- Orchestrator (T1–T3; no summary — T4 seam) -------------------------------

def build_relation(
    file_a: str,
    file_b: str,
    nodes: list[Node],
    edges: list[dict],
    thresholds: dict,
    manifest_paths: list[str] | None = None,
) -> dict:
    """Assemble the structured relation dict from in-memory nodes + edges.

    Pure over its inputs (no I/O) so it is exercised with synthetic fixtures. The
    result deliberately omits `summary`: prose synthesis is T4 and reads this dict.
    """
    nodes_a = nodes_for_file(nodes, file_a, manifest_paths)
    nodes_b = nodes_for_file(nodes, file_b, manifest_paths)
    assert_communities_fresh(nodes_a + nodes_b)

    a_ids = {n.id for n in nodes_a}
    b_ids = {n.id for n in nodes_b}

    cross = cross_file_edges(edges, a_ids, b_ids)
    verdict, miss = classify_verdict(cross, nodes_a, nodes_b, thresholds)

    return {
        "inputs": {"file_a": file_a, "file_b": file_b, "nodes_a": len(nodes_a), "nodes_b": len(nodes_b)},
        "verdict": verdict,
        "thresholds": thresholds,
        "shared_anchors": shared_anchors(nodes, edges, a_ids, b_ids),
        "community_overlap": community_overlap(nodes_a, nodes_b),
        "top_edges": top_edges(cross),
        "edge_stats": edge_stats(cross),
        "provenance": provenance(nodes_a, nodes_b),
        "nearest_miss": miss,
    }


def relate(
    file_a: str,
    file_b: str,
    index_path: Path | str = DEFAULT_INDEX,
    config_path: Path | str = DEFAULT_CONFIG,
    manifest_path: Path | str = DEFAULT_MANIFEST,
    with_summary: bool = True,
    client: ModelClient | None = None,
) -> dict:
    """Read the index (read-only), assemble the structured relation, and attach the
    prose summary (P5-D5) — the only model call. The summary is added HERE, never in
    `build_relation` (which stays pure). `with_summary=False` skips the model call
    (used by tests and `--no-summary`)."""
    nodes = load_node_table(index_path)
    edges = load_edges(index_path)
    thresholds = load_thresholds(config_path)
    manifest_paths = load_manifest_paths(manifest_path)
    relation = build_relation(file_a, file_b, nodes, edges, thresholds, manifest_paths)

    if with_summary:
        if client is None:
            client = ModelClient(load_config(config_path))
        relation["summary"] = synthesize_summary(relation, client)
    return relation


# --- Prose synthesis (T4, P5-D5) ----------------------------------------------

def load_summary_template() -> str:
    """The prose-synthesis prompt template (prompts/relate_summary.txt pattern)."""
    return SUMMARY_PROMPT_PATH.read_text(encoding="utf-8")


def _fmt_edge_stats(stats: dict) -> str:
    return (
        f"similarity={stats['similarity']}, same_as={stats['same_as']}, "
        f"references={stats['references']}, max_weight={stats['max_weight']}, "
        f"mean_weight={stats['mean_weight']}"
    )


def _fmt_community_overlap(overlap: dict) -> str:
    coarse, fine = overlap["coarse"], overlap["fine"]
    return (
        f"coarse: {len(coarse['shared'])} shared communities, jaccard {coarse['jaccard']}; "
        f"fine: {len(fine['shared'])} shared communities, jaccard {fine['jaccard']}"
    )


def _fmt_shared_anchors(anchors: list[dict]) -> str:
    if not anchors:
        return "none"
    return "; ".join(
        f"{a['anchor_key']} (A: {', '.join(a['linked_from_a'])} | B: {', '.join(a['linked_from_b'])})"
        for a in anchors
    )


def _fmt_top_edges(edges: list[dict]) -> str:
    if not edges:
        return "none"
    return "; ".join(f"{e['node_a']}--{e['node_b']} {e['edge_kind']} {e['weight']}" for e in edges)


def _fmt_provenance(prov: dict) -> str:
    return f"A: {prov['a']}; B: {prov['b']}"


def _fmt_nearest_miss(miss: dict | None) -> str:
    if miss is None:
        return "n/a"
    return f"{miss['node_a']} <-> {miss['node_b']} cosine {miss['cosine']}"


def render_summary_facts(relation: dict) -> dict[str, str]:
    """Flatten the structured relation into string slots for the prompt template.
    Every value is a string; the negative case (nearest_miss None / populated) resolves
    to a stable non-empty string."""
    inputs = relation["inputs"]
    return {
        "file_a": inputs["file_a"],
        "file_b": inputs["file_b"],
        "nodes_a": str(inputs["nodes_a"]),
        "nodes_b": str(inputs["nodes_b"]),
        "verdict": relation["verdict"],
        "edge_stats": _fmt_edge_stats(relation["edge_stats"]),
        "community_overlap": _fmt_community_overlap(relation["community_overlap"]),
        "shared_anchors": _fmt_shared_anchors(relation["shared_anchors"]),
        "top_edges": _fmt_top_edges(relation["top_edges"]),
        "provenance": _fmt_provenance(relation["provenance"]),
        "nearest_miss": _fmt_nearest_miss(relation["nearest_miss"]),
    }


def build_summary_prompt(relation: dict, template: str | None = None) -> str:
    """Fill the template's named slots from the structured relation (pre-rendered string
    values, so JSON braces in values never break str.format)."""
    if template is None:
        template = load_summary_template()
    return template.format(**render_summary_facts(relation))


def synthesize_summary(relation: dict, client: ModelClient) -> str:
    """Build the prompt and call the relate_summary prose arm. Returns the summary text
    only — the caller (`relate`) decides where to attach it (never build_relation)."""
    prompt = build_summary_prompt(relation)
    result = client.relate_summary(prompt)
    return result.content.strip()


# --- Human-readable rendering + CLI (T5) --------------------------------------

def render_human(relation: dict) -> str:
    """Readable rendering of the structured dict, plus the summary when present."""
    facts = render_summary_facts(relation)
    lines = [
        f"file_a:            {facts['file_a']} ({facts['nodes_a']} topics)",
        f"file_b:            {facts['file_b']} ({facts['nodes_b']} topics)",
        f"verdict:           {facts['verdict']}",
        f"edge_stats:        {facts['edge_stats']}",
        f"community_overlap: {facts['community_overlap']}",
        f"shared_anchors:    {facts['shared_anchors']}",
        f"top_edges:         {facts['top_edges']}",
        f"provenance:        {facts['provenance']}",
        f"nearest_miss:      {facts['nearest_miss']}",
    ]
    if "summary" in relation:
        lines.append(f"summary:           {relation['summary']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LTG Phase 5 relate(a, b): structured pairwise relation between two corpus files."
    )
    parser.add_argument("--a", required=True, help="Corpus-relative path of file A (as stored in file_path)")
    parser.add_argument("--b", required=True, help="Corpus-relative path of file B")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="Path to the LanceDB index")
    parser.add_argument("--json", action="store_true", help="Emit the full structured dict as JSON")
    parser.add_argument("--no-summary", action="store_true", help="Skip prose synthesis (no model call)")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    relation = relate(args.a, args.b, index_path=args.index, with_summary=not args.no_summary)
    if args.json:
        print(json.dumps(relation, indent=2))
    else:
        print(render_human(relation))


if __name__ == "__main__":
    main()
