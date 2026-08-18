#!/usr/bin/env bash
# run-tests.sh — model-free unit tests for the write-model benchmark's own instrument (T-136).
#
# Covers writemodel_apply.py (locate_function; find_units/resolve_unit/apply_unit) and
# writemodel_corpus.py's ground truth. No GPU, no Ollama, under a second — there is no
# cost argument for ever skipping them, and they are the instrument every P3 measurement
# is read through, so their green-ness must be observed rather than assumed.
#
# Runs FROM benchmarks/lib because the tests import flat (`from writemodel_apply import ...`)
# rather than by package — the same reason overlays/scripts/test-installer.sh cds first.
# Collection is by pytest default, so a new test_*.py here is picked up with no edit.
#
# Args pass through:  ./run-tests.sh -k apply_unit   ./run-tests.sh -x
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
exec python3 -m pytest -q "$@"
