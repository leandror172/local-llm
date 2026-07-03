"""LTG Phase 4 — Leiden community detection over the edges graph.

Reads nodes+edges from LanceDB, writes community_coarse/community_fine back
to the nodes table (P4-D5/P4-D7, ref:ltg-phase4-decisions).
"""

from pathlib import Path
import pyarrow as pa
import lancedb
import networkx as nx
import igraph as ig
import leidenalg

from store import backup_index, open_or_create_table

def build_graph(ids: list[str], edge_rows: list[dict]) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(ids)
    
    for row in edge_rows:
        u, v, w = row["src_id"], row["dst_id"], float(row["weight"])
        if g.has_edge(u, v):
            g[u][v]["weight"] = max(g[u][v]["weight"], w)
        else:
            g.add_edge(u, v, weight=w)
    
    return g

def _leiden_partition(igraph_graph: ig.Graph, resolution: float, seed: int) -> list[int]:
    partition = leidenalg.find_partition(
        igraph_graph,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=resolution,
        seed=seed
    )
    return partition.membership

def leiden_assignments(graph: nx.Graph, resolutions: dict, seed: int) -> dict[str, tuple[int, int]]:
    igraph_graph = ig.Graph.from_networkx(graph)
    
    if graph.number_of_edges() == 0:
        return {name: (i, i) for i, name in enumerate(igraph_graph.vs["_nx_name"])}
    
    coarse_partition = _leiden_partition(igraph_graph, resolutions["coarse"], seed)
    fine_partition = _leiden_partition(igraph_graph, resolutions["fine"], seed)
    
    names = igraph_graph.vs["_nx_name"]
    return {name: (coarse_partition[i], fine_partition[i]) for i, name in enumerate(names)}

def write_communities(
    index_path: Path | str,
    assignments: dict,
    table_name: str = "topics",
    backup: bool = True
) -> None:
    index_path = Path(index_path)
    if backup:
        # append '.bak' (never with_suffix — that strips dotted dir names);
        # single-slot .bak shared across stages — hardening tracked as T-71
        backup_index(index_path, index_path.parent / (index_path.name + ".bak"))

    db = lancedb.connect(str(index_path))
    arrow = db.open_table(table_name).to_arrow()
    
    ids = arrow.column("id").to_pylist()
    coarse_data = pa.array(
        [assignments[i][0] if i in assignments else None for i in ids],
        type=pa.int32()
    )
    fine_data = pa.array(
        [assignments[i][1] if i in assignments else None for i in ids],
        type=pa.int32()
    )
    
    arrow_tables = [
        (coarse_data, "community_coarse"),
        (fine_data, "community_fine")
    ]
    
    for data, name in arrow_tables:
        if name in arrow.schema.names:
            field_index = arrow.schema.get_field_index(name)
            arrow = arrow.set_column(field_index, pa.field(name, pa.int32(), nullable=True), data)
        else:
            arrow = arrow.append_column(name, data)
    
    open_or_create_table(db, table_name, arrow)

import argparse
from collections import Counter, defaultdict

from graph import load_graph_config

def _load_edge_rows(index_path: Path) -> list[dict]:
    db = lancedb.connect(str(index_path))
    edges_table = db.open_table("edges")
    arrow = edges_table.to_arrow()

    src_ids = arrow.column("src_id").to_pylist()
    dst_ids = arrow.column("dst_id").to_pylist()
    weights = arrow.column("weight").to_pylist()

    return [{"src_id": u, "dst_id": v, "weight": w} for u, v, w in zip(src_ids, dst_ids, weights)]

def _load_node_ids_and_groups(index_path: Path, table_name: str) -> tuple[list[str], dict[str, str]]:
    db = lancedb.connect(str(index_path))
    nodes_table = db.open_table(table_name)
    arrow = nodes_table.to_arrow()

    ids = arrow.column("id").to_pylist()
    source_groups = {id_: group for id_, group in zip(ids, arrow.column("source_group").to_pylist())}

    return ids, source_groups

def _print_sanity_report(assignments: dict, groups_by_id: dict) -> None:
    coarse_sizes = Counter(coarse for (coarse, _) in assignments.values())
    fine_sizes = Counter(fine for (_, fine) in assignments.values())

    print(f"coarse communities: {len(coarse_sizes)} (top sizes: {[size for _, size in coarse_sizes.most_common(10)]})")
    print(f"fine communities: {len(fine_sizes)} (top sizes: {[size for _, size in fine_sizes.most_common(10)]})")

    crosstab = defaultdict(Counter)
    for node_id, (coarse, _) in assignments.items():
        crosstab[coarse][groups_by_id.get(node_id, "?")] += 1

    print("coarse community × source_group (communities with >= 10 nodes):")
    for community, total in sorted(coarse_sizes.items(), key=lambda item: item[1], reverse=True):
        if total >= 10:
            group_counts = crosstab[community].most_common()
            print(f"  c{community} (n={total}): " + ", ".join(f"{group}={count}" for group, count in group_counts))

def main() -> None:
    parser = argparse.ArgumentParser(description="LTG Phase 4 Community Detection")
    parser.add_argument("--index", type=Path, default=Path(__file__).parent / "index", help="Index path")
    parser.add_argument("--table", type=str, default="topics", help="Nodes table name")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "config.yaml", help="Config file path")
    parser.add_argument("--no-backup", action="store_true", help="Do not backup the index directory")

    args = parser.parse_args()

    config = load_graph_config(args.config)
    ids, groups_by_id = _load_node_ids_and_groups(args.index, args.table)
    edge_rows = _load_edge_rows(args.index)
    graph = build_graph(ids, edge_rows)
    assignments = leiden_assignments(graph, config["resolutions"], int(config["seed"]))
    write_communities(args.index, assignments, table_name=args.table, backup=not args.no_backup)

    print(f"{len(assignments)} nodes assigned")
    _print_sanity_report(assignments, groups_by_id)

if __name__ == "__main__":
    main()
