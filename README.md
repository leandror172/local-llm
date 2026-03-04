# Local LLM Infrastructure

A layered AI infrastructure built on consumer GPU hardware (RTX 3060 12GB), combining
local model inference, a custom MCP server, specialized model personas, and a benchmark
framework — all designed to run production-quality AI workflows without cloud API costs.

## Motivation

Running LLMs locally for development has compounding advantages:

- **Privacy** — Code and prompts never leave the machine
- **Cost** — No API fees for experimentation and iteration
- **Specialization** — Right model for the right task, not one model for everything
- **Training data** — Every local model call generates labeled examples for future fine-tuning

The deeper goal is a system that **improves itself through usage**: local models generate
output, a human verdict (ACCEPTED / IMPROVED / REJECTED) is recorded alongside it, and
that labeled data feeds a future fine-tuning pipeline to narrow the gap between local
and frontier model quality over time.

---

## Architecture: 10-Layer Plan

The infrastructure is built in layers, each unlocking the next:

| Layer | Goal | Status |
|-------|------|--------|
| 0 | Foundation: empirical baselines (quantization, prompting, structured output) | ✅ Complete |
| 1 | MCP server: expose local models as tools inside Claude Code | ✅ Complete |
| 2 | Local-first CLI: Aider + alternatives evaluated against local Ollama | ✅ Complete |
| 3 | Persona creator: build, test, and register specialized model personas | ✅ Complete |
| 4 | Evaluator: benchmark framework, rubrics, automated code validators | ✅ Complete |
| 5 | Application: expense classifier using local models, with auto-insert | 🔄 Active |
| 6 | Chat interface: Telegram/WhatsApp routing to local or frontier | ⏳ Planned |
| 7 | Fine-tuning pipeline: DPO/SFT on accumulated ACCEPTED/IMPROVED/REJECTED logs | ⏳ Planned |
| 8 | Multi-agent orchestration: architect persona recruits specialist sub-agents | ⏳ Planned |
| 9 | Idle-time runner: autonomous self-improvement during GPU downtime | ⏳ Planned |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Runtime** | WSL2 (Ubuntu 22.04) | Linux environment with GPU passthrough |
| **Inference engine** | Ollama 0.17.5 | Model serving, persona management |
| **Models** | Qwen3.5/Qwen3/Qwen2.5-Coder family | See model lineup below |
| **MCP server** | Python / FastMCP | Exposes local models as Claude Code tools |
| **Persona system** | Modelfiles + registry.yaml | 35+ specialized model configurations |
| **Benchmark framework** | Python + bash + Puppeteer | Rubric-based multi-model evaluation |
| **Containerization** | Docker Compose | Portable deployment (planned primary path for agentic tooling) |
| **GPU** | NVIDIA RTX 3060 12GB | CUDA-accelerated inference, Flash Attention |

### Model Lineup

| Model | Size | VRAM profile | Primary use |
|-------|------|--------------|-------------|
| qwen3.5:9b | 6.6 GB | VRAM-only | Fast generation, classification |
| qwen3.5:27b | 17 GB | 12GB VRAM + 5GB RAM | Dense general-purpose |
| qwen3-coder:30b | 19 GB | 12GB VRAM + 7GB RAM | Agentic coding, 256K ctx, tool calling |
| qwen2.5-coder:14b | 9.0 GB | VRAM-only | Go/Java codegen (proven baseline) |
| qwen3:14b | 9.3 GB | VRAM-only | Architecture reasoning |
| qwen3:30b-a3b | 18 GB | 12GB VRAM + 7GB RAM | Quality ceiling reference |

---

## Performance

Measured on RTX 3060 12GB with Flash Attention enabled. Performance varies significantly
by model size — choose based on task complexity, not raw speed.

| Model tier | Token generation | VRAM usage | Context window | Notes |
|------------|-----------------|------------|----------------|-------|
| 7–9B (e.g. qwen3.5:9b) | 51–67 tok/s | 6–8 GB | 16–32K | Fully in VRAM |
| 14B (e.g. qwen2.5-coder:14b) | ~32 tok/s | 9–10 GB | 10–16K | Fully in VRAM |
| 30B MoE (e.g. qwen3-coder:30b) | ~10–20 tok/s | 12GB VRAM + 7GB RAM | 32K (up to 256K) | Hybrid; known Ollama MoE GPU utilization issue |

> Qwen3 models with `think: true` use 5–17× more tokens for hidden reasoning.
> Default is `think: false` (top-level API parameter — not inside `options{}`).

---

## Project Structure

```
├── modelfiles/                    # Ollama Modelfiles for all 35+ personas
│   ├── go-qwen3coder.Modelfile    # Go 1.22+ on qwen3-coder:30b (agentic, 32K ctx)
│   ├── classifier-qwen35.Modelfile
│   └── ...                        # One file per persona
│
├── personas/                      # Persona tooling
│   ├── registry.yaml              # Source of truth for all active personas
│   ├── create-persona.py          # Conversational persona creator CLI
│   ├── detect-persona.py          # Heuristic codebase analyzer (no LLM calls)
│   └── build-persona.py           # LLM-assisted persona designer
│
├── benchmarks/                    # Evaluation framework
│   ├── prompts/                   # Benchmark prompt sets (Go, Python, Java, shell)
│   ├── lib/                       # Runners, validators, comparison tools
│   └── results/                   # Benchmark output (gitignored)
│
├── mcp-server/                    # MCP server (Python/FastMCP)
│   └── src/ollama_mcp/            # Tools: generate_code, classify, summarize, etc.
│
├── docs/
│   ├── vision-and-intent.md       # Full project philosophy
│   ├── plan-v2.md                 # Detailed 10-layer plan
│   ├── findings/                  # Layer-by-layer empirical findings
│   └── scaffolding-template.md    # Reusable Claude Code project bootstrap guide
│
├── scripts/                       # Setup and verification scripts
└── docker/                        # Docker Compose deployment (planned for agentic tooling)
```

---

## Quick Start

### 1. Prerequisites

- Windows 10/11 with WSL2 enabled
- NVIDIA GPU with 12GB+ VRAM
- NVIDIA driver 545+ (for WSL2 GPU support)

### 2. Install Ollama and pull a model

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Pull a starting model (fits fully in 12GB VRAM)
ollama pull qwen3.5:9b
```

### 3. Create a persona and test it

```bash
ollama create my-go-q35 -f modelfiles/go-qwen35.Modelfile
ollama run my-go-q35 "Write a Go function that reads a CSV file"
```

### 4. Start the MCP server (the interesting part)

The MCP server exposes local models as tools inside Claude Code. Once configured,
Claude can delegate code generation, classification, and summarization to local models
during any session.

```bash
# Install dependencies
cd mcp-server && pip install -e .

# Add to Claude Code (system-wide)
# ~/.claude/.mcp.json — see mcp-server/README.md for config
```

From a Claude Code session, you can then call:
```
mcp__ollama-bridge__generate_code(prompt="...", language="go", model="my-go-qcoder")
```

### 5. Verify GPU is being used

```bash
nvidia-smi              # Should show memory allocated
ollama ps               # Should show model with GPU %
```

---

## Technical Highlights

### MCP Integration (Pattern B: Frontier Delegates to Local)
The MCP server implements "Pattern B" routing: Claude Code (frontier) decides what to
offload, calls a local Ollama model via tool use, and gets the result back in context.
This means local models augment — rather than replace — the frontier model, with the
frontier handling orchestration and quality evaluation.

### Two-Camp Agent Architecture (Empirical Finding)
After testing 5 local agent frameworks (Aider, OpenCode, Qwen Code, Goose, Claude Code),
a clear architectural split emerged:
- **Text-format agents** (Aider): diff-based editing, reliable at 7–8B
- **Tool-calling agents** (OpenCode, Goose): require structured JSON invocations —
  fail systemically at 7–8B, only reliable at 30B+

This is why the MCP server uses FastMCP (text/Python, not JSON tool schemas passed to
small models) and why `qwen3-coder:30b` is the first viable local tool-calling model
on this hardware.

### ACCEPTED / IMPROVED / REJECTED Pipeline
Every local model call during development is evaluated and labeled:
- **ACCEPTED** — used as-is → positive training example
- **IMPROVED** — used with modifications → (prompt, local, corrected) triple
- **REJECTED** + reason → negative example with failure mode label

This is DPO training data collection by design, not retrofit. Target: 500+ labeled
examples for Layer 7 QLoRA fine-tuning.

### Persona System
35+ Modelfiles configure specialized behaviors: temperature (0.1 for classification,
0.3 for code generation, 0.7 for creative tasks), context window, stop sequences, and
ROLE/CONSTRAINTS/FORMAT system prompts. A heuristic codebase analyzer (`detect-persona.py`)
scores a repo on three signals (file extensions 50%, imports 30%, config files 20%)
and recommends the top-3 matching personas — no LLM calls, fully deterministic.

### WSL2 GPU Passthrough
WSL2 exposes the Windows NVIDIA driver's `libcuda.so` directly into the Linux environment
via a paravirtualized GPU architecture. Key constraints: never install Linux NVIDIA
drivers in WSL2 (breaks the Windows driver bridge), use `/usr/lib/wsl/lib/` CUDA paths.

### Memory-Optimized Configuration
With 12GB VRAM as the constraint:
- **Q4_K_M quantization**: 4-bit weights, ~75% memory reduction, minimal quality loss
- **Flash Attention** (`OLLAMA_FLASH_ATTENTION=1`): ~30% VRAM reduction for attention
- **Hybrid offload**: 30B MoE models split across VRAM + system RAM (~19GB total)
- **`num_ctx` tuning**: KV cache grows linearly with context length; 10240 chosen for
  14B models as balance between context and VRAM pressure

---

## Example Application: Expense Classifier (Layer 5)

The expense classifier is an end-to-end example of the infrastructure in action. A Go
CLI (`expense-reporter`) uses local Ollama models to classify Brazilian expenses by
category, then auto-inserts high-confidence results into an Excel workbook.

Two things make this example notable:

1. **Infrastructure usage**: The classifier calls Ollama's `/api/chat` with a JSON Schema
   `format` parameter (structured output — 100% reliable, no speed penalty), using the
   `my-classifier-qcoder` persona (qwen3-coder:30b, 32K context) for few-shot injection.

2. **Infrastructure creation**: The Go CLI itself was partially built using the local model
   system — Cobra command scaffolding generated by `my-go-q25c14` (qwen2.5-coder:14b),
   evaluated, and integrated. The repo uses the same `.claude/` scaffolding template
   from this project, making session continuity, ref-based documentation, and persona
   selection consistent across both codebases.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Inference engine | Ollama over llama.cpp | Better UX, built-in model management, OpenAI-compatible API |
| MCP server language | Python / FastMCP | Lowest friction, best ecosystem; avoids tool-calling requirements on local models |
| Model family | Qwen3.5 / Qwen3 / Qwen2.5-Coder | Best code quality per VRAM at each size tier |
| Quantization | Q4_K_M default | Best quality/memory ratio; Q8 available for comparison |
| Agent approach | Text-format (Aider) over tool-calling | Tool-calling fails at 7–8B; text-format reliable |
| Model selection | Role-based (right model per task) | Reviewer at temp=0.1, coder at 0.3, classifier at 0.1 |
| Environment | WSL2 over native Windows | Linux tooling, systemd, better Docker integration |
| Docker | Maintained, not primary | Native for performance; Docker planned as primary for agentic tools |
| `think` mode | `think: false` default | Top-level payload param (not inside `options{}`); reduces tokens 5–17× |

---

## References

- [Ollama Documentation](https://ollama.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [WSL2 GPU Support](https://docs.nvidia.com/cuda/wsl-user-guide/)
- [Qwen3 Model Family](https://huggingface.co/Qwen)
- [FastMCP](https://github.com/jlowin/fastmcp)

---

*Built and maintained using [Claude Code](https://claude.ai/code).*
