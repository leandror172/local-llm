#!/usr/bin/env bash
# run-tests.sh — unit tests for the engineer-profile HF Space app.
#
# Hermetic by construction: tests/conftest.py substitutes MagicMocks for gradio,
# huggingface_hub and anthropic BEFORE app.py is imported, because all three execute
# top-level code needing network or a GPU. So this needs no venv, no network, no HF
# token — system python3 is enough, and it finishes in well under a second.
#
# Args pass through:  ./run-tests.sh -k context   ./run-tests.sh -x
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
exec python3 -m pytest tests/ -q "$@"
