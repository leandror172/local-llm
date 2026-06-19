#!/usr/bin/env bash
# sync-context.sh — Copy .memories/ and READMEs from all 3 repos into context/
#
# Run before career_chat_upload_hf to bundle cross-repo context for the chatbot.
# .memories/ files are discovered dynamically; flat names: {repo}-{folder}-{type}.md
# READMEs are copied explicitly (not every folder's README is chatbot-relevant).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT_DIR="$SCRIPT_DIR/context"

declare -A REPO_ROOTS=(
  ["llm"]="$HOME/workspaces/llm"
  ["expenses"]="$HOME/workspaces/expenses"
  ["web-research"]="$HOME/workspaces/web-research"
)

# Folder path fragments to skip (too granular or irrelevant for the chatbot)
EXCLUDE=("internal-excel" "internal-generate" "cmd-workbook-inspect")

# Mechanical slug → curated flat name prefix (avoids redundant path segments)
declare -A OVERRIDES=(
  ["expenses-code-expense-reporter"]="expenses-reporter"
  ["web-research-tools-web-research"]="web-research-tools"
)

# Clean previous sync (only managed files, not manually added ones)
rm -f "$CONTEXT_DIR"/llm-*.md "$CONTEXT_DIR"/expenses-*.md "$CONTEXT_DIR"/web-research-*.md "$CONTEXT_DIR"/career-search-*.md

copied=0

copy_memories() {
  local label="$1" root="$2"
  [[ -d "$root" ]] || return 0

  while IFS= read -r f; do
    # Derive slug from the folder containing .memories/
    local mem_dir folder slug
    mem_dir="$(dirname "$f")"          # …/.memories
    folder="$(dirname "$mem_dir")"     # parent of .memories

    if [[ "$folder" == "$root" ]]; then
      slug="$label"
    else
      local rel="${folder#"$root"/}"
      slug="${label}-${rel//\//-}"
    fi

    # Skip excluded fragments
    local skip=0
    for excl in "${EXCLUDE[@]}"; do
      [[ "$slug" == *"$excl"* ]] && skip=1 && break
    done
    [[ "$skip" -eq 1 ]] && continue

    # Apply override if present
    local prefix="${OVERRIDES[$slug]:-$slug}"

    # Derive type suffix (quick or knowledge)
    local basename type
    basename="$(basename "$f")"
    type="${basename,,}"   # QUICK.md → quick.md
    type="${type%.md}"     # → quick

    cp "$f" "$CONTEXT_DIR/${prefix}-${type}.md"
    copied=$((copied + 1))
  done < <(find "$root" -path '*/.memories/QUICK.md' -o -path '*/.memories/KNOWLEDGE.md' | sort)
}

copy_if_exists() {
  local src="$1" dest="$2"
  if [[ -f "$src" ]]; then
    cp "$src" "$CONTEXT_DIR/$dest"
    copied=$((copied + 1))
  fi
}

# ── .memories/ — dynamic discovery ────────────
for label in "${!REPO_ROOTS[@]}"; do
  copy_memories "$label" "${REPO_ROOTS[$label]}"
done

# ── READMEs — explicit (only chatbot-relevant folders) ────────────────────────
LLM_ROOT="${REPO_ROOTS[llm]}"
EXPENSES_ROOT="${REPO_ROOTS[expenses]}"
WEB_RESEARCH_ROOT="${REPO_ROOTS[web-research]}"

copy_if_exists "$LLM_ROOT/README.md"                             "llm-readme.md"
copy_if_exists "$LLM_ROOT/mcp-server/README.md"                  "llm-mcp-server-readme.md"
copy_if_exists "$LLM_ROOT/evaluator/README.md"                   "llm-evaluator-readme.md"
copy_if_exists "$LLM_ROOT/overlays/README.md"                    "llm-overlays-readme.md"
copy_if_exists "$EXPENSES_ROOT/code/README.md"                   "expenses-readme.md"
copy_if_exists "$EXPENSES_ROOT/code/expense-reporter/README.md"  "expenses-reporter-readme.md"
copy_if_exists "$WEB_RESEARCH_ROOT/README.md"                    "web-research-readme.md"
copy_if_exists "$WEB_RESEARCH_ROOT/spike/README.md"              "web-research-spike-readme.md"

# ── career-search portfolio docs (interview context → on-demand knowledge tier) ──
CAREER_ROOT="$HOME/workspaces/career-search"
copy_if_exists "$CAREER_ROOT/portfolio/engineer-personal-projects-profile.md" "career-search-engineer-profile-knowledge.md"
copy_if_exists "$CAREER_ROOT/portfolio/llm-project-concept-context.md"        "career-search-llm-project-knowledge.md"
copy_if_exists "$CAREER_ROOT/portfolio/web-research-project-context.md"       "career-search-web-research-knowledge.md"
copy_if_exists "$CAREER_ROOT/portfolio/portfolio.md"                           "career-search-portfolio-knowledge.md"

echo "Synced $copied files to $CONTEXT_DIR"
