#!/usr/bin/env bash
# run-census-report.sh — print the criterion-5b cuts from a saved census run (s140).
#
# The cuts are the measurement: the headline rate moves ~2x between them, so they are kept in
# a script rather than re-derived by hand each time (s139 did the latter and the table was not
# reproducible). Reads a JSON produced by run-unaddressable-census.sh.
#
#   ./run-census-report.sh ../results/criterion5b-unaddressable-census-20260820.json
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/census_report.py" "$@"
