# retrieval/ — Quick Memory

*Working memory for the LTG substrate. Keep under 30 lines.*

## Status

Session 52 (2026-04-14): Phase 0 decisions **frozen** in `DECISIONS.md`. No code yet.
Next: Phase 1 topic-extractor spike — load-bearing for everything downstream. Do not
advance to Phase 2 unless Phase 1 hits the weighted quality exit threshold (≥2.2).

## What Lives Here

```
retrieval/
  DECISIONS.md              # Phase 0 decisions (frozen, session 52)
  .memories/                # This folder's working + semantic memory
  # Coming in Phase 1:
  extract_topics.py         # Topic extractor runner
  prompts/extract.txt       # Structured-output extraction prompt
  phase1-raw/               # Per-(model, file) raw JSON (gitignored)
  phase1-scores.csv         # Rubric scores
  phase1-results.md         # Narrative summary + winner
  phase1-long-file-findings.md  # >1MB MCP wiki chunking experiment
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

- **Phase 1 is load-bearing.** If quality is poor, iterate the prompt — not the model.
- **VRAM co-residence probe required** before locking bge-m3 (qwen3:14b + bge-m3 ≈ 12GB on 12GB card).
- **Raw extractions gitignored** — only scores + narrative results committed.
- **Warm models before batch runs** via `warm_model` MCP tool to eliminate cold starts.
