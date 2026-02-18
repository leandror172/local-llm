#!/usr/bin/env bash
# test-detect.sh — Verify codebase analyzer against test fixtures.
#
# Tests detect-persona.py against 5 minimal codebases and verifies
# the top-ranked persona matches expectations.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DETECTOR="$REPO_ROOT/personas/run-detect-persona.sh"
TEST_FIXTURES="$SCRIPT_DIR/test-fixtures"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

passed=0
failed=0

test_case() {
    local name="$1"
    local fixture_path="$2"
    local expected_top="$3"

    if [[ ! -d "$fixture_path" ]]; then
        echo -e "${RED}✗${NC} $name — fixture not found"
        failed=$((failed + 1))
        return
    fi

    # Run detector and extract top persona
    local cmd="'$DETECTOR' '$fixture_path' 2>/dev/null"
    local json_cmd='import sys, json; data = json.load(sys.stdin); print(data[0]["persona_name"] if data else "NONE")'

    local top_persona
    top_persona=$( (bash -c "$cmd" | python3 -c "$json_cmd" 2>/dev/null) || echo "ERROR" )

    if [[ "$top_persona" == "ERROR" ]] || [[ -z "$top_persona" ]]; then
        echo -e "${RED}✗${NC} $name — detection failed"
        failed=$((failed + 1))
        return
    fi

    # Check match
    if [[ "$top_persona" == "$expected_top" ]]; then
        echo -e "${GREEN}✓${NC} $name"
        passed=$((passed + 1))
    else
        echo -e "${RED}✗${NC} $name — expected $expected_top, got $top_persona"
        failed=$((failed + 1))
    fi
}

echo "Running codebase analyzer tests..."
echo ""

test_case "Java Backend" "$TEST_FIXTURES/java-backend" "my-java-q3"
test_case "Go gRPC" "$TEST_FIXTURES/go-grpc" "my-go-q3"
test_case "React Frontend" "$TEST_FIXTURES/react-frontend" "my-react-q3"
test_case "Python FastAPI" "$TEST_FIXTURES/python-fastapi" "my-python-q3"
test_case "Monorepo (Mixed)" "$TEST_FIXTURES/monorepo-mixed" "my-java-q3"

echo ""
echo "─────────────────────────────────────────────────"
echo -e "Results: ${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}"

if [[ $failed -eq 0 ]]; then
    exit 0
else
    exit 1
fi
