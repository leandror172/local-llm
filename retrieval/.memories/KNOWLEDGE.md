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
