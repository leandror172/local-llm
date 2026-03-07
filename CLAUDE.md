# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Reference Lookup Convention

Rules in this file may include `[ref:KEY]` tags pointing to detailed reference material.
**To look up:** `.claude/tools/ref-lookup.sh KEY` — prints the referenced section. Run with no args to list all keys.

## WORKFLOW RULES (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** - Always wait for explicit user permission
2. **Step-by-step configuration** - Build config files incrementally, explaining each setting
3. **Explanatory mode active** - Use "Explanatory" output style with Insight boxes
4. **Licensing compliance** - When using or referencing external code/projects, always check and honor their license. If a license requires attribution, add it. Track attributions in `docs/ATTRIBUTIONS.md`.

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
- **Models (VRAM-only):** Qwen2.5-Coder-7B (4.7GB), Qwen3-4B-q8 (4.4GB), Qwen3-8B (5.2GB), Qwen3-8B-q8 (8.5GB), Qwen2.5-Coder-14B (9.0GB), Qwen3-14B (9.3GB), DeepSeek-R1-14B (9.0GB), DeepSeek-Coder-V2-16B (8.9GB) [ref:personas]
- **Models (hybrid VRAM+RAM):** Qwen3-30B-A3B (19GB MoE — 12GB VRAM + ~7GB RAM; expect ~10-20 tok/s, Ollama MoE offload has known perf issues)
- **Future candidates:** Qwen3.5-35B-A3B (24GB, released 2026-02-24, too new + tight memory fit); Qwen3-Coder-30B (19GB, code-specialized MoE, same size as 30B-A3B)
- **Performance:** 63-67 tok/s (Qwen2.5-7B), 51-56 tok/s (Qwen3-8B), 32 tok/s (Qwen3-14B), ~10-20 tok/s (Qwen3-30B-A3B hybrid est.)
- **Qwen3 thinking:** Use API `think: false` (default off; `/no_think` doesn't work) [ref:thinking-mode]
- **Structured output:** Always use `format` param for JSON — 100% reliable, no speed penalty [ref:structured-output]
- **Benchmarks:** Always invoke via bash wrappers (`lib/run-*.sh`), never `python3` directly [ref:bash-wrappers]

## Documentation Rules (HARD REQUIREMENTS)

When creating or modifying files:
1. **New scripts/tools** — add to `[ref:bash-wrappers]` in `.claude/index.md`
2. **New runtime-relevant doc sections** — wrap with `<!-- ref:KEY -->` / `<!-- /ref:KEY -->` blocks; one concept per block [ref:indexing-convention]
3. **New files of any kind** — add to `.claude/index.md` under the appropriate table
4. **§ vs ref:KEY** — use `ref:KEY` for content agents need at runtime; use `§ "Heading"` for background/archive navigation pointers [ref:indexing-convention]

## Git Safety Protocol

For destructive git operations: explain → backup → dry-run → execute → verify. [ref:git-safety]
Use `git worktree` for parallel branch work. [ref:git-worktrees]

## Resuming Multi-Session Work

**On session start:** run `.claude/tools/resume.sh` — outputs current status, next task, recent commits in ~40 lines.
For deeper context: `ref-lookup.sh active-decisions` | `ref-lookup.sh layer4-status` | `ref-lookup.sh bash-wrappers`
**Knowledge index:** `.claude/index.md` maps every topic to its file location. [ref:resume-steps]
**Sensitive data:** `.claude/local/` (gitignored).

## Local Model Usage (Layer 5+)

When working on Layer 5 (expense classifier) and beyond, **try local models first** for
code generation tasks. This generates training data for future distillation.

**Use `mcp__ollama-bridge__generate_code` or `mcp__ollama-bridge__ask_ollama` for:**
- Boilerplate Go code (structs, interfaces, simple functions, test stubs)
- Simple Python utilities and scripts
- Straightforward transformations (parsing, formatting, serialization)

**After receiving local model output, evaluate it explicitly:**
- `ACCEPTED` — used as-is (note the prompt that worked)
- `IMPROVED` — used with modifications (note what changed and why)
- `REJECTED` — not usable (note the failure reason: logic error / wrong API / off-task)

**On ACCEPTED or IMPROVED verdicts, add a rough token estimate — do NOT read files or write code to compute it:**
- Mentally apply `(chars in your prompt + chars in response) / 4` as a ballpark of what Claude would have spent
- Note it inline in one phrase, e.g.: `ACCEPTED — ~300 est. Claude tokens saved`
- Rough is fine; the log records exact values automatically (`claude_tokens_est`, `prompt_eval_count`, `eval_count`) for later analysis

**Do NOT use local models for:**
- Architectural decisions or multi-file reasoning
- Security-sensitive code
- Tasks requiring understanding of large context (>400 tokens of output needed)

Every call is automatically logged to `~/.local/share/ollama-bridge/calls.jsonl`
(prompt, response, model, latency). The (prompt, local_response, your_verdict) pattern
is the raw material for future DPO fine-tuning.

## Current Status

- **Layers 0-4:** Complete (archived in `.claude/archive/`). Full roadmap: `.claude/plan-v2.md` (10 layers).
- **Active layer:** See `ref-lookup.sh current-status` for live state.
