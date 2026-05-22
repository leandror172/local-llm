# LTG Phase 0 Decisions

**Context:** Implementation plan at `ref:plan-latent-topic-graph`. Concept at `ref:concept-latent-topic-graph`. These decisions were reached in session 52 (2026-04-14) before any code was written, per the plan's Phase 0 gate.

Each entry records the decision, the reasoning, alternatives considered, and the conditions under which it should be revisited. Frozen here means "do not relitigate without a concrete trigger from the revisit list."

---

<!-- ref:ltg-scope -->
## 1. Index scope model — per-repo + federation later

**Decision:** One index per repo. Federation layer deferred to Phase 9.

**Why:** The MVP acceptance test (`relate()` over smart-rag cluster files) is intra-repo. Matches existing `.memories/` and `ref:KEY` conventions. Preserves permission boundaries cleanly. Federation interface built speculatively risks being wrong; building it after real single-repo use is cheaper.

**Alternatives considered:** Single global index with scope tags — rejected because permission boundaries become soft, and cross-repo writes would couple unrelated subsystems.

**Revisit when:** A concrete cross-repo query is needed (e.g., chatbot Phase 3 wants a query that spans llm + web-research). Phase 9 formally addresses this.
<!-- /ref:ltg-scope -->

---

<!-- ref:ltg-embedding -->
## 2. Embedding model — `bge-m3` via Ollama

**Decision:** `bge-m3` pulled via Ollama as the primary embedding model. Dense 1024-dim output only (Ollama does not expose bge-m3's sparse or multi-vector outputs).

**Why:** `ollama pull bge-m3` works, which eliminates the original "runtime split" objection (no sentence-transformers / torch install needed). Quality lift over `nomic-embed-text` is ~3-4 MTEB points — modest but compounding across the substrate's lifetime, and re-embedding the corpus later is expensive enough to justify picking the better option upfront. Cross-repo consumers get the model for free via Ollama without any HF/torch footprint.

**Fallback chain if VRAM pressure is unworkable:**
1. `mxbai-embed-large` (~670 MB, MTEB ~64.7, Ollama-native)
2. `snowflake-arctic-embed-l` (~335 MB, MTEB ~66.0, Ollama-native)
3. `nomic-embed-text` (~274 MB, MTEB ~62.4, Ollama-native)

All three are a one-line config swap.

**Phase 2 gating probe — COMPLETE (2026-05-20, session 61):** WARN verdict — bge-m3 evicts qwen3:14b at load time (11.4 GB + 1.2 GB > 12 GB headroom), but query-time interleaved stress (5 rounds embed→infer) showed zero evictions at ~3.5s avg infer latency. **bge-m3 is locked. Sequential constraint: embed.py and infer calls must not run in parallel.** Script: `retrieval/run-vram-probe.sh`. Full VRAM figures: qwen3:14b runtime footprint 11,384 MiB; bge-m3 1,200 MiB; total headroom 12,288 MiB.

**Alternatives considered:** `nomic-embed-text` as simplest-possible default — rejected in favor of bge-m3 once Ollama-native status was confirmed. Running `bge-m3` via `sentence-transformers` — rejected because Ollama-native route exists.

**Sparse signal option:** If exact-token recall (model names, ref keys, flags) proves insufficient with dense-only, add a sidecar BM25 index via `bm25s` (pure Python, light). Evaluated if/when Phase 2 probe queries underperform on technical terms.

**Revisit when:** Phase 2 VRAM probe fails at query time; Phase 2 probe queries show exact-match recall problems; a future Ollama release exposes bge-m3 sparse/multi-vector outputs (would unlock hybrid retrieval for free).
<!-- /ref:ltg-embedding -->

---

<!-- ref:ltg-vector-store -->
## 3. Vector store — LanceDB

**Decision:** LanceDB for all vector storage and node/edge metadata. No separate SQL layer for MVP.

**Why:** Embedded (no server), Arrow/Parquet-backed (readable by polars, DuckDB, pyarrow for free), versioned time-travel built in, single-writer multi-reader fits rebuild-on-demand workflow. Any dimension supported; bge-m3's 1024-dim is trivial.

**Alternatives considered:** Qdrant — server-based, richer filters, overkill for MVP and adds operational surface. sqlite-vss — less mature, more friction. SQLite (metadata) + LanceDB (vectors) split — rejected per decision #7.

**Revisit when:** Phase 4 community queries need SQL expressions Lance can't support, and the workaround is uglier than adding a SQLite metadata layer.
<!-- /ref:ltg-vector-store -->

---

<!-- ref:ltg-graph-lib -->
## 4. Graph library — networkx + leidenalg

**Decision:** networkx for graph construction and traversal; leidenalg for community detection.

**Why:** At MVP scale (hundreds to low thousands of nodes) networkx is plenty fast, pure Python, widely documented. Leiden is strictly better than Louvain (no badly connected communities). `leidenalg` pulls `python-igraph` as a transitive dep, so switching to igraph later if networkx becomes a bottleneck is near-free.

**Alternatives considered:** Raw `python-igraph` — slightly faster, less Pythonic, not needed at this scale. `graph-tool` — fastest but installation is painful (Boost). Both deferred as optimization options.

**Revisit when:** Graph size exceeds ~10k nodes and networkx traversal latency becomes user-visible.
<!-- /ref:ltg-graph-lib -->

---

<!-- ref:ltg-extractor -->
## 5. Topic extractor model — **FROZEN** (session 59, 2026-05-04)

**Decision:** 2-arm specialized routing. All three freeze gates cleared.

| Arm | Model | Rationale |
|---|---|---|
| **Prose files** | `qwen3:14b` | Clear winner — 2.69 Claude-draft prose avg, 2.86 user-track avg. Passes threshold on all 7 prose files under both rater tracks. Universal ranking agreement across two independent scorers. |
| **Code files** | `qwen2.5-coder:14b` | n=1 (build-persona.py); passes threshold at 2.48/2.90 (Claude/user). Best semantic clustering on code. Revisit if corpus expands — user track puts this model only 0.04 above threshold. |

**Single-model fallback:** `qwen3:14b` — loses ≤0.15 quality on cross-reference-index files, gains operational simplicity. Acceptable for MVP.

**Frozen parameters:** `temperature=0.1`, `think=False`, `num_ctx=8192`, `format=json_schema` (structured output, 100% reliable).

**Prompt:** `retrieval/prompts/extract.txt` (single-stage, no iteration needed — qwen3:14b cleared threshold on first sweep).

**Gate evidence:**
1. ~~Two-rater reconciliation~~ — complete (session 58). Identical 4-model ranking under both Claude and user scoring tracks.
2. ~~Determinism re-run~~ — complete (session 59, Branch C). Off-by-one on dense single-line bullets is a confirmed model property; containment/post-pass guard added to Phase 2 action list. Does not change routing decision.
3. ~~MoE eval~~ — complete (session 59). qwen3:30b-a3b unusable (Ollama MoE offload TTFT > 9 min). qwen3-coder:30b fails adjusted threshold (2.06 prose avg after universal speed penalty). Neither displaces existing routing. See `ref:ltg-phase1-moe-eval`.

**Deferred items (Phase 2, not blocking freeze):**
- VRAM co-residence probe: qwen3:14b + bge-m3 ≈ 12 GB on 12 GB card — must confirm before embedding is locked.
- Containment/post-pass guard for qwen3:14b on dense single-line bullet lists (Branch C action from determinism re-run).
- Prompt-iteration experiment: topic-count floor `max(5, major_section_count)` + containment-only overlap rule (tests whether qwen3:8b's whole-section-drop failure is prompt-fixable; deferred because the freeze decision doesn't depend on it).
- Cross-reference-index 3rd arm: qwen3:8b candidate on `smart-rag-index.md`-type files — n=1 evidence, not load-bearing. Revisit with ≥3 cross-ref-index files or after prompt-iteration experiment.

**Full scoring evidence:** `retrieval/spike-results.md` (`ref:ltg-phase1-results`), `retrieval/spike-rater-notes.md` (`ref:ltg-phase1-routing-hypothesis`, `ref:ltg-phase1-moe-eval`, `ref:ltg-phase1-determinism-smart-rag-index`).

**Revisit when:** Phase 2 corpus expansion adds ≥3 cross-reference-index files, or a new model family arrives at 14B-class with > 15 tok/s and qualitatively better span reasoning.
<!-- /ref:ltg-extractor -->

---

<!-- ref:ltg-placement -->
## 6. Code placement — new `retrieval/` top-level directory

**Decision:** New top-level `retrieval/` directory in the llm repo. `mcp-server/` (or the ollama-bridge subtree) gains a thin adapter that imports from `retrieval/`.

**Why:** Multiple downstream consumers are planned (mcp-server adapter, career chatbot Phase 3, web-research Dispatcher, potential evaluator integration). Sub-packaging inside `mcp-server/` causes circular-import grief the moment a second consumer shows up. Top-level placement also makes future extraction to a standalone package trivial.

**Alternatives considered:** `mcp-server/retrieval/` — rejected for circular-import risk. `retrieval-mcp/` as a separate MCP server — deferred; can be split out later if `retrieval/` grows large enough to justify its own server process.

**Revisit when:** `retrieval/` grows to warrant its own MCP server process, or when extraction to a standalone package is needed.
<!-- /ref:ltg-placement -->

---

<!-- ref:ltg-storage-layout -->
## 7. Storage layout — pure LanceDB + sidecars

**Decision:** All node/edge/community data in LanceDB tables. Sidecar files for logs, configs, and decisions:
- `retrieval/extraction_runs.jsonl` — append-only run log
- `retrieval/DECISIONS.md` — this file
- `retrieval/configs/*.yaml` — per-repo configs (Phase 8)
- `retrieval/phase1-results.md` / `phase1-long-file-findings.md` — Phase 1 artifacts

**Why:** Single store = single ingest path = fewer sync bugs. Filter-after-search is a single Lance query rather than two round trips + a manual join. Arrow/Parquet underneath means the "inspect" UX is tool-agnostic. Versioned time-travel is free.

**Debuggability patch:** `retrieval/inspect.py` — ~30-line CLI that takes table name + optional filter and prints rows as a rich-formatted table. Replaces the shell-level debuggability that raw SQLite would provide. Built in Phase 2 alongside the first `store.py`.

**Schema additions anticipated:**
- `embedding` dimension = 1024 (bge-m3)
- Optional `segment_id` / `segment_start` / `segment_end` fields if Phase 1 long-file findings show chunking is required
- Optional `extraction_kind: prose | code` if Phase 1 shows code needs different metadata

**Alternatives considered:** SQLite (nodes/edges/metadata) + LanceDB (vectors only) split — rejected because: (a) two sources of truth with write-ordering risk, (b) filter-after-search becomes two round trips, (c) SQL joins are not needed until Phase 4 at earliest, and at that point adding SQLite as a metadata overlay is a 2-hour add, not a rewrite. Pure JSON — rejected for non-trivial corpus.

**Known loss (accepted):** Shell-level debuggability (`sqlite3 db.sqlite "SELECT..."`) is replaced by `retrieval/inspect.py`. Mitigated, not recovered.

**Revisit when:** Phase 4 surfaces a community-level query that Lance can't express cleanly, or multi-table transaction semantics become load-bearing.
<!-- /ref:ltg-storage-layout -->

---

<!-- ref:ltg-corpus -->
## 8. MVP corpus scope — curated subset + two branch points

**Decision:** Initial MVP corpus is the curated subset:
- `docs/research/`
- `docs/ideas/`
- `.claude/`
- `.memories/`

**Why:** Prose-dominant, acceptance test (`relate()` over smart-rag cluster) lives here, no files exceed context atomically (probably). Widening to the full repo adds noise from benchmark scripts, persona Modelfiles, raw data that don't have "topics" in the intended sense.

**Addition over plan default:** `docs/ideas/` explicitly included — it holds the LTG concept paper itself and the smart-rag1/2/3 conversations, and is where the richest cross-doc `relate()` tests live.

**Phase 1 finding-dependent branch points (revisit after Phase 1 completes):**

1. **Code files.** If the code-file test in the Phase 1 sweep shows clean semantic extraction (score ≥ 2.0 on the semantic-vs-syntactic rubric), widen MVP to include one Python module to prove multi-file-type handling end-to-end. If extraction fails, explicitly exclude code from MVP and document it as Phase 8 territory.

2. **Long files.** If the long-file appendix concludes that a naive or structure-aware chunking strategy works cleanly, optionally widen MVP to include one medium-long file (50–100K tokens if any exist in the curated subset). If chunking is messy, MVP stays at "files that fit in context atomically" and long-file handling becomes Phase 2.5 work before Phase 3 anchors are built.

**Alternatives considered:** Whole llm repo as MVP — rejected because noise dominates signal for the acceptance test. Just `docs/research/` — rejected because `.memories/` and `.claude/` provide structural/conventional content that makes anchor integration (Phase 3) meaningful.

**Revisit when:** Phase 1 completes and the two branch points above have evidence.
<!-- /ref:ltg-corpus -->

---

<!-- ref:ltg-notes -->
## Cross-cutting notes

- **Plan reference:** `ref:plan-latent-topic-graph` in `.claude/index.md` points at the plan file. Concept paper at `ref:concept-latent-topic-graph`.
- **All calls logged:** Every extractor call goes to `~/.local/share/ollama-bridge/calls.jsonl` automatically via the ollama-bridge MCP server. Phase 1 analysis can pull structured data from there.
- **Warm-up:** Use `warm_model` MCP tool before batch extraction runs to eliminate cold-start penalties.
- **No git commits of raw Phase 1 extractions:** `retrieval/phase1-raw/` should be gitignored; scores and narrative results are committed, raw JSON outputs are reproducible and bulky.
<!-- /ref:ltg-notes -->
