# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ WORKFLOW RULES (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** - Always wait for explicit user permission before moving to a new phase
2. **Step-by-step configuration** - When creating configuration files, do NOT create full files at once. Instead, build incrementally, explaining each setting as it's added
3. **Explanatory mode active** - Use "Explanatory" output style. Explain each step like a practical tutorial.

## Troubleshooting Approach

When diagnosing issues:
1. **Ask what's been tried** before suggesting solutions — do not repeat basic steps the user may have already completed
2. **Check prior context** — read session logs and handoff files for previous diagnostic work on the same issue
3. **Propose before executing** — for diagnostic commands that might have side effects, explain the intent first

## Environment Context

This project runs across a **Windows + WSL2 + Git Bash (MINGW)** stack:

- **Claude Code runs in:** Git Bash (MINGW64) on Windows
- **Ollama/Docker run in:** WSL2 (Ubuntu-22.04)
- **Linux commands must use:** `wsl -d Ubuntu-22.04 -- bash -c "..."` — direct `bash` invocations hit MINGW, not WSL
- **Path mangling:** Git Bash rewrites Linux-style paths (e.g., `/mnt/i/` → `C:/Program Files/Git/mnt/i/`). Always wrap in `wsl -- bash -c` to avoid this.
- **sudo commands:** Cannot run through Claude Code (no password prompt support). Ask the user to run them in their WSL terminal.
- **Shell confirmation:** When uncertain which shell a command targets, ask before executing.

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

## Git Operations

### Safety Protocol
For any destructive git operation (deleting `.git` files, rewriting history, force pushing):
1. **Explain** what the command will do and get explicit user approval BEFORE running
2. **Backup first** — create a safety branch: `git branch safety-backup-$(date +%s)`
3. **Dry-run** when available (e.g., `--dry-run`, `--no-act`) and show output before executing
4. **Verify** after each operation: `git fsck --full` and `git log --oneline -5`
5. **If verification fails** — stop and restore from backup, do not attempt to fix forward

Double-check remote URLs before any push. Never delete `.git` directory contents without a backup.

### Worktrees for Parallel Work
When multiple agents or tasks need to work on different branches simultaneously, use `git worktree` instead of switching branches:
```bash
git worktree add ../llm-feature-branch feature-branch
git worktree add ../llm-experiment experiment-branch
```
Each worktree is an isolated checkout sharing the same `.git` object store. Prefer worktrees over branch switching when doing parallel agent work, evaluation comparisons, or any workflow where multiple branches need to be checked out at once.

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

## Next Steps (Plan v2)

A 10-layer plan for building local AI infrastructure has been drafted. See:
- **Vision & goals:** `docs/vision-and-intent.md`
- **Execution plan:** `.claude/plan-v2.md` (layers, tasks, dependencies)
- **Model strategy:** `docs/model-strategy.md` (multi-model inventory, VRAM budgets)
- **Quality techniques:** `docs/closing-the-gap.md` (principles + tasks, integrated into plan)

Start with Layer 0 (foundation upgrades: Qwen3-8B, structured prompts, benchmarks).

## Resuming Multi-Session Work

This project uses a session tracking system for continuity across Claude Code sessions.

**On session start:**
1. Read `.claude/session-context.md` for user preferences and current status
2. Check `.claude/tasks.md` for progress
3. Review `.claude/session-log.md` for recent decisions
4. Review `.claude/plan-v2.md` for the current execution roadmap

**Sensitive data:** Hardware details and local paths are stored in `.claude/local/` (gitignored). Reference these when needed but don't commit them.
