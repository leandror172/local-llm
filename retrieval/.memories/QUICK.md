# retrieval/ — Quick Memory

*Working memory for the LTG substrate. Keep under 30 lines.*

## Status

Session 59 (2026-05-04): Phase 1 **fully closed**. All 3 freeze gates cleared.
Determinism: Branch C (off-by-one model property, 5 runs all ≤3/7, Jaccard 0.60).
MoE: qwen3:30b-a3b unusable (TTFT > 9 min); qwen3-coder:30b 2.06 adj. < 2.2.
**ref:ltg-extractor frozen**: qwen3:14b prose, qwen2.5-coder:14b code.
Phase 2 next: VRAM co-residence probe + LanceDB + bge-m3.

## What Lives Here

```
retrieval/
  DECISIONS.md              # Phase 0 decisions (frozen, session 52)
  .memories/                # This folder's working + semantic memory
  extract_topics.py         # Topic extractor runner (4 models × 8 files)
  viz_sweep.py              # HTML rater renderer — uses ltg-rater.template.html
  ltg-rater.template.html   # Scoring UI (Claude Design, 1600+ lines)
  spike-results.md          # Phase 1 scoring + insights (ref:ltg-phase1-results etc.)
  prompts/extract.txt       # Structured-output extraction prompt
  runs/                     # Sweep outputs: JSONL + rendered HTML + design slice
```

## Frozen Phase 0 Decisions (see DECISIONS.md for full rationale)

- **Scope:** per-repo index, federation deferred to Phase 9 → `ref:ltg-scope`
- **Embedding:** `bge-m3` via Ollama (1024-dim dense) → `ref:ltg-embedding`
- **Vector store:** LanceDB (no separate SQL layer) → `ref:ltg-vector-store`
- **Graph lib:** networkx + leidenalg → `ref:ltg-graph-lib`
- **Extractor:** empirical A/B in Phase 1, no pre-commit → `ref:ltg-extractor`
- **Placement:** `retrieval/` top-level directory → `ref:ltg-placement`
- **Storage layout:** pure LanceDB + JSON/YAML sidecars + `inspect.py` → `ref:ltg-storage-layout`
- **Corpus:** curated subset + 2 branch points → `ref:ltg-corpus`

## Key Rules

- **Phase 1 is load-bearing.** Extractor freeze gates Phase 2. If quality is poor, iterate prompt — not model.
- **VRAM co-residence probe required** before locking bge-m3 (qwen3:14b + bge-m3 ≈ 12GB on 12GB card).
- **Raw extractions gitignored** — only scores + narrative results committed.
- **Warm models before batch runs** via `warm_model` MCP tool to eliminate cold starts.
