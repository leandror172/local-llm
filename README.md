# Local LLM Development Environment

A production-ready setup for running large language models locally on consumer GPU hardware (NVIDIA RTX 3060 12GB), using WSL2 and Ollama. Includes both native and containerized deployment options.

## Motivation

Running LLMs locally offers significant advantages for development workflows:

- **Privacy** — Code and prompts never leave the machine
- **Cost** — No API fees for experimentation and iteration
- **Latency** — Sub-100ms response times for local inference
- **Customization** — Fine-tuned system prompts and model parameters

This project documents the complete setup process, from GPU passthrough configuration to optimized inference settings, creating a reproducible environment that can be deployed on similar hardware.

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Runtime** | WSL2 (Ubuntu 22.04) | Linux environment with GPU passthrough |
| **Inference Engine** | Ollama | Model serving with OpenAI-compatible API |
| **Model** | Qwen2.5-Coder 7B (Q4_K_M) | Code-focused LLM, 4-bit quantized |
| **Containerization** | Docker Compose | Portable deployment option |
| **GPU** | NVIDIA RTX 3060 12GB | CUDA-accelerated inference |

## Performance

Target metrics for RTX 3060 12GB with Qwen2.5-Coder 7B:

| Metric | Expected | Notes |
|--------|----------|-------|
| Token generation | 40-60 tok/s | With Flash Attention enabled |
| Prompt processing | 100-500 tok/s | Varies with prompt length |
| VRAM usage | ~6-7 GB | Q4_K_M quantization |
| Context window | 16K tokens | Configurable up to 32K |
| GPU utilization | 100% | Full offload, no CPU fallback |

## Quick Start

### Prerequisites
- Windows 10/11 with WSL2 enabled
- NVIDIA GPU with 12GB+ VRAM
- NVIDIA driver 545+ (for WSL2 GPU support)

### Native Installation (WSL2)
```bash
# Clone and run setup
git clone https://github.com/leandror172/llm.git
cd llm
./scripts/setup-ollama.sh
./scripts/verify-installation.sh
```

### Docker Installation
```bash
cd docker
./init-docker.sh
```

### Verify
```bash
# Check GPU is detected
nvidia-smi

# Check model is running on GPU
ollama ps  # Should show "100% GPU"

# Test generation
ollama run my-coder "Write a hello world in Go"
```

**API Endpoint:** `http://localhost:11434` (OpenAI-compatible)

## Project Structure

```
├── modelfiles/
│   └── coding-assistant.Modelfile   # Custom model with optimized parameters
├── scripts/
│   ├── setup-ollama.sh              # Idempotent installation script
│   └── verify-installation.sh       # Post-install verification
├── docker/
│   ├── docker-compose.yml           # GPU-enabled container config
│   └── init-docker.sh               # Container initialization
├── local-llm_and_open-claw.md       # Research: LLM engines comparison
├── llm-configuration-research.md    # Research: Configuration options
└── verification-report.md           # Hardware verification results
```

## Technical Highlights

### WSL2 GPU Passthrough
WSL2 uses a paravirtualized GPU architecture where the Windows NVIDIA driver exposes `libcuda.so` directly into the Linux environment. This required careful configuration:
- Ensuring `hypervisorlaunchtype=auto` in Windows boot config
- Verifying VT-x/AMD-V enabled at BIOS level
- Using WSL2-specific CUDA paths (`/usr/lib/wsl/lib/`)

### Memory-Optimized Configuration
With 12GB VRAM as the constraint, the configuration balances context window size against model quality:
- **Q4_K_M quantization**: 4-bit weights reduce memory ~75% with minimal quality loss
- **Flash Attention**: Reduces VRAM usage ~30% for attention computation
- **16K context**: Maximum practical window for 7B model on 12GB

### Portable Configuration
All configuration is externalized for reproducibility:
- Modelfiles define model parameters declaratively
- systemd overrides for service configuration
- Docker Compose for container orchestration
- Idempotent scripts that can re-run safely

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Inference engine | Ollama over llama.cpp | Better UX, built-in model management, OpenAI-compatible API |
| Model | Qwen2.5-Coder over CodeLlama | Superior benchmark performance for code tasks |
| Quantization | Q4_K_M over Q8 | Best quality/memory ratio for 12GB VRAM |
| Environment | WSL2 over native Windows | Linux tooling, systemd support, better Docker integration |
| Dual deployment | Native + Docker | Native for performance, Docker for portability |

## References

- [Ollama Documentation](https://ollama.com/)
- [WSL2 GPU Support](https://docs.nvidia.com/cuda/wsl-user-guide/)
- [Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-7B)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

---

*This environment was configured and documented using [Claude Code](https://claude.ai/code).*
