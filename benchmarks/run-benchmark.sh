#!/bin/bash
# =============================================================================
# Model Benchmark Script — Qwen2.5-Coder vs Qwen3 across coding personas
# =============================================================================
# Runs coding and visual prompts through multiple model personas, collecting:
#   - Raw API responses (JSON)
#   - Extracted code / HTML files
#   - Performance metrics (tok/s, token count, latency)
#   - Comparison report (Markdown)
#
# Usage:
#   ./benchmarks/run-benchmark.sh                          # Run all
#   ./benchmarks/run-benchmark.sh --models my-coder,my-coder-q3
#   ./benchmarks/run-benchmark.sh --prompts visual         # Category filter
#   ./benchmarks/run-benchmark.sh --prompts visual/01-bouncing-ball-rotating-square
#   ./benchmarks/run-benchmark.sh --dry-run                # Show plan only
#   ./benchmarks/run-benchmark.sh --no-skip                # Re-run existing
#   ./benchmarks/run-benchmark.sh --open                   # Auto-open HTML results
#   ./benchmarks/run-benchmark.sh --no-warmup              # Skip model warmup
#
# Exit codes:
#   0 = all benchmarks completed
#   1 = one or more failures
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_API="http://localhost:11434"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="${SCRIPT_DIR}/prompts"
LIB_DIR="${SCRIPT_DIR}/lib"

# Model-to-category mapping
declare -A MODEL_CATEGORY
MODEL_CATEGORY[my-coder]="backend"
MODEL_CATEGORY[my-coder-q3]="backend"
MODEL_CATEGORY[my-creative-coder]="visual"
MODEL_CATEGORY[my-creative-coder-q3]="visual"

# Model-to-base mapping (for display)
declare -A MODEL_BASE
MODEL_BASE[my-coder]="qwen2.5-coder:7b"
MODEL_BASE[my-coder-q3]="qwen3:8b"
MODEL_BASE[my-creative-coder]="qwen2.5-coder:7b"
MODEL_BASE[my-creative-coder-q3]="qwen3:8b"

ALL_MODELS=(my-coder my-coder-q3 my-creative-coder my-creative-coder-q3)

# ---------------------------------------------------------------------------
# CLI Arguments
# ---------------------------------------------------------------------------

FILTER_MODELS=""
FILTER_PROMPTS=""
DRY_RUN=false
SKIP_EXISTING=true
AUTO_OPEN=false
WARMUP=true

show_help() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --models MODEL1,MODEL2   Only test these models"
    echo "  --prompts FILTER         Filter: 'backend', 'visual', or 'category/prompt-id'"
    echo "  --dry-run                Show plan without executing"
    echo "  --no-skip                Re-run even if results exist"
    echo "  --open                   Auto-open HTML results in browser"
    echo "  --no-warmup              Skip model warmup (use if model already loaded)"
    echo "  -h, --help               Show this help"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --models)     FILTER_MODELS="$2"; shift 2 ;;
        --prompts)    FILTER_PROMPTS="$2"; shift 2 ;;
        --dry-run)    DRY_RUN=true; shift ;;
        --no-skip)    SKIP_EXISTING=false; shift ;;
        --open)       AUTO_OPEN=true; shift ;;
        --no-warmup)  WARMUP=false; shift ;;
        -h|--help)    show_help; exit 0 ;;
        *)            echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(timestamp)] $1"; }
separator() { echo "───────────────────────────────────────────────────────────"; }

format_duration() {
    local seconds=$1
    if [ "$seconds" -ge 60 ]; then
        echo "$((seconds / 60))m $((seconds % 60))s"
    else
        echo "${seconds}s"
    fi
}

# ---------------------------------------------------------------------------
# Results directory (timestamped)
# ---------------------------------------------------------------------------

RUN_ID=$(date '+%Y-%m-%dT%H%M%S')
RESULTS_DIR="${SCRIPT_DIR}/results/${RUN_ID}"

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

preflight() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  PREFLIGHT CHECKS"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Check Ollama is running
    if ! curl -sf "${OLLAMA_API}/" > /dev/null 2>&1; then
        log "[FAIL] Ollama not responding at ${OLLAMA_API}"
        log "       Start Ollama first: systemctl start ollama"
        exit 1
    fi
    log "[OK] Ollama responding at ${OLLAMA_API}"

    # Check python3
    if ! command -v python3 &> /dev/null; then
        log "[FAIL] python3 not found (required for extraction)"
        exit 1
    fi
    log "[OK] python3 available"

    # Check all models exist
    local model_list
    model_list=$(curl -sf "${OLLAMA_API}/api/tags" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('models', []):
    print(m['name'].split(':')[0])
" 2>/dev/null)

    local missing=0
    for model in "${ACTIVE_MODELS[@]}"; do
        if echo "$model_list" | grep -q "^${model}$"; then
            log "[OK] Model exists: ${model}"
        else
            log "[FAIL] Model missing: ${model}"
            missing=$((missing + 1))
        fi
    done

    if [ "$missing" -gt 0 ]; then
        log "Create missing models with: ollama create <name> -f modelfiles/<file>.Modelfile"
        exit 1
    fi

    # Check prompt files
    local prompt_count
    prompt_count=$(find "$PROMPTS_DIR" -name '*.md' | wc -l)
    log "[OK] ${prompt_count} prompt files found"

    echo ""
}

# ---------------------------------------------------------------------------
# Prompt parsing
# ---------------------------------------------------------------------------

parse_prompt_metadata() {
    local file="$1"
    # Extract metadata between --- delimiters
    PROMPT_ID=$(sed -n 's/^id: *//p' "$file" | head -1)
    PROMPT_CATEGORY=$(sed -n 's/^category: *//p' "$file" | head -1)
    PROMPT_MODELS=$(sed -n 's/^models: *//p' "$file" | head -1)
    PROMPT_TIMEOUT=$(sed -n 's/^timeout: *//p' "$file" | head -1)
    PROMPT_DESC=$(sed -n 's/^description: *//p' "$file" | head -1)
    PROMPT_SOURCE=$(sed -n 's/^source: *//p' "$file" | head -1)
}

get_prompt_body() {
    local file="$1"
    # Everything after the second ---
    awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$file"
}

# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

run_prompt() {
    local model="$1"
    local prompt_body="$2"
    local output_file="$3"
    local timeout="$4"

    # Build JSON payload safely via python3
    local json_payload
    json_payload=$(python3 -c "
import json, sys
prompt = sys.stdin.read()
print(json.dumps({
    'model': '$model',
    'messages': [{'role': 'user', 'content': prompt}],
    'stream': False
}))
" <<< "$prompt_body")

    # Call API
    local http_code
    http_code=$(curl -sf --max-time "$timeout" \
        -w '%{http_code}' \
        -o "$output_file" \
        -H 'Content-Type: application/json' \
        -d "$json_payload" \
        "${OLLAMA_API}/api/chat" 2>/dev/null) || true

    echo "$http_code"
}

# ---------------------------------------------------------------------------
# Metrics extraction
# ---------------------------------------------------------------------------

extract_metrics() {
    local json_file="$1"
    python3 -c "
import json, sys, re

with open('$json_file') as f:
    d = json.load(f)

eval_count = d.get('eval_count', 0)
eval_duration = d.get('eval_duration', 1)
prompt_eval_count = d.get('prompt_eval_count', 0)
prompt_eval_duration = d.get('prompt_eval_duration', 1)
total_duration = d.get('total_duration', 0)
load_duration = d.get('load_duration', 0)

tok_s = eval_count / (eval_duration / 1e9) if eval_duration > 0 else 0
prompt_tok_s = prompt_eval_count / (prompt_eval_duration / 1e9) if prompt_eval_duration > 0 else 0

# Check for thinking tokens
content = d.get('message', {}).get('content', '')
think_match = re.findall(r'<think>(.*?)</think>', content, re.DOTALL)
think_chars = sum(len(t) for t in think_match)

print(f'{eval_count}|{tok_s:.1f}|{prompt_eval_count}|{prompt_tok_s:.1f}|{total_duration/1e9:.2f}|{load_duration/1e9:.2f}|{think_chars}')
" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Warmup
# ---------------------------------------------------------------------------

warmup_model() {
    local model="$1"
    log "  Warming up ${model} (loading into VRAM)..."
    local warmup_start
    warmup_start=$(date +%s)

    curl -sf --max-time 120 \
        -o /dev/null \
        -H 'Content-Type: application/json' \
        -d "{\"model\":\"${model}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello.\"}],\"stream\":false}" \
        "${OLLAMA_API}/api/chat" 2>/dev/null || true

    local warmup_end
    warmup_end=$(date +%s)
    local warmup_dur=$((warmup_end - warmup_start))
    log "  Model loaded in $(format_duration $warmup_dur)"
}

# ---------------------------------------------------------------------------
# HTML opener (WSL → Windows browser)
# ---------------------------------------------------------------------------

open_html_results() {
    local html_dir="${RESULTS_DIR}/html"
    if [ ! -d "$html_dir" ] || [ -z "$(ls -A "$html_dir" 2>/dev/null)" ]; then
        log "No HTML files to open"
        return
    fi

    log "Opening HTML results in browser..."
    for html_file in "$html_dir"/*.html; do
        local win_path
        win_path=$(wslpath -w "$html_file" 2>/dev/null)
        if [ -n "$win_path" ]; then
            explorer.exe "$win_path" 2>/dev/null &
            sleep 1
        fi
    done
}

# ---------------------------------------------------------------------------
# Build active model and prompt lists
# ---------------------------------------------------------------------------

# Determine which models to run
if [ -n "$FILTER_MODELS" ]; then
    IFS=',' read -ra ACTIVE_MODELS <<< "$FILTER_MODELS"
else
    ACTIVE_MODELS=("${ALL_MODELS[@]}")
fi

# Collect prompt files based on filter
collect_prompts() {
    local category="$1"
    local prompt_files=()

    if [ -n "$FILTER_PROMPTS" ]; then
        # Check if filter is a category name
        if [ "$FILTER_PROMPTS" = "backend" ] || [ "$FILTER_PROMPTS" = "visual" ]; then
            if [ "$category" = "$FILTER_PROMPTS" ]; then
                for f in "${PROMPTS_DIR}/${category}"/*.md; do
                    [ -f "$f" ] && prompt_files+=("$f")
                done
            fi
        else
            # Filter is a specific prompt path (e.g., "visual/01-bouncing-ball")
            local filter_cat="${FILTER_PROMPTS%%/*}"
            local filter_id="${FILTER_PROMPTS#*/}"
            if [ "$category" = "$filter_cat" ]; then
                for f in "${PROMPTS_DIR}/${category}"/*"${filter_id}"*.md; do
                    [ -f "$f" ] && prompt_files+=("$f")
                done
            fi
        fi
    else
        # No filter — all prompts in this category
        for f in "${PROMPTS_DIR}/${category}"/*.md; do
            [ -f "$f" ] && prompt_files+=("$f")
        done
    fi

    echo "${prompt_files[@]}"
}

# ---------------------------------------------------------------------------
# Summary tracking
# ---------------------------------------------------------------------------

declare -a SUMMARY_ENTRIES
TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0

add_summary_entry() {
    # Append a JSON object to the summary array
    SUMMARY_ENTRIES+=("$1")
}

write_summary_json() {
    local out_file="${RESULTS_DIR}/summary.json"
    python3 -c "
import json, sys

entries_json = sys.stdin.read()
entries = json.loads(entries_json)

summary = {
    'run_id': '${RUN_ID}',
    'timestamp': '$(date '+%Y-%m-%d %H:%M:%S')',
    'models': $(python3 -c "
import json
m = {}
$(for model in "${ACTIVE_MODELS[@]}"; do
    echo "m['${model}'] = {'base_model': '${MODEL_BASE[$model]}', 'category': '${MODEL_CATEGORY[$model]}'};"
done)
print(json.dumps(m))
"),
    'results': entries
}

with open('${out_file}', 'w') as f:
    json.dump(summary, f, indent=2)

print(f'Summary written: ${out_file}')
" <<< "[$(IFS=,; echo "${SUMMARY_ENTRIES[*]}")]"
}

# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

main() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  MODEL BENCHMARK — Qwen2.5-Coder vs Qwen3"
    echo "  Run ID: ${RUN_ID}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    preflight

    if [ "$DRY_RUN" = true ]; then
        echo "═══════════════════════════════════════════════════════════════"
        echo "  DRY RUN — showing planned benchmark runs"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
    fi

    # Create results directories
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "${RESULTS_DIR}/raw" "${RESULTS_DIR}/html" "${RESULTS_DIR}/code"
    fi

    local bench_start
    bench_start=$(date +%s)
    local model_count=0

    for model in "${ACTIVE_MODELS[@]}"; do
        local category="${MODEL_CATEGORY[$model]}"
        local base="${MODEL_BASE[$model]}"

        # Collect eligible prompts
        local prompt_files_str
        prompt_files_str=$(collect_prompts "$category")
        if [ -z "$prompt_files_str" ]; then
            continue
        fi
        read -ra prompt_files <<< "$prompt_files_str"

        if [ ${#prompt_files[@]} -eq 0 ]; then
            continue
        fi

        model_count=$((model_count + 1))
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "  MODEL: ${model} (${base}) — ${category} prompts"
        echo "  Prompts: ${#prompt_files[@]}"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""

        if [ "$DRY_RUN" = true ]; then
            for pf in "${prompt_files[@]}"; do
                parse_prompt_metadata "$pf"
                echo "  [PLAN] ${PROMPT_ID} (timeout: ${PROMPT_TIMEOUT}s)"
            done
            continue
        fi

        # Warmup
        if [ "$WARMUP" = true ]; then
            warmup_model "$model"
            echo ""
        fi

        local prompt_idx=0
        local model_tok_s_sum=0
        local model_success=0

        for pf in "${prompt_files[@]}"; do
            prompt_idx=$((prompt_idx + 1))
            parse_prompt_metadata "$pf"

            local result_file="${RESULTS_DIR}/raw/${model}--${PROMPT_ID}.json"

            log "[${prompt_idx}/${#prompt_files[@]}] ${PROMPT_ID}"

            # Idempotency check
            if [ "$SKIP_EXISTING" = true ] && [ -f "$result_file" ]; then
                log "  [SKIP] Result exists"
                TOTAL_SKIP=$((TOTAL_SKIP + 1))

                # Still extract metrics for summary
                local metrics
                metrics=$(extract_metrics "$result_file")
                if [ -n "$metrics" ]; then
                    IFS='|' read -r ec toks pec ptoks total load think_chars <<< "$metrics"
                    model_tok_s_sum=$(python3 -c "print(${model_tok_s_sum} + ${toks})")
                    model_success=$((model_success + 1))

                    add_summary_entry "{\"model\":\"${model}\",\"prompt_id\":\"${PROMPT_ID}\",\"category\":\"${category}\",\"description\":\"${PROMPT_DESC}\",\"status\":\"skipped\",\"eval_count\":${ec},\"tok_s\":${toks},\"prompt_eval_count\":${pec},\"total_seconds\":${total},\"load_seconds\":${load},\"think_tokens\":${think_chars}}"
                fi
                continue
            fi

            log "  Generating... (timeout: ${PROMPT_TIMEOUT}s)"

            # Get prompt body and call API
            local body
            body=$(get_prompt_body "$pf")
            local gen_start
            gen_start=$(date +%s)

            local http_code
            http_code=$(run_prompt "$model" "$body" "$result_file" "$PROMPT_TIMEOUT")

            local gen_end
            gen_end=$(date +%s)
            local gen_dur=$((gen_end - gen_start))

            # Validate response
            if [ ! -f "$result_file" ] || ! python3 -c "import json; json.load(open('${result_file}'))" 2>/dev/null; then
                log "  [FAIL] Invalid or empty response (${gen_dur}s, HTTP ${http_code})"
                TOTAL_FAIL=$((TOTAL_FAIL + 1))
                add_summary_entry "{\"model\":\"${model}\",\"prompt_id\":\"${PROMPT_ID}\",\"category\":\"${category}\",\"description\":\"${PROMPT_DESC}\",\"status\":\"timeout\",\"timeout\":${PROMPT_TIMEOUT}}"
                continue
            fi

            # Extract metrics
            local metrics
            metrics=$(extract_metrics "$result_file")
            IFS='|' read -r ec toks pec ptoks total load think_chars <<< "$metrics"

            log "  [DONE] ${ec} tokens | ${toks} tok/s | ${total}s total"

            # Extract code/HTML
            local extracted_file=""
            local extracted_lines=0
            local html_valid=""

            if [ "$category" = "visual" ]; then
                local html_out="${RESULTS_DIR}/html/${model}--${PROMPT_ID}.html"
                local extract_result
                extract_result=$(python3 "${LIB_DIR}/extract-html.py" "$result_file" "$html_out" 2>/dev/null) || true

                if [ -n "$extract_result" ]; then
                    IFS='|' read -r extracted_lines html_valid <<< "$extract_result"
                    extracted_file="html/${model}--${PROMPT_ID}.html"
                    log "  Extracted: ${extracted_file} (${extracted_lines} lines)"
                else
                    log "  [WARN] No valid HTML extracted"
                fi
            else
                local code_base="${RESULTS_DIR}/code/${model}--${PROMPT_ID}"
                local extract_result
                extract_result=$(python3 "${LIB_DIR}/extract-code.py" "$result_file" "$code_base" "$PROMPT_ID" 2>/dev/null) || true

                if [ -n "$extract_result" ]; then
                    IFS='|' read -r extracted_lines detected_lang ext <<< "$extract_result"
                    extracted_file="code/${model}--${PROMPT_ID}${ext}"
                    log "  Extracted: ${extracted_file} (${extracted_lines} lines, ${detected_lang})"
                else
                    log "  [WARN] No code block extracted"
                fi
            fi

            TOTAL_PASS=$((TOTAL_PASS + 1))
            model_tok_s_sum=$(python3 -c "print(${model_tok_s_sum} + ${toks})")
            model_success=$((model_success + 1))

            local status="success"
            [ -z "$extracted_file" ] && status="success_no_extract"

            add_summary_entry "{\"model\":\"${model}\",\"prompt_id\":\"${PROMPT_ID}\",\"category\":\"${category}\",\"description\":\"${PROMPT_DESC}\",\"status\":\"${status}\",\"eval_count\":${ec},\"tok_s\":${toks},\"prompt_eval_count\":${pec},\"total_seconds\":${total},\"load_seconds\":${load},\"think_tokens\":${think_chars},\"extracted_file\":\"${extracted_file}\",\"extracted_lines\":${extracted_lines:-0}}"
        done

        # Model summary
        if [ "$model_success" -gt 0 ]; then
            local avg_toks
            avg_toks=$(python3 -c "print(f'{${model_tok_s_sum} / ${model_success}:.1f}')")
            echo ""
            separator
            log "MODEL COMPLETE: ${model} — ${model_success}/${#prompt_files[@]} prompts, avg ${avg_toks} tok/s"
            separator
        fi
    done

    if [ "$DRY_RUN" = true ]; then
        echo ""
        log "Dry run complete. ${model_count} models, no API calls made."
        return
    fi

    # Write summary and report
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  GENERATING REPORT"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    if [ ${#SUMMARY_ENTRIES[@]} -gt 0 ]; then
        write_summary_json
        python3 "${LIB_DIR}/generate-report.py" "${RESULTS_DIR}/summary.json" "${RESULTS_DIR}/report.md"
    fi

    # Open HTML results
    if [ "$AUTO_OPEN" = true ]; then
        open_html_results
    fi

    # Final summary
    local bench_end
    bench_end=$(date +%s)
    local bench_dur=$((bench_end - bench_start))

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  BENCHMARK COMPLETE"
    echo "  Duration: $(format_duration $bench_dur)"
    echo "  Results:  PASS=${TOTAL_PASS}  FAIL=${TOTAL_FAIL}  SKIP=${TOTAL_SKIP}"
    echo "  Output:   ${RESULTS_DIR}/"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    [ "$TOTAL_FAIL" -gt 0 ] && exit 1
    exit 0
}

main
