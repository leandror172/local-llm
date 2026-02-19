#!/usr/bin/env bash
# test-ollama-client.sh — Verify personas/lib/ollama_client.py against live Ollama.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURES="$SCRIPT_DIR/test-fixtures/ollama-client"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

passed=0
failed=0

test_case() {
    local name="$1"
    local script_file="$2"
    local expected_pattern="$3"

    if [[ ! -f "$script_file" ]]; then
        echo -e "${RED}✗${NC} $name — fixture not found: $script_file"
        failed=$((failed + 1))
        return
    fi

    local output
    output=$(cd "$REPO_ROOT" && python3 "$script_file" 2>&1) || true

    if echo "$output" | grep -qE "$expected_pattern"; then
        echo -e "${GREEN}✓${NC} $name"
        passed=$((passed + 1))
    else
        echo -e "${RED}✗${NC} $name"
        echo "    Expected pattern: $expected_pattern"
        echo "    Got: $(echo "$output" | head -5)"
        failed=$((failed + 1))
    fi
}

echo "Running Ollama client tests (requires live Ollama)..."
echo ""

test_case "Basic chat"             "$FIXTURES/test_basic.py"   "CONTENT:.*[0-9]"
test_case "Structured JSON output" "$FIXTURES/test_json.py"    "HAS_ANSWER: True"
test_case "Custom system prompt"   "$FIXTURES/test_system.py"  "CONTENT: .+"

echo ""
echo "─────────────────────────────────────────────────"
echo -e "Results: ${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}"

[[ $failed -eq 0 ]] && exit 0 || exit 1
