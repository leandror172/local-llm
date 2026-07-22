# ltg/ — llm repo's LTG instance — Quick Memory

*Instance working memory. The ENGINE (code, tests, phase docs, DECISIONS.md)
lives in the sibling `latent-topic-graph` repo — split out session 107 (T-33,
`docs/plans/ltg-repo-split.md`, `ref:ltg-split-frozen-decisions`).*

## What this directory is

The llm repo's LTG **instance data**: `corpus.yaml` (intent) →
`corpus-manifest.yaml` (frozen resolution) · `config.yaml` (models/roles +
`graph:` thresholds τ=0.70/K=10, probed on THIS corpus) · `index/` (derived
LanceDB, gitignored) · `runs/` (extraction/embed artifacts) · `run-*.sh`
wrappers (cd here, `uv run --project .` → engine entry points via the editable
path-dependency in `pyproject.toml`).

## Current index state

- **Live, queried 2026-07-21** (`run-inspect.sh --stats` + newest `runs/graph-*.json`):
  **1357 nodes** over **190 files**, all embedded with `qwen3-embedding:8b`; edges
  **3779** (3624 similarity τ=0.70/K=10 + 26 same_as + 129 references). The
  1186-topic / 171-anchor split is **inferred** from `--stats`' extractor-model
  breakdown (anchors carry no extractor), not a direct readout — no anchors run
  artifact is retained. Leiden community counts are **not** exposed by `--stats` and no
  community run artifact is retained — re-derive before citing one.
- *Historical marker (do not cite as current):* first post-split rebuild = SP-10
  acceptance PASS (2026-07-05) at 875 topics / 113 files / 101 anchors / 3067 edges,
  all 49 removed anchors traced to moved files (record: engine repo
  `probes/split-acceptance.md`). The corpus has grown ~40% since.
- **Refresh discipline:** these counts drift with every corpus change. They were ~40%
  stale when checked on 2026-07-21. Re-query rather than quoting this block.
- **Rebuild order (MANDATORY):** extract → embed → store → anchors → graph →
  communities; `run-rebuild-all.sh --embeddings runs/<tag>-embeddings.jsonl`
  covers the derivation stages (store onward).
- Corpus root = the llm repo (wrappers pass `--repo-root ..`); instance files
  resolve against this directory (wrappers cd here).

## Rules

- Rebuild the manifest (`run-build-corpus-manifest.sh`) after any corpus.yaml
  change; `source_group` is store-time derived, never writer-supplied.
- Graph thresholds are probe-frozen — re-probe (`run-graph.sh --degree-probe`)
  before changing `config.yaml graph:`.
- Sequential constraint: embed and infer calls must not run in parallel (VRAM).
- Engine questions (schema, decisions, phase history) → sibling repo's
  `DECISIONS.md`, `docs/plans/`, `.memories/`.
- Corpus-specific knowledge (calibration values + provenance, scope rules,
  known retrieval gaps, operating gotchas) → `KNOWLEDGE.md` here.
