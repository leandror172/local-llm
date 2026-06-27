#!/bin/bash
# Tests for --paths flag in ref-lookup.sh
# Usage: .claude/tools/tests/test-ref-lookup-paths.sh
# Exit 0 = all pass, nonzero = at least one failure
#
# Baseline files (captured pre-edit) stored in the same directory as this test.
# Regression tests 7-9 compare against those baselines.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/../ref-lookup.sh"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

PASS=0
FAIL=0
declare -a ERRORS=()

pass() { PASS=$((PASS+1)); echo "PASS: $1"; }
fail() { FAIL=$((FAIL+1)); ERRORS+=("$1"); echo "FAIL: $1"; }
run_test() {
  local name="$1"
  local result="$2"
  [ "$result" -eq 0 ] && pass "$name" || fail "$name"
}

# ─── HERMETIC FIXTURE TESTS ───────────────────────────────────────────────────
FIXTURE=$(mktemp -d)
trap 'rm -rf "$FIXTURE"' EXIT

mkdir -p "$FIXTURE/docs" "$FIXTURE/.claude/local"

cat > "$FIXTURE/docs/a.md" << 'EOF'
<!-- ref:alpha -->
Alpha content
<!-- /ref:alpha -->
EOF

cat > "$FIXTURE/docs/b.md" << 'EOF'
<!-- ref:beta -->
Beta content
<!-- /ref:beta -->
EOF

cat > "$FIXTURE/.claude/local/secret.md" << 'EOF'
<!-- ref:localonly -->
Secret content
<!-- /ref:localonly -->
EOF

PATHS_OUT=$("$SCRIPT" --paths --root "$FIXTURE" 2>/dev/null) || PATHS_OUT=""

# Test 1: --paths emits KEY<TAB>relpath for alpha and beta
t1=0
echo "$PATHS_OUT" | grep -qP "^alpha\tdocs/a\.md$" || t1=1
echo "$PATHS_OUT" | grep -qP "^beta\tdocs/b\.md$" || t1=1
run_test "fixture: alpha and beta present with correct paths" $t1

# Test 2: no localonly line, no path containing .claude/local
t2=0
echo "$PATHS_OUT" | grep -q 'localonly' && t2=1
echo "$PATHS_OUT" | grep -q '\.claude/local' && t2=1
run_test "fixture: .claude/local entries excluded (safety filter)" $t2

# Test 3: --root honored (exactly 2 lines returned, all under docs/)
t3=0
line_count=$(echo "$PATHS_OUT" | grep -c '.' || true)
[ "$line_count" -eq 2 ] || t3=1
echo "$PATHS_OUT" | grep -qv '^[a-z][a-z0-9-]*'$'\t''docs/' && t3=1 || true
run_test "fixture: --root honored (2 lines, all under docs/)" $t3

# ─── REAL-REPO TESTS ───────────────────────────────────────────────────────────
REAL_PATHS=$("$SCRIPT" --paths 2>/dev/null) || REAL_PATHS=""

# Test 4: spot check — indexing-convention -> .claude/index.md
t4=0
echo "$REAL_PATHS" | grep -qP "^indexing-convention\t\.claude/index\.md$" || t4=1
run_test "real-repo: indexing-convention -> .claude/index.md" $t4

# Test 5: for 2 keys, --paths path matches first grep-rl occurrence
# Use keys unique in non-worktree path but ordering still agrees (verified pre-authoring)
for key in indexing-convention bash-wrappers; do
  expected_file=$(grep -rl --include="*.md" "<!-- ref:$key -->" "$PROJECT_ROOT" 2>/dev/null | head -1)
  expected_rel="${expected_file#$PROJECT_ROOT/}"
  actual_rel=$(echo "$REAL_PATHS" | awk -F'\t' -v k="$key" '$1 == k {print $2; exit}')
  t5=0
  [ "$actual_rel" = "$expected_rel" ] || t5=1
  run_test "real-repo: $key path matches grep-rl first occurrence" $t5
done

# Test 6: every --paths key appears in --list
LIST_OUT=$("$SCRIPT" --list 2>/dev/null)
t6=0
while IFS=$'\t' read -r pkey _ppath; do
  [ -z "$pkey" ] && continue
  echo "$LIST_OUT" | grep -qx "$pkey" || { t6=1; echo "  missing from --list: $pkey"; }
done <<< "$REAL_PATHS"
run_test "real-repo: every --paths key appears in --list" $t6

# ─── REGRESSION TESTS ─────────────────────────────────────────────────────────
BASELINE_LIST="$SCRIPT_DIR/baseline-list.txt"
BASELINE_SINGLE="$SCRIPT_DIR/baseline-single-key.txt"
BASELINE_GLOB="$SCRIPT_DIR/baseline-glob.txt"

if [ ! -f "$BASELINE_LIST" ] || [ ! -f "$BASELINE_SINGLE" ] || [ ! -f "$BASELINE_GLOB" ]; then
  echo "SKIP: regression baselines not found in $SCRIPT_DIR — run capture-baselines.sh first"
else
  # Test 7: --list byte-unchanged
  t7=0
  diff <("$SCRIPT" --list 2>/dev/null) "$BASELINE_LIST" > /dev/null 2>&1 || t7=1
  run_test "regression: --list output unchanged" $t7

  # Test 8: single-key lookup unchanged (indexing-convention)
  t8=0
  diff <("$SCRIPT" indexing-convention 2>/dev/null) "$BASELINE_SINGLE" > /dev/null 2>&1 || t8=1
  run_test "regression: single-key lookup (indexing-convention) unchanged" $t8

  # Test 9: glob mode unchanged (bash-wrappers*)
  t9=0
  diff <("$SCRIPT" 'bash-wrappers*' 2>/dev/null) "$BASELINE_GLOB" > /dev/null 2>&1 || t9=1
  run_test "regression: glob mode (bash-wrappers*) unchanged" $t9
fi

# ─── SUMMARY ──────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "${#ERRORS[@]}" -gt 0 ]; then
  echo "Failed tests:"
  for e in "${ERRORS[@]}"; do echo "  - $e"; done
fi
[ "$FAIL" -eq 0 ]
