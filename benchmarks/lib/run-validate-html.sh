#!/usr/bin/env bash
# Validate LLM-generated HTML/JS files for runtime errors using headless Chromium.
# Usage: run-validate-html.sh <file1.html> [file2.html ...] [options]
# Examples:
#   run-validate-html.sh results/decomposed/.../stage-3.html
#   run-validate-html.sh results/2026-02-09T*/html/*.html --quiet
#   run-validate-html.sh results/decomposed/.../stage-*.html --wait 3000

set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -eq 0 ]; then
  echo "Usage: run-validate-html.sh <file1.html> [file2.html ...] [options]" >&2
  echo "Run 'node lib/validate-html.js --help' for all options." >&2
  exit 2
fi

if [ ! -d node_modules/puppeteer ]; then
  echo "Error: Puppeteer not installed. Run 'npm install' in benchmarks/ first." >&2
  exit 2
fi

node lib/validate-html.js "$@"
