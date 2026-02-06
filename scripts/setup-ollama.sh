#!/bin/bash
# =============================================================================
# Ollama Setup Script — RTX 3060 12GB
# =============================================================================
# Idempotent: safe to run multiple times. Skips steps already completed.
#
# What this script does:
#   1. Installs Ollama (if not already present)
#   2. Configures the systemd service (environment overrides)
#   3. Pulls the base model (qwen2.5-coder:7b)
#   4. Creates the custom model (my-coder) from the Modelfile
#
# Prerequisites:
#   - WSL2 with Ubuntu (systemd enabled)
#   - NVIDIA GPU visible via nvidia-smi
#   - Internet connection (for initial install/pull)
#
# Usage:
#   chmod +x scripts/setup-ollama.sh
#   ./scripts/setup-ollama.sh
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — edit these to customize the setup
# ---------------------------------------------------------------------------
BASE_MODEL="qwen2.5-coder:7b"
CUSTOM_MODEL_NAME="my-coder"

# Resolve paths relative to this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
MODELFILE="${REPO_DIR}/modelfiles/coding-assistant.Modelfile"

# Ollama service settings
OLLAMA_OVERRIDE_DIR="/etc/systemd/system/ollama.service.d"
OLLAMA_OVERRIDE_FILE="${OLLAMA_OVERRIDE_DIR}/override.conf"

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
echo "=== Ollama Setup Script ==="
echo ""

# Verify GPU is visible (hard requirement — no point continuing without it)
if ! command -v nvidia-smi &> /dev/null || ! nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not available or GPU not detected."
    echo "  - On WSL2: ensure Windows NVIDIA driver 545+ is installed"
    echo "  - Never install Linux NVIDIA drivers inside WSL2"
    exit 1
fi
echo "[OK] GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader)"

# Verify the Modelfile exists
if [ ! -f "$MODELFILE" ]; then
    echo "ERROR: Modelfile not found at: $MODELFILE"
    echo "  - Expected: modelfiles/coding-assistant.Modelfile in the repo root"
    exit 1
fi
echo "[OK] Modelfile found: $MODELFILE"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Install Ollama
# ---------------------------------------------------------------------------
if command -v ollama &> /dev/null; then
    echo "[SKIP] Ollama already installed: $(ollama --version)"
else
    echo "[INSTALL] Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "[OK] Ollama installed"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 2: Configure systemd service override
# ---------------------------------------------------------------------------
if [ -f "$OLLAMA_OVERRIDE_FILE" ]; then
    echo "[SKIP] Service override already exists: $OLLAMA_OVERRIDE_FILE"
else
    echo "[CONFIG] Creating systemd override..."
    sudo mkdir -p "$OLLAMA_OVERRIDE_DIR"
    sudo tee "$OLLAMA_OVERRIDE_FILE" > /dev/null <<'EOF'
[Service]
# Listen on all interfaces so Windows apps can reach the API
Environment="OLLAMA_HOST=0.0.0.0:11434"

# Allow CORS from any origin (for web UIs / browser extensions)
Environment="OLLAMA_ORIGINS=*"

# Enable Flash Attention: ~30% VRAM savings on context processing
Environment="OLLAMA_FLASH_ATTENTION=1"

# Keep model loaded in VRAM for 30 minutes (default is 5m)
Environment="OLLAMA_KEEP_ALIVE=30m"
EOF
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
    echo "[OK] Service configured and restarted"
    # Give Ollama a moment to initialize after restart
    sleep 3
fi
echo ""

# ---------------------------------------------------------------------------
# Step 3: Pull base model
# ---------------------------------------------------------------------------
# ollama pull is itself idempotent — if the model exists and is up-to-date,
# it finishes instantly with "up to date"
echo "[MODEL] Pulling ${BASE_MODEL}..."
ollama pull "$BASE_MODEL"
echo "[OK] Base model ready"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Create custom model from Modelfile
# ---------------------------------------------------------------------------
# ollama create is also idempotent — re-running it updates the model
# to match the current Modelfile (useful if you change parameters)
echo "[MODEL] Creating custom model: ${CUSTOM_MODEL_NAME}..."
ollama create "$CUSTOM_MODEL_NAME" -f "$MODELFILE"
echo "[OK] Custom model ready"
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "=== Setup Complete ==="
echo ""
echo "Installed models:"
ollama list
echo ""
echo "API endpoint: http://localhost:11434"
echo ""
echo "Quick test:"
echo "  ollama run ${CUSTOM_MODEL_NAME} \"Write a hello world in Go\""
