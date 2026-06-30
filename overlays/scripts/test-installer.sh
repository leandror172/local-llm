#!/bin/bash
# Run the overlay installer's --verify test suite (pytest).
#
# test_verify.py imports `from lib.actions import ...`, so it must run with
# overlays/ as the working directory (it puts overlays/ on sys.path). Tests
# monkeypatch $HOME for user-level install isolation. Args pass through to
# pytest (e.g. `-k eol`, `-x`).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/.."
exec python3 -m pytest test_verify.py -q "$@"
