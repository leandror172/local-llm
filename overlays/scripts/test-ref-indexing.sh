#!/bin/bash
# Run the ref-indexing overlay's test suite.
#
# Hermetic bash tests for ref-lookup.sh (builds its own fixture corpus via
# --root; no repo coupling). Any args are passed through to the underlying test.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$HERE/../ref-indexing/files/tests/test-ref-lookup-paths.sh" "$@"
