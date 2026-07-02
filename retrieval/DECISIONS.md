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
## 2. Embedding model — `qwen3-embedding:8b` via Ollama

**Decision:** `qwen3-embedding:8b` pulled via Ollama as the primary embedding model. Dense 4096-dim output. Upgraded from `bge-m3` (1024-dim, MTEB 63.0) in session 73; +7.5 MTEB points (70.58) with equivalent or better acceptance criteria and improved relate quality (mean similarity 0.663 → 0.697). Re-embedding is cheap (69 topics, ~3s) so upgrading before Phase 3 avoids re-embedding corpus + anchors later.

**Why:** `ollama pull qwen3-embedding:8b` works — same Ollama-native path as bge-m3. VRAM probe (session 73): same WARN verdict as bge-m3 — evicts qwen3:14b at load time only, zero query-time evictions, avg infer latency 4.2s (vs 3.5s with bge-m3 — acceptable). Sequential constraint holds. bge-m3 retained as `index.bak` for rollback.

**Fallback chain if VRAM pressure is unworkable:**
1. `bge-m3` (previous model — index.bak available; one config swap + `store.py` re-run)
2. `mxbai-embed-large` (~670 MB, MTEB ~64.7, Ollama-native)
3. `snowflake-arctic-embed-l` (~335 MB, MTEB ~66.0, Ollama-native)
4. `nomic-embed-text` (~274 MB, MTEB ~62.4, Ollama-native)

**Phase 2 gating probe — COMPLETE (2026-05-20, session 61):** bge-m3 WARN verdict; locked with sequential constraint. Script: `retrieval/run-vram-probe.sh`. Full VRAM figures: qwen3:14b footprint 11,384 MiB; bge-m3 1,200 MiB.

**M-P0b probe — COMPLETE (2026-05-28, session 73):** qwen3-embedding:8b WARN verdict — evicts qwen3:14b at load time (~5 GB footprint vs 1.2 GB for bge-m3), zero query-time evictions over 4 warm rounds, avg infer latency 4.2s. Sequential constraint unchanged. Run: `EMBED_MODEL=qwen3-embedding:8b retrieval/run-vram-probe.sh`.

**Alternatives considered:** Staying with bge-m3 for Phase 3 and upgrading after — rejected because upgrade cost grows each phase (corpus + anchors vs corpus only), and acceptance criteria are equivalent.

**Sparse signal option:** If exact-token recall (model names, ref keys, flags) proves insufficient with dense-only, add a sidecar BM25 index via `bm25s` (pure Python, light). Evaluated if/when Phase 2 probe queries underperform on technical terms.

**Phase 2 complete (2026-05-28, session 72, bge-m3):** embed.py ran 69 topics from 8 corpus files in 5.2s. `embed_mode=description` validated as default. Acceptance run: 7/8 criteria pass (R2 borderline — `.memories/QUICK.md` topics don't surface "session memory" explicitly). A/B with `description_plus_spans` deferred.

**Embedding upgrade complete (2026-05-28, session 73):** Re-embedded 69 topics with `qwen3-embedding:8b` in 2.9s. Acceptance: R1/R3/R4 ✅, R2 ⚠️ borderline (same corpus gap as Phase 2), P1 relate ✅ (improved 0.663→0.697). N-criteria threshold needs recalibration — original > 1.0 threshold was specific to bge-m3's 1024-dim L2 scale; noise queries land at 0.84–0.98 in 4096-dim space (proportionally equivalent). Probe: `retrieval/probes/20260528_202835.md`. `embed.py` and `store.py` now read embed_dim from config.yaml and input JSONL respectively — no hardcoded dimensions.

**Revisit when:** Phase 3 anchor queries show exact-match recall problems on technical terms; a future Ollama release exposes qwen3-embedding sparse outputs (would unlock hybrid retrieval for free).
<!-- /ref:ltg-embedding -->

---

<!-- ref:ltg-vector-store -->
## 3. Vector store — LanceDB

**Decision:** LanceDB for all vector storage and node/edge metadata. No separate SQL layer for MVP.

**Why:** Embedded (no server), Arrow/Parquet-backed (readable by polars, DuckDB, pyarrow for free), versioned time-travel built in, single-writer multi-reader fits rebuild-on-demand workflow. Any dimension supported; dimension is now 4096 (qwen3-embedding:8b).

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

**Frozen parameters:** `temperature=0.1`, `think=False`, `num_ctx=16384`, `format=json_schema` (structured output, 100% reliable).

> **num_ctx three-way note (session 81, 2026-06-01):** The frozen spec above pins `num_ctx=16384` — the operating point under which 2-arm routing was validated. The benchmark `sweep_extractors.py` faithfully uses 16384. **Production `config.yaml` drifted to 32768**, an unconsidered inheritance from the session 75/76 context-ceiling upgrades (q8_0 KV pushed every 14B persona to 32768). The divergence is harmless on the current 8-file corpus — every file fits in 16K, so behavior is identical — and only bites on files >16384 tokens. **Decision (c):** keep both deliberately for now (production gets headroom; benchmark stays at the validated point). **RECHECK trigger:** before Phase 2.5 full-corpus expansion adds long documents — at that point decide whether to (a) align both to 32768 and re-run sweeps, or (b) drop production back to the validated 16384. Tracked in `tasks.md`.

**Prompt:** `retrieval/prompts/extract.txt` (single-stage, no iteration needed — qwen3:14b cleared threshold on first sweep).

**Gate evidence:**
1. ~~Two-rater reconciliation~~ — complete (session 58). Identical 4-model ranking under both Claude and user scoring tracks.
2. ~~Determinism re-run~~ — complete (session 59, Branch C). Off-by-one on dense single-line bullets is a confirmed model property; containment/post-pass guard added to Phase 2 action list. Does not change routing decision.
3. ~~MoE eval~~ — complete (session 59). qwen3:30b-a3b unusable (Ollama MoE offload TTFT > 9 min). qwen3-coder:30b fails adjusted threshold (2.06 prose avg after universal speed penalty). Neither displaces existing routing. See `ref:ltg-phase1-moe-eval`.

**Deferred items (Phase 2, not blocking freeze):**
- ~~VRAM co-residence probe~~ — complete (session 73). bge-m3 WARN (session 61); qwen3-embedding:8b WARN (session 73). Upgraded to qwen3-embedding:8b before Phase 3.
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

**Debuggability patch:** `retrieval/ltg_inspect.py` — ~30-line CLI that takes table name + optional filter and prints rows as a rich-formatted table. Replaces the shell-level debuggability that raw SQLite would provide. Built in Phase 2 alongside the first `store.py`.

**Schema additions anticipated:**
- `embedding` dimension = 4096 (qwen3-embedding:8b; upgraded from 1024/bge-m3 in session 73)
- Optional `segment_id` / `segment_start` / `segment_end` fields if Phase 1 long-file findings show chunking is required
- Optional `extraction_kind: prose | code` if Phase 1 shows code needs different metadata

**Alternatives considered:** SQLite (nodes/edges/metadata) + LanceDB (vectors only) split — rejected because: (a) two sources of truth with write-ordering risk, (b) filter-after-search becomes two round trips, (c) SQL joins are not needed until Phase 4 at earliest, and at that point adding SQLite as a metadata overlay is a 2-hour add, not a rewrite. Pure JSON — rejected for non-trivial corpus.

**Known loss (accepted):** Shell-level debuggability (`sqlite3 db.sqlite "SELECT..."`) is replaced by `retrieval/ltg_inspect.py`. Mitigated, not recovered.

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

<!-- ref:ltg-phase2-schema -->
## Phase 2 Schema — 16-field LanceDB row (2026-05-28, session 72)

Final PyArrow schema as committed in `retrieval/store.py`. All fields are strings unless noted.

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `"{file_path}:{topic_slug}"` |
| `file_path` | string | Relative to repo root |
| `topic_name` | string | Snake-case slug from extractor |
| `description` | string | Topic description — embedded text (default mode) |
| `spans` | string | JSON-encoded list of `[start, end]` line pairs |
| `vector` | list<float32>[4096] | qwen3-embedding:8b dense embedding |
| `embed_model` | string | e.g. `"qwen3-embedding:8b"` |
| `embed_dim` | int32 | 4096 |
| `embed_mode` | string | `"description"` or `"description_plus_spans"` |
| `embedding_timestamp` | string | ISO 8601 UTC |
| `extractor_model` | string | `"qwen3:14b"` or `"qwen2.5-coder:14b"` |
| `extraction_run_id` | string | UUID from Phase 1 JSONL |
| `extraction_timestamp` | string | ISO 8601 UTC |
| `file_role` | string | From Phase 1 JSONL (e.g. `"long_research_doc"`) |
| `node_kind` | string | `"extracted"` (Phase 2 default; anchor/community added in Phases 3–4) |
| `scope_tags` | string | JSON-encoded list; `"[]"` in Phase 2 |
| `segment_id` | string (nullable) | Null in Phase 2; used if chunking added in Phase 2.5 |
| `segment_range` | string (nullable) | Null in Phase 2 |

**Key design notes:**
- `spans` and `scope_tags` are JSON-encoded strings, not nested struct types — LanceDB nested types add schema complexity with no query benefit at MVP scale.
- `vector` field is named `"vector"` (not `"embedding"`) — LanceDB's default ANN builder convention.
- Forward-compat fields (`node_kind`, `scope_tags`, `segment_id`, `segment_range`) written with defaults in Phase 2 so Phase 3/4 can filter without a schema migration.
- LanceDB pin: `lancedb>=0.20,<0.29` (verified `0.25.0`) — 0.29.x has a broken `lance_namespace` import (`CreateEmptyTableRequest` not exported).
- Script renamed: `retrieval/ltg_inspect.py` (not `inspect.py` — shadows Python stdlib `inspect` module via `sys.path[0]`).
<!-- /ref:ltg-phase2-schema -->

---

<!-- ref:ltg-notes -->
## Cross-cutting notes

- **Plan reference:** `ref:plan-latent-topic-graph` in `.claude/index.md` points at the plan file. Concept paper at `ref:concept-latent-topic-graph`.
- **All calls logged:** Every extractor call goes to `~/.local/share/ollama-bridge/calls.jsonl` automatically via the ollama-bridge MCP server. Phase 1 analysis can pull structured data from there.
- **Warm-up:** Use `warm_model` MCP tool before batch extraction runs to eliminate cold-start penalties.
- **No git commits of raw Phase 1 extractions:** `retrieval/phase1-raw/` should be gitignored; scores and narrative results are committed, raw JSON outputs are reproducible and bulky.
<!-- /ref:ltg-notes -->

---

<!-- ref:ltg-phase3-decisions -->
## Phase 3 Decisions — Anchor Integration (frozen 2026-06-02, session 82)

**Full decision discussion + reasoning:** `docs/plans/ltg-phase3-decisions-discussion.md` (`ref:ltg-phase3-discussion`)
**Prereqs all clear:** extractor retrofit ✓ (session 80/81), qwen3-embedding:8b ✓ (session 73), num_ctx ✓ (session 76).

---

### Keystone — Dual-path architecture (yes)

`ref:KEY` anchors are a **parallel retrieval surface**, not merely merge-targets. Two co-existing surfaces:
- **Span-topics path** — fuzzy/discovery-oriented; ANN over LLM-extracted topic nodes; recall-oriented.
- **Ref-keys path** — precise/authoritative; over the hand-curated `ref:KEY` graph; authority-oriented.

This generalizes concept-paper property #4 (anchor stratification) from binary anchor-vs-extracted into configurable provenance-class weighting. Both surfaces must stay independently queryable for Phase 6 routing.

---

### D2 — Anchor scope: repo-wide (A)

Walk all `*.md` files in the repo via: `grep -rnoE '<!-- ref:[a-z0-9-]+ -->' . --include='*.md'`. This gives `file:line:marker` — both source-file path and line number in one pass.

**Not `ref-lookup.sh --list`** — it emits key names only, no file paths (verified session 82). Ingestion must use the repo grep.

**Safety filter (mandatory):** exclude `.claude/local/` and all gitignored/sensitive paths from the grep results before ingesting. No ref block from a sensitive path should become an anchor node.

**Integrity check:** "every ref key found by the ingestion grep in tracked, non-sensitive files appears as at least one anchor node." The check universe is the grep output after filtering — not literally "every key in the repo."

**Empirical basis (session 81):** only 2 of 138 ref keys live inside the 8 extracted corpus files; orphan anchors cause no merge noise (nothing to merge with). The noise argument for corpus-scoped ingestion (option B) is dissolved. The ref-path needs the whole ref graph to function as an authoritative surface — corpus scoping would only produce tautological self-summary merges.

---

### D5 — Merge representation: alias-link, M:N

Physical merge (row mutation) is incompatible with the dual-path architecture — it destroys the standalone anchor as a ref-path node. Both rows must survive.

**Representation:**
- Anchor row: `node_kind = anchor`, `confidence = 1.0`, `anchor_key = "ref:KEY"`.
- Topic row: `node_kind = extracted`, `confidence = 0.7` (unchanged on alias), `alias_of = JSON list`.
- `alias_of` stores a **JSON-encoded list of anchor keys** (e.g., `'["ref:concept-ltg", "ref:plan-ltg"]'`). A scalar is insufficient — M:N multiplicity observed in probe: both `ref:concept-ltg` and `ref:plan-ltg` alias the same two topics.

**`node_kind` update:** drop `merged` from the enum. `node_kind ∈ {extracted, anchor}` (Phase 3; `community` added in Phase 4). Alias state = `alias_of != null`. Keeping `merged` would introduce a redundant second source of truth (with `alias_of`) that can diverge on partial writes and creates a Phase 4 migration burden.

**Phase 4 flag:** `alias_of` on the topic row is a proto-edge — a `same_as`/`alias` edge at confidence ~1.0 produced early. ~~Phase 4 will relocate it to the edge table.~~ **Updated session 101 (P4-D6):** Phase 4 *projects* it into `same_as` edges at graph build — the column stays as the anchors-rebuild artifact; consumers read the edge table only. See "Phase 4 decisions" below. No downstream code should hard-depend on the topic-row location.

**Anchor row field population (all Phase 2 fields + Phase 3 additions):**

| Field | Anchor value | Notes |
|---|---|---|
| `id` | `anchor_key` | Globally unique; used by integrity check |
| `file_path` | Source file from ingestion grep | `file:line` → `file` part |
| `topic_name` | Snake-case of bare key | e.g., `concept_latent_topic_graph` |
| `description` | `mechanical+key` description string | The embedded text |
| `spans` | `"[[start_line, start_line]]"` | Single-line point; grep returns start line; raw body re-derived from `file_path`+`spans` (satisfies D3 retrieval-payload) |
| `vector` | 4096-dim embedding of `mechanical+key` description | Same embedding model as topics |
| `embed_model` | `"qwen3-embedding:8b"` | |
| `embed_dim` | `4096` | |
| `embed_mode` | `"description"` | `mechanical+key` is a description |
| `embedding_timestamp` | ISO 8601 UTC at ingestion time | |
| `extractor_model` | `""` | Not extracted; leave empty |
| `extraction_run_id` | `""` | Not extracted |
| `extraction_timestamp` | `""` | Not extracted |
| `file_role` | `"anchor"` | Distinct from topic `file_role` values |
| `node_kind` | `"anchor"` | |
| `scope_tags` | `"[]"` | Phase 3 default |
| `segment_id` | `null` | |
| `segment_range` | `null` | |
| `source_class` | `"anchor_ref"` | Phase 3 addition |
| `confidence` | `1.0` | Phase 3 addition; structural authority |
| `anchor_key` | `"ref:KEY"` | Phase 3 addition; full key string |
| `alias_of` | `null` | Phase 3 addition; anchors do not alias other anchors |

**Multiplicity:** many topics → one anchor (link all above threshold); one topic → many anchors (JSON list). Both directions confirmed in probe data.

---

### D1 — Confidence model: capture fields now, defer tuning (C)

Three distinct concepts — do not smear:
1. **Retrieval weight** — config-keyed by `source_class`; ranking multiplier. Phase 5 tunes.
2. **Node provenance confidence** — "how much do I trust this node exists as stated." **Phase 3 writes this.**
3. **Edge confidence** — anchor edge 1.0, extracted edge = similarity. **Phase 4**, not Phase 3.

**`confidence` field in Phase 3 = node provenance (#2) only.** Not edge-weight, not retrieval-weight.

Values:
- Anchor: `1.0` — **structural authority** (follows explicit `<!-- ref:KEY -->` convention; likely PR-reviewed). NOT "human-declared" — most anchors in this repo were added by LLMs. A future `human_reviewed` boolean could split this if the distinction becomes load-bearing. Deferred.
- Extracted: `0.7` — LLM-extracted default. Placeholder chosen for "reliable but uncertain." Nothing consumes it until Phase 4/5.
- **Aliasing does NOT modify `topic.confidence`.** The plan's "merged nodes preserve anchor confidence" was written for physical merge. Under alias-link, 1.0 lives on the anchor row. The aliased topic row keeps 0.7 — it is still LLM-extracted; an alias link changes the relationship, not the provenance.

---

### D1b — Taxonomy granularity: config projection, coarse start

`source_class` for an extracted node is a deterministic function of `(file_path, node_kind)` — stored fields. So the taxonomy is a **config-defined mapping**, not a data property.

Start coarse: `anchor_ref` vs `topic_extracted`. Add QUICK/KNOWLEDGE split or other sub-classes via a config edit + ~3s re-tag whenever wanted. No migration needed.

**Store `source_class` denormalized** (string column) — cheap, makes `ltg_inspect` filtering simple (`WHERE source_class = 'anchor_ref'`). Config mapping is the source of truth; the column is a convenience cache.

`node_kind` and `source_class` are **separate axes**: `node_kind` = provenance/origin; `source_class` = content-type-for-weighting. They coincide only on the anchor row.

---

### D3 — Anchor description for embedding: `mechanical+key`

**Default method:** `key_name (hyphenated, as-is) + heading + first_non_metadata_prose_line`

```
description = f"{bare_key}: {heading} — {first_prose_line}"
```

**Key-name inclusion is load-bearing.** Probe confirmed (session 82, 6 methods):
- `ref:plan-ltg` mechanical (body only): top cosine 0.822, 0 merges. Key name rescues: 0.898/0.861, 2 merges.
- Hyphenated key name (`key_only`) outperforms space-normalized (`key_words`) consistently — qwen3-embedding:8b treats hyphenated identifiers as meaningful compound units. **Do not space-normalize key names.**

**`parse_first_prose_line` skip rules** (already implemented in probe): skip blank lines, italic-only metadata (`*...*`), sub-headings (`##`+), horizontal rules (`---`), HTML comment markers. `plan-ltg`'s first prose line was `**Status:** Ready for execution` — an operational line. Key-name inclusion compensates without needing LLM escalation.

**Escalation:** LLM one-liner fallback if a key's top merge scores are **weak** (not based on first-line classification). Detection mechanics belong in `anchors.py`. The `concept-` / `plan-` naming prefix is a free signal for anchors likely to need escalation.

**`key_only` as fast fallback:** key name alone (no body) gets 2 merges on concept-type anchors, 1 on plan-type. Useful for a batch/no-LLM mode.

**Provisional hedge:** all positive merges in the probe were LTG-self-referential (key tokens `latent-topic-graph`, `ltg-` appear directly in target topics — the most favorable case). False-merge precision on generically-named anchors (`ref:git-safety`, `ref:patterns-index`) is **untested**. Key-name inclusion may cost precision on those. Recheck at Phase 2.5.

---

### D6 — Acceptance

1. **Sanity check:** `ref:smart-rag-research` and `ref:rag-repowise` (the only 2 of 138 ref keys inside the 8 extracted corpus files) merge with topics from their own files. Largely tautological (self-summary blocks) — exercises embedding pipeline, not the anchor-merge mechanism. Fires trivially.

2. **Real test (probe-verified, provisional):** Cross-file merges from orphan anchors:
   - `ref:concept-ltg` ↔ `.memories/QUICK.md::ltg_implementation` (cosine 0.972) + `.memories/KNOWLEDGE.md::latent_topic_graph` (0.970) — both via `mechanical+key`.
   - `ref:plan-ltg` ↔ `.memories/QUICK.md::ltg_implementation` (0.898) + `.memories/KNOWLEDGE.md::latent_topic_graph` (0.861) — both via `mechanical+key`.
   - These are **abstract-to-abstract** merges (concept/plan anchor ↔ `.memories/` summary of the same concept). The harder cross-pollination case (anchor ↔ incidental applied mention, e.g., `graph_exploitation` at 0.836) sits below threshold. That is the Phase 2.5 story.
   - Provisional: validated on LTG-self-referential anchors; broad validation defers to Phase 2.5.
   - **M:N validated in data:** both concept and plan anchors alias the same two topics — `alias_of` as JSON list is correct.

3. **Honest orphan example:** `ref:ltg-corpus` consistently no-merge (0.619–0.816 across all 6 methods). Correct — corpus-scope is a meta-decision not reflected in extracted content.

4. **Stale corpus note:** the 8 corpus files have likely changed since Phase 2 extraction. Phase 3 anchor integration runs against the current snapshot. If re-extraction runs before Phase 2.5, re-run anchor linking against fresh topics.

---

### D7 — Path-selection binding time: deferred to Phase 6

Phase 3's only obligation: **don't foreclose.** Store both surfaces (anchor rows + topic rows), keep them linked via `alias_of`. D2=A + D5=alias-link already deliver this.

Phase 6 (`retrieve_context`) is the dual-path consumer and the correct home for the routing decision. Lean for Phase 6: query-time routing (one index, blend per query class via `config.yaml` weight table) — strictly more expressive, near-zero cost at current scale.

---

### New schema fields (extending `ref:ltg-phase2-schema`)

| Field | Type | Default | Notes |
|---|---|---|---|
| `source_class` | string | `"topic_extracted"` / `"anchor_ref"` | Denormalized; config-projection of `(file_path, node_kind)`; coarse to start |
| `confidence` | float | `0.7` (extracted), `1.0` (anchor) | Node-provenance only. Not edge-weight. Not upgraded on alias. |
| `anchor_key` | string (nullable) | `null` | The `ref:KEY` string for anchor rows |
| `alias_of` | string (nullable) | `null` | JSON-encoded list of anchor keys on topic rows. Phase 4 relocates to edge table. |

---

### Threshold mechanics

- **cosine 0.85 → L2 ≤ 0.5477**: formula `L2 = sqrt(2 × (1 − cosine))`, valid only for unit-normalized vectors.
- **Unit normalization confirmed**: qwen3-embedding:8b outputs unit-normalized vectors (probe: norm = 0.999999–1.000000 across all methods). The L2↔cosine conversion is valid.
- **Probe distribution (3 anchors, session 82):** strong merges at cosine 0.86–0.98; noise floor 0.81–0.84; ~0.05 precision margin. `graph_exploitation` at cosine 0.836 is arguably a real semantic relation excluded for precision — the precision/recall tension is real.
- **Provisional:** threshold set from a 3-anchor probe on LTG-self-referential anchors. Recalibrate from the observed full-distribution at Phase 2.5.
- **Register-match diagnostic:** if the 2 in-corpus sanity-check merges come back weak, check register-mismatch first (heading-only vs LLM-summary) before touching the threshold.

---

### Phase integration notes

- **Phase 4:** `alias_of` links are proto-edges (anchor-topic alias edge, confidence ~1.0). Phase 4 *projects* them into the edge table when building the graph (P4-D6: projection, not relocation — the column stays). Anchor↔anchor edges land as mention-based `references` edges (P4-D3, a superset of the original "index.md cross-references" phrasing). Decisions frozen session 101 → "Phase 4 decisions" below.
- **Phase 5:** `source_class` weights get tuned against a retrieval loop. Phase 3 lands the field; Phase 5 sets non-default values.
- **Phase 6:** dual-path `retrieve_context` consumer; D7 routing decision lives here.
- **Phase 2.5:** threshold recalibration, key-name weighting recheck (false-merge precision on generic anchors), broad merge validation (non-LTG corpus), stale-corpus re-extraction.
<!-- /ref:ltg-phase3-decisions -->

---

<!-- ref:ltg-phase4-decisions -->
## Phase 4 decisions — graph + communities (session 101, 2026-07-02)

Frozen before implementation. Full elaboration, task breakdown, and risks:
`docs/plans/ltg-phase4-graph-communities.md` (`ref:ltg-phase4-plan`).

| # | Decision | Locked value | Key reason |
|---|----------|--------------|------------|
| P4-D1 | Similarity computation | Exact (`M @ M.T`, unit-normalized) | 1018×4096 is one matmul (~100–300 ms, 8 MB); ANN's silent recall loss can disconnect nodes from communities. Mirrors Phase-3 exact-matching rationale. Revisit at ~10k nodes (with `ref:ltg-graph-lib`). |
| P4-D2 | Similarity-edge retention | `tau_floor` + union top-K, configurable (`graph:` section, `retrieval/config.yaml`) | Floor kills manufactured edges in sparse regions; cap kills the archive hairball (51% of corpus is mutually-similar session logs). Values frozen from a Step-0 degree-distribution probe, not guessed. Mutual-kNN is the tightening lever. |
| P4-D3 | Anchor↔anchor `references` edges | Mention-based, repo-wide: scan each ref block's body for other known `ref:KEY` mentions (self excluded); directed, weight 1.0 | Faithful superset of "index.md cross-refs"; table co-location alone is not a semantic relation. Bodies re-read via `_read_block_lines` (the frozen `Anchor` dataclass carries no body). |
| P4-D4 | Edge storage | New LanceDB `edges` table in `retrieval/index/`; undirected kinds stored once, canonical `src_id < dst_id` | Pure-LanceDB storage decision (`ref:ltg-storage-layout`) extended to edges. Edge-confidence == `weight` (cosine for `similarity`, 1.0 for `same_as`/`references`) — resolves the Phase-3 "edge confidence" deferral. |
| P4-D5 | Community storage | Nullable `community_coarse`/`community_fine` int32 columns on the nodes table; all writers default null | Anchors rebuild rewrites the nodes table → nullable + wipe-then-regenerate avoids writer coupling. Rebuild order: extract → embed → store → anchors → graph → communities. Separate membership table only if Phase 5 needs community metadata. `node_kind="community"` stays reserved, unused. |
| P4-D6 | `alias_of` handling | **Projection, not relocation** — column stays as the anchors-rebuild artifact; `graph.py` projects it to `same_as` edges; consumers read edges only | Removing the column would couple graph-build into the anchors rebuild flow and force a schema migration; projection honors "nothing depends on the row location" at zero migration cost. Supersedes the Phase-3 "relocate" phrasing above. |
| P4-D7 | Community detection | networkx → igraph conversion; `leidenalg` `RBConfigurationVertexPartition`, weighted, fixed seed; two configurable resolutions (provisional 0.5 / 1.5) | Graph lib frozen at Phase 0 (`ref:ltg-graph-lib`); seed makes partitions reproducible; resolutions are corpus-relative — the acceptance walk-through tunes them. |

**Related session-101 verdict:** T-63 (near-miss tuning) is NOT a Phase-4 blocker — session-96 calibration shows sub-0.85 near-misses are coincidental topical adjacency; the one real miss (`plan-latent-topic-graph` @ 0.8379) still surfaces as a ~0.84 `similarity` edge. Phase 4's top-edge walk-through supplies T-63's tuning evidence.
<!-- /ref:ltg-phase4-decisions -->
