# Attributions & License Tracking

Tracks external code/projects used by this repo, per the licensing-compliance
rule in `CLAUDE.md` (Workflow Rules #4). One row per dependency that is more
than a trivial transitive; add a row when adopting anything new.

**Redistribution note:** this repo is currently a private/local project, so
copyleft (GPL) dependencies impose no obligations today. If any part of
`retrieval/` is ever published or distributed, the GPL rows below make the
combined-work licensing question explicit — revisit before publishing.

## Python dependencies (retrieval/ — LTG substrate)

| Project | License | Used for | Since |
|---------|---------|----------|-------|
| [leidenalg](https://github.com/vtraag/leidenalg) | **GPL-3.0+** | Leiden community detection (`communities.py`, Phase 4) | 2026-07-02 (PR #66) |
| [python-igraph](https://github.com/igraph/python-igraph) | **GPL-2.0+** | Graph backend required by leidenalg (transitive) | 2026-07-02 (PR #66) |
| [networkx](https://github.com/networkx/networkx) | BSD-3-Clause | Graph construction / edge dedup (`communities.py`, Phase 4) | 2026-07-02 (PR #66) |
| [numpy](https://github.com/numpy/numpy) | BSD-3-Clause | Similarity matmul + top-K selection (`graph.py`, Phase 4) | 2026-07-02 (PR #66) |
| [LanceDB](https://github.com/lancedb/lancedb) | Apache-2.0 | Vector store (`store.py`, Phase 2) | 2026-05-28 |
| [pyarrow](https://github.com/apache/arrow) | Apache-2.0 | Arrow tables / schema (`store.py`, Phase 2) | 2026-05-28 |
| [httpx](https://github.com/encode/httpx) | BSD-3-Clause | Ollama API client (`model_client.py`) | 2026-05-27 |
| [PyYAML](https://github.com/yaml/pyyaml) | MIT | Config parsing | 2026-05-27 |

## Other attributions

*(none yet — add rows here when external code or content requiring attribution
is incorporated elsewhere in the repo)*
