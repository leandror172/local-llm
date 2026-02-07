# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ WORKFLOW RULES (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** - Always wait for explicit user permission before moving to a new phase
2. **Step-by-step configuration** - When creating configuration files, do NOT create full files at once. Instead, build incrementally, explaining each setting as it's added
3. **Explanatory mode active** - Use "Explanatory" output style. Explain each step like a practical tutorial.

## Repository Purpose

Research, documentation, and **portable configuration artifacts** for running local LLMs on an RTX 3060 12GB GPU. Contains both setup guides and executable scripts/configs for deploying Ollama with Qwen2.5-Coder.

## Repository Structure

```
├── .claude/                         # Session tracking & agent context
│   ├── plan.md                      # Master implementation plan
│   ├── tasks.md                     # Current progress checklist
│   ├── session-context.md           # Agent handoff instructions
│   ├── session-log.md               # Detailed session history
│   ├── session-handoff-*.md         # Detailed handoff docs per session
│   └── local/                       # Sensitive data (gitignored)
│       └── hardware-inventory.md    # Hardware specs
├── modelfiles/
│   └── coding-assistant.Modelfile   # Custom model: my-coder (Java/Go backend)
├── scripts/
│   ├── setup-ollama.sh              # Idempotent native installation
│   └── verify-installation.sh       # 14-check verification suite
├── docker/
│   ├── docker-compose.yml           # Portable Docker GPU config
│   └── init-docker.sh               # Docker initialization
├── docs/
│   ├── closing-the-gap.md           # Guide: local 7B vs frontier model quality
│   ├── model-comparison-hello-world.md  # Benchmark: Qwen 7B vs Claude Opus
│   ├── modelfile-reference.md       # Configuration rationale for all settings
│   ├── sampling-parameters.md       # Educational: temperature & top-p
│   └── sampling-temperature-top-p.png   # Visual sampling distribution chart
├── local-llm_and_open-claw.md      # Research: LLM engines, OpenClaw, WSL2 setup
├── llm-configuration-research.md    # Research: Ollama config, Docker, portability
└── verification-report.md           # Hardware/software verification results
```

## Quick Start

**Native (WSL2/Linux):**
```bash
./scripts/setup-ollama.sh
./scripts/verify-installation.sh
```

**Docker (portable):**
```bash
cd docker && ./init-docker.sh
```

**API endpoint:** `http://localhost:11434`

## Key Technical Decisions

- **Inference Engine**: Ollama (CLI-first, OpenAI-compatible API)
- **Primary Model**: Qwen2.5-Coder-7B Q4_K_M (~4.7GB on disk, ~6.3GB VRAM with 16K ctx)
- **Custom Model**: `my-coder` — Java/Go backend expert (temp 0.3, 16K context)
- **Environment**: WSL2 primary, Docker Compose for portability
- **Measured Performance**: 63-67 tok/s native, 64 tok/s Docker (target was 40-60)

## Important Constraints

- 12GB VRAM = use 7B models for optimal context window; 14B fits but limits context to ~4K
- **Never install Linux NVIDIA drivers in WSL2** — uses Windows driver's `libcuda.so`
- Flash Attention enabled (`OLLAMA_FLASH_ATTENTION=1`) saves ~30% VRAM
- Port 11434 must be available; check with `ss -tlnp | grep 11434`
- Native Ollama and Docker Ollama **cannot run simultaneously** (port conflict)
- Git Bash mangles Linux paths — use `wsl -- bash -c "..."` to avoid `/mnt/` rewriting
- Use API (`/api/chat`, `stream: false`) not CLI (`ollama run`) for programmatic access

## Verification Commands

```bash
# Automated (recommended)
./scripts/verify-installation.sh    # 14 checks: GPU, service, models, API, benchmark

# Manual spot checks
nvidia-smi                          # GPU visible? Need driver 545+
ollama ps                           # Shows "100% GPU"? Good
curl -s http://localhost:11434/     # "Ollama is running"

# Performance check (use API, not CLI, for clean output)
curl -s http://localhost:11434/api/chat -d '{
  "model": "my-coder",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{d[\"eval_count\"]/d[\"eval_duration\"]*1e9:.1f} tok/s')"
```

## Project Status

All 6 phases complete:

| Phase | Status | Highlights |
|-------|--------|------------|
| 0. Verification | Done | GPU passthrough, WSL2 kernel, driver 591.74 |
| 1. WSL2 Setup | Done | systemd enabled by default, CUDA toolkit skipped |
| 2. Ollama Install | Done | v0.15.4, 67 tok/s on first test |
| 3. Configuration | Done | Modelfile, my-coder, systemd override, setup script |
| 4. Docker | Done | Docker CE 29.2.1, NVIDIA Container Toolkit, 64 tok/s |
| 5. Verification | Done | 14/14 automated checks pass |
| 6. Documentation | Done | This file, final directory structure verified |

## Resuming Multi-Session Work

This project uses a session tracking system for continuity across Claude Code sessions.

**On session start:**
1. Read `.claude/session-context.md` for user preferences and current status
2. Check `.claude/tasks.md` for progress
3. Review `.claude/session-log.md` for recent decisions

**Sensitive data:** Hardware details and local paths are stored in `.claude/local/` (gitignored). Reference these when needed but don't commit them.
