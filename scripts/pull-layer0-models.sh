#!/bin/bash
# =============================================================================
# Model Downloader — RTX 3060 12GB
# =============================================================================
# Downloads all models for the local AI infrastructure, ordered by priority.
#
# Tier 1 — Daily Drivers (Layer 0, needed immediately):
#   qwen3:8b                          Q4_K_M   ~5.2 GB   Primary coding
#   qwen3:14b                         Q4_K_M   ~9.3 GB   Heavy reasoning
#   qwen3:4b-q8_0                     Q8_0     ~4.4 GB   Fast classification
#
# Tier 2 — Specialized (Later layers, pre-downloaded):
#   llama3.1:8b-instruct-q5_K_M       Q5_K_M   ~5.7 GB   General writing
#   nomic-embed-text                   native   ~274 MB   Embeddings / RAG
#
# Tier 3 — Experimental (test & compare):
#   deepseek-r1:14b                    Q4_K_M   ~9.0 GB   Chain-of-thought
#   deepseek-coder-v2:16b              MoE      ~8.9 GB   MoE code model
#
# Total download: ~43.8 GB (disk space is not a constraint: 562 GB free)
#
# Usage:
#   # Interactive (watch progress in terminal):
#   ./scripts/pull-layer0-models.sh
#
#   # Background (log to file, walk away):
#   nohup ./scripts/pull-layer0-models.sh > pull-models.log 2>&1 &
#   tail -f pull-models.log      # check progress anytime
#   grep 'TIER.*COMPLETE' pull-models.log   # check tier milestones
#
#   # In a tmux/screen session (recommended):
#   tmux new -s models
#   ./scripts/pull-layer0-models.sh
#   # Ctrl+B, D to detach; tmux attach -t models to reattach
#
# Idempotent: safe to re-run. Already-downloaded models finish in <1s.
# Continues past failures — re-run to retry only what failed.
# =============================================================================

set -uo pipefail
# Note: we use pipefail but NOT -e, because we want to continue pulling
# remaining models even if one fails.

# ---------------------------------------------------------------------------
# Model definitions — grouped by tier, pulled in this exact order
# ---------------------------------------------------------------------------

# Format: "tag|description|tier"
MODEL_ENTRIES=(
    # ── Tier 1: Daily Drivers (Layer 0) ──────────────────────────────
    "qwen3:8b|Primary coding model (replaces qwen2.5-coder:7b)|1"
    "qwen3:14b|Heavy reasoning / architecture decisions|1"
    "qwen3:4b-q8_0|Fast classification and routing|1"

    # ── Tier 2: Specialized (Later layers) ───────────────────────────
    "llama3.1:8b-instruct-q5_K_M|General writing and documentation (Layer 3)|2"
    "nomic-embed-text|Embeddings for RAG / vector search (Layer 7)|2"

    # ── Tier 3: Experimental ─────────────────────────────────────────
    "deepseek-r1:14b|Chain-of-thought reasoning / evaluator role|3"
    "deepseek-coder-v2:16b|MoE code model (16B total, 2.4B active)|3"
)

# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------
declare -A RESULTS
declare -A DURATIONS
TOTAL=${#MODEL_ENTRIES[@]}
SUCCESS=0
FAILED=0
SKIPPED=0
CURRENT_TIER=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    echo "[$(timestamp)] $1"
}

separator() {
    echo "─────────────────────────────────────────────────────────────"
}

tier_banner() {
    local tier=$1
    local label=$2
    local count=$3
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  TIER ${tier}: ${label} (${count} models)"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

tier_complete_banner() {
    local tier=$1
    local label=$2
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  TIER ${tier} COMPLETE: ${label}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

format_duration() {
    local secs=$1
    local mins=$((secs / 60))
    local remaining=$((secs % 60))
    if [ $mins -gt 0 ]; then
        echo "${mins}m ${remaining}s"
    else
        echo "${remaining}s"
    fi
}

# Parse a model entry: "tag|description|tier"
parse_entry() {
    local entry="$1"
    MODEL_TAG="${entry%%|*}"
    local rest="${entry#*|}"
    MODEL_DESC="${rest%%|*}"
    MODEL_TIER="${rest##*|}"
}

# Count models per tier
count_tier() {
    local target_tier=$1
    local count=0
    for entry in "${MODEL_ENTRIES[@]}"; do
        parse_entry "$entry"
        [ "$MODEL_TIER" = "$target_tier" ] && count=$((count + 1))
    done
    echo $count
}

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
echo ""
separator
echo "  Model Downloader — Local AI Infrastructure"
echo "  Started: $(timestamp)"
separator
echo ""

# Check Ollama is available
if ! command -v ollama &> /dev/null; then
    log "ERROR: ollama not found. Is it installed?"
    log "  Run: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi
log "Ollama version: $(ollama --version 2>&1 | grep -oP '[\d.]+')"

# Check Ollama service is running
if ! ollama list &> /dev/null; then
    log "Ollama service not responding. Attempting to start..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start ollama
        sleep 3
        if ! ollama list &> /dev/null; then
            log "ERROR: Still cannot reach Ollama. Start it manually."
            exit 1
        fi
    else
        log "ERROR: Cannot start Ollama. Please start it manually."
        exit 1
    fi
fi

# Check GPU
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null)
    log "GPU: ${GPU_NAME} (${GPU_MEM})"
else
    log "WARNING: nvidia-smi not available — models will run on CPU"
fi

# Show disk space
OLLAMA_DIR="${HOME}/.ollama"
if [ -d "$OLLAMA_DIR" ]; then
    DISK_FREE=$(df -h "$OLLAMA_DIR" | awk 'NR==2{print $4}')
    DISK_USED=$(du -sh "$OLLAMA_DIR" 2>/dev/null | cut -f1)
    log "Ollama storage: ${DISK_USED} used, ${DISK_FREE} free"
fi

# Show currently installed models
echo ""
log "Currently installed models:"
ollama list 2>/dev/null | while IFS= read -r line; do
    echo "  $line"
done

TIER1_COUNT=$(count_tier 1)
TIER2_COUNT=$(count_tier 2)
TIER3_COUNT=$(count_tier 3)

echo ""
separator
log "Downloading ${TOTAL} models (~43.8 GB total)"
log "  Tier 1: ${TIER1_COUNT} daily drivers    (~18.9 GB)"
log "  Tier 2: ${TIER2_COUNT} specialized      (~6.0 GB)"
log "  Tier 3: ${TIER3_COUNT} experimental     (~17.9 GB)"
separator

# ---------------------------------------------------------------------------
# Pull each model, emitting tier banners at transitions
# ---------------------------------------------------------------------------
START_TIME=$(date +%s)
PULL_NUM=0

TIER_LABELS=([1]="Daily Drivers" [2]="Specialized" [3]="Experimental")

for entry in "${MODEL_ENTRIES[@]}"; do
    parse_entry "$entry"
    PULL_NUM=$((PULL_NUM + 1))

    # Emit tier banner on transition
    if [ "$MODEL_TIER" != "$CURRENT_TIER" ]; then
        # Close previous tier
        if [ "$CURRENT_TIER" != "0" ]; then
            tier_complete_banner "$CURRENT_TIER" "${TIER_LABELS[$CURRENT_TIER]}"
        fi

        # Open new tier
        local_count=$(count_tier "$MODEL_TIER")
        tier_banner "$MODEL_TIER" "${TIER_LABELS[$MODEL_TIER]}" "$local_count"
        CURRENT_TIER="$MODEL_TIER"
    fi

    log "[${PULL_NUM}/${TOTAL}] Pulling: ${MODEL_TAG}"
    log "  Role: ${MODEL_DESC}"
    PULL_START=$(date +%s)

    if ollama pull "$MODEL_TAG" 2>&1; then
        PULL_END=$(date +%s)
        PULL_DURATION=$((PULL_END - PULL_START))
        DURATIONS[$MODEL_TAG]=$PULL_DURATION

        if [ $PULL_DURATION -lt 5 ]; then
            log "  ✓ Already up to date (skipped)"
            RESULTS[$MODEL_TAG]="skipped"
            SKIPPED=$((SKIPPED + 1))
        else
            log "  ✓ Downloaded in $(format_duration $PULL_DURATION)"
            RESULTS[$MODEL_TAG]="success"
            SUCCESS=$((SUCCESS + 1))
        fi
    else
        PULL_END=$(date +%s)
        PULL_DURATION=$((PULL_END - PULL_START))
        DURATIONS[$MODEL_TAG]=$PULL_DURATION
        log "  ✗ FAILED to pull ${MODEL_TAG}"
        log "    Check the tag name at: https://ollama.com/library"
        RESULTS[$MODEL_TAG]="failed"
        FAILED=$((FAILED + 1))
    fi
done

# Close final tier
if [ "$CURRENT_TIER" != "0" ]; then
    tier_complete_banner "$CURRENT_TIER" "${TIER_LABELS[$CURRENT_TIER]}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo ""
separator
echo "  Download Summary"
echo "  Completed: $(timestamp)"
echo "  Duration:  $(format_duration $TOTAL_DURATION)"
separator
echo ""

# Print results grouped by tier
for tier in 1 2 3; do
    echo "  Tier ${tier}: ${TIER_LABELS[$tier]}"
    for entry in "${MODEL_ENTRIES[@]}"; do
        parse_entry "$entry"
        [ "$MODEL_TIER" != "$tier" ] && continue

        STATUS="${RESULTS[$MODEL_TAG]:-unknown}"
        DURATION="${DURATIONS[$MODEL_TAG]:-0}"

        case "$STATUS" in
            success)  ICON="✓"; TIME=" ($(format_duration $DURATION))" ;;
            skipped)  ICON="○"; TIME=" (already present)" ;;
            failed)   ICON="✗"; TIME=" (FAILED)" ;;
            *)        ICON="?"; TIME="" ;;
        esac

        printf "    %s  %-40s %s%s\n" "$ICON" "$MODEL_TAG" "$MODEL_DESC" "$TIME"
    done
    echo ""
done

log "Results: ${SUCCESS} downloaded, ${SKIPPED} already present, ${FAILED} failed"

# Show final model list
echo ""
log "All installed models:"
ollama list 2>/dev/null | while IFS= read -r line; do
    echo "  $line"
done

# Show updated disk usage
if [ -d "$OLLAMA_DIR" ]; then
    DISK_USED_AFTER=$(du -sh "$OLLAMA_DIR" 2>/dev/null | cut -f1)
    DISK_FREE_AFTER=$(df -h "$OLLAMA_DIR" | awk 'NR==2{print $4}')
    echo ""
    log "Disk: ${DISK_USED_AFTER} used by Ollama, ${DISK_FREE_AFTER} free"
fi

echo ""

# Exit with error if any pulls failed
if [ $FAILED -gt 0 ]; then
    log "WARNING: ${FAILED} model(s) failed to download. Re-run to retry."
    exit 1
fi

separator
echo "  All models downloaded!"
echo "  Next steps:"
echo "    - Benchmark: qwen3:8b vs qwen2.5-coder:7b"
echo "    - Create updated my-coder persona on qwen3:8b"
echo "    - Rewrite system prompt in skeleton format"
separator
echo ""
