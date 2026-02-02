# Running local LLMs on RTX 3060 12GB: A comprehensive guide for backend engineers

**Your RTX 3060 12GB is an excellent local LLM platform** capable of running 7B-14B parameter coding models at 35-80 tokens/second—fast enough for real-time code completion. Combined with OpenClaw's autonomous agent capabilities and WSL2's seamless CUDA support, you can build a powerful local development assistant that rivals cloud services while maintaining privacy and reducing costs. This guide provides the complete implementation roadmap.

## Inference engines: Ollama wins for developer integration

The local LLM ecosystem has matured significantly, with five primary engines competing for attention. For a backend engineer integrating LLMs into development workflows, **Ollama emerges as the clear winner** due to its CLI-first design, OpenAI-compatible REST API, and minimal resource footprint.

**Ollama** delivers the best developer experience with two-command setup (`ollama pull`, `ollama run`) and native Windows support. Its REST API at `localhost:11434` integrates seamlessly with tooling, making it ideal for programmatic access from Java or Go applications. Benchmarks show **38-45 tokens/second** for 8B models on RTX 3060 12GB with GGUF Q4_K_M quantization.

**LM Studio** offers an excellent GUI for model experimentation with one-click Hugging Face downloads and visual controls for context size and GPU layers. Some benchmarks show it achieving **237 t/s vs Ollama's 149 t/s** on specific hardware (Mac M3), though Windows performance is comparable between engines. Best for beginners or when you want to visually experiment before committing to a model.

**text-generation-webui** (oobabooga) provides the richest feature set including multiple backend support (llama.cpp, ExLlamaV2, TensorRT-LLM), extension ecosystem for PDF/image handling, and built-in LoRA fine-tuning. The one-click Windows installer makes setup straightforward, but the complexity may be overkill for pure coding assistance.

**llama.cpp direct** offers maximum performance and control—the ability to quantize models yourself, fine-tune CPU/GPU layer offloading, and access bleeding-edge optimizations. Requires Visual Studio Build Tools compilation on Windows, making it better suited for power users willing to invest setup time.

### Quantization formats and your 12GB VRAM constraint

Understanding quantization is essential for maximizing your VRAM. **GGUF** (GGML Unified Format) is the dominant format for consumer hardware, supporting CPU+GPU hybrid offloading that's perfect for VRAM-limited cards.

| Format | Best Use Case | 12GB VRAM Fit | Speed |
|--------|---------------|---------------|-------|
| **GGUF Q4_K_M** | Balance of quality/size | 7B: excellent, 13B: good | Best overall |
| **GGUF Q5_K_M** | Quality priority | 7B: excellent, 13B: tight | Slightly slower |
| **GPTQ 4-bit** | Maximum speed (with Marlin) | GPU-only, similar sizes | 1.5x faster than FP16 |
| **EXL2 4bpw** | Mixed-precision flexibility | Most flexible sizing | Fastest inference |
| **AWQ 4-bit** | Accuracy-sensitive tasks | Similar to GPTQ | Moderate |

**Q4_K_M is the sweet spot** for your RTX 3060—a 7B model uses ~6-7GB VRAM with excellent quality retention, leaving headroom for context and system overhead. For 13B-14B models, Q4_K_M uses ~8.5-11.5GB, fitting tightly but workably.

### Windows vs WSL2 performance verdict

Performance benchmarks show **virtually identical GPU inference speeds** between Windows native and WSL2 once CUDA is properly configured. LM Studio testing showed 102 t/s on Windows versus 100-118 t/s on WSL2 for the same model. The choice comes down to tooling preference rather than performance concerns. File I/O is significantly slower crossing the Windows↔Linux boundary (32 seconds vs 3 seconds for 1GB writes), but this doesn't affect inference once models are loaded.

## Coding models: Qwen2.5-Coder dominates the 12GB class

For a Java/Go backend engineer, model selection significantly impacts coding assistance quality. After analyzing benchmarks and 12GB VRAM constraints, **Qwen2.5-Coder-14B-Instruct at Q4_K_M quantization emerges as the optimal choice**.

### Top recommendation: Qwen2.5-Coder-14B

Qwen2.5-Coder achieves **88.4% on HumanEval** (7B version), trained on 5.5 trillion tokens with 70% code across 40+ languages including explicit Java and Go support. Its **128K native context window** is crucial for understanding multi-file codebases. At Q4_K_M quantization, it fits comfortably in 12GB (~8.5GB VRAM) while delivering **35-50 tokens/second**.

```bash
ollama run qwen2.5-coder:14b
```

For faster iteration during code completion, **Qwen2.5-Coder-7B at Q5_K_M** delivers **60-80 tokens/second** with minimal quality loss—excellent for real-time autocomplete scenarios.

### Alternative models worth considering

**DeepSeek-Coder-V2-Lite** uses Mixture-of-Experts architecture (16B total, 2.4B active), achieving 81.1% on HumanEval with 128K context. It fits in 12GB at Q5_K_M (~10.5GB) and delivers 25-35 t/s—slightly slower but excellent for complex reasoning tasks.

**StarCoder2-15B** excels at multi-language support (trained on 619 languages) and Fill-in-the-Middle completion, making it strong for code completion specifically. At Q4_K_M it uses ~9GB VRAM.

**CodeLlama-13B** remains solid but shows its 2023 age—HumanEval scores of ~55% lag significantly behind Qwen2.5-Coder's 88%.

### Java and Go specific insights

No models are specifically optimized for Java or Go, but Qwen2.5-Coder and StarCoder2 have strong training data representation from GitHub for both languages. The 128K context window in Qwen2.5-Coder and DeepSeek-Coder-V2-Lite is particularly valuable for understanding larger Java codebases with their typical verbose structure. For IDE integration, the **Continue** extension works well with Ollama backend in VS Code, while JetBrains IDEs (IntelliJ, GoLand) have native local AI support.

## OpenClaw setup: autonomous agents with local model fallback

OpenClaw (formerly Clawdbot/Moltbot) is an open-source autonomous AI assistant with **145,000+ GitHub stars** that can execute real-world tasks via messaging platforms. Its official Ollama integration makes it ideal for combining cloud API quality with local model cost savings.

### Installation and initial configuration

OpenClaw requires Node.js 22+ and installs via npm:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
openclaw channels login  # Shows WhatsApp QR code
openclaw gateway --port 18789
```

**Windows users must use WSL2**—native Windows is untested with known tool compatibility issues. Run Tailscale on the Windows host if needed for remote access, proxying to WSL2.

### Claude API integration for quality

For production-quality coding assistance, configure Anthropic's Claude API:

1. Create API key at Anthropic Console
2. During `openclaw onboard`, select "Anthropic API Key"
3. Recommended model: Claude Opus 4.5 for long-context tasks

Cost expectations: Light use ~$5-10/day, heavy use $30-50+/day. OpenClaw tracks usage automatically.

### Ollama integration for cost reduction

OpenClaw's official Ollama support enables local model fallback:

```bash
# Install and pull models
ollama pull qwen2.5-coder:14b
export OLLAMA_API_KEY="ollama-local"  # Any value works
```

OpenClaw auto-discovers models from `localhost:11434`. For explicit configuration or remote Ollama instances, edit `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4.5",
        "fallback": ["ollama/qwen2.5-coder:14b"]
      }
    }
  }
}
```

This configuration uses Claude as primary with automatic fallback to local Qwen during rate limits or for cost reduction.

### The SOUL.md persistence mechanism

SOUL.md is OpenClaw's unique "personality file"—a markdown document defining agent identity, preferences, and behavioral guidelines that persist across sessions. Located at `<workspace>/SOUL.md`, it provides continuity with phrases like "Each session, you wake up fresh. These files are your memory." Related files include `AGENTS.md` for configuration, `USER.md` for user information, and `MEMORY.md` for daily logs.

### Security: essential sandboxing for autonomous agents

OpenClaw requires significant system access including filesystem read/write, shell execution, and browser control. Three critical risk vectors demand attention:

- **Root risk**: Host compromise if agent misbehaves
- **Agency risk**: Unintended destructive actions
- **Keys risk**: Credential theft/leakage

**Docker sandboxing is strongly recommended** for any untrusted inputs:

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "non-main",
        "docker": {
          "image": "openclaw-sandbox-common:bookworm-slim"
        }
      }
    }
  }
}
```

Additional security practices: Never run as root, create dedicated workspace folders, set API spending limits at provider dashboards, enable `requireMention: true` in group chats, avoid exposing port 18789 directly to the internet, and consider running on separate hardware from your primary development machine. Prompt injection remains an unsolved industry-wide problem—malicious instructions in processed documents can potentially manipulate agent behavior.

## Linux GPU environments: WSL2 is the clear winner

For running Linux with CUDA access while keeping Windows 10 as your host OS, **WSL2 emerges as the only practical option** for consumer GPUs. The other approaches either don't work or require enterprise hardware.

### WSL2 with CUDA: production-ready and easy

WSL2's CUDA support has matured since 2020 and delivers **95-99% of native Linux performance** for ML workloads. Your RTX 3060 12GB is fully compatible (compute capability 8.6).

Setup is straightforward:
```bash
wsl --install
wsl --update
# Inside WSL: CUDA auto-detected via Windows driver
# Do NOT install Linux NVIDIA drivers
```

**Critical gotcha**: Never install Linux NVIDIA drivers in WSL2—the Windows driver provides the necessary `libcuda.so` stub. All major frameworks work: Ollama (excellent), llama.cpp (excellent), PyTorch, TensorFlow, and Docker with nvidia-container-toolkit.

For Docker GPU containers in WSL2:
```bash
sudo apt-get install nvidia-container-toolkit
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi
```

Keep project files in the Linux filesystem (`/home/user/`) rather than `/mnt/c/` for optimal I/O performance.

### VirtualBox and VMware: fundamentally unable to passthrough GPUs

**VirtualBox cannot do GPU passthrough** on consumer hardware—PCI passthrough was removed in version 6.1 and was Linux-host-only anyway. It only offers virtual SVGA with maximum 256MB emulated VRAM.

**VMware Workstation also lacks GPU passthrough**—only VMware ESXi (Type 1 hypervisor that replaces Windows) supports it, and even then consumer GPUs require specific passthrough configuration versus enterprise vGPU licensing.

### Hyper-V: requires Windows Server for real GPU access

Discrete Device Assignment (DDA) provides true GPU passthrough but requires **Windows Server edition**—not available on Windows 10/11 Pro/Home. GPU Partitioning (GPU-P) exists on desktop Windows but consumer GPUs including RTX 3060 don't support it.

### The Hyper-V and VirtualBox conflict

WSL2 requires Hyper-V components, which force VirtualBox into slow NEM (nested emulation) fallback mode—indicated by a green turtle icon. You can switch modes at boot via `bcdedit /set hypervisorlaunchtype off|auto`, but this requires reboots. Since VirtualBox can't do GPU passthrough anyway, this conflict is academic for your use case.

### When dual-boot makes sense

Dual-boot provides 100% native performance and full CUDA profiler/debugger access. Choose it if you need absolute maximum GPU performance, extended Linux-only sessions, or professional CUDA development tools. Use NTFS for shared data partitions (readable from both OSes). Otherwise, WSL2's convenience outweighs the marginal performance difference.

## Implementation path: start with quality, then optimize for cost

Given your setup (RTX 3060 12GB, 32GB RAM, Windows 10, Java/Go background), here's the recommended implementation sequence:

### Phase 1: Establish the foundation (Week 1)

Start with **WSL2 + Ollama + Qwen2.5-Coder-14B** to validate local inference works on your hardware:

```bash
# In WSL2
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:14b
ollama run qwen2.5-coder:14b "Write a Go function that implements rate limiting"
```

Confirm you're getting 35-50 t/s and acceptable quality. This costs nothing and establishes your local baseline.

### Phase 2: Add OpenClaw with Claude API (Week 2)

Install OpenClaw in WSL2 and configure it with your Anthropic API key. Start with Claude as the primary model to experience what high-quality autonomous assistance feels like:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

Use Claude Sonnet 4.5 for daily coding tasks, keeping initial daily spend under $10-15. Enable Docker sandboxing immediately—don't skip this step.

### Phase 3: Configure hybrid mode for cost optimization (Week 3+)

Once you understand OpenClaw's patterns and trust its operation, configure fallback to local models:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4.5",
        "fallback": ["ollama/qwen2.5-coder:14b"]
      }
    }
  }
}
```

This approach uses Claude for complex, long-context tasks where quality matters most, while local Qwen handles simpler completions and periods when you've hit rate limits. Expect **50-70% cost reduction** while maintaining quality for critical work.

### Why this order matters

Starting with local infrastructure first risks frustration—local models, while impressive, noticeably lag behind Claude for complex reasoning and multi-file refactoring. You might conclude the technology "isn't ready" when actually you're comparing against the wrong baseline.

Starting with OpenClaw + Claude establishes what's possible: genuine autonomous coding assistance that understands your codebase, follows complex instructions, and maintains context across sessions. The local fallback then becomes a cost optimization rather than a compromise—you know what you're trading off and can adjust the balance based on task complexity.

### Practical daily workflow

For routine development: Let OpenClaw with Claude handle complex refactoring, debugging, and architectural decisions. Use local Qwen2.5-Coder via Continue extension for real-time autocomplete in your IDE. Reserve cloud tokens for the ~20% of tasks where quality differential actually matters.

For experimentation: Run Ollama directly (`ollama run qwen2.5-coder:14b`) to test prompts before deploying them through OpenClaw. The 60-80 t/s with the 7B model enables rapid iteration.

Your 12GB VRAM is genuinely the sweet spot—large enough for 14B models that approach cloud quality, small enough that you're forced into quantization decisions that keep inference fast. Combined with 32GB system RAM for offloading edge cases, you have a capable local LLM development environment that will only improve as models get more efficient.