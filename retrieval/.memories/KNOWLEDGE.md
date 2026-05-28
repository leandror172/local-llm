# retrieval/ — Knowledge (Semantic Memory)

*Accumulated decisions and findings for the LTG substrate. Read on demand.*
*Consolidated from session logs and probe outputs — not raw notes.*

---

<!-- ref:ltg-vram-probe -->
## VRAM Co-Residence: qwen3:14b + bge-m3 (2026-05-20, session 61)

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
## VRAM Co-Residence: qwen3:14b + qwen3-embedding:8b (2026-05-28, session 73)

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
## Phase 1 Extractor — Final Findings (sessions 54–59)

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
## Phase 0 Frozen Decisions Index (session 52)

Full rationale in `retrieval/DECISIONS.md`. Summary of what was decided and why:

| Decision | Choice | Key reason |
|----------|--------|------------|
| Index scope | Per-repo; federation Phase 9 | Avoid distributed-system complexity at MVP |
| Embedding | bge-m3 via Ollama (1024-dim dense) | Ollama-native; +3-4 MTEB vs nomic; no torch install |
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
## Phase 2 — Embedding + Storage Results (2026-05-28, session 72)

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
