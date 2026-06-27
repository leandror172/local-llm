# retrieval/ — Quick Memory

*Working memory for the LTG substrate. Keep under 30 lines.*

## Status

Session 59 (2026-05-04): Phase 1 **fully closed**. ref:ltg-extractor frozen: qwen3:14b prose, qwen2.5-coder:14b code.
Session 61 (2026-05-20): VRAM probe complete → bge-m3 locked (sequential constraint). → `ref:ltg-vram-probe`
Session 72 (2026-05-28): **Phase 2 complete.** Index at `retrieval/index/`, 69 topics from 8 files. 7/8 acceptance queries pass (R2 borderline). → `ref:ltg-phase2-findings`
Session 73 (2026-05-28): **M-P0b complete.** Upgraded embedding model: bge-m3 (1024-dim) → **qwen3-embedding:8b (4096-dim)**. WARN verdict (same as bge-m3 — load-time eviction only, zero query-time). Acceptance equivalent (R1/R3/R4 ✅, R2 ⚠️ same gap, relate 0.663→0.697). → `ref:ltg-embedding`
Sessions 78–80 (2026-05-29→06-01): **Extractor retrofit complete.** `routing.py`, `schemas.py`, `ModelClient` extracted; 148 tests green; parity verified end-to-end. PR open.
Session 81 (2026-06-01): Phase 3 anchor-integration DISCOVERY started. Dual-path RAG framing: `ref:KEY` anchors as a parallel retrieval surface (span-topics / ref-keys / both), configurable per-class weights; merge → alias-link (keep both rows). Empirical: 2 of 138 ref keys live in the 8 extracted files.
Session 82 (2026-06-02): **Phase 3 anchor decisions FROZEN.** All 7 decisions D1–D7 settled: dual-path RAG + alias-link confirmed. **Next: `anchors.py` TDD.**
Session 94 (2026-06-20): **Phase 3 anchor integration COMPLETE.** `anchors.py` built TDD (contract-pin + 4 subagent slices), 254 tests. store.py schema 18→22 (+source_class/confidence/anchor_key/alias_of). Live rebuild: 212 rows (69 topics + 143 anchors); concept-latent-topic-graph merges both .memories topics, M:N proven, orphan no-merge, staleness+near-miss diagnostics firing. `plan-latent-topic-graph` non-merge (0.7742 — D3 operational-metadata failure on drifted corpus) → Phase 2.5/3.5. PR #55. Plan: `docs/plans/ltg-phase3-anchors-implementation.md`.
Session 96 (2026-06-26): **Phase 2.5 corpus expansion COMPLETE.** Config-driven corpus (`corpus.yaml` → frozen `corpus-manifest.yaml`, 113 files sha256-pinned @ commit). Full rebuild: **875 topics / 113 files + 143 anchors = 1018 rows**, all `ok`/0 failures. `source_group` provenance field live (T-65 cheap half, store-time derived). **T-34 recalibration:** `COSINE_THRESHOLD=0.85` validated-keep (continuous dist; sub-0.85 near-misses = coincidental, would be false merges); noise-query threshold measured (real L2≤0.58, true-noise 0.75; recommend L2≈0.65, **documented not wired** — n=1 caveat). Generic anchors no-false-merge (Step 5 PASS). `plan-latent-topic-graph` healed 0.7742→0.8379 (still <0.85 → T-63). **retrieval/ migrated to uv Python 3.12** (T-18 slice). Findings: `probes/phase2.5-calibration.md`. **Next: Phase 4 (graph + communities) — `alias_of` are proto-edges.**
T-30 (2026-06-26): **`ModelClient.embed_query` added** (thin named-method, +2 lines). Delegates to `embed_texts(texts, role="embedding")`. 3 unit tests added. `embed_texts` stays public — T-31 will migrate callers.

## Deeper Memory → KNOWLEDGE.md

- **VRAM co-residence probe** — actual footprints, WARN verdict rationale, sequential constraint, script gotcha → `ref:ltg-vram-probe`
- **Phase 1 extractor summary** — final scores, failure modes, MoE eval, determinism finding → `ref:ltg-phase1-summary`
- **Phase 0 decisions index** — all 8 frozen decisions with key reasons → `ref:ltg-phase0-decisions-index`

## What Lives Here

```
retrieval/
  DECISIONS.md              # Phase 0 decisions (frozen, session 52)
  .memories/                # This folder's working + semantic memory
  config.yaml               # Two-level model/role config (Phase 2+)
  corpus.yaml               # Corpus-selection intent: roots/globs/ordered groups (Phase 2.5)
  corpus-manifest.yaml      # FROZEN resolution: 113 files + group + sha256 + commit (Phase 2.5)
  corpus_groups.py          # Shared glob matcher (assign_group/glob_to_regex) — manifest + store
  build_corpus_manifest.py  # Freeze tool: corpus.yaml → manifest (run-build-corpus-manifest.sh)
  pyproject.toml / uv.lock  # uv-managed Python 3.12 env (session 96; mirrors mcp-server)
  model_client.py           # ModelClient — embed + extract routing (retrofit); embed_query(texts) added T-30
  embed.py                  # Embedding pipeline (config-driven, Phase 2)
  store.py                  # LanceDB write path (Phase 2)
  ltg_inspect.py            # Acceptance/inspection CLI (Phase 2)
  routing.py                # 2-arm extractor routing (retrofit, sessions 78–80)
  schemas.py                # Pydantic schemas for extractor output (retrofit)
  sweep_extractors.py       # Batch sweep runner (retrofit)
  extract_topics.py         # Topic extractor runner (Phase 1 spike)
  viz_sweep.py              # HTML rater renderer — uses ltg-rater.template.html
  ltg-rater.template.html   # Scoring UI (Claude Design, 1600+ lines)
  spike-results.md          # Phase 1 scoring + insights (ref:ltg-phase1-results etc.)
  preflight.sh / run-preflight.sh  # Pre-run model availability check
  run-vram-probe.sh         # VRAM co-residence probe
  run-embed.sh / run-store.sh / run-inspect.sh / run-extract-topics.sh / run-sweep-extractors.sh
  prompts/extract.txt       # Structured-output extraction prompt
  tests/                    # 13 test files, 269 tests (pytest via `uv run`)
  runs/                     # Extraction/embed outputs (large *-embeddings.jsonl gitignored)
  probes/                   # Acceptance + calibration findings markdown
  index/                    # LanceDB vector store (875 topics + 143 anchors, 113 files; gitignored)
```

## Frozen Phase 0 Decisions (see DECISIONS.md for full rationale)

- **Scope:** per-repo index, federation deferred to Phase 9 → `ref:ltg-scope`
- **Embedding:** `qwen3-embedding:8b` via Ollama (4096-dim dense; upgraded from bge-m3 session 73) → `ref:ltg-embedding`
- **Vector store:** LanceDB (no separate SQL layer) → `ref:ltg-vector-store`
- **Graph lib:** networkx + leidenalg → `ref:ltg-graph-lib`
- **Extractor:** empirical A/B in Phase 1, no pre-commit → `ref:ltg-extractor`
- **Placement:** `retrieval/` top-level directory → `ref:ltg-placement`
- **Storage layout:** pure LanceDB + JSON/YAML sidecars + `ltg_inspect.py` → `ref:ltg-storage-layout`
- **Corpus:** curated subset + 2 branch points → `ref:ltg-corpus`

## Key Rules

- **Phase 1 is load-bearing.** Extractor freeze gates Phase 2. If quality is poor, iterate prompt — not model.
- **Sequential constraint:** embed.py and infer calls must not run in parallel. Applies to both bge-m3 (session 61) and qwen3-embedding:8b (session 73).
- **Raw extractions gitignored** — only scores + narrative results committed.
- **Warm models before batch runs** via `warm_model` MCP tool to eliminate cold starts.
- **retrieval/ runs on uv Python 3.12** (session 96). Always invoke via `run-*.sh` (they `uv run --project`); never bare `python3`. Tests: `cd retrieval && uv run pytest`.
- **Corpus is config-driven** (`corpus.yaml`) and frozen per-run (`corpus-manifest.yaml`, sha256+commit). Re-extraction reads the manifest; rebuild it via `run-build-corpus-manifest.sh` after any corpus.yaml change. `source_group` is derived store-time from file_path — never writer-supplied.
