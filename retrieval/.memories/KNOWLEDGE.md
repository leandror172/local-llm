# retrieval/ — Latent Topic Graph (RAG) — Knowledge (Semantic Memory)

*Accumulated decisions and findings for the LTG substrate. Read on demand.*
*Consolidated from session logs and probe outputs — not raw notes.*

---

<!-- ref:ltg-phase2.5-corpus -->
## LTG RAG Phase 2.5: Full-Corpus Expansion + Retrieval Calibration (2026-06-26, session 96)

**Outcome:** Index moved from an 8-file/69-topic snapshot to the full curated MVP corpus: **875 topics from 113 files + 143 anchors = 1018 rows**. Extraction 113/113 `ok`, 0 failures, 875 topics; embed 875 rows 4096-dim, 0 failed, 54.7s. Closes T-36; lands T-65 cheap half; measurement-closes T-34.

### Corpus is now config-driven + frozen
- `corpus.yaml` declares **intent**: `include_roots` (+ individually-named `.claude` files), `include_globs` (`**/.memories/*.md` — scattered across 7 folders), `exclude_globs` (`.claude/local/**`, `*.bak*`), `file_extensions` (`.md` only — code deferred to Phase 8), and ordered `groups` (first-match-wins; `.memories` and `.claude/archive` rules MUST precede the `.claude/**` catch-all).
- `build_corpus_manifest.py` resolves it against `git ls-files` (tracked content only — gitignored `.claude/local/` never enters) and freezes the **resolution**: `corpus-manifest.yaml` records commit SHA + per-file sha256 + group. **No repo copy** — freeze = commit + hashes; re-hash to detect drift.
- The matcher (`glob_to_regex`, `assign_group`) lives in shared `corpus_groups.py`. **`**/` must match zero leading dirs** (`(?:.*/)?`, not `.*/`) — else root-level `.memories/*.md` is silently dropped (caught by dry-run during build).
- Corpus scope (decided session 95): `.claude/archive/` IN, tagged `archive` (~51% of corpus); `.claude/local/` OUT; no chunking (largest file < 16K ceiling).

### source_group (T-65 cheap half)
New schema field, orthogonal to `source_class`. Records WHERE a row came from (archive/docs-research/memories/docs-ideas/claude-meta/ungrouped). **Derived authoritatively at store-time** in `store.rows_to_arrow_table` from `file_path` via corpus.yaml groups — writers never supply it (so it can't drift; `test_anchors_rows` excludes it as the one store-derived field). Anchors group by their defining file (98 `ungrouped` = anchors defined outside corpus roots — correct). Phase-5 query-type weighting (T-65 full) consumes it; logic deferred.

### T-34 calibration (full findings: `probes/phase2.5-calibration.md`)
- **Anchor `COSINE_THRESHOLD=0.85` validated-keep.** Best-match cosine across 143 anchors is *continuous* (median 0.755, p90 0.863, max 0.954), not bimodal. Sub-0.85 near-misses are coincidental topical adjacency → lowering would add **false merges**, not recall. 21 genuine alias merges at ≥0.85.
- **Noise-query threshold:** real queries land L2≤0.58 (cosine≥0.83). Validated with 9 noise probes (1 tech-adjacent "Kubernetes" @ 0.746 + 8 pure off-corpus @ **0.91–1.17**, mean 1.03): real and pure-noise bands separated by a **~0.33-wide empty gap** (0.58→0.91), 0/8 below 0.65. Old `>1.0` L2 (bge-m3 era) badly stale. **Recommend L2≈0.70 (cosine≈0.76)** — mid-gap, defensible from n=9. **Wiring deferred** (only remaining T-34 work): `acceptance_mode` is record-only; add `NOISE_L2_THRESHOLD` + pass/fail assertions. The value is grounded — not blocked on data.
- **Step 5 generic-anchor precision PASS:** `ref:git-safety`/`ref:indexing-convention`/`ref:bash-wrappers` correctly no-merge; §9 false-merge risk did not materialize. Minor borderline M:N secondary links (`ref:smart-rag-research`→`user_preferences`, `ref:rag-dify`→`ollama_pipeline_configuration`) — T-63 candidates.
- **Staleness healed:** `plan-latent-topic-graph` rose 0.7742 (stale, session 94) → 0.8379 (fresh) after re-extraction — still <0.85, a clean T-63 (Phase 3.5) escalation target.

### Python 3.12 (T-18 retrieval slice)
`retrieval/` now has a uv-managed 3.12 env (`pyproject.toml` + `uv.lock`, mirrors `mcp-server`). Wrappers `uv run --project`. 269 tests green under 3.12. Benchmarks/scripts/`.claude/tools` remain on system 3.10 (repo-wide T-18 still open).
<!-- /ref:ltg-phase2.5-corpus -->

---

<!-- ref:ltg-vram-probe -->
## RAG Embedding VRAM Co-Residence: qwen3:14b + bge-m3 (2026-05-20, session 61)

**Verdict:** WARN → proceed. bge-m3 locked as embedding model.

### What was tested
Script `retrieval/run-vram-probe.sh` ran 4 stages:
1. Preflight (model availability)
2. Sequential load of qwen3:14b, then bge-m3
3. Co-residence check via `ollama ps`
4. 5 interleaved rounds of embed→infer, timed

### Findings

**VRAM footprint (actual, not nominal):**
- qwen3:14b runtime: **11,384 MiB** (weights + KV cache + activations; ~2 GB over nominal 9.3 GB)
- bge-m3: **~1,200 MiB**
- Total: ~12,584 MiB — exceeds 12,288 MiB card capacity by ~300 MiB

**Load-time behavior:** Ollama evicts qwen3:14b when bge-m3 is loaded. Both cannot
coexist in VRAM simultaneously. `ollama ps` confirmed only one model loaded at a time.

**Query-time behavior (the key question):** 5 rounds of embed→infer alternating,
rounds 2–5 timed. Zero evictions detected. Avg infer latency: **3,559 ms**. Max: 3,725 ms.
Conclusion: Ollama's LRU eviction + reload cycle is fast enough that interleaved use is
viable in practice — the model stays warm across a sequence of calls even with embeds
between them.

### Constraint derived

**embed.py must be sequential — no parallel embed+infer calls.**

The indexing pipeline (extract → embed → store) is inherently sequential anyway, so
this is not a practical limitation. The only scenario where parallelism could matter is
real-time query (embed query → infer synthesis simultaneously), and the probe shows
that scenario is also fine with sequential calls.

### Script note
The probe script hit a `set -euo pipefail` + SIGPIPE bug in the preflight check:
`ollama list | grep -q "bge-m3"` fails because bge-m3 is the first entry — grep exits
early on match, sends SIGPIPE to ollama, pipefail propagates exit 141. Fixed by
capturing `$(ollama list)` first, then grepping the variable. A common trap with
`grep -q` inside pipefail scripts.

**Fallback (not needed):** If a future Ollama version or model update pushes runtime
footprint higher and query-time eviction appears, drop to `mxbai-embed-large` (~670 MB)
and re-run `retrieval/run-vram-probe.sh`.
<!-- /ref:ltg-vram-probe -->

---

<!-- ref:ltg-m-p0b-probe -->
## RAG Embedding VRAM Co-Residence: qwen3:14b + qwen3-embedding:8b (2026-05-28, session 73)

**Verdict:** WARN → proceed. qwen3-embedding:8b adopted. Sequential constraint unchanged.

### What was tested
Same script (`retrieval/run-vram-probe.sh`) with `EMBED_MODEL=qwen3-embedding:8b`.

### Findings

**VRAM footprint:**
- qwen3:14b runtime: **11,499 MiB** (consistent with session 61)
- qwen3-embedding:8b: **~5,000 MiB** (vs bge-m3's 1,200 MiB — 4× larger)
- Combined exceeds 12,288 MiB — eviction at load time confirmed

**Load-time behavior:** Same as bge-m3 — Ollama evicts qwen3:14b when embedding model loads. Only one in VRAM at a time.

**Query-time behavior:** 5 interleaved rounds. Zero evictions. Avg infer latency: **4,168 ms** (vs 3,559 ms with bge-m3 — +18% overhead, acceptable). Max: 4,850 ms.

### Acceptance results (post-upgrade)
- R1/R3/R4 ✅ — same correct top-1 files as Phase 2
- R2 ⚠️ borderline — same corpus gap (`.memories/QUICK.md` doesn't surface "session memory" explicitly)
- P1 relate ✅ — mean similarity improved 0.663 → 0.697
- N-threshold note: original > 1.0 threshold was calibrated for bge-m3's 1024-dim L2 scale. Noise queries land at 0.84–0.98 in 4096-dim space — proportionally equivalent, threshold recalibration deferred to Phase 3.

Probe: `retrieval/probes/20260528_202835.md`

### Script fix (session 73)
`run-vram-probe.sh` hardcoded `EMBED_MODEL="bge-m3"` — env override was silently ignored. Fixed to `EMBED_MODEL="${EMBED_MODEL:-bge-m3}"` (bash default-if-unset idiom). Both model variables now honor env overrides.

### Code fix (session 73)
`embed.py` hardcoded `embed_dim=1024` in two `main()` call sites. Fixed to read `embed_dim` from `config.yaml` via `load_config`. `store.py` hardcoded `1024` in `SCHEMA` constant and `rows_to_arrow_table`. Fixed: `SCHEMA` → `build_schema(embed_dim: int)` function; `rows_to_arrow_table` infers dim from first input row's `embed_dim` field.
<!-- /ref:ltg-m-p0b-probe -->

---

<!-- ref:ltg-phase1-summary -->
## LTG Topic-Extractor Model Evaluation (RAG ingestion) — Final Findings (sessions 54–59)

**Frozen decision:** 2-arm routing — `qwen3:14b` for prose, `qwen2.5-coder:14b` for code.

### Scores (adjusted, 8-file average)

| Model | Claude track | User track | Verdict |
|-------|-------------|------------|---------|
| qwen3:14b | 2.44 | 2.61 | ✅ winner |
| qwen3:8b | 2.27 | 2.63 | ✅ backup (not adopted — see below) |
| qwen2.5-coder:14b | 1.76 | 2.16 | ✅ code arm (above threshold on user track) |
| gemma3:12b | 1.61 | 1.82 | ❌ |

### Key failure modes (load-bearing for Phase 2 prompt design)

- **qwen3:14b off-by-one on dense single-line bullets** (confirmed deterministic, 5/5 runs):
  cross-reference index files (e.g. `smart-rag-index.md`) trigger systematic span boundary
  errors. Mitigation: containment/post-pass guard at retrieval time. Does not affect prose files.
- **qwen3:8b whole-section drops:** structurally drops entire sections (confirmed in 2 files,
  ~22% content loss). Rubric underpenalizes this (dim 8 = 10% weight only). Not adopted
  for production despite strong user-track score because the failure mode is silent and
  hard to detect at retrieval time.
- **qwen2.5-coder:14b rule-3 violations on prose:** generates structural-meta topics
  ("all topics in file X") rather than atomic topics. Acceptable for code files where
  structure is the signal; unacceptable for prose.
- **gemma3:12b boilerplate:** low coverage (some files 34%), conflation of distinct concepts.

### MoE eval (session 59, both rejected)

- **qwen3:30b-a3b:** TTFT > 9 min on this hardware. Ollama MoE hybrid offload loads all
  attention layers during prefill at RAM bus speeds. Architecture limitation, not config.
- **qwen3-coder:30b:** Completed 8/8 files at 6.7–14.8 tok/s. Adjusted score 2.06 < 2.2
  threshold. Speed penalty universal. Does not displace qwen3:14b.

### Determinism finding (Branch C, session 59)

qwen3:14b off-by-one on `smart-rag-index.md` is a model property, not sampling variance.
5 runs: all scored ≤3/7 on the 7 cross-cutting-pattern bullets. Jaccard median 0.600.
Three deterministic failure modes: semantic conflation (B2), index shift −1 (B6), structural
absorption (B5). → containment/post-pass guard is the mitigation, not a routing change.

**Full details:** `retrieval/spike-results.md` (ref keys: `ltg-phase1-results`, `ltg-phase1-insights`,
`ltg-phase1-routing-hypothesis`, `ltg-phase1-determinism-smart-rag-index`, `ltg-phase1-moe-eval`)
<!-- /ref:ltg-phase1-summary -->

---

<!-- ref:ltg-phase0-decisions-index -->
## LTG RAG Architecture Decisions (embeddings, vector store, graph) — Phase 0 Index (session 52)

Full rationale in `retrieval/DECISIONS.md`. Summary of what was decided and why:

| Decision | Choice | Key reason |
|----------|--------|------------|
| Index scope | Per-repo; federation Phase 9 | Avoid distributed-system complexity at MVP |
| Embedding | qwen3-embedding:8b via Ollama (4096-dim dense) | Phase 0 chose bge-m3; upgraded session 73 (M-P0b) — MTEB 63.0→70.58; see `ref:ltg-m-p0b-probe` |
| Vector store | LanceDB (no SQL layer) | Embedded, Arrow-backed, filter+ANN in one query |
| Graph lib | networkx + leidenalg | Sufficient for MVP corpus; no server overhead |
| Extractor | Empirical A/B Phase 1 → frozen | See `ref:ltg-phase1-summary` above |
| Code placement | `retrieval/` top-level | Separate from src; importable; own DECISIONS.md |
| Storage layout | Pure LanceDB + JSON/YAML sidecars | Single store = single ingest path = fewer sync bugs |
| MVP corpus | `docs/research/` + `docs/ideas/` + `.claude/` + `.memories/` | Highest signal density for concept validation |

Ref keys for individual decisions: `ltg-scope`, `ltg-embedding`, `ltg-vector-store`,
`ltg-graph-lib`, `ltg-extractor`, `ltg-placement`, `ltg-storage-layout`, `ltg-corpus`.
<!-- /ref:ltg-phase0-decisions-index -->

---

<!-- ref:ltg-phase2-findings -->
## LTG RAG Phase 2 — Embedding + Vector Store (LanceDB) Results (2026-05-28, session 72)

### Pipeline runs

| Step | Command | Output | Time |
|------|---------|--------|------|
| Embed | `run-embed.sh --input retrieval/runs/20260416-181839.jsonl` | `retrieval/embeddings.jsonl` | 5.2s |
| Store | `run-store.sh --input retrieval/embeddings.jsonl --index retrieval/index` | `retrieval/index/` | 1.1s |
| Acceptance | `run-inspect.sh --acceptance --output-md retrieval/probes/acceptance-2026-05-28.md` | probe markdown | 2.3s |

**Total acceptance run: 2.3s (target < 5s) ✅**

### Acceptance query results

| # | Query | Top-1 file | Top-1 L2 score | Pass? |
|---|-------|-----------|---------------|-------|
| R1 | git co-change analysis | `smart-rag-repowise.md` | 0.73 | ✅ |
| R2 | memory across sessions | `.claude/plan-v2.md` | 0.84 | ❌ borderline |
| R3 | models for topic extraction | `.claude/plan-v2.md` | 0.96 | ✅ (KNOWLEDGE.md in top-3) |
| R4 | Repowise analyzes repos | `smart-rag-repowise.md` | 0.80 | ✅ |
| N1 | expense report accuracy | `.memories/QUICK.md` | 1.08 | ✅ (L2 > 0.95 → cos < 0.55) |
| N2 | Kubernetes deployment YAML | `smart-rag-index.md` | 1.01 | ✅ |
| P1 | relate repowise vs smart-rag3 | — | mean cos 0.66 | ✅ (10 pairs > 0.55) |

**Note on scores:** LanceDB returns L2 distance (not cosine similarity). For unit-normalised vectors: `L2 = sqrt(2*(1-cosine))`. So L2 < 0.95 ≈ cosine > 0.55.

### R2 underperformance analysis

Query "how do we handle memory across sessions" — `.memories/QUICK.md`'s extracted topics (`repo_structure_and_conventions`, `prompt_decomposition`) don't mention session memory explicitly. `.claude/plan-v2.md`'s `memory_and_learning_systems` topic wins. Per plan: one borderline recall query with small divergence → document and proceed, no A/B needed.

**If R2 matters for Phase 3:** Re-embed `.memories/QUICK.md` with `embed_mode=description_plus_spans` to include span text in the vector, which would surface the "Working memory for the repo" line.

### Surprising findings

1. **`inspect.py` name collision:** `retrieval/inspect.py` shadowed Python stdlib `inspect` module via `sys.path[0]`, breaking `httpx` and `pyarrow` imports in all other retrieval scripts. Renamed to `ltg_inspect.py`.
2. **L2 vs cosine:** LanceDB defaults to L2 distance for ANN search. The plan's acceptance thresholds (cosine < 0.55) translate to L2 > 0.949 for unit-normalised vectors. Both negative queries scored L2 > 1.0 ✅.
3. **Relate preview:** No divergences between `smart-rag-repowise.md` and `smart-rag3.md` (both cover smart-RAG concepts). Mean cosine 0.663 — semantically very close. The acceptance relate file `smart-rag-claude-mem.md` was not in the Phase 1 corpus; substituted `smart-rag3.md`.
4. **qwen2.5-coder:14b timeout issue:** 3 consecutive timeouts during test generation (warm model confirmed). Escalated to qwen3:14b which generated both test functions and implementation within the 300s timeout.
<!-- /ref:ltg-phase2-findings -->

<!-- ref:ltg-phase4-findings -->
## Phase 4 — Graph + Communities (session 102, 2026-07-02)

Full findings: `probes/phase4-degree-probe.md` (T3) + `probes/phase4-acceptance.md` (T7).
Plan + decisions: `ref:ltg-phase4-plan`, `ref:ltg-phase4-decisions`.

### What was built
`graph.py` (edges build: exact matmul similarity @ frozen τ=0.70/K=10, `alias_of`→`same_as`
projection, mention-based `references`; `--degree-probe` mode; `run-graph.sh`) and
`communities.py` (networkx→igraph→Leiden RBConfiguration, seeded, coarse 0.5/fine 1.5;
`run-communities.sh`). `edges` LanceDB table (7 fields); nodes schema 23→25 (nullable
int32 `community_coarse`/`community_fine`, writers default null). Live: 3332 edges
(3189/28/115), 203 coarse / 213 fine communities, rebuild ≈11 s, zero model calls.

### Surprising findings / gotchas
1. **Archive hairball never materialized** — 24.4% archive×archive edge share vs 18.3%
   random baseline (archive = 42.8% of nodes). Union top-K caps it structurally.
2. **Isolation is τ-only.** Isolated-node count (184 @ 0.70) is identical across all K —
   union-kNN can only remove edges below the floor-graph, never add. The floor sets the
   connectivity ceiling.
3. **Phantom nodes from anchor staleness:** `references` edges scan the repo live, but
   node rows are frozen at the last anchors rebuild — anchors created since (3 of them,
   incl. Phase 4's own refs) appear as edge endpoints with no row; networkx auto-creates
   them, `write_communities` silently skips them. Benign; disappears when the documented
   rebuild order runs (anchors before graph).
4. **Backup semantics unified (PR #66 review round, 2026-07-03):** the index dir holds TWO
   tables, so `store.backup_index` is now **copy-based** (`copytree`) and single-sourced —
   the original move-then-recreate destroyed the live `edges` table on every anchors rebuild,
   and communities' private copytree backup (buggy `with_suffix('.bak')`) then clobbered the
   only surviving copy in `index.bak`. `_write_index` overwrites only `topics`; edges survives
   (still stale until regenerated). Single-slot `.bak` hardening remains T-71.
5. **Mid-file `__main__` guard:** append-driven development left the guard above later
   defs; imports (tests) never notice — only the live CLI run caught it. Guard belongs at EOF.
6. **`same_as` count ≠ merge count by design:** 21 alias-merged topics → 28 edges (7 are M:N).
7. **PR #66 review round (2026-07-03):** 9-angle review → 8 findings fixed via Opus/Sonnet
   subagents + inline: copy-based backup (item 4), `--table` silently ignored in build mode,
   zero-norm NaN guard in `_normalize_vectors`, empty-YAML `KeyError` in `load_graph_config`,
   top-k selection unified probe↔build (one vectorized mask — probe stats can't drift from the
   built graph), all LanceDB writes routed through `store.open_or_create_table`, leidenalg
   **GPL-3** recorded in new `docs/ATTRIBUTIONS.md`, dataflow model (mermaid + stage×state
   matrix) at `docs/diagrams/ltg-phase4-dataflow.md` (`ref:ltg-phase4-dataflow`). 310 tests.
   Known-not-fixed: `(?<!/)ref:` regex matches `href:`/`xref:` substrings; double full-table
   reads in build paths; networkx carried only for nx→igraph conversion.
<!-- /ref:ltg-phase4-findings -->

## Phase history ledger (moved from QUICK.md, session 102 — append new entries HERE, not in QUICK)

- Session 59 (2026-05-04): Phase 1 closed — extractor frozen (qwen3:14b prose, qwen2.5-coder:14b code). `ref:ltg-phase1-summary`
- Session 61 (2026-05-20): VRAM probe → bge-m3 locked, sequential constraint. `ref:ltg-vram-probe`
- Session 72 (2026-05-28): Phase 2 complete — 69 topics / 8 files, 7/8 acceptance. `ref:ltg-phase2-findings`
- Session 73 (2026-05-28): M-P0b — embedding upgraded bge-m3 (1024) → qwen3-embedding:8b (4096). `ref:ltg-embedding`
- Sessions 78–80: extractor retrofit (routing.py/schemas.py/ModelClient, 148 tests, parity verified).
- Sessions 81–82: Phase 3 discovery + decisions FROZEN (dual-path, alias-link M:N). `ref:ltg-phase3-decisions`
- Session 94 (2026-06-20): Phase 3 complete — anchors.py, schema 18→22, 212 rows, PR #55.
- Session 96 (2026-06-26): Phase 2.5 complete — config-driven corpus, 1018 rows (875 topics/113 files + 143 anchors), T-34 measured, uv 3.12 migration. `probes/phase2.5-calibration.md`
- T-30 (2026-06-26): `ModelClient.embed_query` named wrapper added.
- Session 101 (2026-07-02): Phase 4 designed — P4-D1–D7 frozen. `ref:ltg-phase4-decisions`
- Session 102 (2026-07-02): **Phase 4 complete** — graph.py + communities.py, edges table (3367), schema 23→25, Leiden 207/214, all acceptance PASS, anchors-rebuild idempotency bug found+fixed live. PR #66. `ref:ltg-phase4-findings`, `ref:ltg-phase4-degree-probe`, `ref:ltg-phase4-acceptance`
