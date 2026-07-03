#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"

# LTG derivation-stage rebuild sequencer (T-71).
#
# Runs the four index-touching stages in order: store -> anchors -> graph ->
# communities. extract/embed are deliberately OUT of scope (GPU-expensive,
# run separately via run-extract-topics.sh / run-embed.sh).
#
# Backup scheme (T-71): this wrapper takes ONE authoritative backup of the
# live index into plain {index}.bak *before* running any stage, then passes
# --no-backup to every stage so nothing overwrites that slot mid-rebuild.
# {index}.bak is therefore always the last known-good full-pipeline state.
# Ad-hoc single-stage runs (store.py / anchors.py / communities.py invoked
# directly, without this wrapper) instead default to their own stage-suffixed
# slot ({index}.bak-store / .bak-anchors / .bak-communities) so they never
# clobber each other or this wrapper's .bak.
#
# Usage:
#   retrieval/run-rebuild-all.sh --embeddings retrieval/embeddings.jsonl \
#       [--index retrieval/index] [--repo-root .]
#
# --embeddings is required (store.py's --input: the embed stage's output
# JSONL). --index/--repo-root default to the same defaults the stages use.

INDEX="$SCRIPT_DIR/index"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EMBEDDINGS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --embeddings) EMBEDDINGS="$2"; shift 2 ;;
    --index) INDEX="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$EMBEDDINGS" ]]; then
  echo "error: --embeddings <path to embed-stage output JSONL> is required" >&2
  exit 1
fi

echo "== T-71 rebuild-all: authoritative pre-rebuild backup =="
uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/store.py" \
  --index "$INDEX" --backup-only

echo "== stage 1/4: store =="
uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/store.py" \
  --input "$EMBEDDINGS" --index "$INDEX" --no-backup

echo "== stage 2/4: anchors =="
uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/anchors.py" \
  --repo-root "$REPO_ROOT" --index "$INDEX" --no-backup

echo "== stage 3/4: graph =="
uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/graph.py" \
  --index "$INDEX" --repo-root "$REPO_ROOT"

echo "== stage 4/4: communities =="
uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/communities.py" \
  --index "$INDEX" --no-backup

echo "== rebuild-all complete: authoritative backup at ${INDEX}.bak =="
