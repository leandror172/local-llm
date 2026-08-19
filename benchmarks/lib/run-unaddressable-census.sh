#!/usr/bin/env bash
# run-unaddressable-census.sh — P3-T0 criterion 5b (s139).
#
# What share of REAL edits touch something `replace_unit` cannot address? Walks this repo's
# non-merge history, and for every MODIFIED .py file compares the AST top-level sets of the
# before and after revisions. Structural, never textual: a `+import math` diff line may be a
# FUNCTION-LOCAL import (not top-level at all), and a parenthesized multi-line import has its
# added lines indented, so a grep undercounts it — measured, 8.4% textual vs 10.7% structural.
#
# No model, no GPU. Reads git only. Takes ~1 min over ~300 commits.
#
#   ./run-unaddressable-census.sh out.json
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/../.."
exec python3 "$HERE/unaddressable_census.py" "${1:-/dev/stdout}"
