# ltg/ — llm repo's LTG instance — Knowledge (Semantic Memory)

*Instance-specific accumulated knowledge: values measured/frozen on THIS corpus
and gotchas for operating THIS index. Engine knowledge (phase findings, design
decisions, API gotchas) lives in the sibling `latent-topic-graph` repo:
`.memories/KNOWLEDGE.md`, `DECISIONS.md`, `probes/`.*

## Corpus scope + groups (frozen session 95/96; edit corpus.yaml with care)

- Scope: `.md` only (code deferred to Phase 8); `.claude/archive/` IN as its own
  `archive` group (~51% of corpus); `.claude/local/` OUT (gitignored → never
  enters via `git ls-files` resolution); no chunking (largest file < 16K ceiling).
- `groups` are **first-match-wins**: the `.memories` and `.claude/archive` rules
  MUST stay ahead of the `.claude/**` catch-all.
- After ANY corpus.yaml change: `run-build-corpus-manifest.sh` (freeze = commit
  SHA + per-file sha256; re-hash detects drift). `source_group` is store-time
  derived from these groups — never writer-supplied.

## Calibration values frozen on THIS corpus (provenance for revisits)

- **Anchor `COSINE_THRESHOLD=0.85` — validated-keep** (session 96, n=143):
  best-match cosine is *continuous* (median 0.755, p90 0.863), not bimodal;
  lowering adds false merges, not recall. Full data: engine repo
  `probes/phase2.5-calibration.md`.
- **Noise-query threshold — recommend L2≈0.70 (cosine≈0.76)**: real queries
  ≤0.58, pure-noise ≥0.91 (n=9, ~0.33-wide empty gap). Wiring = T-34 (engine
  repo tasks); the value is corpus-grounded, re-measure if corpus shifts a lot.
- **Graph τ=0.70 / K=10 — probe-frozen** (session 102 degree probe, engine
  `probes/phase4-degree-probe.md`): archive hairball debunked (24.4% edge share
  vs 18.3% random); isolation is τ-only (K can't reconnect below the floor).
  **Re-probe (`run-graph.sh --degree-probe`) before touching `config.yaml graph:`.**

## Known retrieval gaps (this corpus)

- **R2 borderline** ("memory across sessions"): `.memories/QUICK.md` topics don't
  say "session memory" explicitly; `.claude/plan-v2.md` wins. Documented-and-
  proceed since Phase 2; fix option = `embed_mode=description_plus_spans`.
- **Dense cross-ref-index files** (e.g. old `smart-rag-index.md` class): qwen3:14b
  deterministic off-by-one on single-line bullet lists — containment/post-pass
  guard still deferred (llm tasks). Affects extraction quality, not routing.
- **~26 anchors in the 0.80–0.85 near-miss band** (incl. `plan-latent-topic-graph`
  @ 0.8379) — T-63 Phase 3.5 escalation targets, visible as similarity edges.

## Operating this index

- **Acceptance is delta-shaped, not equality-shaped** (SP-10 lesson): this index
  legitimately *shrinks* when docs move out of the repo — trace removed
  anchor_keys to moved/deleted files instead of expecting stable counts.
  Post-split baseline (2026-07-05): 976 nodes (875 topics/113 files + 101
  anchors) / 3067 edges; record in engine `probes/split-acceptance.md`.
- **`runs/` contains TRACKED Phase-1 sweep artifacts** — never glob-delete
  (`rm runs/2026*.jsonl` once caught 4 tracked files; `git status` before rm).
- **Backups are single-slot**: `run-rebuild-all.sh` takes ONE authoritative
  pre-rebuild `index.bak`; ad-hoc stage runs use suffixed slots
  (`.bak-store`/`.bak-anchors`/`.bak-communities`), one writer per slot.
- **Sequential constraint:** embed and infer must not run in parallel (12GB
  VRAM; probe evidence in engine KNOWLEDGE `ref:ltg-vram-probe`).
