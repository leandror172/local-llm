# retrieval/ — Quick Memory

*Working memory for the LTG substrate. Keep under 30 lines.*

## Status

Session 59 (2026-05-04): Phase 1 **fully closed**. ref:ltg-extractor frozen: qwen3:14b prose, qwen2.5-coder:14b code.
Session 61 (2026-05-20): VRAM probe complete → **bge-m3 locked** (sequential constraint applies). → `ref:ltg-vram-probe`
Session 72 (2026-05-28): **Phase 2 complete.** Index at `retrieval/index/`, 69 topics from 8 files. 7/8 acceptance queries pass (R2 borderline — documented). Total acceptance run 2.3s. **Next: Phase 3 — anchor integration.** → `ref:ltg-phase2-findings`

## Deeper Memory → KNOWLEDGE.md

- **VRAM co-residence probe** — actual footprints, WARN verdict rationale, sequential constraint, script gotcha → `ref:ltg-vram-probe`
- **Phase 1 extractor summary** — final scores, failure modes, MoE eval, determinism finding → `ref:ltg-phase1-summary`
- **Phase 0 decisions index** — all 8 frozen decisions with key reasons → `ref:ltg-phase0-decisions-index`

## What Lives Here

```
retrieval/
  DECISIONS.md              # Phase 0 decisions (frozen, session 52)
  .memories/                # This folder's working + semantic memory
  extract_topics.py         # Topic extractor runner (4 models × 8 files)
  run-vram-probe.sh         # VRAM co-residence probe script (Phase 2 gate)
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
- **Storage layout:** pure LanceDB + JSON/YAML sidecars + `ltg_inspect.py` → `ref:ltg-storage-layout`
- **Corpus:** curated subset + 2 branch points → `ref:ltg-corpus`

## Key Rules

- **Phase 1 is load-bearing.** Extractor freeze gates Phase 2. If quality is poor, iterate prompt — not model.
- **VRAM probe complete (session 61):** bge-m3 locked; sequential-only constraint applies to embed.py.
- **Raw extractions gitignored** — only scores + narrative results committed.
- **Warm models before batch runs** via `warm_model` MCP tool to eliminate cold starts.
