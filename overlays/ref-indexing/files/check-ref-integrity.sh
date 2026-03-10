#!/bin/bash
# Validate ref block integrity across all *.md files in the project.
# Delegates to check-ref-integrity.py for the actual logic.
#
# Usage: .claude/tools/check-ref-integrity.sh [--root /abs/path/to/repo]
exec python3 "$(dirname "$0")/check-ref-integrity.py" "$@"
