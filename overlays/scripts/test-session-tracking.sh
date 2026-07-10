#!/bin/bash
# Run the session-tracking overlay's handoff-pipeline test suite (pytest).
#
# The suite lives beside the modules it tests (files/handoff/), and the tests
# import siblings as top-level modules (`from applier import ...`), so it must
# run with that dir as the working directory. Args pass through to pytest
# (e.g. `-k harvest`, `-x`, `-vv`).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/../session-tracking"
exec python3 -m pytest -q "$@"
