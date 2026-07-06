#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
cd "$SCRIPT_DIR"

# LTG derivation-stage rebuild sequencer (T-71) — llm INSTANCE copy.
#
# Runs the four index-touching stages in order: store -> anchors -> graph ->
# communities. extract/embed are deliberately OUT of scope (GPU-expensive,
# run separately via run-extract-topics.sh / run-embed.sh).
#
# Backup scheme (T-71): ONE authoritative backup of the live index into plain
# {index}.bak before any stage; every stage then runs --no-backup so nothing
# overwrites that slot mid-rebuild. Ad-hoc single-stage runs (the individual
# wrappers) default to their own stage-suffixed slot instead.
#
# Usage (from anywhere):
#   ltg/run-rebuild-all.sh --embeddings runs/<tag>-embeddings.jsonl
#       [--index index] [--repo-root ..]
# Paths are resolved relative to ltg/ (this wrapper cds here first).

INDEX="$PWD/index"
REPO_ROOT="$(cd .. && pwd)"
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
uv run --project . ltg-store \
  --index "$INDEX" --backup-only

echo "== stage 1/4: store =="
uv run --project . ltg-store \
  --input "$EMBEDDINGS" --index "$INDEX" --no-backup

echo "== stage 2/4: anchors =="
uv run --project . ltg-anchors \
  --repo-root "$REPO_ROOT" --index "$INDEX" --no-backup

echo "== stage 3/4: graph =="
uv run --project . ltg-graph \
  --index "$INDEX" --repo-root "$REPO_ROOT"

echo "== stage 4/4: communities =="
uv run --project . ltg-communities \
  --index "$INDEX" --no-backup

echo "== rebuild-all complete: authoritative backup at ${INDEX}.bak =="
