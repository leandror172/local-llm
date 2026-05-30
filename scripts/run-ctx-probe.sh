#!/usr/bin/env bash
# Context-window ceiling probe for 14B models post OLLAMA_KV_CACHE_TYPE=q8_0
#
# OLLAMA_KV_CACHE_TYPE=q8_0 (enabled session 75, system-wide) halves KV VRAM.
# This probe confirms the new viable num_ctx ceiling for 14B models by loading
# each model at 16K (baseline), 24K, and 32K and recording VRAM footprint.
#
# Usage:
#   scripts/run-ctx-probe.sh                              # all 14B models, default ctx sizes
#   INFER_MODELS="qwen3:14b" scripts/run-ctx-probe.sh     # single model
#   CTX_SIZES="16384 24576 32768" scripts/run-ctx-probe.sh
#   OLLAMA_URL=http://localhost:11435 scripts/run-ctx-probe.sh  # non-default port
#
# Verdict per (model, ctx):
#   PASS  — request succeeded, VRAM headroom > 500 MiB
#   WARN  — request succeeded, VRAM headroom 100–500 MiB
#   FAIL  — OOM/error from Ollama
#
# After running: update personas/models.yaml + personas/registry.yaml

set -euo pipefail

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
INFER_MODELS="${INFER_MODELS:-qwen3:14b qwen2.5-coder:14b}"
CTX_SIZES="${CTX_SIZES:-16384 24576 32768}"
VRAM_TOTAL_MIB=12288
HEADROOM_WARN_MIB=500
HEADROOM_FAIL_MIB=100
VERBOSE="${VERBOSE:-0}"

# ── helpers ───────────────────────────────────────────────────────────────────

log()     { echo "  $*"; }
ok()      { echo "  ✓ $*"; }
warn_msg(){ echo "  ⚠ $*"; }
fail_msg(){ echo "  ✗ $*"; }
section() { echo; echo "── $1 ──────────────────────────────────────────────────────"; }

vram_used_mib() {
  nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | tr -d ' '
}

vram_line() {
  nvidia-smi --query-gpu=memory.used,memory.free,memory.total \
    --format=csv,noheader,nounits 2>/dev/null \
    | awk -F', ' '{printf "VRAM: %s/%s MiB (%s MiB free)\n",$1,$3,$2}'
}

unload_all() {
  # Unload every currently loaded model by setting keep_alive=0s
  local loaded
  loaded=$(curl -s --max-time 10 "$OLLAMA_URL/api/ps" 2>/dev/null \
    | python3 -c "
import sys,json
d=json.load(sys.stdin)
for m in d.get('models',[]):
    print(m['name'])
" 2>/dev/null || echo "")
  for m in $loaded; do
    curl -s --max-time 30 "$OLLAMA_URL/api/generate" \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"$m\",\"keep_alive\":\"0s\",\"prompt\":\"\",\"stream\":false}" \
      > /dev/null 2>&1 || true
    log "unloaded $m"
  done
  sleep 1
}

load_and_probe() {
  local model="$1"
  local ctx="$2"

  local resp exit_code=0
  resp=$(curl -s --max-time 120 "$OLLAMA_URL/api/generate" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$model\",
      \"prompt\": \"Say only: ok\",
      \"stream\": false,
      \"think\": false,
      \"options\": {\"num_ctx\": $ctx, \"num_predict\": 8}
    }") || exit_code=$?

  if [[ $VERBOSE -eq 1 ]]; then
    log "raw resp: ${resp:0:120}"
  fi

  local success=0
  local err_msg=""
  if [[ $exit_code -ne 0 ]]; then
    err_msg="curl failed (exit $exit_code)"
  else
    success=$(echo "$resp" | python3 -c "
import sys,json
try:
    r=json.load(sys.stdin)
    if 'response' in r:
        print(1)
    else:
        print(0)
        import sys; print(r.get('error','unknown error'), file=sys.stderr)
except Exception as e:
    print(0)
    print(str(e), file=sys.stderr)
" 2>/tmp/ctx-probe-err || echo 0)
    err_msg=$(cat /tmp/ctx-probe-err 2>/dev/null || echo "")
  fi

  local tok_s=""
  if [[ "$success" == "1" ]]; then
    tok_s=$(echo "$resp" | python3 -c "
import sys,json
r=json.load(sys.stdin)
ec=r.get('eval_count',0)
ed=r.get('eval_duration',1)
if ec>0 and ed>0:
    print(f'{ec/(ed/1e9):.1f}')
" 2>/dev/null || echo "")
  fi

  echo "$success|$err_msg|$tok_s"
}

# ── main ──────────────────────────────────────────────────────────────────────

echo "════════════════════════════════════════════════════════════"
echo "  Context-Window Ceiling Probe — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  OLLAMA_KV_CACHE_TYPE=q8_0 assumed (system-wide, session 75)"
echo "  OLLAMA_URL=$OLLAMA_URL"
echo "════════════════════════════════════════════════════════════"

# Verify Ollama is reachable
if ! curl -s --max-time 5 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
  echo "  ✗ Cannot reach Ollama at $OLLAMA_URL"
  echo "    Try: OLLAMA_URL=http://localhost:11435 $0"
  exit 1
fi
ok "Ollama reachable at $OLLAMA_URL"
log "$(vram_line)"

# Results table (populated below)
declare -A RESULTS   # [model|ctx] = "verdict|vram_used|tok_s"

# ── probe loop ────────────────────────────────────────────────────────────────

for model in $INFER_MODELS; do
  section "Model: $model"

  # Verify model is pulled
  if ! curl -s "$OLLAMA_URL/api/tags" | python3 -c "
import sys,json
d=json.load(sys.stdin)
names=[m['name'] for m in d.get('models',[])]
import sys
sys.exit(0 if any('$model' in n for n in names) else 1)
" 2>/dev/null; then
    fail_msg "$model not found — skipping (run: ollama pull $model)"
    for ctx in $CTX_SIZES; do
      RESULTS["$model|$ctx"]="SKIP|0|"
    done
    continue
  fi

  for ctx in $CTX_SIZES; do
    log "Testing ctx=$ctx — unloading all models first..."
    unload_all
    baseline=$(vram_used_mib)

    log "Loading $model at num_ctx=$ctx..."
    t0=$(date +%s%3N)
    probe_result=$(load_and_probe "$model" "$ctx")
    t1=$(date +%s%3N)
    elapsed_s=$(( (t1 - t0) / 1000 ))

    success=$(echo "$probe_result" | cut -d'|' -f1)
    err_msg=$(echo "$probe_result" | cut -d'|' -f2)
    tok_s=$(echo "$probe_result" | cut -d'|' -f3)

    vram_after=$(vram_used_mib)
    vram_model=$(( vram_after - baseline ))
    headroom=$(( VRAM_TOTAL_MIB - vram_after ))

    if [[ "$success" == "1" ]]; then
      if [[ $headroom -gt $HEADROOM_WARN_MIB ]]; then
        verdict="PASS"
      elif [[ $headroom -gt $HEADROOM_FAIL_MIB ]]; then
        verdict="WARN"
      else
        verdict="WARN(tight)"
      fi
      tok_label=""
      [[ -n "$tok_s" ]] && tok_label=" ${tok_s} tok/s"
      ok "$model @ ctx=$ctx → $verdict | VRAM: ${vram_after} MiB used (+${vram_model} over baseline) | ${headroom} MiB free${tok_label} | ${elapsed_s}s load"
    else
      verdict="FAIL"
      fail_msg "$model @ ctx=$ctx → FAIL | $err_msg | VRAM: ${vram_after} MiB"
    fi

    RESULTS["$model|$ctx"]="$verdict|$vram_after|$tok_s"
  done
done

# ── summary table ─────────────────────────────────────────────────────────────

echo
echo "════════════════════════════════════════════════════════════"
echo "  SUMMARY"
echo "════════════════════════════════════════════════════════════"
printf "  %-30s %8s %12s %12s %10s\n" "Model" "ctx" "verdict" "VRAM used" "tok/s"
printf "  %-30s %8s %12s %12s %10s\n" "-----" "---" "-------" "---------" "-----"

for model in $INFER_MODELS; do
  for ctx in $CTX_SIZES; do
    key="$model|$ctx"
    if [[ -v "RESULTS[$key]" ]]; then
      verdict=$(echo "${RESULTS[$key]}" | cut -d'|' -f1)
      vram=$(echo "${RESULTS[$key]}" | cut -d'|' -f2)
      tok_s=$(echo "${RESULTS[$key]}" | cut -d'|' -f3)
      headroom=$(( VRAM_TOTAL_MIB - vram ))
      printf "  %-30s %8s %12s %9s MiB %10s\n" "$model" "$ctx" "$verdict" "$vram" "${tok_s:-—}"
    fi
  done
done

echo
log "$(vram_line)"
echo
echo "  Next steps if probes pass:"
echo "    1. Update personas/models.yaml num_ctx comments for each model"
echo "    2. Update personas/registry.yaml num_ctx for personas using these models"
echo "    3. Update ref:active-decisions num_ctx line in .claude/session-context.md"
echo "════════════════════════════════════════════════════════════"
