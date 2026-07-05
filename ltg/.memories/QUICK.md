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

- 875 topics (113 files) + 147 anchors = 1022 nodes; edges 3367 (similarity
  τ=0.70/K=10 + same_as + references); Leiden 207 coarse / 214 fine.
  (Pre-split counts — the first post-split rebuild drops the anchors whose
  ref blocks moved to the engine repo; delta must be explainable, SP-10.)
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
