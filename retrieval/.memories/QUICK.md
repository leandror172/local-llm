# retrieval/ — Latent Topic Graph (RAG) — Quick Memory

*Working memory for the LTG substrate. Current-state only, keep under ~30 lines —
per-session history lives in KNOWLEDGE.md ("Phase history ledger") and session logs.*

## Current State (as of 2026-07-04, session 106)

**Phases 0–5 COMPLETE. Next: T-33 REPO SPLIT (lean decided session 106: split BEFORE Phase 6) — freeze S-D1–S-D7 → author plan → execute (1.5–2 sessions); Phase 6 then lands in the NEW repo** (`ref:ltg-plan-phase-6`).

- **T-33 split discovery** (`docs/plans/ltg-repo-split-discovery.md`, `ref:ltg-split-decisions`): imports are fully self-contained; the llm-repo coupling is data+convention — `corpus.yaml`, anchors git-grep, and the **`store.py:44` `REPO_ROOT = parent.parent` landmine** (assumes retrieval/ sits inside the corpus repo; dies at split). Engine moves; `corpus.yaml` + `index/` stay (per-repo instance data). Design stance in force NOW: engine never imports source-specific code; sources emit schema rows with distinct `source_class`. Registry/product record: `docs/ideas/ltg-model-registry-design.md` Part 2 (`ref:model-registry-library-decision`, T-76 deferred). Future code/mechanical node source: T-77 signature extractor.

- **Phase 5 `relate(a,b)` ACCEPTED** (`ref:ltg-phase5-acceptance`): `relate.py` + `run-relate.sh` + `prompts/relate_summary.txt` (role `relate_summary`, qwen3:14b think:false — the only model call; `--no-summary` skips it). Read-only over topics+edges. Verdict = **cascade** on edge evidence (same_as→strong; max similarity-kind weight ≥0.85→strong; any similarity edge→moderate; else nearest-miss matmul ≥0.55→weak); bands FINAL at provisional values. Deferred: T-73 anchor-key input, T-75 divergence view.

- **Index** (`retrieval/index/`, gitignored): 875 topics (113 files) + 147 anchors = **1022 nodes**; `edges` table **3367 edges** (3222 similarity @ frozen τ=0.70/K=10 + 28 same_as + 117 references); Leiden communities 207 coarse / 214 fine, 1022/1022 assigned.
- **Rebuild order (MANDATORY):** extract → embed → store → anchors → graph → communities. Graph + communities are pure derivation (~11 s, **zero model calls**) — always regenerate after an anchors rebuild. Anchors rebuild is idempotent since the session-102 `_topic_rows_only` fix — but store-from-embeddings first remains the canonical full path. Backups are **copy-based** since the PR #66 review round: `edges` survives an anchors rebuild (stale until regenerated); single-slot `.bak` hardening = T-71.
- **Models:** extractor qwen3:14b prose / qwen2.5-coder:14b code (frozen Phase 1); embedding qwen3-embedding:8b (4096-dim).
- **P4-D6:** consumers read relationships from the `edges` table, never the `alias_of` row column. Null community columns mean "not regenerated since last anchors rebuild".
- **Reports:** Phase 4 → `ref:ltg-phase4-degree-probe` + `ref:ltg-phase4-acceptance` + `ref:ltg-phase4-findings`; dataflow model → `ref:ltg-phase4-dataflow` (stage×state matrix — update in the same PR that changes stage behavior); Phase 2.5 → `probes/phase2.5-calibration.md`; Phase 2 → `ref:ltg-phase2-findings`.
- **Open threads:** T-33 (split — S-D1–S-D7 to freeze), T-63 (near-miss escalation — Phase 4 edge evidence now in hand), T-34 (noise-threshold wiring), T-31 (embed unification), T-35/T-38–T-41 (extraction experiments), T-76 (model-registry library, deferred w/ triggers), T-77 (signature extractor node source).

## Deeper Memory → KNOWLEDGE.md

- **Phase history ledger** — per-session completion history (moved out of this file, session 102)
- **Phase 4 findings** — hairball debunked, τ-only isolation, phantom-node staleness, rebuild-idempotency bug → `ref:ltg-phase4-findings`
- **VRAM co-residence probe** — footprints, WARN rationale, sequential constraint → `ref:ltg-vram-probe`
- **Phase 1 extractor summary** — final scores, failure modes, MoE eval, determinism → `ref:ltg-phase1-summary`
- **Phase 0 decisions index** — all 8 frozen decisions with key reasons → `ref:ltg-phase0-decisions-index`

## What Lives Here (RAG pipeline scripts)

```
retrieval/
  DECISIONS.md              # Phase 0 + 3 + 4 decisions (frozen)
  .memories/                # This folder's working + semantic memory
  config.yaml               # Two-level model/role config + graph: section (Phase 4)
  corpus.yaml               # Corpus-selection intent: roots/globs/ordered groups (Phase 2.5)
  corpus-manifest.yaml      # FROZEN resolution: 113 files + group + sha256 + commit (Phase 2.5)
  corpus_groups.py          # Shared glob matcher (assign_group/glob_to_regex) — manifest + store
  build_corpus_manifest.py  # Freeze tool: corpus.yaml → manifest (run-build-corpus-manifest.sh)
  pyproject.toml / uv.lock  # uv-managed Python 3.12 env (session 96; mirrors mcp-server)
  model_client.py           # ModelClient — embed + extract routing; embed_query(texts) (T-30)
  embed.py                  # Embedding pipeline (config-driven, Phase 2)
  store.py                  # LanceDB write path (Phase 2; schema 25 fields)
  ltg_inspect.py            # Acceptance/inspection CLI (Phase 2)
  anchors.py                # Phase 3: ref:KEY anchor ingest + alias matching (run-anchors.sh)
  graph.py                  # Phase 4: edges build (similarity/same_as/references) + degree probe (run-graph.sh)
  communities.py            # Phase 4: Leiden 2-resolution communities → nodes table (run-communities.sh)
  relate.py                 # Phase 5: pairwise relate(a,b) — aggregation, banding, prose summary (run-relate.sh)
  prompts/relate_summary.txt # Phase 5 synthesis prompt (template slots from structured dict)
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
  tests/                    # 24 test files, 377 tests (pytest via `uv run`)
  runs/                     # Extraction/embed outputs + graph run reports (large *-embeddings.jsonl gitignored)
  probes/                   # Acceptance + calibration findings markdown (ref-anchored)
  index/                    # LanceDB store: topics (1022 rows) + edges (3367) tables (gitignored)
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

- **Sequential constraint:** embed.py and infer calls must not run in parallel (bge-m3 session 61; qwen3-embedding:8b session 73).
- **Raw extractions gitignored** — only scores + narrative results committed.
- **Warm models before batch runs** via `warm_model` MCP tool to eliminate cold starts.
- **retrieval/ runs on uv Python 3.12** (session 96). Always invoke via `run-*.sh` (they `uv run --project`); never bare `python3`. Tests: `cd retrieval && uv run pytest`.
- **Corpus is config-driven** (`corpus.yaml`) and frozen per-run (`corpus-manifest.yaml`, sha256+commit). Rebuild the manifest via `run-build-corpus-manifest.sh` after any corpus.yaml change. `source_group` is derived store-time from file_path — never writer-supplied.
- **Graph thresholds live in `config.yaml graph:`** — frozen by probe (`ref:ltg-phase4-degree-probe`); re-probe before changing.
