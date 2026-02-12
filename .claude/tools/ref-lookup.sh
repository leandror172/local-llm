#!/bin/bash
# Resolve a [ref:KEY] tag from CLAUDE.md to its reference content.
# Searches .claude/ for <!-- ref:KEY --> markers and prints the section.
#
# Usage: .claude/tools/ref-lookup.sh <KEY>
# Example: .claude/tools/ref-lookup.sh bash-wrappers

set -euo pipefail

KEY="${1:-}"
if [ -z "$KEY" ]; then
  echo "Usage: $0 <KEY>"
  echo "Available keys:"
  grep -roh '<!-- ref:[a-z-]* -->' .claude/ 2>/dev/null | sed 's/<!-- ref://;s/ -->//' | sort -u
  exit 1
fi

FILE=$(grep -rl "<!-- ref:$KEY -->" .claude/ 2>/dev/null | head -1)
if [ -z "$FILE" ]; then
  echo "ref:$KEY not found in .claude/"
  exit 1
fi

sed -n "/<!-- ref:$KEY -->/,/<!-- \/ref:$KEY -->/p" "$FILE"
