#!/usr/bin/env bash
# run-tests.sh — the ollama-bridge / oficina pytest suite.
#
# The single definition of "run this suite". `make test` delegates here and so does
# the repo-root aggregator (scripts/run-all-tests.sh), so the same invocation works
# from make, a bare shell, or CI — and the command exists in exactly one place.
#
# Runs under `uv run` so the project venv is used; invoking pytest directly misses it.
# Args pass through:  ./run-tests.sh -k refs   ./run-tests.sh tests/oficina/ -x
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/.."
exec uv run pytest tests/ "$@"
