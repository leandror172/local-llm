#!/bin/bash
# =============================================================================
# Ollama Installation Verification Script
# =============================================================================
# Runs a comprehensive check of the Ollama installation:
#   1. GPU visibility
#   2. Service status and configuration
#   3. Model inventory and GPU allocation
#   4. API endpoint health
#   5. Generation performance benchmark
#
# Usage:
#   chmod +x scripts/verify-installation.sh
#   ./scripts/verify-installation.sh
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed
# =============================================================================

set -uo pipefail

PASS=0
FAIL=0
WARN=0
CUSTOM_MODEL="my-coder"
PERF_TARGET_MIN=40   # tok/s
PERF_TARGET_MAX=60   # tok/s (exceeding is fine)

pass() { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }
warn() { echo "  [WARN] $1"; WARN=$((WARN + 1)); }

# ---------------------------------------------------------------------------
# 1. GPU Visibility
# ---------------------------------------------------------------------------
echo ""
echo "=== 1. GPU Visibility ==="

if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null)
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null)
    DRIVER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null)
    pass "GPU detected: ${GPU_NAME} (${GPU_VRAM}, driver ${DRIVER})"
else
    fail "nvidia-smi not available or GPU not detected"
fi

# ---------------------------------------------------------------------------
# 2. Service Status
# ---------------------------------------------------------------------------
echo ""
echo "=== 2. Service Status ==="

if systemctl is-active ollama &> /dev/null; then
    pass "Ollama service is running"
else
    fail "Ollama service is not running"
fi

if systemctl is-enabled ollama &> /dev/null; then
    pass "Ollama service is enabled (auto-start)"
else
    warn "Ollama service is not enabled for auto-start"
fi

if [ -f /etc/systemd/system/ollama.service.d/override.conf ]; then
    pass "Systemd override config exists"

    # Check key settings from the override
    if grep -q "OLLAMA_HOST=0.0.0.0" /etc/systemd/system/ollama.service.d/override.conf; then
        pass "OLLAMA_HOST configured (all interfaces)"
    else
        warn "OLLAMA_HOST not set to 0.0.0.0"
    fi

    if grep -q "OLLAMA_FLASH_ATTENTION=1" /etc/systemd/system/ollama.service.d/override.conf; then
        pass "Flash Attention enabled"
    else
        warn "Flash Attention not enabled"
    fi
else
    warn "No systemd override config found"
fi

# ---------------------------------------------------------------------------
# 3. Models
# ---------------------------------------------------------------------------
echo ""
echo "=== 3. Models ==="

if command -v ollama &> /dev/null; then
    pass "Ollama CLI available: $(ollama --version 2>/dev/null || echo 'unknown version')"
else
    fail "Ollama CLI not found"
fi

MODEL_LIST=$(ollama list 2>/dev/null)
if echo "$MODEL_LIST" | grep -q "qwen2.5-coder"; then
    pass "Base model installed: qwen2.5-coder:7b"
else
    fail "Base model qwen2.5-coder:7b not found"
fi

if echo "$MODEL_LIST" | grep -q "$CUSTOM_MODEL"; then
    pass "Custom model installed: ${CUSTOM_MODEL}"
else
    fail "Custom model ${CUSTOM_MODEL} not found"
fi

# ---------------------------------------------------------------------------
# 4. API Endpoints
# ---------------------------------------------------------------------------
echo ""
echo "=== 4. API Endpoints ==="

if curl -sf http://localhost:11434/ > /dev/null 2>&1; then
    pass "API root responds (http://localhost:11434)"
else
    fail "API root not responding"
fi

TAGS_RESPONSE=$(curl -sf http://localhost:11434/api/tags 2>/dev/null)
if [ -n "$TAGS_RESPONSE" ]; then
    pass "/api/tags endpoint responds"
else
    fail "/api/tags endpoint not responding"
fi

# Test chat endpoint (also warms up the model for the benchmark)
echo "  [ .. ] Testing /api/chat endpoint (loading model)..."
CHAT_RESPONSE=$(curl -sf --max-time 120 http://localhost:11434/api/chat -d "{
  \"model\": \"${CUSTOM_MODEL}\",
  \"messages\": [{\"role\": \"user\", \"content\": \"Say: verification passed\"}],
  \"stream\": false
}" 2>/dev/null)

if echo "$CHAT_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('done') else 1)" 2>/dev/null; then
    pass "/api/chat endpoint responds with ${CUSTOM_MODEL}"
else
    fail "/api/chat endpoint failed"
fi

# Check GPU allocation after model load
GPU_ALLOC=$(ollama ps 2>/dev/null | grep "$CUSTOM_MODEL" | awk '{print $4, $5}')
if echo "$GPU_ALLOC" | grep -q "100%"; then
    pass "Model running at 100% GPU"
else
    if [ -n "$GPU_ALLOC" ]; then
        warn "Model GPU allocation: ${GPU_ALLOC} (expected 100% GPU)"
    else
        fail "Model not loaded in GPU"
    fi
fi

# ---------------------------------------------------------------------------
# 5. Performance Benchmark
# ---------------------------------------------------------------------------
echo ""
echo "=== 5. Performance Benchmark ==="

echo "  [ .. ] Running benchmark (this takes a few seconds)..."
BENCH_RESPONSE=$(curl -sf --max-time 120 http://localhost:11434/api/chat -d "{
  \"model\": \"${CUSTOM_MODEL}\",
  \"messages\": [{\"role\": \"user\", \"content\": \"Write a thread-safe counter struct in Go with Increment, Decrement, and Value methods.\"}],
  \"stream\": false
}" 2>/dev/null)

if [ -n "$BENCH_RESPONSE" ]; then
    EVAL_RATE=$(echo "$BENCH_RESPONSE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
count = d.get('eval_count', 0)
dur = d.get('eval_duration', 1) / 1e9
rate = count / dur if dur > 0 else 0
print(f'{rate:.1f}')
" 2>/dev/null)

    EVAL_COUNT=$(echo "$BENCH_RESPONSE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('eval_count', 0))
" 2>/dev/null)

    if [ -n "$EVAL_RATE" ]; then
        RATE_INT=${EVAL_RATE%.*}
        if [ "$RATE_INT" -ge "$PERF_TARGET_MIN" ]; then
            pass "Generation speed: ${EVAL_RATE} tok/s (${EVAL_COUNT} tokens) — target: ${PERF_TARGET_MIN}+ tok/s"
        else
            fail "Generation speed: ${EVAL_RATE} tok/s — below target of ${PERF_TARGET_MIN} tok/s"
        fi
    else
        fail "Could not parse benchmark results"
    fi
else
    fail "Benchmark request failed"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "==========================================="
echo "  PASS: ${PASS}   FAIL: ${FAIL}   WARN: ${WARN}"
echo "==========================================="

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "  Some checks failed. Review the output above."
    exit 1
else
    echo ""
    echo "  All checks passed!"
    exit 0
fi
