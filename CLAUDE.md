# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Reference Lookup Convention

Rules in this file may include `[ref:KEY]` tags pointing to detailed reference material.
**To look up:** `.claude/tools/ref-lookup.sh KEY` — prints the referenced section. Run with no args to list all keys.

## WORKFLOW RULES (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** - Always wait for explicit user permission
2. **Step-by-step configuration** - Build config files incrementally, explaining each setting
3. **Explanatory mode active** - Use "Explanatory" output style with Insight boxes

## Troubleshooting Approach

1. **Ask what's been tried** before suggesting solutions
2. **Check prior context** — read session logs and handoff files first
3. **Propose before executing** — explain intent for diagnostic commands with side effects

## Environment Context

- **Claude Code runs in:** WSL2 (Ubuntu-22.04) natively
- **Ollama/Docker run in:** WSL2 (Ubuntu-22.04)
- **sudo commands:** Cannot run through Claude Code. Ask the user.
- **API endpoint:** `http://localhost:11434` — use `/api/chat` with `stream: false`, not CLI
- **Port 11434:** Native and Docker Ollama cannot run simultaneously

## Repository Purpose

Local AI infrastructure on RTX 3060 12GB: multiple specialized models, benchmarking, MCP integration with Claude Code, agent personas.

## Key Technical Facts

- **12GB VRAM** — 7-8B models for full context; 14B fits but ~4K context limit [ref:model-selection]
- **Never install Linux NVIDIA drivers in WSL2** — uses Windows driver's `libcuda.so`
- **Flash Attention** enabled (`OLLAMA_FLASH_ATTENTION=1`)
- **Models:** Qwen2.5-Coder-7B, Qwen3-8B, Qwen3-14B, Qwen3-4B, Llama3.1, DeepSeek variants [ref:personas]
- **Performance:** 63-67 tok/s (Qwen2.5-7B), 51-56 tok/s (Qwen3-8B), 32 tok/s (Qwen3-14B)
- **Qwen3 thinking:** Use API `think: false` (default off; `/no_think` doesn't work) [ref:thinking-mode]
- **Structured output:** Always use `format` param for JSON — 100% reliable, no speed penalty [ref:structured-output]
- **Benchmarks:** Always invoke via bash wrappers (`lib/run-*.sh`), never `python3` directly [ref:bash-wrappers]

## Git Safety Protocol

For destructive git operations: explain → backup → dry-run → execute → verify. [ref:git-safety]
Use `git worktree` for parallel branch work. [ref:git-worktrees]

## Resuming Multi-Session Work

**On session start:** read `.claude/session-context.md` (preferences + status), then `.claude/tasks.md` (progress).
**Knowledge index:** `.claude/index.md` maps every topic to its file location.
**Sensitive data:** `.claude/local/` (gitignored).

## Current Status

- **Phases 0-6:** Complete (archived → `.claude/archive/phases-0-6.md`)
- **Layer 0:** Complete — 12/12 tasks (findings → `.claude/archive/layer-0-findings.md`)
- **Active:** Layer 1 — MCP Server (Ollama as Claude Code tool)
- **Full roadmap:** `.claude/plan-v2.md` (10 layers)
