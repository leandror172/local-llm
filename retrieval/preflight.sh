#!/usr/bin/env bash
set -euo pipefail

PY=python3
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
PHASE1_JSONL="retrieval/runs/20260416-181839.jsonl"
EMBED_MODEL="${EMBED_MODEL:-bge-m3}"

echo "== LTG Phase 2 pre-flight =="

echo -n "[1/5] Python deps... "
$PY -c "import httpx, lancedb, pyarrow" 2>/dev/null \
  && echo "ok" \
  || { echo "MISSING — run: pip install httpx 'lancedb>=0.20,<0.29' pyarrow"; exit 2; }

echo -n "[2/5] Ollama reachable at $OLLAMA_URL... "
curl -fsS "$OLLAMA_URL/api/tags" >/dev/null \
  && echo "ok" \
  || { echo "FAIL — start Ollama or set OLLAMA_URL"; exit 3; }

echo -n "[3/5] Embed model '$EMBED_MODEL' pulled... "
curl -fsS "$OLLAMA_URL/api/tags" | grep -q "\"$EMBED_MODEL" \
  && echo "ok" \
  || { echo "MISSING — run: ollama pull $EMBED_MODEL"; exit 4; }

echo -n "[4/5] Phase 1 input ($PHASE1_JSONL)... "
[ -s "$PHASE1_JSONL" ] \
  && echo "ok ($(wc -l <"$PHASE1_JSONL") rows)" \
  || { echo "MISSING — re-run Phase 1 or check path"; exit 5; }

echo -n "[5/5] Disk space in retrieval/... "
AVAIL_KB=$(df -k retrieval/ | awk 'NR==2 {print $4}')
[ "$AVAIL_KB" -gt 102400 ] \
  && echo "ok ($((AVAIL_KB/1024)) MB free)" \
  || { echo "LOW (<100MB); not a blocker, but consider cleaning"; }

echo "== Pre-flight OK =="
