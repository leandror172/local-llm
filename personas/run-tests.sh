#!/usr/bin/env bash
# Run pytest for the personas module.
# All args forwarded to pytest (e.g. -v, -k test_name, etc.)
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m pytest "$@"
