#!/usr/bin/env bash
# run-write-model-bench.sh — oficina write-model benchmark (T-104).
# Wraps writemodel_bench.py. Serial 14B generations (VRAM ceiling) — the full sweep is a
# multi-hour sit; smoke-test with --limit/--per-bucket first.
# Design + decision rule: ref:oficina-write-model-benchmark
#
# Examples:
#   ./run-write-model-bench.sh --per-bucket 1 --buckets small --runs 1   # smoke: 3 gens
#   ./run-write-model-bench.sh                                           # full: 12×3×3 = 108 gens
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/writemodel_bench.py" "$@"
