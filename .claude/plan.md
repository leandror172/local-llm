# Plan: Install and Configure Local LLM with Portable Setup

## Overview

Install Ollama with Qwen2.5-Coder on WSL2, creating a semi-portable configuration that can be migrated to native Linux or other machines. Both native and Docker approaches will be implemented.

**Target Stack:**
- Inference Engine: Ollama
- Model: Qwen2.5-Coder-7B (Q4_K_M quantization)
- Environment: WSL2 (primary), Docker Compose (portable)
- Expected Performance: 40-60 tokens/second on RTX 3060 12GB

---

## Phase 0: Verification (Pre-flight Checks)

Validate hardware, software, and existing configurations before any installation.

### 0.1 Hardware Verification

**0.1.1 Check GPU from Windows (PowerShell)**
```powershell
# Get GPU details
Get-WmiObject Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion

# Check NVIDIA driver version (need 545+)
nvidia-smi
```

**0.1.2 Check system memory**
```powershell
Get-WmiObject Win32_ComputerSystem | Select-Object TotalPhysicalMemory
# Need: 32GB+ recommended for comfortable operation
```

**0.1.3 Check available disk space**
```powershell
Get-PSDrive C | Select-Object Used, Free
# Need: 50-100GB free for models
```

### 0.2 WSL2 Verification

**0.2.1 Check WSL version and status**
```powershell
wsl --version
wsl --list --verbose
# Need: WSL version 2, kernel 5.10.43.3+
```

**0.2.2 Check if WSL2 is installed and Ubuntu available**
```powershell
wsl cat /proc/version
# Should show Linux kernel version
```

**0.2.3 Check systemd status inside WSL2**
```bash
# Inside WSL2
systemctl --version
cat /etc/wsl.conf | grep systemd
```

### 0.3 GPU Visibility in WSL2

**0.3.1 Verify NVIDIA driver passthrough**
```bash
# Inside WSL2 - this MUST work before proceeding
nvidia-smi
# Should show RTX 3060 with ~12288MiB memory
```

**0.3.2 Check CUDA availability**
```bash
# Inside WSL2
ls /usr/lib/wsl/lib/libcuda*
# Should show libcuda.so files from Windows driver
```

### 0.4 Existing Software Check

**0.4.1 Check if Ollama already installed**
```bash
which ollama
ollama --version
systemctl status ollama 2>/dev/null
```

**0.4.2 Check Docker availability (for Phase 3)**
```bash
docker --version
docker compose version
```

**0.4.3 Check for conflicting services on port 11434**
```bash
ss -tlnp | grep 11434
```

### 0.5 Create Verification Report

Document findings in `verification-report.md` with:
- GPU model and VRAM
- Driver version
- WSL2 kernel version
- systemd status
- Existing installations
- Disk space available
- Any blockers identified

---

## Phase 1: WSL2 Environment Setup

Prepare WSL2 for Ollama installation.

### 1.1 Enable systemd (if not already enabled)

**1.1.1 Create/update wsl.conf**
```bash
sudo tee /etc/wsl.conf > /dev/null <<EOF
[boot]
systemd=true
EOF
```

**1.1.2 Restart WSL2 (from PowerShell)**
```powershell
wsl --shutdown
# Then reopen Ubuntu terminal
```

**1.1.3 Verify systemd is running**
```bash
systemctl list-units --type=service | head -20
```

### 1.2 Install CUDA Toolkit (optional but recommended)

Only the toolkit, NEVER the drivers.

**1.2.1 Add CUDA repository**
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
```

**1.2.2 Download and install CUDA toolkit**
```bash
wget https://developer.download.nvidia.com/compute/cuda/12.6.2/local_installers/cuda-repo-wsl-ubuntu-12-6-local_12.6.2-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-6-local_12.6.2-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-6-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update && sudo apt-get -y install cuda-toolkit-12-6
```

### 1.3 Verify GPU is ready

**1.3.1 Final GPU check**
```bash
nvidia-smi
# Must show RTX 3060 with ~12288MiB
```

---

## Phase 2: Native Ollama Installation

Install Ollama directly on WSL2 (primary method).

### 2.1 Install Ollama

**2.1.1 Run installation script**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**2.1.2 Verify GPU detection in install output**
Expected: `>>> NVIDIA GPU installed.`

**2.1.3 Check service status**
```bash
sudo systemctl status ollama
```

### 2.2 Pull Primary Model

**2.2.1 Pull Qwen2.5-Coder 7B**
```bash
ollama pull qwen2.5-coder:7b
# ~4.7GB download
```

**2.2.2 Verify model installed**
```bash
ollama list
```

### 2.3 Initial Test

**2.3.1 Run quick generation test**
```bash
ollama run qwen2.5-coder:7b "Write a hello world in Go" --verbose
```

**2.3.2 Verify GPU usage**
```bash
ollama ps
# Should show "100% GPU"
```

---

## Phase 3: Configuration & Optimization

Create optimized, portable configuration files.

### 3.1 Create Project Directory Structure

```bash
mkdir -p ~/llm-config/{modelfiles,scripts,docker}
```

### 3.2 Create Modelfile for Coding Assistant

**File: `modelfiles/coding-assistant.Modelfile`**
```dockerfile
FROM qwen2.5-coder:7b

# Optimized for RTX 3060 12GB
PARAMETER num_ctx 16384
PARAMETER num_gpu 999
PARAMETER num_batch 512

# Coding-optimized inference
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Stop sequences
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

SYSTEM """You are an expert backend software engineer specializing in Java and Go.
You write clean, well-documented, production-ready code.
Follow SOLID principles and idiomatic language conventions.
Explain your reasoning when relevant.
Format all code in markdown code blocks with language tags."""
```

### 3.3 Create Custom Model

```bash
ollama create my-coder -f modelfiles/coding-assistant.Modelfile
```

### 3.4 Configure Ollama Service

**3.4.1 Create systemd override**
```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
EOF
```

**3.4.2 Apply configuration**
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 3.5 Create Setup Script (Portable)

**File: `scripts/setup-ollama.sh`**
```bash
#!/bin/bash
# Idempotent Ollama setup for RTX 3060 12GB
set -e

MODELS=("qwen2.5-coder:7b")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELFILE_DIR="${SCRIPT_DIR}/../modelfiles"

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Configure environment
if ! grep -q "OLLAMA_HOST" /etc/systemd/system/ollama.service.d/override.conf 2>/dev/null; then
    sudo mkdir -p /etc/systemd/system/ollama.service.d
    sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KEEP_ALIVE=30m"
EOF
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
fi

sleep 5

# Pull models
for model in "${MODELS[@]}"; do
    echo "Pulling $model..."
    ollama pull "$model"
done

# Create custom models from Modelfiles
if [ -f "${MODELFILE_DIR}/coding-assistant.Modelfile" ]; then
    echo "Creating custom model: my-coder"
    ollama create my-coder -f "${MODELFILE_DIR}/coding-assistant.Modelfile"
fi

echo "Setup complete!"
ollama list
```

---

## Phase 4: Docker Portable Setup

Create Docker Compose configuration for maximum portability.

### 4.1 Install Docker Prerequisites

**4.1.1 Install Docker Engine**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Log out and back in
```

**4.1.2 Install NVIDIA Container Toolkit**
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

**4.1.3 Verify GPU access in Docker**
```bash
docker run --rm --gpus all ubuntu nvidia-smi
```

### 4.2 Create Docker Compose Configuration

**File: `docker/docker-compose.yml`**
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
      - ../modelfiles:/modelfiles:ro
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_KEEP_ALIVE=30m
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_FLASH_ATTENTION=1
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  ollama_data:
```

### 4.3 Create Docker Initialization Script

**File: `docker/init-docker.sh`**
```bash
#!/bin/bash
set -e

echo "Starting Ollama container..."
docker compose up -d

echo "Waiting for Ollama to be ready..."
until docker exec ollama ollama list &>/dev/null; do
    sleep 2
done

echo "Pulling model..."
docker exec ollama ollama pull qwen2.5-coder:7b

echo "Creating custom model..."
docker exec ollama ollama create my-coder -f /modelfiles/coding-assistant.Modelfile

echo "Done! API available at http://localhost:11434"
docker exec ollama ollama list
```

---

## Phase 5: Verification & Testing

Complete testing to ensure everything works correctly.

### 5.1 Service Verification

**5.1.1 Check Ollama service**
```bash
systemctl status ollama
curl -s http://localhost:11434/
```

**5.1.2 Check GPU detection in logs**
```bash
journalctl -u ollama --no-pager | grep -i -E 'gpu|cuda|nvidia'
```

### 5.2 Model Verification

**5.2.1 List models**
```bash
ollama list
```

**5.2.2 Check model GPU allocation**
```bash
ollama ps
# Must show "100% GPU"
```

### 5.3 Performance Verification

**5.3.1 Run benchmark prompt**
```bash
ollama run qwen2.5-coder:7b --verbose "Write a function in Go that implements a thread-safe LRU cache"
```

**5.3.2 Check metrics**
- `eval_rate`: Should be 40-60 tok/s
- `prompt_eval_rate`: Should be 100-500 tok/s

**5.3.3 Monitor GPU during generation**
```bash
# In separate terminal
watch -n 1 nvidia-smi
# Should see GPU-Util spike to 60-100%
```

### 5.4 API Verification

**5.4.1 Test generate endpoint**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Hello",
  "stream": false
}'
```

**5.4.2 Test chat endpoint**
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "my-coder",
  "messages": [{"role": "user", "content": "Explain Go interfaces in 2 sentences"}],
  "stream": false
}'
```

### 5.5 Create Verification Script

**File: `scripts/verify-installation.sh`**
```bash
#!/bin/bash
echo "=== Ollama Installation Verification ==="

echo -e "\n1. Service Status:"
systemctl is-active ollama && echo "✓ Service running" || echo "✗ Service not running"

echo -e "\n2. API Availability:"
curl -sf http://localhost:11434/ > /dev/null && echo "✓ API responding" || echo "✗ API not responding"

echo -e "\n3. GPU Detection:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

echo -e "\n4. Installed Models:"
ollama list

echo -e "\n5. GPU Allocation:"
ollama ps

echo -e "\n6. Generation Test:"
ollama run qwen2.5-coder:7b "Say 'test passed'" 2>/dev/null | head -1

echo -e "\n=== Verification Complete ==="
```

---

## Phase 6: Documentation & Artifacts

Update repository documentation.

### 6.1 Update CLAUDE.md

Add sections for:
- New directory structure
- How to run the LLM
- Configuration file locations
- Docker vs native usage

### 6.2 Final Directory Structure

```
I:\workspaces\llm\
├── CLAUDE.md                          # Updated project guidance
├── local-llm_and_open-claw.md         # Original research
├── llm-configuration-research.md       # Detailed config research
├── verification-report.md              # Phase 0 findings
├── modelfiles/
│   └── coding-assistant.Modelfile      # Custom model config
├── scripts/
│   ├── setup-ollama.sh                 # Idempotent native setup
│   └── verify-installation.sh          # Verification checklist
└── docker/
    ├── docker-compose.yml              # Portable Docker config
    └── init-docker.sh                  # Docker initialization
```

---

## Execution Order Summary

1. **Phase 0**: Run all verification commands, document in `verification-report.md`
2. **Phase 1**: Setup WSL2 environment (systemd, optional CUDA toolkit)
3. **Phase 2**: Install Ollama native, pull model, initial test
4. **Phase 3**: Create configuration files and custom model
5. **Phase 4**: Setup Docker portable environment
6. **Phase 5**: Run full verification suite
7. **Phase 6**: Update documentation

---

## Critical Files to Create/Modify

| File | Purpose |
|------|---------|
| `verification-report.md` | Hardware/software verification results |
| `modelfiles/coding-assistant.Modelfile` | Custom model configuration |
| `scripts/setup-ollama.sh` | Idempotent native installation |
| `scripts/verify-installation.sh` | Verification checklist |
| `docker/docker-compose.yml` | Portable Docker configuration |
| `docker/init-docker.sh` | Docker initialization |
| `CLAUDE.md` | Updated project documentation |

## Success Criteria

- [ ] `nvidia-smi` shows RTX 3060 in WSL2
- [ ] `ollama ps` shows "100% GPU"
- [ ] Generation speed is 40-60 tok/s
- [ ] API responds at `http://localhost:11434`
- [ ] Custom model `my-coder` created and working
- [ ] Docker setup runs independently
- [ ] All artifacts are version-controlled and portable
