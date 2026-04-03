#!/usr/bin/env bash
# sync-context.sh — Copy .memories/ and READMEs from all 3 repos into context/
#
# Run before career_chat_upload_hf to bundle cross-repo context for the chatbot.
# Files are renamed to flat names: {repo}-{folder}-{type}.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT_DIR="$SCRIPT_DIR/context"
LLM_ROOT="$HOME/workspaces/llm"
EXPENSES_ROOT="$HOME/workspaces/expenses"
WEB_RESEARCH_ROOT="$HOME/workspaces/web-research"

# Clean previous sync (only managed files, not manually added ones)
rm -f "$CONTEXT_DIR"/llm-*.md "$CONTEXT_DIR"/expenses-*.md "$CONTEXT_DIR"/web-research-*.md

copied=0

copy_if_exists() {
    local src="$1" dest="$2"
    if [[ -f "$src" ]]; then
        cp "$src" "$CONTEXT_DIR/$dest"
        copied=$((copied + 1))
    fi
}

# ── llm repo ──────────────────────────────────
copy_if_exists "$LLM_ROOT/.memories/QUICK.md"                    "llm-quick.md"
copy_if_exists "$LLM_ROOT/.memories/KNOWLEDGE.md"                "llm-knowledge.md"
copy_if_exists "$LLM_ROOT/mcp-server/.memories/QUICK.md"         "llm-mcp-server-quick.md"
copy_if_exists "$LLM_ROOT/mcp-server/.memories/KNOWLEDGE.md"     "llm-mcp-server-knowledge.md"
copy_if_exists "$LLM_ROOT/evaluator/.memories/QUICK.md"          "llm-evaluator-quick.md"
copy_if_exists "$LLM_ROOT/evaluator/.memories/KNOWLEDGE.md"      "llm-evaluator-knowledge.md"
copy_if_exists "$LLM_ROOT/personas/.memories/QUICK.md"           "llm-personas-quick.md"
copy_if_exists "$LLM_ROOT/personas/.memories/KNOWLEDGE.md"       "llm-personas-knowledge.md"
copy_if_exists "$LLM_ROOT/benchmarks/.memories/QUICK.md"         "llm-benchmarks-quick.md"
copy_if_exists "$LLM_ROOT/benchmarks/.memories/KNOWLEDGE.md"     "llm-benchmarks-knowledge.md"
copy_if_exists "$LLM_ROOT/overlays/.memories/QUICK.md"           "llm-overlays-quick.md"
copy_if_exists "$LLM_ROOT/overlays/.memories/KNOWLEDGE.md"       "llm-overlays-knowledge.md"
copy_if_exists "$LLM_ROOT/README.md"                             "llm-readme.md"
copy_if_exists "$LLM_ROOT/mcp-server/README.md"                  "llm-mcp-server-readme.md"
copy_if_exists "$LLM_ROOT/evaluator/README.md"                   "llm-evaluator-readme.md"
copy_if_exists "$LLM_ROOT/overlays/README.md"                    "llm-overlays-readme.md"

# ── expenses repo ─────────────────────────────
copy_if_exists "$EXPENSES_ROOT/.memories/QUICK.md"               "expenses-quick.md"
copy_if_exists "$EXPENSES_ROOT/.memories/KNOWLEDGE.md"           "expenses-knowledge.md"
# Sub-folder memories (if they exist)
copy_if_exists "$EXPENSES_ROOT/code/.memories/QUICK.md"          "expenses-code-quick.md"
copy_if_exists "$EXPENSES_ROOT/code/.memories/KNOWLEDGE.md"      "expenses-code-knowledge.md"
copy_if_exists "$EXPENSES_ROOT/code/expense-reporter/.memories/QUICK.md"   "expenses-reporter-quick.md"
copy_if_exists "$EXPENSES_ROOT/code/expense-reporter/.memories/KNOWLEDGE.md" "expenses-reporter-knowledge.md"
copy_if_exists "$EXPENSES_ROOT/code/README.md"                   "expenses-readme.md"
copy_if_exists "$EXPENSES_ROOT/code/expense-reporter/README.md"  "expenses-reporter-readme.md"

# ── web-research repo ─────────────────────────
copy_if_exists "$WEB_RESEARCH_ROOT/.memories/QUICK.md"           "web-research-quick.md"
copy_if_exists "$WEB_RESEARCH_ROOT/.memories/KNOWLEDGE.md"       "web-research-knowledge.md"
copy_if_exists "$WEB_RESEARCH_ROOT/engine/.memories/QUICK.md"    "web-research-engine-quick.md"
copy_if_exists "$WEB_RESEARCH_ROOT/engine/.memories/KNOWLEDGE.md" "web-research-engine-knowledge.md"
copy_if_exists "$WEB_RESEARCH_ROOT/spike/.memories/QUICK.md"     "web-research-spike-quick.md"
copy_if_exists "$WEB_RESEARCH_ROOT/spike/.memories/KNOWLEDGE.md" "web-research-spike-knowledge.md"
copy_if_exists "$WEB_RESEARCH_ROOT/tools/web-research/.memories/QUICK.md"   "web-research-tools-quick.md"
copy_if_exists "$WEB_RESEARCH_ROOT/tools/web-research/.memories/KNOWLEDGE.md" "web-research-tools-knowledge.md"
copy_if_exists "$WEB_RESEARCH_ROOT/README.md"                    "web-research-readme.md"
copy_if_exists "$WEB_RESEARCH_ROOT/spike/README.md"              "web-research-spike-readme.md"

echo "Synced $copied files to $CONTEXT_DIR"
