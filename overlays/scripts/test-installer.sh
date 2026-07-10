#!/bin/bash
# Run the overlay installer test suites (pytest): --verify mode (test_verify.py)
# and customizable: keep-regions (test_customizable.py).
#
# Both import `from lib.actions import ...`, so they must run with overlays/ as
# the working directory (they put overlays/ on sys.path). Tests monkeypatch $HOME
# for user-level install isolation. Args pass through to pytest (e.g. `-k eol`, `-x`).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/.."
exec python3 -m pytest test_verify.py test_customizable.py test_signals.py -q "$@"
