#!/bin/bash
# Resolve a [ref:KEY] tag to its reference content.
# Searches all *.md files in the project for <!-- ref:KEY --> markers.
#
# Usage: .claude/tools/ref-lookup.sh <KEY> [--root /abs/path/to/repo]
#        .claude/tools/ref-lookup.sh --list [--root /abs/path/to/repo]
#        .claude/tools/ref-lookup.sh 'ltg-plan-*' [--root /abs/path/to/repo]
#
# KEY may contain a trailing wildcard (*) for prefix search.
# All matching blocks are printed in key-sorted order, separated by a blank line.
#
# --root overrides the default project root (repo containing this script).
# Use it to look up refs from a different repository.

set -euo pipefail

# Resolve default project root (one level above .claude/tools/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments: extract optional --root before processing KEY
KEY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    *)
      KEY="$1"
      shift
      ;;
  esac
done

# Validate root directory
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "Error: --root directory not found: $PROJECT_ROOT"
  exit 1
fi

# --list mode: print all available keys and exit 0 (MCP-friendly)
if [ "$KEY" = "--list" ] || [ "$KEY" = "list" ]; then
  grep -roh --include="*.md" '<!-- ref:[a-z0-9-]* -->' "$PROJECT_ROOT" 2>/dev/null \
    | sed 's/<!-- ref://;s/ -->//' | sort -u
  exit 0
fi

if [ -z "$KEY" ]; then
  echo "Usage: $0 <KEY> [--root /abs/path/to/repo]"
  echo "Available keys:"
  grep -roh --include="*.md" '<!-- ref:[a-z0-9-]* -->' "$PROJECT_ROOT" 2>/dev/null \
    | sed 's/<!-- ref://;s/ -->//' | sort -u
  exit 1
fi

# Glob mode: KEY contains '*' — expand to all matching keys and emit each block.
if [[ "$KEY" == *"*"* ]]; then
  PATTERN="^${KEY//\*/[a-z0-9-]*}$"
  MATCHES=$(grep -roh --include="*.md" '<!-- ref:[a-z0-9-]* -->' "$PROJECT_ROOT" 2>/dev/null \
    | sed 's/<!-- ref://;s/ -->//' | grep -E "$PATTERN" | sort -u)
  if [ -z "$MATCHES" ]; then
    echo "No ref keys matching pattern: $KEY"
    exit 1
  fi
  FIRST=1
  while IFS= read -r MATCH_KEY; do
    MFILE=$(grep -rl --include="*.md" "<!-- ref:$MATCH_KEY -->" "$PROJECT_ROOT" 2>/dev/null | head -1)
    [ -z "$MFILE" ] && continue
    [ "$FIRST" -eq 0 ] && echo
    FIRST=0
    sed -n "/<!-- ref:$MATCH_KEY -->/,/<!-- \/ref:$MATCH_KEY -->/p" "$MFILE"
  done <<< "$MATCHES"
  exit 0
fi

FILE=$(grep -rl --include="*.md" "<!-- ref:$KEY -->" "$PROJECT_ROOT" 2>/dev/null | head -1)
if [ -z "$FILE" ]; then
  echo "ref:$KEY not found in any *.md file under $PROJECT_ROOT"
  exit 1
fi

sed -n "/<!-- ref:$KEY -->/,/<!-- \/ref:$KEY -->/p" "$FILE"
