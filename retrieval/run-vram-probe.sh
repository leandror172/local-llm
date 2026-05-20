#!/usr/bin/env bash
# VRAM co-residence probe: qwen3:14b + bge-m3
# Phase 2 gate for LTG embedding model selection.
# Tests whether both models can coexist in VRAM at query time.
#
# Usage:
#   retrieval/run-vram-probe.sh              # 5 interleaved rounds (default)
#   retrieval/run-vram-probe.sh --rounds N   # custom round count
#   retrieval/run-vram-probe.sh --verbose    # show raw API response excerpts
#
# Exit codes: 0 = PASS or WARN, 1 = FAIL or error
#
# Verdict criteria:
#   PASS — both models in ollama ps after load; infer rounds 2+ all < 15s
#   WARN — eviction at load time only (sequential indexing ok; no query-time overlap)
#   FAIL — eviction at query time (infer > 15s after interleaved embed)
#          → drop to mxbai-embed-large and re-run

set -euo pipefail

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
ROUNDS=5
EVICTION_THRESHOLD_MS=15000
VERBOSE=0
INFER_MODEL="qwen3:14b"
EMBED_MODEL="bge-m3"

while [[ $# -gt 0 ]]; do
  case $1 in
    --rounds) ROUNDS="$2"; shift 2 ;;
    --verbose) VERBOSE=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ── helpers ───────────────────────────────────────────────────────────────────

log()     { echo "  $*"; }
ok()      { echo "  ✓ $*"; }
warn_msg(){ echo "  ⚠ $*"; }
fail_msg(){ echo "  ✗ $*"; }
section() { echo; echo "── $1 ──────────────────────────────────────────────────────"; }
ms_now()  { date +%s%3N; }

vram_status() {
  nvidia-smi --query-gpu=memory.used,memory.free,memory.total \
    --format=csv,noheader,nounits 2>/dev/null \
    | awk -F', ' '{printf "VRAM: %s MiB used / %s MiB free / %s MiB total\n",$1,$2,$3}'
}

both_loaded() {
  local ps; ps=$(ollama ps 2>/dev/null)
  echo "$ps" | grep -q "$INFER_MODEL" && echo "$ps" | grep -q "$EMBED_MODEL"
}

loaded_models() {
  ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}' | tr '\n' ' '
}

do_embed() {
  local input="$1"
  local resp
  resp=$(curl -s --max-time 60 "$OLLAMA_URL/api/embed" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$EMBED_MODEL\",\"input\":\"$input\"}")
  [[ $VERBOSE -eq 1 ]] && log "embed raw: ${resp:0:100}..."
  python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'embeddings' not in r:
    print('ERROR:' + r.get('error','unknown'), file=sys.stderr); sys.exit(1)
print(len(r['embeddings'][0]))
" <<< "$resp"
}

do_infer() {
  local prompt="$1"
  local resp
  resp=$(curl -s --max-time 120 "$OLLAMA_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$INFER_MODEL\",\"stream\":false,\"think\":false,\"messages\":[{\"role\":\"user\",\"content\":\"$prompt\"}]}")
  [[ $VERBOSE -eq 1 ]] && log "infer raw: ${resp:0:100}..."
  python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'message' not in r:
    print('ERROR:' + r.get('error','unknown'), file=sys.stderr); sys.exit(1)
print(r['message']['content'][:60].strip())
" <<< "$resp"
}

# ── preflight ─────────────────────────────────────────────────────────────────

echo "════════════════════════════════════════════════════════════"
echo "  VRAM Co-Residence Probe — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  infer=$INFER_MODEL  embed=$EMBED_MODEL  rounds=$ROUNDS"
echo "════════════════════════════════════════════════════════════"

section "Preflight — model availability"
OLLAMA_LIST=$(ollama list 2>/dev/null)
for model in "$INFER_MODEL" "$EMBED_MODEL"; do
  if echo "$OLLAMA_LIST" | grep -q "$model"; then
    ok "$model pulled"
  else
    fail_msg "$model not found — run: ollama pull $model"
    exit 1
  fi
done
log "$(vram_status)"

# ── stage 1: baseline ─────────────────────────────────────────────────────────

section "Stage 1 — Unload any cached models (5-min idle timeout)"
log "currently loaded: $(loaded_models || echo '(none)')"
log "if models are loaded from a prior session, baseline VRAM may be high"

# ── stage 2: load infer model ─────────────────────────────────────────────────

section "Stage 2 — Load $INFER_MODEL (first call; expect 20-40s)"
t0=$(ms_now)
result=$(do_infer "say ok")
t1=$(ms_now)
elapsed=$(( t1 - t0 ))
ok "infer: '${result}' (${elapsed}ms)"
log "$(vram_status)"
log "loaded: $(loaded_models)"

# ── stage 3: load embed model alongside ──────────────────────────────────────

section "Stage 3 — Load $EMBED_MODEL alongside $INFER_MODEL"
t0=$(ms_now)
dims=$(do_embed "thinking mode handling in Ollama")
t1=$(ms_now)
elapsed=$(( t1 - t0 ))
ok "embed: ${dims} dims (${elapsed}ms)"
log "$(vram_status)"
log "loaded: $(loaded_models)"

echo
co_residence_ok=0
if both_loaded; then
  ok "BOTH MODELS IN VRAM simultaneously"
  co_residence_ok=1
else
  warn_msg "one model was evicted during load — sequential-only mode"
fi

# ── stage 4: interleaved stress ───────────────────────────────────────────────

section "Stage 4 — Interleaved stress ($ROUNDS rounds, embed→infer alternating)"
log "round 1 is warmup (excluded from eviction stats); threshold=${EVICTION_THRESHOLD_MS}ms"

eviction_count=0
max_infer_ms=0
total_infer_ms=0

for i in $(seq 1 "$ROUNDS"); do
  dims=$(do_embed "probe query round $i semantic retrieval test")

  t0=$(ms_now)
  result=$(do_infer "say ok $i")
  t1=$(ms_now)
  infer_ms=$(( t1 - t0 ))

  if [[ $i -eq 1 ]]; then
    ok "round $i (warmup): embed=${dims}d  infer=${infer_ms}ms"
    continue
  fi

  total_infer_ms=$(( total_infer_ms + infer_ms ))
  [[ $infer_ms -gt $max_infer_ms ]] && max_infer_ms=$infer_ms

  if [[ $infer_ms -gt $EVICTION_THRESHOLD_MS ]]; then
    eviction_count=$(( eviction_count + 1 ))
    warn_msg "round $i: embed=${dims}d  infer=${infer_ms}ms  ← EVICTION (>${EVICTION_THRESHOLD_MS}ms)"
  else
    ok "round $i: embed=${dims}d  infer=${infer_ms}ms  '${result:0:20}'"
  fi
done

warm_rounds=$(( ROUNDS - 1 ))
avg_infer_ms=0
[[ $warm_rounds -gt 0 ]] && avg_infer_ms=$(( total_infer_ms / warm_rounds ))

# ── verdict ───────────────────────────────────────────────────────────────────

echo
echo "════════════════════════════════════════════════════════════"
echo "  VERDICT"
echo "════════════════════════════════════════════════════════════"
log "co-residence after load:   $([ $co_residence_ok -eq 1 ] && echo 'YES' || echo 'NO (evicted at load)')"
log "evictions during stress:   $eviction_count / $warm_rounds warm rounds"
log "max infer latency (r2+):   ${max_infer_ms}ms"
log "avg infer latency (r2+):   ${avg_infer_ms}ms"
log "$(vram_status)"
echo

if [[ $eviction_count -eq 0 && $co_residence_ok -eq 1 ]]; then
  echo "  ✅  PASS — both models coexist at query time."
  echo "      Proceed with Phase 2: embed.py + store.py with bge-m3."
  exit 0
elif [[ $eviction_count -eq 0 ]]; then
  echo "  ⚠   WARN — eviction at load time only (query-time is ok)."
  echo "      Phase 2 indexing must be sequential (no parallel embed+infer)."
  echo "      Proceed with Phase 2, but note the sequential constraint."
  exit 0
else
  echo "  ❌  FAIL — query-time eviction detected ($eviction_count / $warm_rounds rounds)."
  echo "      Action: switch EMBED_MODEL to mxbai-embed-large and re-run."
  echo "        ollama pull mxbai-embed-large"
  echo "        EMBED_MODEL=mxbai-embed-large retrieval/run-vram-probe.sh"
  exit 1
fi
