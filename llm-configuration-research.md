# Portable local LLM deployment with Ollama and Qwen2.5-Coder

Running local LLMs provides complete privacy, zero per-query costs, and offline capability for coding assistance. For a backend architect with an **RTX 3060 12GB**, the optimal setup uses **Qwen2.5-Coder 7B (Q4_K_M)** which delivers **40-60 tokens/second** with full GPU utilization—fast enough for real-time coding assistance while leaving VRAM headroom for context. This document provides both design rationale and copy-paste implementation commands suitable for ClaudeCode execution across WSL2, native Linux, and Docker environments.

The key design decision is **Docker Compose for GPU-enabled Linux/WSL2** and **native installation for development machines**—Docker provides reproducibility and team portability, while native installation offers simplest setup for single-user scenarios. Infrastructure-as-code tools like Terraform are overkill for this use case; simple shell scripts or Ansible suffice for multi-machine deployment.

---

## Installation and environment setup

### WSL2 installation (Windows 10/11)

WSL2 requires special handling: the Windows NVIDIA driver provides CUDA support, so you must **never install Linux NVIDIA drivers inside WSL2**—this breaks GPU passthrough. Enable systemd first, then install Ollama.

**Prerequisites verification and WSL2 setup:**
```powershell
# PowerShell - Check WSL version (need 5.10.43.3+ kernel)
wsl cat /proc/version

# Enable WSL2 features if needed
wsl --install -d Ubuntu
wsl --set-default-version 2
```

**Inside WSL2 Ubuntu—enable systemd (required for Ollama service):**
```bash
# Edit WSL configuration
sudo tee /etc/wsl.conf > /dev/null <<EOF
[boot]
systemd=true
EOF
```

Then restart WSL from PowerShell: `wsl --shutdown` and reopen Ubuntu.

**Verify GPU visibility before installing Ollama:**
```bash
nvidia-smi
# Should show RTX 3060 with ~12GB VRAM
# If this fails, update Windows NVIDIA drivers (not Linux drivers)
```

**Install CUDA toolkit for WSL2 (toolkit only, never cuda-drivers):**
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.6.2/local_installers/cuda-repo-wsl-ubuntu-12-6-local_12.6.2-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-6-local_12.6.2-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-6-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update && sudo apt-get -y install cuda-toolkit-12-6
```

**Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Expected output confirms NVIDIA GPU detection:
```
>>> Downloading ollama...
>>> Installing ollama to /usr/local/bin...
>>> Creating ollama systemd service...
>>> Enabling and starting ollama service...
>>> NVIDIA GPU installed.
```

### Native Linux installation

Native Linux installation is straightforward—the install script handles systemd service creation and GPU detection automatically.

```bash
# Quick install (recommended)
curl -fsSL https://ollama.com/install.sh | sh

# Verify service is running
sudo systemctl status ollama

# Add current user to ollama group for model access
sudo usermod -a -G ollama $(whoami)
# Log out and back in for group changes
```

**Manual systemd service creation (if needed):**
```bash
sudo useradd -r -s /bin/false -U -m -d /usr/share/ollama ollama

sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ollama
```

### Directory structure and key paths

Understanding where Ollama stores data is critical for backup, migration, and troubleshooting.

| Component | Linux/WSL2 Path | Purpose |
|-----------|-----------------|---------|
| **Binary** | `/usr/local/bin/ollama` | Executable |
| **Models (user)** | `~/.ollama/models/` | Downloaded models |
| **Models (service)** | `/usr/share/ollama/.ollama/models/` | When running as systemd service |
| **Manifests** | `models/manifests/registry.ollama.ai/library/<model>/<tag>` | Model metadata JSON |
| **Blobs** | `models/blobs/sha256-<hash>` | Actual GGUF weight files |
| **Logs** | `journalctl -u ollama` | Service logs |

**Change model storage location:**
```bash
export OLLAMA_MODELS=/mnt/data/ollama-models
# Or for systemd service:
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_MODELS=/mnt/data/ollama-models"
```

### Essential environment variables

Configure these persistently in systemd for production deployments:

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

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

| Variable | Default | Purpose | RTX 3060 Recommendation |
|----------|---------|---------|-------------------------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | API bind address | `0.0.0.0:11434` for LAN access |
| `OLLAMA_MODELS` | `~/.ollama/models` | Model storage | External drive for large libraries |
| `OLLAMA_FLASH_ATTENTION` | `0` | Memory-efficient attention | `1` (saves ~30% VRAM) |
| `OLLAMA_KV_CACHE_TYPE` | `f16` | KV cache precision | `q8_0` for larger contexts |
| `OLLAMA_KEEP_ALIVE` | `5m` | Model unload delay | `30m` for frequent use |
| `OLLAMA_NUM_PARALLEL` | Auto | Concurrent requests | `2` for 12GB VRAM |

### GPU verification checklist

**Step 1: Confirm NVIDIA driver:**
```bash
nvidia-smi
# Expect: RTX 3060, ~12288MiB memory, driver version 545+
```

**Step 2: Check Ollama detected GPU:**
```bash
journalctl -u ollama --no-pager | grep -i -E 'gpu|cuda|nvidia'
# Look for: inference compute id=GPU-xxx library=CUDA compute=8.6 name="NVIDIA GeForce RTX 3060"
```

**Step 3: Verify GPU usage during inference:**
```bash
# Terminal 1: Start generation
ollama run qwen2.5-coder:7b "Write a hello world in Go"

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi
# Expect: Memory-Usage increases to ~6-7GB, GPU-Util spikes to 60-100%
```

**Step 4: Check model processor allocation:**
```bash
ollama ps
# Good output:
# NAME                ID           SIZE     PROCESSOR    UNTIL
# qwen2.5-coder:7b    abc123...    4.7 GB   100% GPU     4 minutes from now
```

If `PROCESSOR` shows `100% CPU` or `50%/50% CPU/GPU`, the model isn't fully utilizing your GPU—see troubleshooting section.

---

## Configuration management and portability

### Modelfile fundamentals

Modelfiles are the configuration-as-code mechanism for Ollama—they define model behavior, parameters, and system prompts. Every custom configuration should be captured in a Modelfile for reproducibility.

**Complete Modelfile for RTX 3060 12GB with Qwen2.5-Coder:**
```dockerfile
# coding-assistant.Modelfile
FROM qwen2.5-coder:7b

# Optimize for 12GB VRAM with comfortable headroom
PARAMETER num_ctx 16384
PARAMETER num_gpu 999
PARAMETER num_batch 512

# Coding-optimized inference settings
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Stop sequences for clean output
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# System prompt for backend development
SYSTEM """You are an expert backend software engineer specializing in Java and Go.
You write clean, well-documented, production-ready code.
Follow SOLID principles and idiomatic language conventions.
Explain your reasoning when relevant.
Format all code in markdown code blocks with language tags."""
```

**Create and use the custom model:**
```bash
ollama create my-coder -f coding-assistant.Modelfile
ollama run my-coder
```

**Export existing model configuration for backup:**
```bash
ollama show qwen2.5-coder:7b --modelfile > qwen2.5-coder-backup.Modelfile
```

### Docker-based deployment

Docker provides the best portability for GPU-enabled Linux and WSL2 deployments. The key requirements are: NVIDIA Container Toolkit installed, `--gpus` flag for GPU access, and volume mounts for model persistence.

**Prerequisites—install NVIDIA Container Toolkit:**
```bash
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access in Docker
docker run --rm --gpus all ubuntu nvidia-smi
```

**Production Docker Compose configuration:**
```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
      - ./modelfiles:/modelfiles:ro
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

  # Optional: Web UI for testing
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - open_webui_data:/app/backend/data
    depends_on:
      ollama:
        condition: service_healthy
    restart: unless-stopped

volumes:
  ollama_data:
  open_webui_data:
```

**Start and initialize:**
```bash
docker compose up -d

# Pull model inside container
docker exec ollama ollama pull qwen2.5-coder:7b

# Create custom model
docker cp coding-assistant.Modelfile ollama:/tmp/
docker exec ollama ollama create my-coder -f /tmp/coding-assistant.Modelfile

# Verify
docker exec ollama ollama list
```

### Export and migration strategies

**Strategy comparison for model portability:**

| Approach | Speed | Offline | Complexity | Best For |
|----------|-------|---------|------------|----------|
| Fresh `ollama pull` | Slow | No | Lowest | Internet-connected setups |
| rsync model directory | Fast | Yes | Low | LAN transfers, backups |
| Docker volume export | Medium | Yes | Medium | Docker-to-Docker migration |
| Baked Docker image | Slow build | Yes | High | Immutable deployments |
| NAS/shared storage | Instant | N/A | Medium | Team environments |

**rsync for direct model transfer (recommended for most cases):**
```bash
# Source machine
rsync -avP ~/.ollama/models/ user@target:/home/user/.ollama/models/

# Target machine - fix permissions if needed
chown -R $(whoami):$(whoami) ~/.ollama/models
chmod -R 755 ~/.ollama/models

# Verify
ollama list
```

**Docker volume backup and restore:**
```bash
# Export
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar cvf /backup/ollama-backup.tar /data

# Import on new system
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar xvf /backup/ollama-backup.tar -C /
```

### Infrastructure-as-code assessment

**When to use each approach:**

| Tool | Use Case | Verdict for Ollama |
|------|----------|-------------------|
| **Shell scripts** | Personal setup, single machine | ✅ Recommended for most cases |
| **Docker Compose** | Team standardization, reproducibility | ✅ Recommended for shared environments |
| **Ansible** | Multi-machine deployment, configuration drift | ✅ Useful for 3+ machines |
| **Terraform** | Cloud infrastructure provisioning | ⚠️ Overkill for local; useful for cloud GPU instances |

**Simple idempotent setup script (preferred over Ansible for single machines):**
```bash
#!/bin/bash
# setup-ollama.sh - Idempotent Ollama setup for RTX 3060

set -e

MODELS=("qwen2.5-coder:7b" "nomic-embed-text")
OLLAMA_HOST="0.0.0.0:11434"

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
Environment="OLLAMA_HOST=${OLLAMA_HOST}"
Environment="OLLAMA_FLASH_ATTENTION=1"
EOF
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
fi

# Wait for service
sleep 5

# Pull models
for model in "${MODELS[@]}"; do
    echo "Pulling $model..."
    ollama pull "$model"
done

echo "Setup complete!"
ollama list
```

---

## Model management for RTX 3060 12GB

### Qwen2.5-Coder variants and VRAM fit

The RTX 3060's **12GB VRAM** is the critical constraint. Model size plus KV cache must fit entirely in VRAM for optimal performance—partial CPU offloading causes **5-10x slowdown**.

| Model | Quantization | Disk Size | VRAM Usage | Context Fit | Speed | Recommendation |
|-------|--------------|-----------|------------|-------------|-------|----------------|
| **qwen2.5-coder:7b** | Q4_K_M | 4.7GB | ~6-7GB | 32K tokens | 40-60 tok/s | ✅ **Optimal choice** |
| qwen2.5-coder:14b | Q4_K_M | 9.0GB | ~10-11GB | 4-8K tokens | 15-30 tok/s | ⚠️ Tight fit, reduced context |
| qwen2.5-coder:14b | Q3_K_M | ~7GB | ~9GB | 8-16K tokens | 20-30 tok/s | ✅ Good 14B compromise |
| qwen2.5-coder:32b | Q4_K_M | 20GB | ~22-24GB | N/A | N/A | ❌ Won't fit |

**VRAM calculation rule of thumb:**
```
Total VRAM ≈ Model Weight File × 1.2 + KV Cache
KV Cache ≈ Context Length × 0.5MB (for 7B) or × 1MB (for 14B)
```

For **7B at 16K context**: ~4.7GB × 1.2 + 16K × 0.5MB ≈ **6.4GB** → fits comfortably

**Pull the recommended model:**
```bash
ollama pull qwen2.5-coder:7b
```

### Model operations reference

```bash
# List installed models with sizes
ollama list

# Show model details (architecture, quantization, parameters)
ollama show qwen2.5-coder:7b

# Remove unused models to free space
ollama rm qwen2.5-coder:32b

# Copy model for customization
ollama cp qwen2.5-coder:7b my-coder-base

# Update all models to latest versions
ollama list | tail -n +2 | awk '{print $1}' | xargs -I {} ollama pull {}

# Check running models and GPU allocation
ollama ps

# Unload model from memory
ollama stop qwen2.5-coder:7b
```

### Creating optimized custom models

**For maximum 14B performance on 12GB (reduced context):**
```dockerfile
# qwen14b-tight.Modelfile
FROM qwen2.5-coder:14b

PARAMETER num_ctx 4096
PARAMETER num_gpu 999
PARAMETER temperature 0.3

SYSTEM """Expert coding assistant for Java and Go development."""
```

```bash
ollama create qwen14b-tight -f qwen14b-tight.Modelfile
```

**Importing custom GGUF from HuggingFace:**
```dockerfile
# custom-model.Modelfile
FROM /path/to/downloaded/model.gguf

PARAMETER num_ctx 8192
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
```

---

## GPU and CPU configuration

### GPU layer control

The `num_gpu` parameter controls **how many transformer layers** load to GPU (not number of GPUs). Ollama auto-detects VRAM and optimizes by default, but explicit control is useful for predictable behavior.

| Setting | Effect |
|---------|--------|
| `num_gpu 0` | CPU-only inference |
| `num_gpu 999` | Force maximum GPU layers |
| `num_gpu 25` | Load exactly 25 layers to GPU (partial offload) |

**Performance cliff warning:** Partial offloading (e.g., 50% GPU) can be **slower than pure CPU** due to PCIe transfer overhead. Either fit the model entirely in VRAM or use CPU-only.

**Benchmark data (Qwen 8B on RTX 3060):**
| Configuration | Speed |
|---------------|-------|
| 100% GPU | 40+ tok/s |
| 50% GPU / 50% CPU | 8-12 tok/s |
| 100% CPU | 5-8 tok/s |

### Forcing CPU-only operation

Useful when GPU is busy with other tasks or for testing:

```bash
# Method 1: Environment variable
export CUDA_VISIBLE_DEVICES=-1
ollama serve

# Method 2: Modelfile parameter
# In Modelfile: PARAMETER num_gpu 0

# Method 3: API request option
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Hello",
  "options": {"num_gpu": 0}
}'
```

**CPU performance expectations (i5-12600K):**
| Model | Expected Speed |
|-------|----------------|
| 7B Q4_K_M | 5-8 tok/s |
| 14B Q4_K_M | 2-4 tok/s |

### VRAM optimization techniques

**Enable Flash Attention (saves ~30% VRAM):**
```bash
export OLLAMA_FLASH_ATTENTION=1
```

**Quantize KV cache (saves ~50% KV memory, slight quality loss):**
```bash
export OLLAMA_KV_CACHE_TYPE=q8_0  # Good balance
# or
export OLLAMA_KV_CACHE_TYPE=q4_0  # Aggressive, more quality loss
```

**Reduce context for larger models:**
```dockerfile
# In Modelfile
PARAMETER num_ctx 4096  # Instead of default 32K
```

### Monitoring GPU utilization

```bash
# Real-time monitoring during inference
watch -n 1 nvidia-smi

# Check Ollama's view of model allocation
ollama ps

# API check for detailed model info
curl -s http://localhost:11434/api/ps | jq '.models[] | {name, size_vram, processor}'
```

**What to look for:**
- **GPU-Util**: 60-100% during generation = healthy
- **Memory-Usage**: Should match model size + KV cache
- **PROCESSOR in ollama ps**: Should show "100% GPU" for optimal performance

---

## Networking and API access

### REST API quick reference

Ollama's API is OpenAI-compatible at `/v1/` endpoints and has native endpoints at `/api/`.

**Core endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/generate` | POST | One-shot text generation |
| `/api/chat` | POST | Multi-turn chat completions |
| `/api/embed` | POST | Generate embeddings |
| `/api/tags` | GET | List installed models |
| `/api/ps` | GET | List running models |
| `/v1/chat/completions` | POST | OpenAI-compatible chat |

**Basic generation example:**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a Go function to parse JSON",
  "stream": false,
  "options": {"temperature": 0.3}
}'
```

**Chat completion (maintains conversation):**
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen2.5-coder:7b",
  "messages": [
    {"role": "system", "content": "You are a Go expert."},
    {"role": "user", "content": "How do I handle errors idiomatically?"}
  ],
  "stream": false
}'
```

### Network exposure configuration

**Localhost only (default, secure):**
```bash
OLLAMA_HOST=127.0.0.1:11434
```

**LAN access (team sharing):**
```bash
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_ORIGINS=*
```

**WSL2 access from Windows host (mirrored networking—Windows 11):**
Create `%UserProfile%\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```
Then `wsl --shutdown` and restart.

**WSL2 port forwarding (Windows 10):**
```powershell
# Get WSL IP
$wslIp = wsl hostname -I
$wslIp = $wslIp.Trim()

# Configure port proxy
netsh interface portproxy add v4tov4 listenport=11434 listenaddress=0.0.0.0 connectport=11434 connectaddress=$wslIp

# Add firewall rule
New-NetFirewallRule -DisplayName "Ollama WSL2" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```

### Security considerations

**Ollama has NO built-in authentication.** For any network exposure beyond localhost, use a reverse proxy.

**Nginx with basic auth:**
```nginx
server {
    listen 443 ssl http2;
    server_name ollama.internal;
    
    ssl_certificate /etc/ssl/certs/ollama.crt;
    ssl_certificate_key /etc/ssl/private/ollama.key;
    
    auth_basic "Ollama API";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location / {
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host localhost:11434;
    }
}
```

**Create password file:**
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd apiuser
```

### Continue VS Code extension integration

Continue is the recommended IDE integration for local Ollama. Configure in `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Qwen2.5-Coder 7B",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://localhost:11434",
      "systemMessage": "You are an expert backend engineer specializing in Java and Go."
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen2.5-Coder 7B",
    "provider": "ollama",
    "model": "qwen2.5-coder:7b",
    "apiBase": "http://localhost:11434"
  }
}
```

**For remote Ollama (e.g., from Windows to WSL2):**
```json
{
  "models": [
    {
      "title": "Remote Qwen",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://192.168.1.100:11434"
    }
  ]
}
```

### OpenAI API compatibility

Use Ollama as a drop-in replacement for OpenAI in existing tools:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1/",
    api_key="ollama"  # Required but ignored
)

response = client.chat.completions.create(
    model="qwen2.5-coder:7b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Testing and verification checklist

### Post-installation verification

Run this checklist after any installation or configuration change:

```bash
#!/bin/bash
# verify-ollama.sh - Complete verification checklist

echo "=== 1. Service Status ==="
systemctl status ollama --no-pager || echo "FAIL: Service not running"

echo -e "\n=== 2. API Availability ==="
curl -s http://localhost:11434/ || echo "FAIL: API not responding"

echo -e "\n=== 3. GPU Detection ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || echo "FAIL: nvidia-smi failed"

echo -e "\n=== 4. Ollama GPU Logs ==="
journalctl -u ollama --no-pager | grep -i "inference compute" | tail -1 || echo "WARN: No GPU inference log found"

echo -e "\n=== 5. Model List ==="
ollama list || echo "FAIL: Cannot list models"

echo -e "\n=== 6. Generation Test ==="
ollama run qwen2.5-coder:7b "Say 'GPU test passed'" --verbose 2>&1 | grep -E "(eval_rate|100% GPU)" || echo "CHECK: Verify GPU usage"

echo -e "\n=== 7. Running Models ==="
ollama ps || echo "FAIL: Cannot check running models"

echo -e "\n=== Verification Complete ==="
```

### Performance benchmarking

**Quick benchmark with timing:**
```bash
ollama run qwen2.5-coder:7b --verbose "Write a function to calculate fibonacci numbers in Go"
```

**Key metrics from verbose output:**
- `prompt_eval_rate`: Input processing speed (expect 100-500 tok/s)
- `eval_rate`: **Generation speed** (expect 40-60 tok/s for 7B on RTX 3060)

**Benchmark reference for RTX 3060 12GB:**
| Model | Expected eval_rate |
|-------|-------------------|
| 3-4B models | 80-100+ tok/s |
| 7-8B Q4_K_M | 40-60 tok/s |
| 14B Q4_K_M | 15-30 tok/s |
| 14B Q3_K_M | 20-35 tok/s |

### Common issues and solutions

**Problem: GPU not detected (shows 100% CPU in `ollama ps`)**
```bash
# Check driver
nvidia-smi

# Reload NVIDIA UVM driver
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm

# Restart Ollama
sudo systemctl restart ollama
```

**Problem: Out of memory errors**
```bash
# Use smaller model or reduce context
# In Modelfile: PARAMETER num_ctx 4096

# Enable KV cache quantization
export OLLAMA_KV_CACHE_TYPE=q8_0
```

**Problem: Slow performance (< 10 tok/s on GPU)**
```bash
# Check if model spilling to CPU
ollama ps  # Look for "CPU/GPU" split

# Solution: Use smaller model or reduce context
ollama run qwen2.5-coder:7b  # Instead of 14b
```

**Problem: WSL2 GPU not detected**
```bash
# Verify Windows driver (not Linux driver) is installed
nvidia-smi  # Should work in WSL2

# Ensure systemd is enabled in /etc/wsl.conf
cat /etc/wsl.conf  # Should have [boot] systemd=true

# Restart WSL from PowerShell
wsl --shutdown
```

### Health check for automated monitoring

```bash
#!/bin/bash
# ollama-health.sh - For cron or monitoring systems

OLLAMA_URL="http://localhost:11434"

# Check API responds
if ! curl -sf "${OLLAMA_URL}/api/tags" > /dev/null; then
    echo "CRITICAL: Ollama API not responding"
    exit 2
fi

# Check a model is available
MODEL_COUNT=$(curl -sf "${OLLAMA_URL}/api/tags" | jq '.models | length')
if [ "$MODEL_COUNT" -eq 0 ]; then
    echo "WARNING: No models installed"
    exit 1
fi

echo "OK: Ollama healthy, ${MODEL_COUNT} models available"
exit 0
```

**Docker Compose health check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-sf", "http://localhost:11434/api/tags"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

---

## Design recommendations summary

### When to use each deployment approach

| Scenario | Recommendation |
|----------|----------------|
| Personal dev machine | Native install + shell script automation |
| Team shared server | Docker Compose with GPU passthrough |
| CI/CD testing | Docker Compose (CPU-only acceptable for integration tests) |
| Multi-machine deployment | Ansible + Docker Compose |
| Cloud GPU instances | Terraform for infra + Docker Compose for Ollama |

### Storage strategy

For a backend architect's workflow with 32GB RAM and 12GB VRAM:

1. **Primary storage**: Local SSD for active models (~50-100GB allocated)
2. **Model selection**: Keep 2-3 models installed (coding model + embedding model)
3. **Backup**: rsync to NAS weekly, or Docker volume export
4. **Portability**: Git repository with Modelfiles + docker-compose.yml + setup script

### Recommended daily workflow

```bash
# Start of day - verify everything works
ollama ps  # Check if model already loaded
nvidia-smi  # Verify GPU available

# If needed, pull latest model
ollama pull qwen2.5-coder:7b

# Use Continue extension in VS Code for coding assistance
# Or direct API for scripts/automation

# End of day - optional cleanup
ollama stop qwen2.5-coder:7b  # Free VRAM for gaming/other tasks
```

### Quick reference card

```bash
# Installation
curl -fsSL https://ollama.com/install.sh | sh

# Essential model
ollama pull qwen2.5-coder:7b

# Verify GPU
ollama ps  # Should show "100% GPU"

# API test
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"Hello","stream":false}'

# Enable flash attention (add to systemd)
Environment="OLLAMA_FLASH_ATTENTION=1"

# Expose to network (add to systemd)
Environment="OLLAMA_HOST=0.0.0.0:11434"

# Restart after config changes
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

This configuration delivers **40-60 tokens/second** generation speed with Qwen2.5-Coder 7B—fast enough for real-time coding assistance while maintaining full context windows for complex refactoring tasks. The Docker Compose approach ensures reproducibility across WSL2, native Linux, and cloud deployments without the overhead of full infrastructure-as-code tooling.