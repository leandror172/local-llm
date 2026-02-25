#!/usr/bin/env bash
# Validate LLM-generated code files using native compilers/linters.
# Usage: run-validate-code.sh <file1> [file2 ...] [options]
# Supported: .go (go build + go vet), .sh (shellcheck), .py (python3 compile)
# Examples:
#   run-validate-code.sh results/code/my-coder--01-go-lru-cache.go
#   run-validate-code.sh test-fixtures/go/*.go --quiet
#   run-validate-code.sh test-fixtures/python/*.py --quiet

set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -eq 0 ]; then
  echo "Usage: run-validate-code.sh <file1> [file2 ...] [options]" >&2
  echo "Run 'python3 lib/validate-code.py --help' for all options." >&2
  exit 2
fi

# Tool availability checks (python3 always present; Go/Java/shellcheck may not be)
if printf '%s\n' "$@" | grep -q '\.go$'; then
  if ! command -v go &> /dev/null; then
    echo "Error: Go compiler not found. Install Go first:" >&2
    echo "  wget -q https://go.dev/dl/go1.23.6.linux-amd64.tar.gz" >&2
    echo "  sudo tar -C /usr/local -xzf go1.23.6.linux-amd64.tar.gz" >&2
    echo "  export PATH=\$PATH:/usr/local/go/bin" >&2
    exit 2
  fi
fi

if printf '%s\n' "$@" | grep -q '\.java$'; then
  if ! command -v javac &> /dev/null; then
    echo "Error: javac not found. Install with:" >&2
    echo "  sudo apt-get install default-jdk-headless" >&2
    exit 2
  fi
fi

if printf '%s\n' "$@" | grep -q '\.sh$'; then
  if ! command -v shellcheck &> /dev/null; then
    echo "Error: shellcheck not found. Install with:" >&2
    echo "  sudo apt-get install shellcheck" >&2
    exit 2
  fi
fi

python3 lib/validate-code.py "$@"
