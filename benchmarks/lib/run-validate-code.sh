#!/usr/bin/env bash
# Validate LLM-generated code files using native compilers/linters.
# Usage: run-validate-code.sh <file1.go> [file2.go ...] [options]
# Examples:
#   run-validate-code.sh results/code/my-coder--01-go-lru-cache.go
#   run-validate-code.sh test-fixtures/go/*.go --quiet

set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -eq 0 ]; then
  echo "Usage: run-validate-code.sh <file1.go> [file2.go ...] [options]" >&2
  echo "Run 'python3 lib/validate-code.py --help' for all options." >&2
  exit 2
fi

if ! command -v go &> /dev/null; then
  echo "Error: Go compiler not found. Install Go first:" >&2
  echo "  wget -q https://go.dev/dl/go1.23.6.linux-amd64.tar.gz" >&2
  echo "  sudo tar -C /usr/local -xzf go1.23.6.linux-amd64.tar.gz" >&2
  echo "  export PATH=\$PATH:/usr/local/go/bin" >&2
  exit 2
fi

python3 lib/validate-code.py "$@"
