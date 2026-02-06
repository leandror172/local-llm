#!/bin/bash
# =============================================================================
# Docker Initialization Script — Ollama + Custom Model
# =============================================================================
# Run this AFTER `docker compose up -d` to pull models and create the
# custom coding assistant inside the container.
#
# What this script does:
#   1. Starts the Ollama container (if not already running)
#   2. Waits for the Ollama API to become ready
#   3. Pulls the base model (qwen2.5-coder:7b)
#   4. Creates the custom model (my-coder) from the mounted Modelfile
#
# Usage:
#   cd docker/
#   docker compose up -d       # start the container first
#   ./init-docker.sh           # then run this script
#
# Or simply:
#   ./init-docker.sh           # does both (starts container if needed)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONTAINER_NAME="ollama"
BASE_MODEL="qwen2.5-coder:7b"
CUSTOM_MODEL_NAME="my-coder"
MODELFILE_PATH="/modelfiles/coding-assistant.Modelfile"
MAX_WAIT_SECONDS=60

# ---------------------------------------------------------------------------
# Change to the directory containing docker-compose.yml
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Ollama Docker Initialization ==="
echo ""

# ---------------------------------------------------------------------------
# Step 1: Ensure the container is running
# ---------------------------------------------------------------------------
if docker compose ps --format '{{.State}}' 2>/dev/null | grep -q "running"; then
    echo "[SKIP] Container already running"
else
    echo "[START] Starting Ollama container..."
    docker compose up -d
fi
echo ""

# ---------------------------------------------------------------------------
# Step 2: Wait for Ollama API to be ready
# ---------------------------------------------------------------------------
echo "[WAIT] Waiting for Ollama API (up to ${MAX_WAIT_SECONDS}s)..."
elapsed=0
until docker exec "$CONTAINER_NAME" ollama list &>/dev/null; do
    if [ "$elapsed" -ge "$MAX_WAIT_SECONDS" ]; then
        echo "ERROR: Ollama did not become ready within ${MAX_WAIT_SECONDS}s"
        echo "  Check logs: docker compose logs"
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done
echo "[OK] Ollama API is ready (took ${elapsed}s)"
echo ""

# ---------------------------------------------------------------------------
# Step 3: Pull base model
# ---------------------------------------------------------------------------
echo "[MODEL] Pulling ${BASE_MODEL}..."
docker exec "$CONTAINER_NAME" ollama pull "$BASE_MODEL"
echo "[OK] Base model ready"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Create custom model from mounted Modelfile
# ---------------------------------------------------------------------------
echo "[MODEL] Creating custom model: ${CUSTOM_MODEL_NAME}..."
docker exec "$CONTAINER_NAME" ollama create "$CUSTOM_MODEL_NAME" -f "$MODELFILE_PATH"
echo "[OK] Custom model ready"
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "=== Docker Setup Complete ==="
echo ""
echo "Installed models:"
docker exec "$CONTAINER_NAME" ollama list
echo ""
echo "Container status:"
docker compose ps
echo ""
echo "API endpoint: http://localhost:11434"
echo ""
echo "Quick test:"
echo "  docker exec $CONTAINER_NAME ollama run ${CUSTOM_MODEL_NAME} \"Write a hello world in Go\""
