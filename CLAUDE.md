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
│   └── local/                       # Sensitive data (gitignored)
│       └── hardware-inventory.md    # Hardware specs
├── local-llm_and_open-claw.md      # Research: LLM engines, OpenClaw, WSL2 setup
├── llm-configuration-research.md    # Research: Ollama config, Docker, portability
├── verification-report.md           # Hardware/software verification results
├── modelfiles/
│   └── coding-assistant.Modelfile   # Custom model configuration
├── scripts/
│   ├── setup-ollama.sh              # Idempotent native installation
│   └── verify-installation.sh       # Verification checklist
└── docker/
    ├── docker-compose.yml           # Portable Docker GPU config
    └── init-docker.sh               # Docker initialization
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
- **Primary Model**: Qwen2.5-Coder-7B Q4_K_M (~6-7GB VRAM, 40-60 t/s)
- **Custom Model**: `my-coder` - optimized for Java/Go backend development
- **Environment**: WSL2 primary, Docker Compose for portability
- **Expected Performance**: 40-60 tokens/second on RTX 3060 12GB

## Important Constraints

- 12GB VRAM = use 7B models for optimal context window; 14B fits but reduces context
- **Never install Linux NVIDIA drivers in WSL2** - uses Windows driver's libcuda.so
- Flash Attention enabled (`OLLAMA_FLASH_ATTENTION=1`) saves ~30% VRAM
- Port 11434 must be available; check with `ss -tlnp | grep 11434`

## Verification Commands

```bash
nvidia-smi                    # GPU visible? Need driver 545+
ollama ps                     # Shows "100% GPU"? Good
ollama run my-coder --verbose # Check eval_rate: 40-60 tok/s expected
```

## Resuming Multi-Session Work

This project uses a session tracking system for continuity across Claude Code sessions.

**On session start:**
1. Read `.claude/session-context.md` for user preferences and current status
2. Check `.claude/tasks.md` for progress
3. Review `.claude/session-log.md` for recent decisions

**Sensitive data:** Hardware details and local paths are stored in `.claude/local/` (gitignored). Reference these when needed but don't commit them.
